from . import config
import re
import os
import glob
from netCDF4 import Dataset
import numpy as np
import codecs

met_files=[]
met_times_files={}
wrf_times={}

dx=dy=true_lat1=true_lat2=0
cen_lat=0
cen_lon=0
projection=""

spec_number=0
nx=ny=nz=nw=0
wrf_p_top=0
znu=[]
xlon=[[]]
xlat=[[]]

wrf_vars=[]

#mapping for basemap projections
projections={"Lambert Conformal":"lcc","Mercator":"merc"}

wrf_bnd_lons=[]
wrf_bnd_lats=[]


def _normalize_wrf_time(time_text):
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})[:_](\d{2})[:_](\d{2})', str(time_text))
    if not match:
        raise ValueError("Could not parse WRF time: " + str(time_text))
    return "{}-{}-{}_{}:{}:{}".format(*match.groups())


def _extract_met_time(file_path):
    basename = os.path.basename(file_path)
    try:
        return _normalize_wrf_time(basename)
    except ValueError:
        raise ValueError("Could not extract WRF time from met_em file name: " + str(file_path))


def _extract_met_lon_lat(metfile):
    lon_name = None
    lat_name = None

    if "XLONG_M" in metfile.variables and "XLAT_M" in metfile.variables:
        lon_name = "XLONG_M"
        lat_name = "XLAT_M"
    elif "XLONG" in metfile.variables and "XLAT" in metfile.variables:
        lon_name = "XLONG"
        lat_name = "XLAT"

    if lon_name is None or lat_name is None:
        raise ValueError("Could not find XLONG/XLAT fields in met_em file.")

    lon = metfile.variables[lon_name][:]
    lat = metfile.variables[lat_name][:]

    if lon.ndim == 3:
        lon = lon[0,:]
    if lat.ndim == 3:
        lat = lat[0,:]

    return lon, lat


def get_pressure_from_metfile(metfile):
    PSFC=metfile.variables['PSFC'][:]
    WRF_Pres = np.zeros([nz,ny,nx])
    for z_level in reversed(range(nz)):
        WRF_Pres[nz-1-z_level,:]=PSFC*znu[0,z_level]+ (1.0 - znu[0,z_level])*wrf_p_top
    return WRF_Pres

def get_met_file_by_time_old(time):
    return met_times_files.get(time)

def get_met_file_by_time(time):
    normalized_time = _normalize_wrf_time(time)
    met_file = met_times_files.get(time)
    if met_file is not None:
        return met_file
    met_file = met_times_files.get(normalized_time)
    if met_file is not None:
        return met_file

    # Fallback: search currently matched files by timestamp in basename.
    for candidate in met_files:
        try:
            if _extract_met_time(candidate) == normalized_time:
                return candidate
        except ValueError:
            continue
        if str(time) in os.path.basename(candidate):
            return candidate

    raise FileNotFoundError(
        "Could not resolve met_em file for time "
        + str(time)
        + " using mask "
        + str(config.wrf_met_files)
        + "."
    )

def get_index_in_file_by_time(time):
    return wrf_times.get(time)

def get_BaseMapProjectionByWrfProjection():
    return projections.get(projection)

numbers = re.compile(r'(\d+)')
def numericalSort1(value):
    basename = os.path.basename(value)
    try:
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})[:_](\d{2})[:_](\d{2})', basename)
        if match:
            return "".join(match.groups())
        normalized = _normalize_wrf_time(basename)
        return normalized.replace("-", "").replace("_", "").replace(":", "")
    except ValueError:
        pass
    return basename


def get_ordered_met_files():
    return met_files


def update_boundaries(WRF_SPECIE_BND,wrfbdy_f,name,index):
    WRF_SPECIE_LEFT_BND  =WRF_SPECIE_BND[:,0:ny]
    WRF_SPECIE_TOP_BND   =WRF_SPECIE_BND[:,ny:ny+nx]
    WRF_SPECIE_RIGHT_BND =WRF_SPECIE_BND[:,ny+nx:2*ny+nx]
    WRF_SPECIE_BOT_BND   =WRF_SPECIE_BND[:,2*ny+nx:2*ny+2*nx]

    wrfbxs=np.repeat(WRF_SPECIE_LEFT_BND[np.newaxis,:,:], nw, axis=0)
    wrfbxe=np.repeat(WRF_SPECIE_RIGHT_BND[np.newaxis,:,:], nw, axis=0)
    wrfbys=np.repeat(WRF_SPECIE_BOT_BND[np.newaxis,:,:], nw, axis=0)
    wrfbye=np.repeat(WRF_SPECIE_TOP_BND[np.newaxis,:,:], nw, axis=0)

    #print ("\t\t\tUpdating BC for "+name)
    wrfbdy_f.variables[name+"_BXS"][index,:]=wrfbdy_f.variables[name+"_BXS"][index,:]+wrfbxs
    wrfbdy_f.variables[name+"_BXE"][index,:]=wrfbdy_f.variables[name+"_BXE"][index,:]+wrfbxe
    wrfbdy_f.variables[name+"_BYS"][index,:]=wrfbdy_f.variables[name+"_BYS"][index,:]+wrfbys
    wrfbdy_f.variables[name+"_BYE"][index,:]=wrfbdy_f.variables[name+"_BYE"][index,:]+wrfbye


