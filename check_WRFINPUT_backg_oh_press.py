import pathes
import time
import wrf_module

start_time = time.time()

import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np

wrf_module.initialise()
cur_time=wrf_module.wrf_times.keys()[wrf_module.wrf_times.values().index(0)]


metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
WRF_Pres=wrf_module.get_pressure_from_metfile(metfile)
WRF_Pres=np.mean(WRF_Pres, axis=(1,2))
WRF_Pres=(WRF_Pres/100.0)  #convert to hPa, 1 hPa = 100 Pa
metfile.close()

wrfinput = Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r')
Z = (wrfinput.variables['PH'][0,:] + wrfinput.variables['PHB'][0,:]) / 9.81
Z=np.mean(Z, axis=(1,2))/1000.0
WRF_BCKG_OH=wrfinput.variables["BACKG_OH"][0,:]
WRF_BCKG_OH=np.flipud(WRF_BCKG_OH)
WRF_BCKG_OH=np.mean(WRF_BCKG_OH, axis=(1,2))
WRF_BCKG_OH=WRF_BCKG_OH*1e6 #converting to ppmv
wrfinput.close()


fig = plt.figure(figsize=(8,8))
plt.gca().invert_yaxis()

plt.ylabel('Pressure, hPa',fontsize=15)
plt.xlabel('Background OH, ppm',fontsize=15)
plt.yscale('log')
plt.xscale('log')
plt.axhline(y=wrf_module.wrf_p_top/100.0, color='b',linestyle='--')
plt.plot(WRF_BCKG_OH,WRF_Pres,'-r',label='OH profile',linewidth=2.5)
plt.title("Averaged WRFINPUT OH profile at %s"%cur_time)

axes = plt.gca()
axes.set_xlim([1e-8,1e-2])
axes.set_ylim([1000.0,0.01])
#axes.set_xticklabels([])
#axes.set_yticklabels([])
plt.grid()

plt.show()
#plt.savefig('wrfinput_profile_0.png')
#plt.close()


print("--- %s seconds ---" % (time.time() - start_time))
