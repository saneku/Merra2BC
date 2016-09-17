import pathes
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
merra_files=[]
mera_times={}                           #map between time and index in file
mera_times_files={}                     #map between time and file index
mer_number_of_x_points=0
mer_number_of_y_points=0
mer_number_of_z_points=0

times_per_file=0

merra_points=0

numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    return parts[9]

def get_ordered_mera_files_in_mera_dir():
    return merra_files

def get_file_index_by_time(time):
    return mera_times_files.get(time)

def get_index_in_file_by_time(time):
    return mera_times.get(time)

def get_file_name_by_index(index):
    return merra_files[index]


#********************************
#Horizontal interpolation of 3d Merra field on WRF boundary
def hor_interpolate_3dfield_on_wrf_boubdary(FIELD, wrf_length, wrf_lon, wrf_lat):
    FIELD_HOR=np.zeros([mer_number_of_z_points, wrf_length])
    for z_level in range(mer_number_of_z_points):
        FIELD_HOR[z_level,:]=interpolate.griddata(merra_points, FIELD[z_level,:,:].ravel(), (wrf_lon, wrf_lat), method='linear',fill_value=0)
    return FIELD_HOR

#Vertical interpolation of Merra boundary on WRF boundary
def ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_nz, wrf_length):
    WRF_SPECIE_BND = np.zeros([wrf_nz,wrf_length])  # Required SPEC on WRF boundary
    for i in range(0,wrf_length):
        f = interpolate.interp1d(MER_HOR_PRES_BND[:,i], MER_HOR_SPECIE_BND[:,i], kind='linear',bounds_error=False,fill_value=0)
        WRF_SPECIE_BND[:,i]=f(WRF_PRES_BND[:,i])
    return WRF_SPECIE_BND
#********************************


#TODO ASK SERGEY HOW HE INTERPOLATES ON MERRA GRID?
#Horizontal interpolation of 3d Merra field on WRF horizontal grid
def hor_interpolate_3dfield_on_wrf_grid(FIELD, wrf_ny, wrf_nx, wrf_lon, wrf_lat):
    FIELD_HOR=np.zeros([mer_number_of_z_points, wrf_ny, wrf_nx])
    for z_level in range(mer_number_of_z_points):
        #f = interpolate.interp2d(mera_lon, mera_lat, MER_Pres[z_level,:,:], kind='linear')
        #MER_HOR_Pres[z_level,:,:]=f(wrf_lon[0,:], wrf_lat[0,:])
        FIELD_HOR[z_level,:,:]= interpolate.griddata(merra_points, FIELD[z_level,:,:].ravel(), (wrf_lon, wrf_lat), method='linear',fill_value=0)
    return FIELD_HOR



#*******************************
#*******************************
#*******************************
def hor_interpolate_3dfield_on_wrf_grid1(wrf_ny, wrf_nx, wrf_lon, wrf_lat,FIELD):
    #print 'process id: '+str(os.getpid())+"  FIELD.shape="+str(FIELD.shape)#+" wrf_ny="+str(wrf_ny)+" wrf_nx="+str(wrf_nx)#+" shape="+FIELD.shape
    #print 'process id: '+str(os.getpid())+" FIELD_HOR.shape="+str(FIELD_HOR.shape)
    FIELD_HOR=np.zeros([FIELD.shape[0], wrf_ny, wrf_nx])

    for z_level in range(FIELD.shape[0]):
        FIELD_HOR[z_level,:,:]= interpolate.griddata(merra_points, FIELD[z_level,:,:].ravel(), (wrf_lon, wrf_lat), method='linear',fill_value=0)
    return FIELD_HOR


def threaded_hor_interpolate_3dfield_on_wrf_grid(FIELD, wrf_ny, wrf_nx, wrf_lon, wrf_lat):
    # Make the Pool of number_of_workers workers
    N=pathes.number_of_workers
    pool = Pool(N)
    result=np.zeros([mer_number_of_z_points, wrf_ny, wrf_nx])
    func = partial(hor_interpolate_3dfield_on_wrf_grid1, wrf_ny, wrf_nx, wrf_lon, wrf_lat)
    result=pool.map(func, np.array_split(FIELD, N))
    pool.close()
    pool.join()

    return np.concatenate(result)

#*******************************
#*******************************
#*******************************


def ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE, MER_HOR_PRES,WRF_PRES,wrf_nz, wrf_ny, wrf_nx):
    WRF_SPECIE = np.zeros([wrf_nz,wrf_ny,wrf_nx])  # Required SPEC on WRF grid
    for x in range(0,wrf_nx,1):
        for y in range(0,wrf_ny,1):
            f = interpolate.interp1d(MER_HOR_PRES[:,y,x], MER_HOR_SPECIE[:,y,x], kind='linear',bounds_error=False,fill_value=0)
            WRF_SPECIE[:,y,x]=f(WRF_PRES[:,y,x])
    return WRF_SPECIE


#extracts 3d field from merra2 file from given time
def get_3dfield_by_time(time,merra_file,field_name):
    mera_time_idx=get_index_in_file_by_time(time)
    return np.flipud(merra_file.variables[field_name][mera_time_idx,:])


#TODO What is the right way to restore pressure?
def get_pressure_by_time(time,merra_file):
    global Ptop_mera
    MER_Pres = np.zeros([mer_number_of_z_points,mer_number_of_y_points,mer_number_of_x_points])
    #filling top layer with Ptop_mera
    MER_Pres[0,:,:]=Ptop_mera
    #OR
    #MER_Pres[mer_number_of_z_points-1,:,:]=Ptop_mera

    # Extract delta P from NetCDF file at index defined by time
    mera_time_idx=get_index_in_file_by_time(time)
    DELP = merra_file.variables['DELP'][mera_time_idx,:]  #Pa

    #for z_level in reversed(range(mer_number_of_z_points-1)):
    #    MER_Pres[z_level,:,:]=MER_Pres[z_level+1,:,:]+DELP[z_level+1,:,:]
    #OR
    for z_level in range(mer_number_of_z_points-1):
        MER_Pres[z_level+1]=MER_Pres[z_level]+DELP[z_level]

    MER_Pres=np.flipud(MER_Pres)
    return MER_Pres



def initialise():
    global merra_files,mer_number_of_x_points,mer_number_of_y_points,mer_number_of_z_points,mera_lon,mera_lat,times_per_file,merra_points

    merra_files=sorted([f for f in os.listdir(pathes.mera_dir) if re.match(pathes.mera_files, f)], key=numericalSort)
    merra_f = Dataset(pathes.mera_dir+"/"+merra_files[0],'r')
    mer_number_of_x_points=merra_f.variables['lon'].size
    mer_number_of_y_points=merra_f.variables['lat'].size
    mer_number_of_z_points=merra_f.variables['lev'].size

    mera_lon  = merra_f.variables['lon'][:]
    mera_lat  = merra_f.variables['lat'][:]

    xx, yy = np.meshgrid(mera_lon, mera_lat)
    xx=xx.ravel()
    yy=yy.ravel()
    merra_points=(xx, yy)

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
