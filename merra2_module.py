import pathes
import re
import os
from netCDF4 import Dataset
from datetime import datetime, timedelta
import numpy as np


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


def get_pressure_by_time(time,merra_file):
    global Ptop_mera
    MER_Pres = np.zeros([mer_number_of_z_points,mer_number_of_y_points,mer_number_of_x_points])
    #filling top layer with Ptop_mera
    MER_Pres[0,:,:]=Ptop_mera
    # Extract delta P from NetCDF file at index defined by time
    mera_time_idx=get_index_in_file_by_time(time)
    DELP = merra_file.variables['DELP'][mera_time_idx,:]  #Pa

    #        for z_level in reversed(range(mer_number_of_z_points-1)):
    #            MER_Pres[z_level,:,:]=MER_Pres[z_level+1,:,:]+DELP[z_level+1,:,:]

    for z_level in range(mer_number_of_z_points-1):
        MER_Pres[z_level+1]=MER_Pres[z_level]+DELP[z_level]

    return MER_Pres



def initialise():
    global merra_files,mer_number_of_x_points,mer_number_of_y_points,mer_number_of_z_points,mera_lon,mera_lat,times_per_file

    merra_files=sorted([f for f in os.listdir(pathes.mera_dir) if re.match(pathes.mera_files, f)], key=numericalSort)
    merra_f = Dataset(pathes.mera_dir+"/"+merra_files[0],'r')
    mer_number_of_x_points=merra_f.variables['lon'].size
    mer_number_of_y_points=merra_f.variables['lat'].size
    mer_number_of_z_points=merra_f.variables['lev'].size

    mera_lon  = merra_f.variables['lon'][:]
    mera_lat  = merra_f.variables['lat'][:]

    #number of times in  mera file
    times_per_file=merra_f.variables['time'].size
    #print merra_file.RangeBeginningDate
    merra_f.close()


    index=0
    for merra_file in merra_files:
        date=numbers.split(merra_file)[9]
        for i in range(0,times_per_file,1):
            t=datetime.strptime(date, '%Y%m%d')+timedelta(minutes =(i*(24/times_per_file)*60))
            mera_times_files.update({t.strftime("%Y-%m-%d_%H:%M:%S"):index})
            mera_times.update({t.strftime("%Y-%m-%d_%H:%M:%S"):i})
        index=index+1

#initialise()
