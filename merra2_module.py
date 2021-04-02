import config
import re
import os
from netCDF4 import Dataset
from datetime import datetime, timedelta
import numpy as np
from scipy import interpolate

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

numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    return parts[9]

def get_file_index_by_time(time):
    return mera_times_files.get(time)

def get_index_in_file_by_time(time):
    return mera_times.get(time)

def get_file_name_by_index(index):
    return merra_files[index]



#********************************
#Horizontal interpolation of 3d Merra field on WRF boundary
def hor_interpolate_3dfield_on_wrf_boubdary(FIELD, wrf_length, wrf_lon, wrf_lat):
    FIELD_BND=np.zeros([mer_number_of_z_points, wrf_length])
    for z_level in range(mer_number_of_z_points):
        f = interpolate.RectBivariateSpline(mera_lat, mera_lon, FIELD[z_level,:,:],kx=1, ky=1)
        FIELD_BND[z_level,:]=f(wrf_lat,wrf_lon,grid=False)
    return FIELD_BND

#Vertical interpolation of Merra boundary on WRF boundary
def ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_nz, wrf_length):
    WRF_SPECIE_BND = np.zeros([wrf_nz,wrf_length])  # Required SPEC on WRF boundary
    for i in range(0,wrf_length):
        f = interpolate.interp1d(MER_HOR_PRES_BND[:,i], MER_HOR_SPECIE_BND[:,i], kind='linear',bounds_error=False,fill_value=0)
        WRF_SPECIE_BND[:,i]=f(WRF_PRES_BND[:,i])
    return WRF_SPECIE_BND

#Horizontal interpolation of 3d Merra field on WRF horizontal grid
def hor_interpolate_3dfield_on_wrf_grid(FIELD, wrf_ny, wrf_nx, wrf_lon, wrf_lat):
    FIELD_HOR=np.zeros([mer_number_of_z_points, wrf_ny, wrf_nx])

    for z_level in range(mer_number_of_z_points):
        f = interpolate.RectBivariateSpline(mera_lat, mera_lon, FIELD[z_level,:,:],kx=1, ky=1)
        FIELD_HOR[z_level,:,:]=f(wrf_lat,wrf_lon,grid=False).reshape(wrf_ny, wrf_nx)

    return FIELD_HOR

#Vertical interpolation on WRF grid
def ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE, MER_HOR_PRES,WRF_PRES,wrf_nz, wrf_ny, wrf_nx):
    WRF_SPECIE = np.zeros([wrf_nz,wrf_ny,wrf_nx])  # Required SPEC on WRF grid
    for x in range(0,wrf_nx,1):
        for y in range(0,wrf_ny,1):
            f = interpolate.interp1d(MER_HOR_PRES[:,y,x], MER_HOR_SPECIE[:,y,x], kind='linear',bounds_error=False,fill_value=0)
            WRF_SPECIE[:,y,x]=f(WRF_PRES[:,y,x])
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
    global merra_files,mer_number_of_x_points,mer_number_of_y_points,mer_number_of_z_points,mera_lon,mera_lat,merra_vars,shifted_lons,shift_index

    merra_files=sorted([f for f in os.listdir(config.mera_dir) if re.match(config.mera_files, f)], key=numericalSort)
    #print "Open "+config.mera_dir+"/"+merra_files[0]
    merra_f = Dataset(config.mera_dir+"/"+merra_files[0],'r')
    mer_number_of_x_points=merra_f.variables['lon'].size
    mer_number_of_y_points=merra_f.variables['lat'].size
    #not all merra2 files (loading diagnostic) have 'lev' variable
    try:
        mer_number_of_z_points=merra_f.variables['lev'].size
    except Exception:
        pass

    print "MERRA2 dimensions: [bottom_top]="+str(mer_number_of_z_points)+" [south_north]="+str(mer_number_of_y_points)+" [west_east]="+str(mer_number_of_x_points)

    merra_vars = [var for var in merra_f.variables]

    mera_lon  = merra_f.variables['lon'][:]
    mera_lat  = merra_f.variables['lat'][:]

    #if data is given in range of 0_360, then we need to shift lons and data to the -180_180
    if(max(mera_lon)>180):
        print "###########################"
        print "ATTENTION!!!:"
        print "SHIFTING LONGITUDES"
        index=0
        for lon in mera_lon:
            if lon >180:
                mera_lon[index]=mera_lon[index]-360.0
            index=index+1
        shift_index=len(mera_lon)/2
        mera_lon=np.roll(mera_lon,shift_index)
        shifted_lons=True
        print "###########################"

    print "Lower left corner: lat="+str(min(mera_lat))+" long="+str(min(mera_lon))
    print "Upper right corner: lat="+str(max(mera_lat))+" long="+str(max(mera_lon))

    #number of times in  mera file
    times_per_file=merra_f.variables['time'].size
    merra_f.close()

    index=0
    for merra_file in merra_files:
        date=numbers.split(merra_file)[9]
        for i in range(0,times_per_file,1):
            t=datetime.strptime(date, '%Y%m%d')+timedelta(minutes =(i*(24/times_per_file)*60))
            mera_times_files.update({t.strftime("%Y-%m-%d_%H:%M:%S"):index})
            mera_times.update({t.strftime("%Y-%m-%d_%H:%M:%S"):i})
        index=index+1
