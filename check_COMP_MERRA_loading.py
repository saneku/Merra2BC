# -*- coding: utf-8 -*-
import pathes
import time
start_time = time.time()
import merra2_module
from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from datetime import datetime, timedelta

#modules initialisation
merra2_module.initialise()

g=9.81
dust_array=['DU001','DU002','DU003','DU004','DU005']


fig = plt.figure(figsize=(20,20))
#ash_map = Basemap(projection='cyl',llcrnrlat=10,urcrnrlat=60,llcrnrlon=0,urcrnrlon=50,resolution='c',area_thresh=100.)
ash_map = Basemap(projection='cyl',llcrnrlon=min(merra2_module.mera_lon), llcrnrlat=min(merra2_module.mera_lat), urcrnrlon=max(merra2_module.mera_lon), urcrnrlat=max(merra2_module.mera_lat),resolution='l',area_thresh=100.)

lons,lats= np.meshgrid(merra2_module.mera_lon,merra2_module.mera_lat)
x, y = ash_map(lons,lats)

index=0
merra_files = merra2_module.get_ordered_mera_files_in_mera_dir()
for merra_f in merra_files:
    print "Processing MERRA2 file: " + merra_f
    mf = Dataset(pathes.mera_dir+"/"+merra_f,'r')

    mera_start_time=mf.RangeBeginningDate
    mera_start_time=datetime.strptime(mera_start_time, '%Y-%m-%d')
    mera_times =mf.variables['time'][:] #time in minutes since mera_start_time

    for mera_time_idx in range(0,len(mera_times),1):
        ash_map.drawcoastlines(linewidth=1)
        ash_map.drawmapboundary(linewidth=0.25)

        mera_cur_time=str(mera_start_time+timedelta(minutes=mera_times[mera_time_idx]))

        #MERA_DELP=merra2_module.get_3dfield_by_time(mera_time_idx,mf,"DELP")
        MERA_DELP=mf.variables['DELP'][mera_time_idx,:,:]

        #total dust contains sum of all dust bins from MERRA2
        MER_DUST = np.zeros([merra2_module.mer_number_of_z_points,merra2_module.mer_number_of_y_points,merra2_module.mer_number_of_x_points])
        for merra_specie in dust_array:
            #MER_DUST=MER_DUST+merra2_module.get_3dfield_by_time(mera_time_idx,mf,merra_specie)
            MER_DUST=MER_DUST+mf.variables[merra_specie][mera_time_idx,:,:]#   merra2_module.get_3dfield_by_time(mera_time_idx,mf,merra_specie)


        MERRA_LOAD=MERA_DELP*MER_DUST/g
        MERRA_LOAD=np.sum(MERRA_LOAD, axis=0)

        clevs =np.linspace(0, 5e-3,num=100, endpoint=True)
        cs = ash_map.contourf(x,y,MERRA_LOAD,clevs,cmap=plt.cm.Spectral_r)

        # draw parallels.
        parallels = np.arange(0.,90,10.)
        ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
        # draw meridians
        meridians = np.arange(0.,180.,10.)
        ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)
        ash_map.plot(x,y,'k.', ms=1,alpha=.25)



        cbar = plt.colorbar(cs, orientation='horizontal')
        cbar.set_label("Merra computed dust Mass Loading (kg m-2)")
        cbar.formatter.set_powerlimits((0, 0))
        cbar.update_ticks()

        plt.gca().set_aspect('equal', adjustable='box')
        plt.xlabel('Longitude',fontsize=15)
        plt.ylabel('Lattitude',fontsize=15)
        plt.title("Merra computed Total Mass Loading (kg m-2) at %s"%mera_cur_time)

        print "\t " + mera_cur_time

        plt.savefig('merra_comp_loading_%d.png'%(index))
        plt.clf()
        index=index+1

    mf.close()

#plt.show()
plt.close()


print("--- %s seconds ---" % (time.time() - start_time))
