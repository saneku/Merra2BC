# -*- coding: utf-8 -*-
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os
import re
import time
from mpl_toolkits.basemap import Basemap

start_time = time.time()

import pathes
pathes.mera_dir="/home/ukhova/Downloads/Merra2ForVISUVI_data/Diagnostic"
pathes.mera_files="MERRA2_300.tavg1_2d_aer_Nx*"
gas="SO2CMASS"# SO4CMASS
x_limit={'SO2CMASS':4e-2,'SO4CMASS':3e-4,'o3':4e-3}


import merra2_module
merra2_module.initialise()

#---------------------------
fig = plt.figure(figsize=(8,8))
#ash_map = Basemap(projection='merc',llcrnrlat=10,urcrnrlat=60,llcrnrlon=0,urcrnrlon=50,resolution='c',area_thresh=100.)
#ash_map = Basemap(width=4400000,height=4400000,resolution='l',area_thresh=100.,projection='lcc', lat_1=30.,lat_2=40,lat_0=35,lon_0=25)
ash_map = Basemap(projection='cyl',llcrnrlon=min(merra2_module.mera_lon), llcrnrlat=min(merra2_module.mera_lat), urcrnrlon=max(merra2_module.mera_lon), urcrnrlat=max(merra2_module.mera_lat),resolution='l',area_thresh=100.)


lons,lats=np.meshgrid(merra2_module.mera_lon,merra2_module.mera_lat)
x, y = ash_map(lons,lats)

findex=0
merra_files = merra2_module.get_ordered_mera_files_in_mera_dir()
#for mf in merra_files:
for index in range(0,len(merra_files),6):
    mf=merra_files[index]
    print "Processing MERRA2 diagnostic file: " + mf
    merra_file = Dataset(pathes.mera_dir+"/"+mf,'r')

    mera_start_time=merra_file.RangeBeginningDate
    mera_start_time=datetime.strptime(mera_start_time, '%Y-%m-%d')
    mera_times =merra_file.variables['time'][:] #time in minutes since mera_start_time

    avg_by=0
    sum_gas= np.zeros([merra2_module.mer_number_of_y_points,merra2_module.mer_number_of_x_points])
    for mera_time_idx in range(0,len(mera_times),1):

        mera_cur_time=str(mera_start_time+timedelta(minutes=mera_times[mera_time_idx]))

        #GAS loading
        sum_gas = sum_gas + merra_file.variables[gas][mera_time_idx,:,:];

        avg_by=avg_by+1
        print "\t " + mera_cur_time

    print "Averaging "+gas+" by "+str(avg_by)+" value's"
    sum_gas=sum_gas/float(avg_by)


    #clevs =np.linspace(0, x_limit.get(gas),num=100, endpoint=True)
    #cs = ash_map.contourf(x,y,sum_gas,clevs,cmap=plt.cm.Spectral_r)
    cs = ash_map.contourf(x,y,sum_gas,100,cmap=plt.cm.Spectral_r)

    ash_map.drawcoastlines(linewidth=1)
    ash_map.drawmapboundary(linewidth=0.25)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,180.,10.)
    ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

    #xpt,ypt = ash_map(14.42,40.82) # Location of visuvi
    #ash_map.plot(xpt,ypt,'bo')  # plot a blue dot there

    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("Merra2 Diag daily averaged "+gas+" loading by "+str(avg_by)+ " values")
    cbar.formatter.set_powerlimits((0, 0))
    cbar.update_ticks()

    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlabel('Longitude',fontsize=10)
    plt.ylabel('Lattitude',fontsize=10)


#        plt.title("%s on %s" % ("MERA diag:dust extinction AOT, 550nm", mera_cur_time))
    plt.title(mera_cur_time[:-9])
    plt.savefig('merra_diag_'+gas+'_avg_loading_%d.png'%(findex))
    plt.clf()
    findex=findex+1

    #plt.show()
    merra_file.close()

plt.close()
print("--- %s seconds ---" % (time.time() - start_time))
