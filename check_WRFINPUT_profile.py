#comparing total dust loading with computed based on MERRA2 data
#as it is IC take only first time

import pathes
import time
import wrf_module
import merra2_module
start_time = time.time()

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np

g=9.81
ny_cs=3

#dust bins from wrfinput
dust_array=['DUST_1','DUST_2','DUST_3','DUST_4','DUST_5']

merra2_module.initialise()
wrf_module.initialise()
time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()
#sorting times for processing
time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))

cur_time=time_intersection[0]

#total dust contains sum of all dust bins from wrfinput
wrfinput = Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r')
WRF_DUST = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
for dust in dust_array:
    WRF_DUST=WRF_DUST+wrfinput.variables[dust][0,:]

metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
WRF_Pres=wrf_module.get_pressure_from_metfile(metfile)
WRF_DUST=np.flipud(WRF_DUST)

fig = plt.figure(figsize=(20,20))
WRF_DUST=WRF_DUST[:,ny_cs,:]

#converting to kg/kg
WRF_DUST=WRF_DUST*1e-9

WRF_Pres=WRF_Pres[:,ny_cs,:]
WRF_Pres=(WRF_Pres/100.0)  #convert to hPa, 1 hPa = 100 Pa

lons=wrf_module.xlon[ny_cs,:]
lons=np.repeat(lons, wrf_module.nz, axis=0)
lons=lons.reshape(wrf_module.nx,wrf_module.nz)
lons=lons.transpose()


##################################
clevs =np.linspace(0, 1.7e-6,num=100, endpoint=False)
cs = plt.contourf(lons,WRF_Pres,WRF_DUST,clevs,cmap=plt.cm.Spectral_r)
#cs = plt.contourf(lons,WRF_Pres,WRF_DUST,cmap=plt.cm.Spectral_r)
plt.plot(lons,WRF_Pres,'k.', ms=1,alpha=0.35,color="white")

cbar = plt.colorbar(cs, orientation='horizontal')
cbar.set_label("Total dust, kg kg-1")
cbar.formatter.set_powerlimits((0, 0))
cbar.update_ticks()
plt.gca().set_aspect('equal', adjustable='box')
plt.xlabel('Longitude',fontsize=15)
plt.ylabel('Pressure, hPa',fontsize=15)
plt.yscale('log')
plt.gca().set_ylim([100,1000])
plt.gca().invert_yaxis()
plt.title("WRF IC Total dust vertical crossection at %s"%cur_time)
############################

plt.show()
plt.close()
wrfinput.close()


print("--- %s seconds ---" % (time.time() - start_time))
