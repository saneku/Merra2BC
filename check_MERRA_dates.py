# -*- coding: utf-8 -*-
from netCDF4 import Dataset
from datetime import datetime, timedelta

import pathes
import merra2_module

merra2_module.initialise()

merra_files = merra2_module.get_ordered_mera_files_in_mera_dir()
#print merra_files

for mf in merra_files:
#    print "Processing: " + mf
    merra_file = Dataset(pathes.mera_dir+"/"+mf,'r')

    start_time=merra_file.RangeBeginningDate
    start_time=datetime.strptime(start_time, '%Y-%m-%d')
    times =merra_file.variables['time'][:] #time in minutes since start_time

    for time_idx in range(0,len(times),1):
        print str(start_time+timedelta(minutes=times[time_idx]))

    merra_file.close()
