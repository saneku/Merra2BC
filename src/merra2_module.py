from . import config
import re
import os
import glob
from netCDF4 import Dataset
from datetime import datetime, timedelta
import numpy as np

from multiprocessing import Pool
from functools import partial

Ptop_mera=1 #Pa   (=0.01 hPa)
mera_lat=0
mera_lon=0

shifted_lons=False
shift_index=0

merra_files=[]
mera_times={}                           #map between time and index in file
mera_times_files={}                     #map between time and file index
merra_vars=[]
mer_number_of_x_points=0
mer_number_of_y_points=0
mer_number_of_z_points=0

_hor_grid_cache=None
_hor_bnd_cache=None

numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(os.path.basename(value))
    if len(parts) > 9:
        return parts[9]
    return os.path.basename(value)


def _extract_date_token(file_path):
    parts = numbers.split(os.path.basename(file_path))
    if len(parts) > 9 and len(parts[9]) == 8:
        return parts[9]

    match = re.search(r'(\d{8})', os.path.basename(file_path))
    if match:
        return match.group(1)

    raise ValueError("Could not extract YYYYMMDD date from file name: " + str(file_path))

def get_file_index_by_time(time):
    return mera_times_files.get(time)

def get_index_in_file_by_time(time):
    return mera_times.get(time)

def get_file_name_by_index(index):
    return os.path.basename(merra_files[index])


def get_file_path_by_index(index):
    return merra_files[index]



#********************************
def _build_axis_weights(source_axis, target_values):
    idx_hi = np.searchsorted(source_axis, target_values, side='right')
    idx_hi = np.clip(idx_hi, 1, len(source_axis) - 1)
    idx_lo = idx_hi - 1

    source_lo = source_axis[idx_lo]
    source_hi = source_axis[idx_hi]
    span = source_hi - source_lo

    frac = np.zeros(target_values.shape, dtype=np.float64)
    valid = span != 0
    frac[valid] = (target_values[valid] - source_lo[valid]) / span[valid]
    frac = np.clip(frac, 0.0, 1.0)

    return idx_lo, idx_hi, frac


def _build_bilinear_cache(target_lat, target_lon):
    flat_lat = np.asarray(target_lat, dtype=np.float64).reshape(-1)
    flat_lon = np.asarray(target_lon, dtype=np.float64).reshape(-1)

    lat_lo, lat_hi, lat_frac = _build_axis_weights(mera_lat, flat_lat)
    lon_lo, lon_hi, lon_frac = _build_axis_weights(mera_lon, flat_lon)

    return {
        "lat_ref": target_lat,
        "lon_ref": target_lon,
        "size": flat_lat.size,
        "lat_lo": lat_lo,
        "lat_hi": lat_hi,
        "lon_lo": lon_lo,
        "lon_hi": lon_hi,
        "w00": (1.0 - lat_frac) * (1.0 - lon_frac),
        "w10": lat_frac * (1.0 - lon_frac),
        "w01": (1.0 - lat_frac) * lon_frac,
        "w11": lat_frac * lon_frac,
    }


def _apply_bilinear_cache(field3d, cache):
    z_count = field3d.shape[0]
    out = np.empty((z_count, cache["size"]), dtype=field3d.dtype)

    lat_lo = cache["lat_lo"]
    lat_hi = cache["lat_hi"]
    lon_lo = cache["lon_lo"]
    lon_hi = cache["lon_hi"]
    w00 = cache["w00"]
    w10 = cache["w10"]
    w01 = cache["w01"]
    w11 = cache["w11"]

    for z_level in range(z_count):
        layer = field3d[z_level,:,:]
        out[z_level,:] = (
            layer[lat_lo, lon_lo] * w00
            + layer[lat_hi, lon_lo] * w10
            + layer[lat_lo, lon_hi] * w01
            + layer[lat_hi, lon_hi] * w11
        )

    return out


#Horizontal interpolation of 3d Merra field on WRF boundary
def hor_interpolate_3dfield_on_wrf_boubdary(FIELD, wrf_length, wrf_lon, wrf_lat):
    global _hor_bnd_cache

    if (_hor_bnd_cache is None) or (_hor_bnd_cache["lat_ref"] is not wrf_lat) or (_hor_bnd_cache["lon_ref"] is not wrf_lon):
        _hor_bnd_cache = _build_bilinear_cache(wrf_lat, wrf_lon)

    if _hor_bnd_cache["size"] != wrf_length:
        raise ValueError("WRF boundary size mismatch for horizontal interpolation cache.")

    return _apply_bilinear_cache(FIELD, _hor_bnd_cache)

