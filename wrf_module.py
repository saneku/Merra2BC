import config
import re
import os
from netCDF4 import Dataset
import numpy as np

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

def get_pressure_from_metfile(metfile):
    PSFC=metfile.variables['PSFC'][:]
    WRF_Pres = np.zeros([nz,ny,nx])
    for z_level in reversed(range(nz)):
        WRF_Pres[nz-1-z_level,:]=PSFC*znu[0,z_level]+ (1.0 - znu[0,z_level])*wrf_p_top
    return WRF_Pres

def get_met_file_by_time_old(time):
    return met_times_files.get(time)

def get_met_file_by_time(time):
    return "met_em.d01."+time+".nc"


def get_index_in_file_by_time(time):
    return wrf_times.get(time)

def get_BaseMapProjectionByWrfProjection():
    return projections.get(projection)

numbers = re.compile(r'(\d+)')
def numericalSort1(value):
    parts = numbers.split(value)
    return int(float(parts[3])*1e6+float(parts[5])*1e4+float(parts[7])*1e2+float(parts[9]))


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

    #print "\t\t\tUpdating BC for "+name
    wrfbdy_f.variables[name+"_BXS"][index,:]=wrfbdy_f.variables[name+"_BXS"][index,:]+wrfbxs
    wrfbdy_f.variables[name+"_BXE"][index,:]=wrfbdy_f.variables[name+"_BXE"][index,:]+wrfbxe
    wrfbdy_f.variables[name+"_BYS"][index,:]=wrfbdy_f.variables[name+"_BYS"][index,:]+wrfbys
    wrfbdy_f.variables[name+"_BYE"][index,:]=wrfbdy_f.variables[name+"_BYE"][index,:]+wrfbye


def update_tendency_boundaries(wrfbdy_f,name,index,dt,wrf_sp_index):
    if(index>0):
        print "\t\t\tUpdating Tendency BC for "+name
        wrfbdy_f.variables[name+"_BTXS"][index-1,:]=(wrfbdy_f.variables[name+"_BXS"][index,:]-wrfbdy_f.variables[name+"_BXS"][index-1,:])/dt
        wrfbdy_f.variables[name+"_BTXE"][index-1,:]=(wrfbdy_f.variables[name+"_BXE"][index,:]-wrfbdy_f.variables[name+"_BXE"][index-1,:])/dt
        wrfbdy_f.variables[name+"_BTYS"][index-1,:]=(wrfbdy_f.variables[name+"_BYS"][index,:]-wrfbdy_f.variables[name+"_BYS"][index-1,:])/dt
        wrfbdy_f.variables[name+"_BTYE"][index-1,:]=(wrfbdy_f.variables[name+"_BYE"][index,:]-wrfbdy_f.variables[name+"_BYE"][index-1,:])/dt


def initialise():
    global met_files,wrf_times,wrf_p_top,znu,xlon,xlat,nx,ny,nz,nw,wrf_bnd_lons,wrf_bnd_lats,spec_number,wrf_vars,cen_lat,cen_lon,projection,dx,dy,true_lat2,true_lat1

    met_files=sorted([f for f in os.listdir(config.wrf_met_dir) if re.match(config.wrf_met_files, f)], key=numericalSort1)
    wrfbddy = Dataset(config.wrf_dir+"/"+config.wrf_bdy_file,'r')
    for i in range(0,len(wrfbddy.variables['Times'][:]),1):
        wrf_times.update({''.join(wrfbddy.variables['Times'][i]):i})
        met_times_files.update({''.join(wrfbddy.variables['Times'][i]):met_files[i]})


    nx=len(wrfbddy.dimensions['west_east'])
    ny=len(wrfbddy.dimensions['south_north'])
    nz=len(wrfbddy.dimensions['bottom_top'])
    nw=len(wrfbddy.dimensions['bdy_width'])
    wrfbddy.close()

    #Reading "PRESSURE TOP OF THE MODEL, PA" and "eta values on half (mass) levels"
    wrfinput=Dataset(config.wrf_dir+"/"+config.wrf_input_file,'r')
    wrf_p_top=wrfinput.variables['P_TOP'][:]
    znu=wrfinput.variables['ZNU'][:]
    xlon=wrfinput.variables['XLONG'][0,:]
    xlat=wrfinput.variables['XLAT'][0,:]
    wrf_vars=[var for var in wrfinput.variables]

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


    print "\nWRF dimensions: [bottom_top]="+str(nz)+" [south_north]="+str(ny)+" [west_east]="+str(nx)+" [bdy_width]="+str(nw)
    print "P_TOP="+str(wrf_p_top)+" Pa"

    print "Lower left corner: lat="+str(min(wrf_bnd_lats))+" long="+str(min(wrf_bnd_lons))
    print "Upper right corner: lat="+str(max(wrf_bnd_lats))+" long="+str(max(wrf_bnd_lons))


    spec_number=len(config.spc_map)
