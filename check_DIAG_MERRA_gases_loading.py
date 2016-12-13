# -*- coding: utf-8 -*-
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from mpl_toolkits.basemap import Basemap
import time

start_time = time.time()

gas_spec_array=['SO2CMASS','SO4CMASS']#,'TO3']
x_limit={'SO2CMASS':7e-5,'SO4CMASS':7e-5,'TO3':4e-3}

coefficient={'SO2CMASS':1.0,'SO4CMASS':1.0,'TO3':2.1e-5}
#1 DU = 2.6867×10^20 molecules/m^2 or 0.4462×10^-3 moles/m^2
#for Ozone 0.4462×10^-3 * 48 g/mole=21.4176×10^-3 g/m^2
# => 1 DU=2.1*10^-5 kg/m^2

import pathes
pathes.mera_dir="/home/ukhova/Downloads/Merra2ForVISUVI_data/Diagnostic"
pathes.mera_files="MERRA2_300.tavg1_2d_aer_Nx*"

import merra2_module
merra2_module.initialise()

#---------------------------
fig = plt.figure(figsize=(20,20))
ash_map = Basemap(projection='cyl',llcrnrlon=min(merra2_module.mera_lon), llcrnrlat=min(merra2_module.mera_lat), urcrnrlon=max(merra2_module.mera_lon), urcrnrlat=max(merra2_module.mera_lat),resolution='l',area_thresh=100.)

lons,lats=np.meshgrid(merra2_module.mera_lon,merra2_module.mera_lat)
x, y = ash_map(lons,lats)

index=0
merra_files = merra2_module.get_ordered_mera_files_in_mera_dir()
for mf in merra_files:

    print "Processing MERRA2 diagnostic file: " + mf
    merra_file = Dataset(pathes.mera_dir+"/"+mf,'r')

    mera_start_time=merra_file.RangeBeginningDate
    mera_start_time=datetime.strptime(mera_start_time, '%Y-%m-%d')
    mera_times =merra_file.variables['time'][:] #time in minutes since mera_start_time

    for mera_time_idx in range(0,len(mera_times),3):
        mera_cur_time=str(mera_start_time+timedelta(minutes=mera_times[mera_time_idx]))

        for gas in gas_spec_array:
            MERRA_LOAD = merra_file.variables[gas][mera_time_idx,:,:];

            MERRA_LOAD=MERRA_LOAD*coefficient.get(gas)

            clevs =np.linspace(0, x_limit.get(gas),num=100, endpoint=True)
            cs = ash_map.contourf(x,y,MERRA_LOAD,clevs,cmap=plt.cm.Spectral_r)

            ash_map.drawcoastlines(linewidth=1)
            ash_map.drawmapboundary(linewidth=0.25)

            # draw parallels.
            parallels = np.arange(-90.,90.,10.)
            ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
            # draw meridians
            meridians = np.arange(0.,360.,10.)
            ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)
            #ash_map.plot(x,y,'k.', ms=1,alpha=.25)

            cbar = plt.colorbar(cs, orientation='horizontal')
            cbar.set_label("Merra diag. "+gas+" Mass Loading (kg m-2)")
            cbar.formatter.set_powerlimits((0, 0))
            cbar.update_ticks()

            plt.gca().set_aspect('equal', adjustable='box')
            plt.xlabel('Longitude',fontsize=15)
            plt.ylabel('Lattitude',fontsize=15)
            plt.title("Merra diag. "+gas+" Mass Loading (kg m-2) at %s"%mera_cur_time)

            plt.savefig('merra_diag_%s_loading_%d.png'%(gas,index))
            plt.clf()
        index=index+1
        print "\t " + mera_cur_time

    merra_file.close()

#plt.show()
plt.close()

print("--- %s seconds ---" % (time.time() - start_time))