#Vertical interpolation of Merra boundary on WRF boundary
def ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_nz, wrf_length):
    WRF_SPECIE_BND = np.zeros([wrf_nz,wrf_length])  # Required SPEC on WRF boundary
    for i in range(0,wrf_length):
        # np.interp expects an increasing coordinate. Vertical profiles here are top-down.
        src_pres = MER_HOR_PRES_BND[::-1,i]
        src_spec = MER_HOR_SPECIE_BND[::-1,i]
        # Use nearest-value extrapolation instead of zeros for levels outside MERRA pressure range.
        # This avoids artificial empty cells near the surface on finer WRF grids.
        WRF_SPECIE_BND[:,i]=np.interp(
            WRF_PRES_BND[:,i],
            src_pres,
            src_spec,
            left=src_spec[0],
            right=src_spec[-1],
        )
    return WRF_SPECIE_BND

#Horizontal interpolation of 3d Merra field on WRF horizontal grid
def hor_interpolate_3dfield_on_wrf_grid(FIELD, wrf_ny, wrf_nx, wrf_lon, wrf_lat):
    global _hor_grid_cache

    if (_hor_grid_cache is None) or (_hor_grid_cache["lat_ref"] is not wrf_lat) or (_hor_grid_cache["lon_ref"] is not wrf_lon):
        _hor_grid_cache = _build_bilinear_cache(wrf_lat, wrf_lon)

    if _hor_grid_cache["size"] != wrf_ny * wrf_nx:
        raise ValueError("WRF grid size mismatch for horizontal interpolation cache.")

    field_hor = _apply_bilinear_cache(FIELD, _hor_grid_cache)
    return field_hor.reshape(FIELD.shape[0], wrf_ny, wrf_nx)

#Vertical interpolation on WRF grid
def ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE, MER_HOR_PRES,WRF_PRES,wrf_nz, wrf_ny, wrf_nx):
    WRF_SPECIE = np.zeros([wrf_nz,wrf_ny,wrf_nx])  # Required SPEC on WRF grid
    for x in range(0,wrf_nx,1):
        for y in range(0,wrf_ny,1):
            src_pres = MER_HOR_PRES[::-1,y,x]
            src_spec = MER_HOR_SPECIE[::-1,y,x]
            WRF_SPECIE[:,y,x]=np.interp(
                WRF_PRES[:,y,x],
                src_pres,
                src_spec,
                left=src_spec[0],
                right=src_spec[-1],
            )
    return WRF_SPECIE
#********************************

#extracts 3d field from merra2 file from given time
def get_3dfield_by_time(time,merra_file,field_name):
    mera_time_idx=get_index_in_file_by_time(time)
    field=merra_file.variables[field_name][mera_time_idx,:]

    if shifted_lons:
        field=np.roll(field,shift_index,axis=2)

    return np.flipud(field)


def get_pressure_by_time(time,merra_file):
    global Ptop_mera
    #MER_Pres will be restored on 73 edges
    MER_Pres = np.zeros([mer_number_of_z_points+1,mer_number_of_y_points,mer_number_of_x_points])
    #filling top edge with Ptop_mera
    MER_Pres[0,:,:]=Ptop_mera

    # Extract deltaP from NetCDF file at index defined by time
    mera_time_idx=get_index_in_file_by_time(time)
    DELP = merra_file.variables['DELP'][mera_time_idx,:]  #Pa

    for z_level in range(mer_number_of_z_points):
        MER_Pres[z_level+1]=MER_Pres[z_level]+DELP[z_level]

    #BUT! we need pressure on 72 levels
    #=> averaging pressure values on adjacent edges
    MER_Pres = (MER_Pres[0:mer_number_of_z_points:1][:,:] + MER_Pres[1::1][:,:]) / 2

    if shifted_lons:
        MER_Pres=np.roll(MER_Pres,shift_index,axis=2)

    MER_Pres=np.flipud(MER_Pres)
    return MER_Pres



