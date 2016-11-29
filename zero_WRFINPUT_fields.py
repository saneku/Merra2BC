# -*- coding: utf-8 -*-
import pathes
import time

start_time = time.time()

from netCDF4 import Dataset

zero=1e-16
fields_to_zero=['o3','co']

wrfinput = Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r+')
for field in fields_to_zero:
	print "zeroing ",field
	wrfinput.variables[field][:]=zero

wrfinput.close()
print("--- %s seconds ---" % (time.time() - start_time))
