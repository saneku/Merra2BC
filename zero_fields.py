# -*- coding: utf-8 -*-
import config
import time

start_time = time.time()

from netCDF4 import Dataset

zero=1e-16
fields_to_zero=['o3','co','so2','sulf']

#---------------------------------------

print "SETTING TO ZERO INITIAL CONDITIONS"
#INITIAL CONDITIONS
wrfinput = Dataset(config.wrf_dir+"/"+config.wrf_input_file,'r+')
for field in fields_to_zero:
	print "Setting to zero IC for ",field
	wrfinput.variables[field][:]=zero
wrfinput.close()


print "\n\nSETTING TO ZERO BOUNDARY CONDITIONS AND TENDENCIES"
#BOUNDARY CONDITIONS
wrfbddy = Dataset(config.wrf_dir+"/"+config.wrf_bdy_file,'r+')
for field in fields_to_zero:
	print "Setting to zero BC for ",field
	wrfbddy.variables[field+"_BXS"][:]=zero
	wrfbddy.variables[field+"_BXE"][:]=zero
	wrfbddy.variables[field+"_BYS"][:]=zero
	wrfbddy.variables[field+"_BYE"][:]=zero

	print "Setting to zero Tendency BC for ",field
	wrfbddy.variables[field+"_BTXS"][:]=zero
	wrfbddy.variables[field+"_BTXE"][:]=zero
	wrfbddy.variables[field+"_BTYS"][:]=zero
	wrfbddy.variables[field+"_BTYE"][:]=zero
wrfbddy.close()
print("--- %s seconds ---" % (time.time() - start_time))