def update_tendency_boundaries(wrfbdy_f,name,index,dt,wrf_sp_index):
    if(index>0):
        print ("\t\t\tUpdating Tendency BC for "+name)
        wrfbdy_f.variables[name+"_BTXS"][index-1,:]=(wrfbdy_f.variables[name+"_BXS"][index,:]-wrfbdy_f.variables[name+"_BXS"][index-1,:])/dt
        wrfbdy_f.variables[name+"_BTXE"][index-1,:]=(wrfbdy_f.variables[name+"_BXE"][index,:]-wrfbdy_f.variables[name+"_BXE"][index-1,:])/dt
        wrfbdy_f.variables[name+"_BTYS"][index-1,:]=(wrfbdy_f.variables[name+"_BYS"][index,:]-wrfbdy_f.variables[name+"_BYS"][index-1,:])/dt
        wrfbdy_f.variables[name+"_BTYE"][index-1,:]=(wrfbdy_f.variables[name+"_BYE"][index,:]-wrfbdy_f.variables[name+"_BYE"][index-1,:])/dt


def initialise():
    global met_files,wrf_times,wrf_p_top,znu,xlon,xlat,nx,ny,nz,nw,wrf_bnd_lons,wrf_bnd_lats,spec_number,wrf_vars,cen_lat,cen_lon,projection,dx,dy,true_lat2,true_lat1

    met_files=sorted(glob.glob(config.wrf_met_files), key=numericalSort1)
    met_times_files.clear()
    wrf_times.clear()
    nw=0

    if not met_files:
        raise FileNotFoundError(
            "No met_em files matched mask " + str(config.wrf_met_files) + "."
        )

    wrfbdy_var_names = []
    has_wrfbdy_ptop = False
    has_wrfbdy_znu = False

    if config.do_BC:
        wrfbddy = Dataset(config.wrf_bdy_file,'r')
        wrf_time_len = len(wrfbddy.variables['Times'][:])
        if len(met_files) < wrf_time_len:
            wrfbddy.close()
            raise FileNotFoundError(
                "Not enough met_em files matching mask "
                + str(config.wrf_met_files)
                + ". Found "
                + str(len(met_files))
                + ", but wrfbdy has "
                + str(wrf_time_len)
                + " timestamps."
            )

        for i in range(0,wrf_time_len,1):
            wrftime = codecs.utf_8_decode(b''.join(wrfbddy.variables['Times'][i]))[0]
            wrf_times.update({wrftime:i})
            met_times_files.update({wrftime:met_files[i]})

        nw=len(wrfbddy.dimensions['bdy_width'])
        wrfbdy_var_names=[var for var in wrfbddy.variables]
        if "P_TOP" in wrfbddy.variables:
            wrf_p_top=wrfbddy.variables["P_TOP"][:]
            has_wrfbdy_ptop = True
        if "ZNU" in wrfbddy.variables:
            znu=wrfbddy.variables["ZNU"][:]
            has_wrfbdy_znu = True
        if "bottom_top" in wrfbddy.dimensions:
            nz=len(wrfbddy.dimensions["bottom_top"])
        wrfbddy.close()
    else:
        for i, met_file in enumerate(met_files):
            wrftime = _extract_met_time(met_file)
            wrf_times.update({wrftime:i})
            met_times_files.update({wrftime:met_file})

    # BC-only mode does not require wrfinput if wrfbdy contains vertical metadata.
    if config.do_IC or not config.do_BC:
        wrfinput=Dataset(config.wrf_input_file,'r')
        wrf_p_top=wrfinput.variables['P_TOP'][:]
        znu=wrfinput.variables['ZNU'][:]
        xlon=wrfinput.variables['XLONG'][0,:]
        xlat=wrfinput.variables['XLAT'][0,:]
        wrf_vars=[var for var in wrfinput.variables]

        nx=len(wrfinput.dimensions['west_east'])
        ny=len(wrfinput.dimensions['south_north'])
        nz=len(wrfinput.dimensions['bottom_top'])

        projection=wrfinput.getncattr('MAP_PROJ_CHAR')
        cen_lat=wrfinput.getncattr('CEN_LAT')
        cen_lon=wrfinput.getncattr('CEN_LON')
        dy=wrfinput.getncattr('DY')
        dx=wrfinput.getncattr('DX')

        true_lat1=wrfinput.getncattr('TRUELAT1')
        true_lat2=wrfinput.getncattr('TRUELAT2')

        wrfinput.close()
    else:
        if not has_wrfbdy_ptop or not has_wrfbdy_znu:
            raise ValueError(
                "BC-only mode requires P_TOP and ZNU in wrfbdy, or provide --wrf_input_file."
            )

        metfile0 = Dataset(met_files[0], 'r')
        xlon, xlat = _extract_met_lon_lat(metfile0)
        metfile0.close()

        ny = xlat.shape[0]
        nx = xlon.shape[1]
        wrf_vars = sorted(set([var[:-4] for var in wrfbdy_var_names if var.endswith("_BXS")]))

    wrf_bnd_lons=np.concatenate((xlon[:,0],xlon[ny-1,:],xlon[:,nx-1],xlon[0,:]), axis=0)
    wrf_bnd_lats=np.concatenate((xlat[:,0],xlat[ny-1,:],xlat[:,nx-1],xlat[0,:]), axis=0)


    print ("\nWRF dimensions: [bottom_top]="+str(nz)+" [south_north]="+str(ny)+" [west_east]="+str(nx)+" [bdy_width]="+str(nw))
    print ("P_TOP="+str(wrf_p_top)+" Pa")

    print ("Lower left corner: lat="+str(min(wrf_bnd_lats))+" long="+str(min(wrf_bnd_lons)))
    print ("Upper right corner: lat="+str(max(wrf_bnd_lats))+" long="+str(max(wrf_bnd_lons)))


    spec_number=len(config.spc_map)
