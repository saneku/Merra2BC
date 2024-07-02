# -*- coding: utf-8 -*-
import config
from datetime import timedelta
from datetime import datetime
import numpy as np
import os
from netCDF4 import Dataset

fields=['QNIFA2D','QNWFA2D']
required_emission_dt = timedelta(hours=1) # 3600seconds

print ("\nINTERPOLATING EMISSIONS")
#EMISSIONS
wrf_emis = Dataset(config.wrf_dir+"/"+config.wrf_emis_file,'r+')
old_time_list=[datetime.strptime(str(b''.join(t)), "b'%Y-%m-%d_%H:%M:%S'") for t in wrf_emis.variables['Times'][:]]
differences = [(old_time_list[i] - old_time_list[i-1]).total_seconds() for i in range(1, len(old_time_list))]

#difference in emissions time not equal to the required. Interpolate!
if differences[0]!=required_emission_dt.total_seconds():
	new_time_list = []
	start_time = old_time_list[0]
	end_time = old_time_list[-1]

	current_time = start_time
	while current_time <= end_time:
		new_time_list.append(current_time)
		current_time += timedelta(hours=1)

	os.system(f"cp {config.wrf_dir+"/"+config.wrf_emis_file} {config.wrf_dir+"/"+config.wrf_emis_file}_new")
 
	wrfemissions_new = Dataset(f"{config.wrf_dir+"/"+config.wrf_emis_file}_new", 'a')
	aux_times = np.chararray((len(new_time_list), 19), itemsize=1)	
	for i, t in enumerate(new_time_list):
		aux_times[i] = list(t.strftime("%Y-%m-%d_%H:%M:%S"))
	wrfemissions_new.variables['Times'][:] = aux_times
 
	# Find intersection between two datetime lists
	intersection = set(new_time_list) & set(old_time_list)
	# Get indices of intersection
	indices_list_new = [i for i, dt in enumerate(new_time_list) if dt in intersection]
	indices_list_old = [i for i, dt in enumerate(old_time_list) if dt in intersection]

	for f in fields:
		wrfemissions_new.variables[f][:]=0.
		wrfemissions_new.variables[f][indices_list_new,:] = wrf_emis.variables[f][indices_list_old,:]
	
	for i,_ in enumerate(indices_list_new[:-1]):
		for k in np.arange(indices_list_new[i]+1,indices_list_new[i+1]):
			weight = (k-indices_list_new[i])/(indices_list_new[i+1]-indices_list_new[i])
			for f in fields:
				wrfemissions_new.variables[f][k,:] = wrfemissions_new.variables[f][indices_list_new[i],:] * (1.-weight) + wrfemissions_new.variables[f][indices_list_new[i+1],:] * weight
 
	wrfemissions_new.close()
	
	os.system(f"rm {config.wrf_dir+"/"+config.wrf_emis_file}")
	os.system(f"mv {config.wrf_dir+"/"+config.wrf_emis_file}_new {config.wrf_dir+"/"+config.wrf_emis_file}")

else:
    print(f"dt in emission file is {required_emission_dt.total_seconds()} seconds, which is needed. Exiting...")

print ("DONE!")
wrf_emis.close()
