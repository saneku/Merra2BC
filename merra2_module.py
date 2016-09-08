import pathes
import re
import os
from netCDF4 import Dataset
from datetime import datetime, timedelta
import numpy as np


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

#print mera_times
#print "\n"
#print mera_times_files


'''
wrf_times
{0: '2010-07-14_00:00:00', 1: '2010-07-14_06:00:00', 2: '2010-07-14_12:00:00', 3: '2010-07-14_18:00:00', 4: '2010-07-15_00:00:00',
 5: '2010-07-15_06:00:00', 6: '2010-07-15_12:00:00', 7: '2010-07-15_18:00:00', 8: '2010-07-16_00:00:00', 9: '2010-07-16_06:00:00',
10: '2010-07-16_12:00:00', 11: '2010-07-16_18:00:00', 12: '2010-07-17_00:00:00', 13: '2010-07-17_06:00:00',
14: '2010-07-17_12:00:00', 15: '2010-07-17_18:00:00', 16: '2010-07-18_00:00:00', 17: '2010-07-18_06:00:00',
18: '2010-07-18_12:00:00', 19: '2010-07-18_18:00:00', 20: '2010-07-19_00:00:00', 21: '2010-07-19_06:00:00',
22: '2010-07-19_12:00:00', 23: '2010-07-19_18:00:00'}

'''
