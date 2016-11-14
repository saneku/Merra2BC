__author__ = 'ukhova'

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]


from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import os
import numpy as np
import matplotlib.pyplot as plt
import re
import sys

import pathes
import wrf_module

wrf_module.initialise()

list1 = []

import fnmatch
import os
for file1 in os.listdir(pathes.wrf_dir):
    if fnmatch.fnmatch(file1, 'wrfout_d01_2010*'):
        list1.append(file1)

list1.sort(key=natural_keys)

fig = plt.figure(figsize=(8,8))
ash_map = Basemap(width=wrf_module.dx*wrf_module.nx,height=wrf_module.dy*wrf_module.ny,resolution='l',area_thresh=100.,projection=wrf_module.get_BaseMapProjectionByWrfProjection(), lat_1=wrf_module.true_lat1,lat_2=wrf_module.true_lat2,lat_0=wrf_module.cen_lat,lon_0=wrf_module.cen_lon)
x, y = ash_map(wrf_module.xlon, wrf_module.xlat)

pic_index=0
for index in range(0,len(list1),2):
    print "Reading: "+list1[index]
    
    wrfout = Dataset(pathes.wrf_dir+list1[index],'r')
    times =wrfout.variables['Times'][:]
   
    sum_aod= np.zeros([wrf_module.ny,wrf_module.nx])
    avg_by=np.minimum(len(times),24)
    for time_idx in range(0,avg_by,1):
        print ' '+''.join(times[time_idx])

        z = (wrfout.variables['PH'][time_idx,:] + wrfout.variables['PHB'][time_idx,:]) / 9.81
        dz=np.diff(z,axis=0)
        dz=dz/(1000.0) #dz in km        
        aod=dz*wrfout.variables['TAUAER3'][time_idx,:]
        #aod=dz*wrfout.variables['EXTCOF55'][time_idx,:]
        aod=np.sum(aod, axis=0)
        sum_aod=sum_aod+aod
        
    print "Averaging by "+str(avg_by)+" value's"
    sum_aod=sum_aod/float(avg_by)

    clevs =np.linspace(0, 3.66821,num=100)
    cs = ash_map.contourf(x,y,sum_aod,clevs,cmap=plt.cm.Spectral_r)

    ash_map.drawcoastlines(linewidth=1)
    ash_map.drawmapboundary(linewidth=0.25)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,180.,10.)
    ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("WRF daily averaged by "+str(avg_by)+ " values total AOD, 550 nm")  

    plt.title((''.join(times[0])[:-9]))
    plt.savefig("wrf_avg_aod_"+(''.join(times[0]))+"_"+str(pic_index))        
    plt.clf()
    pic_index=pic_index+1
    
    wrfout.close()
    
plt.close()