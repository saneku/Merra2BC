'''
wrf_dir="/home/ukhova/Downloads/"
wrf_met_files="met_em.d01.2010*"
wrf_input_file="wrfinput_d01"
wrf_bdy_file="wrfbdy_d01"

mera_dir="/home/ukhova/Downloads/Merra2ForVISUVI/"
mera_files="svc_MERRA2_300.inst3_3d_aer_Nv.20100*"
'''

import pathes
import re
import os
from netCDF4 import Dataset

met_files=[]
wrf_times={}

def get_index_in_file_by_time(time):
    return wrf_times.get(time)


numbers = re.compile(r'(\d+)')
def numericalSort1(value):
    parts = numbers.split(value)
    return int(float(parts[3])*1e6+float(parts[5])*1e4+float(parts[7])*1e2+float(parts[9]))


def get_ordered_met_files():
    return met_files


def initialise():
    global met_files,wrf_times

    met_files=sorted([f for f in os.listdir(pathes.wrf_dir) if re.match(pathes.wrf_met_files, f)], key=numericalSort1)
    wrfbddy = Dataset(pathes.wrf_dir+"/"+pathes.wrf_bdy_file,'r')
    for i in range(0,len(wrfbddy.variables['Times'][:]),1):
        #wrf_times.append(''.join(wrfbddy.variables['Times'][i]))
        wrf_times.update({''.join(wrfbddy.variables['Times'][i]):i})

    wrfbddy.close()

#initialise()

#print met_files
#print "\n"
#print wrf_times

'''
wrf_times
{'2010-07-16_06:00:00': 9, '2010-07-17_00:00:00': 12, '2010-07-15_18:00:00': 7, '2010-07-19_12:00:00': 22, '2010-07-18_00:00:00': 16, '2010-07-16_00:00:00': 8, '2010-07-16_18:00:00': 11, '2010-07-19_06:00:00': 21, '2010-07-19_00:00:00': 20, '2010-07-15_06:00:00': 5, '2010-07-17_06:00:00': 13, '2010-07-14_06:00:00': 1, '2010-07-15_12:00:00': 6, '2010-07-14_00:00:00': 0, '2010-07-14_18:00:00': 3, '2010-07-18_18:00:00': 19, '2010-07-14_12:00:00': 2, '2010-07-18_12:00:00': 18, '2010-07-17_12:00:00': 14, '2010-07-15_00:00:00': 4, '2010-07-19_18:00:00': 23, '2010-07-16_12:00:00': 10, '2010-07-18_06:00:00': 17, '2010-07-17_18:00:00': 15}
'''