def initialise():
    global merra_files,mer_number_of_x_points,mer_number_of_y_points,mer_number_of_z_points,mera_lon,mera_lat,merra_vars,shifted_lons,shift_index,_hor_grid_cache,_hor_bnd_cache,mera_times,mera_times_files

    _hor_grid_cache=None
    _hor_bnd_cache=None
    mera_times.clear()
    mera_times_files.clear()

    merra_files=sorted(glob.glob(config.merra2_files), key=numericalSort)
    if not merra_files:
        raise FileNotFoundError(
            "No MERRA2 files matched mask: " + str(config.merra2_files)
        )

    merra_f = Dataset(merra_files[0],'r')
    mer_number_of_x_points=merra_f.variables['lon'].size
    mer_number_of_y_points=merra_f.variables['lat'].size
    #not all merra2 files (loading diagnostic) have 'lev' variable
    try:
        mer_number_of_z_points=merra_f.variables['lev'].size
    except Exception:
        pass

    print ("MERRA2 dimensions: [bottom_top]="+str(mer_number_of_z_points)+" [south_north]="+str(mer_number_of_y_points)+" [west_east]="+str(mer_number_of_x_points))

    merra_vars = [var for var in merra_f.variables]

    mera_lon  = merra_f.variables['lon'][:]
    mera_lat  = merra_f.variables['lat'][:]

    #if data is given in range of 0_360, then we need to shift lons and data to the -180_180
    if(max(mera_lon)>180):
        print ("###########################")
        print ("ATTENTION!!!:")
        print ("SHIFTING LONGITUDES")
        index=0
        for lon in mera_lon:
            if lon >180:
                mera_lon[index]=mera_lon[index]-360.0
            index=index+1
        shift_index=len(mera_lon)/2
        mera_lon=np.roll(mera_lon,shift_index)
        shifted_lons=True
        print ("###########################")

    print ("Lower left corner: lat="+str(min(mera_lat))+" long="+str(min(mera_lon)))
    print ("Upper right corner: lat="+str(max(mera_lat))+" long="+str(max(mera_lon)))

    # Number of times can differ by file; keep per-file values.
    times_per_file_by_file = [merra_f.variables['time'].size]
    merra_f.close()

    for merra_file in merra_files[1:]:
        check_f = Dataset(merra_file, 'r')
        cur_x = check_f.variables['lon'].size
        cur_y = check_f.variables['lat'].size

        if (cur_x != mer_number_of_x_points) or (cur_y != mer_number_of_y_points):
            check_f.close()
            raise ValueError(
                "Incompatible MERRA grids matched --merra2_files. "
                + "Reference grid is "
                + str(mer_number_of_y_points)
                + "x"
                + str(mer_number_of_x_points)
                + ", but "
                + os.path.basename(merra_file)
                + " is "
                + str(cur_y)
                + "x"
                + str(cur_x)
                + ". Use a single consistent collection/grid per run."
            )

        if 'lev' not in check_f.variables:
            check_f.close()
            raise ValueError(
                "Variable 'lev' is missing in " + os.path.basename(merra_file) + "."
            )
        cur_z = check_f.variables['lev'].size
        if cur_z != mer_number_of_z_points:
            check_f.close()
            raise ValueError(
                "Incompatible MERRA vertical levels matched --merra2_files. "
                + "Reference has "
                + str(mer_number_of_z_points)
                + " levels, but "
                + os.path.basename(merra_file)
                + " has "
                + str(cur_z)
                + "."
            )

        times_per_file_by_file.append(check_f.variables['time'].size)
        check_f.close()

    index=0
    for merra_file, times_per_file in zip(merra_files, times_per_file_by_file):
        date=_extract_date_token(merra_file)
        for i in range(0,times_per_file,1):
            t=datetime.strptime(date, '%Y%m%d')+timedelta(minutes =(i*(24/times_per_file)*60))
            time_key = t.strftime("%Y-%m-%d_%H:%M:%S")
            if time_key in mera_times_files:
                prev_index = mera_times_files.get(time_key)
                raise ValueError(
                    "Duplicate MERRA timestamp "
                    + time_key
                    + " found in both "
                    + os.path.basename(merra_files[prev_index])
                    + " and "
                    + os.path.basename(merra_file)
                    + ". Narrow --merra2_files (do not mix collections like aer/chm)."
                )

            mera_times_files.update({time_key:index})
            mera_times.update({time_key:i})
        index=index+1
