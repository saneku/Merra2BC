# -*- coding: utf-8 -*-
from src import config
import time

from netCDF4 import Dataset

start_time = time.time()


zero = 1e-16
#For GOCART
fields_to_zero=['o3','co','so2','sulf','SEAS_1','SEAS_2','SEAS_3','SEAS_4','BC1','BC2','OC1','OC2','dms']

#For MOSAIC 8 bins
fields_to_zero=['o3','co','so2',
				'oin_a01','oin_a02','oin_a03','oin_a04','oin_a05','oin_a06','oin_a07','oin_a08',
				'num_a01','num_a02','num_a03','num_a04','num_a05','num_a06','num_a07','num_a08',
				'na_a01' ,'na_a02' ,'na_a03' ,'na_a04' ,'na_a05' ,'na_a06' ,'na_a07' ,'na_a08' ,
				'cl_a01' ,'cl_a02' ,'cl_a03' ,'cl_a04' ,'cl_a05' ,'cl_a06' ,'cl_a07' ,'cl_a08',
			        'so4_a01','so4_a02','so4_a03','so4_a04','so4_a05','so4_a06','so4_a07','so4_a08' ]

if not config.do_IC and not config.do_BC:
    print("Nothing to do: both --do_IC and --do_BC are false.")
    print("--- %s seconds ---" % (time.time() - start_time))
    raise SystemExit(0)

if config.do_IC:
    print("SETTING TO ZERO INITIAL CONDITIONS")
    wrfinput_path = config.wrf_dir + "/" + config.wrf_input_file
    print("Processing wrfinput:", wrfinput_path)
    wrfinput = Dataset(wrfinput_path, "r+")
    for field in fields_to_zero:
        print("Setting to zero IC for", field)
        wrfinput.variables[field][:] = zero
    wrfinput.close()

if config.do_BC:
    print("\n\nSETTING TO ZERO BOUNDARY CONDITIONS AND TENDENCIES")
    wrfbdy_path = config.wrf_dir + "/" + config.wrf_bdy_file
    print("Processing wrfbdy:", wrfbdy_path)
    wrfbddy = Dataset(wrfbdy_path, "r+")
    for field in fields_to_zero:
        print("Setting to zero BC for", field)
        wrfbddy.variables[field + "_BXS"][:] = zero
        wrfbddy.variables[field + "_BXE"][:] = zero
        wrfbddy.variables[field + "_BYS"][:] = zero
        wrfbddy.variables[field + "_BYE"][:] = zero

        print("Setting to zero Tendency BC for", field)
        wrfbddy.variables[field + "_BTXS"][:] = zero
        wrfbddy.variables[field + "_BTXE"][:] = zero
        wrfbddy.variables[field + "_BTYS"][:] = zero
        wrfbddy.variables[field + "_BTYE"][:] = zero
    wrfbddy.close()

print("--- %s seconds ---" % (time.time() - start_time))
