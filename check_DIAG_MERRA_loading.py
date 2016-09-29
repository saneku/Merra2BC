# -*- coding: utf-8 -*-
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from mpl_toolkits.basemap import Basemap
import time

start_time = time.time()

g=9.81
path="/home/ukhova/Downloads/Merra2ForVISUVI_data/Diagnostic/MERRA2_300.tavg1_2d_aer_Nx.20100714.SUB.nc4"

merra_file = Dataset(path,'r')
mer_number_of_x_points=merra_file.variables['lon'].size
mer_number_of_y_points=merra_file.variables['lat'].size

mera_lon  = merra_file.variables['lon'][:]
mera_lat  = merra_file.variables['lat'][:]
lons,lats= np.meshgrid(mera_lon,mera_lat)


#---------------------------
fig = plt.figure(figsize=(20,20))
#ash_map = Basemap(projection='cyl',llcrnrlat=10,urcrnrlat=60,llcrnrlon=0,urcrnrlon=50,resolution='c',area_thresh=100.)
ash_map = Basemap(projection='cyl',llcrnrlon=min(mera_lon), llcrnrlat=min(mera_lat), urcrnrlon=max(mera_lon), urcrnrlat=max(mera_lat),resolution='c',area_thresh=100.)
ash_map.drawcoastlines(linewidth=1)
ash_map.drawmapboundary(linewidth=0.25)
x, y = ash_map(lons,lats)

mera_start_time=merra_file.RangeBeginningDate
mera_start_time=datetime.strptime(mera_start_time, '%Y-%m-%d')
cur_time=str(mera_start_time+timedelta(minutes=0))
mera_time_idx=0

MERRA_LOAD = merra_file.variables['DUCMASS'][mera_time_idx,:,:];

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
cbar.set_label("Merra diag. dust5 Mass Loading (kg m-2)")
cbar.formatter.set_powerlimits((0, 0))
cbar.update_ticks()

plt.gca().set_aspect('equal', adjustable='box')
plt.xlabel('Longitude',fontsize=15)
plt.ylabel('Lattitude',fontsize=15)
plt.title("Merra diag. Total Mass Loading (kg m-2) at %s"%cur_time)

plt.show()
plt.close()
merra_file.close()



print("--- %s seconds ---" % (time.time() - start_time))
