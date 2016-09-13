# -*- coding: utf-8 -*-
import pathes
import time
start_time = time.time()
import merra2_module
import wrf_module
import utils
from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

#modules initialisation
merra2_module.initialise()
wrf_module.initialise()

ny_cs=20
dust_array=['DU001','DU002','DU003','DU004','DU005']

time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()

if(len(time_intersection)!=len(wrf_module.wrf_times)):
    utils.error_message("WRF time range is not fully covered by MERRA2 time range. Exiting...")

#sorting times for processing
time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))

cur_time=time_intersection[0]
index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
#print "Opening mera file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" with initial time: "+cur_time
merra_f = Dataset(pathes.mera_dir+"/"+merra2_module.get_file_name_by_index(index_of_opened_mera_file),'r')
MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)

#total dust contains sum of all dust bins from MERRA2
MER_DUST = np.zeros([merra2_module.mer_number_of_z_points,merra2_module.mer_number_of_y_points,merra2_module.mer_number_of_x_points])
for merra_specie in dust_array:
    MER_DUST=MER_DUST+merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

fig = plt.figure(figsize=(20,20))

MER_DUST=MER_DUST[:,ny_cs,:]

MERA_PRES=MERA_PRES[:,ny_cs,:]
MERA_PRES=(MERA_PRES/100.0)  #convert to hPa, 1 hPa = 100 Pa

lons=merra2_module.mera_lon
lons=np.repeat(lons, merra2_module.mer_number_of_z_points, axis=0)
lons=lons.reshape(merra2_module.mer_number_of_x_points,merra2_module.mer_number_of_z_points)
lons=lons.transpose()


##################################
clevs =np.linspace(0, 1.7e-6,num=100, endpoint=False)
cs = plt.contourf(lons,MERA_PRES,MER_DUST,clevs,cmap=plt.cm.Spectral_r)
#cs = plt.contourf(lons,MERA_PRES,MER_DUST,cmap=plt.cm.Spectral_r)
plt.plot(lons,MERA_PRES,'k.', ms=1,alpha=0.35,color="white")

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
plt.title("MERRA2 Total dust vertical crossection at %s"%cur_time)
############################


plt.show()
plt.close()
merra_f.close()

print("--- %s seconds ---" % (time.time() - start_time))
