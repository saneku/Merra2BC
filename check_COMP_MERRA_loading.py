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

g=9.81
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

MERA_DELP=merra2_module.get_3dfield_by_time(cur_time,merra_f,"DELP")

#total dust contains sum of all dust bins from MERRA2
MER_DUST = np.zeros([merra2_module.mer_number_of_z_points,merra2_module.mer_number_of_y_points,merra2_module.mer_number_of_x_points])
for merra_specie in dust_array:
    MER_DUST=MER_DUST+merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)


MERRA_LOAD=MERA_DELP*MER_DUST/g
MERRA_LOAD=np.sum(MERRA_LOAD, axis=0)


fig = plt.figure(figsize=(20,20))


#ash_map = Basemap(projection='cyl',llcrnrlat=10,urcrnrlat=60,llcrnrlon=0,urcrnrlon=50,resolution='c',area_thresh=100.)
ash_map = Basemap(projection='cyl',llcrnrlon=min(merra2_module.mera_lon), llcrnrlat=min(merra2_module.mera_lat), urcrnrlon=max(merra2_module.mera_lon), urcrnrlat=max(merra2_module.mera_lat),resolution='c',area_thresh=100.)
ash_map.drawcoastlines(linewidth=1)
ash_map.drawmapboundary(linewidth=0.25)
lons,lats= np.meshgrid(merra2_module.mera_lon,merra2_module.mera_lat)
x, y = ash_map(lons,lats)

clevs =np.linspace(0, 5e-3,num=100, endpoint=True)
cs = ash_map.contourf(x,y,MERRA_LOAD,clevs,cmap=plt.cm.Spectral_r)

# draw parallels.
parallels = np.arange(0.,90,10.)
ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
# draw meridians
meridians = np.arange(0.,60.,10.)
ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)
ash_map.plot(x,y,'k.', ms=1,alpha=.25)



cbar = plt.colorbar(cs, orientation='horizontal')
cbar.set_label("Merra computed dust5 Mass Loading (kg m-2)")
cbar.formatter.set_powerlimits((0, 0))
cbar.update_ticks()

plt.gca().set_aspect('equal', adjustable='box')
plt.xlabel('Longitude',fontsize=15)
plt.ylabel('Lattitude',fontsize=15)
plt.title("Merra computed Total Mass Loading (kg m-2) at %s"%cur_time)

plt.show()
plt.close()
merra_f.close()

print("--- %s seconds ---" % (time.time() - start_time))
