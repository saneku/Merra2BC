# -*- coding: utf-8 -*-
import netCDF4 as nc
from netCDF4 import Dataset
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np

import pathes
import wrf_module

#gas_spec_array=['so2','sulf','o3']
gas='so2'
molar_mass_map={'air':29.0,'so2':64.0,'sulf':96.0,'o3':48.0}  #g mole-1

x_limit={'so2':4e-2,'sulf':3e-4,'o3':4e-3}


#wrf_module.wrf_dir="/home/ukhova/Apps/WRF/V3.7.1/WRFV3.7.1/run_visuvi_tutorial/with_BCS"
wrf_module.initialise()


#--------------------------
import re
def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split('(\d+)', text) ]

list1 = []
import fnmatch
import os
for file1 in os.listdir(pathes.wrf_dir):
    if fnmatch.fnmatch(file1, 'wrfout_d01_2010*'):
        list1.append(file1)

list1.sort(key=natural_keys)
#--------------------------

g=9.81
fig = plt.figure(figsize=(8,8))

ash_map = Basemap(width=wrf_module.dx*wrf_module.nx,height=wrf_module.dy*wrf_module.ny,resolution='l',area_thresh=100.,projection=wrf_module.get_BaseMapProjectionByWrfProjection(), lat_1=wrf_module.true_lat1,lat_2=wrf_module.true_lat2,lat_0=wrf_module.cen_lat,lon_0=wrf_module.cen_lon)
x, y = ash_map(wrf_module.xlon, wrf_module.xlat)


pic_index=0
for index in range(0,len(list1),2):
    print "Reading: "+list1[index]

    nc_fid = Dataset(pathes.wrf_dir+list1[index],'r')
    times =nc_fid.variables['Times'][:]

    sum_gas= np.zeros([wrf_module.ny,wrf_module.nx])
    avg_by=np.minimum(len(times),24)
    for time_idx in range(0,avg_by,1):
        print ' '+''.join(times[time_idx])

        PSFC=nc_fid.variables['PSFC'][time_idx,:]
        WRF_Pres = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
        for z_level in reversed(range(wrf_module.nz)):
            WRF_Pres[wrf_module.nz-1-z_level,:]=PSFC*wrf_module.znu[0,z_level]+ (1.0 - wrf_module.znu[0,z_level])*wrf_module.wrf_p_top
        WRF_DELP=np.diff(WRF_Pres,axis=0)

        #for gas in gas_spec_array:
        WRF_GAS=nc_fid.variables[gas][time_idx,:]

        WRF_GAS=np.delete(WRF_GAS, 0, axis=0)
        WRF_GAS=np.flipud(WRF_GAS)

        #converting to kg/kg from ppmv
        WRF_GAS=WRF_GAS*1e-6*molar_mass_map[gas]/molar_mass_map['air']

        WRF_LOAD=WRF_DELP*WRF_GAS/g
        sum_gas=sum_gas+np.sum(WRF_LOAD, axis=0)

    print "Averaging "+gas+" by "+str(avg_by)+" value's"
    sum_gas=sum_gas/float(avg_by)

    clevs =np.linspace(0, x_limit.get(gas),num=100, endpoint=True)
    cs = ash_map.contourf(x,y,sum_gas,clevs,cmap=plt.cm.Spectral_r)
    #cs = ash_map.contourf(x,y,sum_gas,100,cmap=plt.cm.Spectral_r)

    ash_map.drawcoastlines(linewidth=1)
    ash_map.drawmapboundary(linewidth=0.25)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,180.,10.)
    ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

	#cs = ash_map.contourf(x,y,aod,100,cmap=plt.cm.Spectral_r)

    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("wrfoutput averaged "+gas+" loading (kg m-2)")
    cbar.formatter.set_powerlimits((0, 0))
    cbar.update_ticks()

    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlabel('Longitude',fontsize=10)
    plt.ylabel('Lattitude',fontsize=10)


    plt.title("%s on %s" % ("WRFOUTPUT averaged "+gas+" Loading (kg m-2)", ''.join(times[time_idx])))

#    plt.show()
    print 'Saving wrfout_'+gas+'_avg_loading_%d.png'%pic_index
    plt.savefig('wrfout_'+gas+'_avg_loading_%d.png'%pic_index)
    plt.clf()
    pic_index=pic_index+1


plt.close()
nc_fid.close()
