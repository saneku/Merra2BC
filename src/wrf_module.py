from . import config
from . import utils
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
CO2_PPMV=400.0
CH4_PPMV=1.7

def get_pressure_from_metfile(metfile):
    PSFC=metfile.variables['PSFC'][:]
    WRF_Pres = np.zeros([nz,ny,nx])
    for z_level in reversed(range(nz)):
        WRF_Pres[nz-1-z_level,:]=PSFC*znu[0,z_level]+ (1.0 - znu[0,z_level])*wrf_p_top
    return WRF_Pres

def get_met_file_by_time_old(time):
    return met_times_files.get(time)

def get_met_file_by_time(time):
    met_file = met_times_files.get(time)
    if met_file is not None:
        return met_file

    # Fallback: search currently matched files by timestamp in basename.
    for candidate in met_files:
        if time in os.path.basename(candidate):
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

def _normalize_time_key(time_key):
    tkey = str(time_key).strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2})_(\d{2})[:_](\d{2})[:_](\d{2})$", tkey)
    if match:
        return (
            match.group(1)
            + "_"
            + match.group(2)
            + ":"
            + match.group(3)
            + ":"
            + match.group(4)
        )
    return tkey

def _extract_met_time_from_file(file_path):
    with Dataset(file_path, 'r') as met_f:
        if 'Times' not in met_f.variables or len(met_f.variables['Times'][:]) == 0:
            raise ValueError("Could not read Times from met_em file: " + str(file_path))
        wrf_time = codecs.utf_8_decode(b''.join(met_f.variables['Times'][0]))[0]
        return _normalize_time_key(wrf_time)

numbers = re.compile(r'(\d+)')
def numericalSort1(value):
    basename = os.path.basename(value)
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})_(\d{2}):(\d{2}):(\d{2})', basename)
    if match:
        return "".join(match.groups())
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


def _require_var(nc_file, var_name, file_label):
    if var_name not in nc_file.variables:
        utils.error_message(
            "Variable " + var_name + " is missing in " + file_label + ". Exiting..."
        )
    return nc_file.variables[var_name]


def init_co2_ch4_ic(wrfinput_f):
    print (
        "\t\t - Setting fixed IC fields: co2="
        + str(CO2_PPMV)
        + " ppmv, ch4="
        + str(CH4_PPMV)
        + " ppmv"
    )
    _require_var(wrfinput_f, "co2", "wrfinput")[:] = CO2_PPMV
    _require_var(wrfinput_f, "ch4", "wrfinput")[:] = CH4_PPMV


def init_co2_ch4_bc(wrfbdy_f):
    print (
        "\t\t - Setting fixed BC fields: co2="
        + str(CO2_PPMV)
        + " ppmv, ch4="
        + str(CH4_PPMV)
        + " ppmv; tendencies set to 0"
    )
    for spec_name, value in [("co2", CO2_PPMV), ("ch4", CH4_PPMV)]:
        _require_var(wrfbdy_f, spec_name + "_BXS", "wrfbdy")[:] = value
        _require_var(wrfbdy_f, spec_name + "_BXE", "wrfbdy")[:] = value
        _require_var(wrfbdy_f, spec_name + "_BYS", "wrfbdy")[:] = value
        _require_var(wrfbdy_f, spec_name + "_BYE", "wrfbdy")[:] = value

        _require_var(wrfbdy_f, spec_name + "_BTXS", "wrfbdy")[:] = 0.0
        _require_var(wrfbdy_f, spec_name + "_BTXE", "wrfbdy")[:] = 0.0
        _require_var(wrfbdy_f, spec_name + "_BTYS", "wrfbdy")[:] = 0.0
        _require_var(wrfbdy_f, spec_name + "_BTYE", "wrfbdy")[:] = 0.0


def initialise():
    global met_files,wrf_times,wrf_p_top,znu,xlon,xlat,nx,ny,nz,nw,wrf_bnd_lons,wrf_bnd_lats,spec_number,wrf_vars,cen_lat,cen_lon,projection,dx,dy,true_lat2,true_lat1

    met_files=sorted(glob.glob(config.wrf_met_files), key=numericalSort1)
    met_times_files.clear()
    wrf_times.clear()
    nw=0

    if len(met_files) == 0:
        raise FileNotFoundError(
            "Could not find met_em files matching mask " + str(config.wrf_met_files)
        )

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
            wrftime = _normalize_time_key(wrftime)
            wrf_times.update({wrftime:i})
            met_times_files.update({wrftime:met_files[i]})

        nw=len(wrfbddy.dimensions['bdy_width'])
        wrfbddy.close()
    else:
        for i, met_file in enumerate(met_files):
            wrftime = _extract_met_time_from_file(met_file)
            wrf_times.update({wrftime:i})
            met_times_files.update({wrftime:met_file})

    #Reading "PRESSURE TOP OF THE MODEL, PA" and "eta values on half (mass) levels"
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

    wrf_bnd_lons=np.concatenate((xlon[:,0],xlon[ny-1,:],xlon[:,nx-1],xlon[0,:]), axis=0)
    wrf_bnd_lats=np.concatenate((xlat[:,0],xlat[ny-1,:],xlat[:,nx-1],xlat[0,:]), axis=0)


    print ("\nWRF dimensions: [bottom_top]="+str(nz)+" [south_north]="+str(ny)+" [west_east]="+str(nx)+" [bdy_width]="+str(nw))
    print ("P_TOP="+str(wrf_p_top)+" Pa")

    print ("Lower left corner: lat="+str(min(wrf_bnd_lats))+" long="+str(min(wrf_bnd_lons)))
    print ("Upper right corner: lat="+str(max(wrf_bnd_lats))+" long="+str(max(wrf_bnd_lons)))


    spec_number=len(config.spc_map)
