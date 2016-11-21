# -*- coding: utf-8 -*-
import netCDF4 as nc

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np

import pathes
import wrf_module

#pathes.wrf_dir="/home/ukhova/Apps/WRF/V3.7.1/WRFV3.7.1/run_visuvi_tutorial"
wrf_module.initialise()

nc_fid = nc.MFDataset(pathes.wrf_dir+'/wrfout_d01*')
times =nc_fid.variables['Times'][:]

fig = plt.figure(figsize=(20,20))

ash_map = Basemap(width=wrf_module.dx*wrf_module.nx,height=wrf_module.dy*wrf_module.ny,resolution='l',area_thresh=100.,projection=wrf_module.get_BaseMapProjectionByWrfProjection(), lat_1=wrf_module.true_lat1,lat_2=wrf_module.true_lat2,lat_0=wrf_module.cen_lat,lon_0=wrf_module.cen_lon)
x, y = ash_map(wrf_module.xlon, wrf_module.xlat)

for time_idx in range(0,len(times),1):
    z = (nc_fid.variables['PH'][time_idx,:] + nc_fid.variables['PHB'][time_idx,:]) / 9.81
    dz=np.diff(z,axis=0)
    dz=dz/(1000.0) #dz in km
    aod=dz*nc_fid.variables['EXTCOF55'][time_idx,:]
    aod=np.sum(aod, axis=0)

    ash_map.drawcoastlines(linewidth=1)
    ash_map.drawmapboundary(linewidth=0.25)

    clevs =np.linspace(0, 3.66821,num=100)
    cs = ash_map.contourf(x,y,aod,clevs,cmap=plt.cm.Spectral_r)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,180.,10.)
    ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

	#cs = ash_map.contourf(x,y,aod,100,cmap=plt.cm.Spectral_r)

    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("WRF total AOD, 550 nm")
    cbar.formatter.set_powerlimits((0, 0))
    cbar.update_ticks()

    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlabel('Longitude',fontsize=15)
    plt.ylabel('Lattitude',fontsize=15)
    plt.title("%s on %s" % ("WRF total AOD", ''.join(times[time_idx])))

#    plt.show()
    print 'processing wrf_aod_%d.png'%time_idx
    plt.savefig('wrf_aod_%d.png'%time_idx)
    plt.clf()

plt.close()
nc_fid.close()
