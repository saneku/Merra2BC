# -*- coding: utf-8 -*-
import netCDF4 as nc

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np

import pathes
import wrf_module


dust_array=['oin_a02','oin_a03','oin_a04','oin_a05','oin_a06','oin_a07','oin_a08']

wrf_module.wrf_dir="/home/ukhova/Apps/WRF/V3.7.1/WRFV3.7.1/run_visuvi_tutorial"
wrf_module.initialise()

nc_fid = nc.MFDataset(wrf_module.wrf_dir+'/wrfout*')
times =nc_fid.variables['Times'][:]
znu=nc_fid.variables['ZNU'][0,:]
wrf_p_top=nc_fid.variables['P_TOP'][0]

g=9.81
fig = plt.figure(figsize=(20,20))

ash_map = Basemap(width=wrf_module.dx*wrf_module.nx,height=wrf_module.dy*wrf_module.ny,resolution='l',area_thresh=100.,projection=wrf_module.get_BaseMapProjectionByWrfProjection(), lat_1=wrf_module.true_lat1,lat_2=wrf_module.true_lat2,lat_0=wrf_module.cen_lat,lon_0=wrf_module.cen_lon)
x, y = ash_map(wrf_module.xlon, wrf_module.xlat)


for time_idx in range(0,len(times),1):
    PSFC=nc_fid.variables['PSFC'][time_idx,:]
    WRF_Pres = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
    for z_level in reversed(range(wrf_module.nz)):
        WRF_Pres[wrf_module.nz-1-z_level,:]=PSFC*wrf_module.znu[0,z_level]+ (1.0 - wrf_module.znu[0,z_level])*wrf_p_top
    WRF_DELP=np.diff(WRF_Pres,axis=0)

    WRF_DUST = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
    for dust in dust_array:
        WRF_DUST=WRF_DUST+nc_fid.variables[dust][time_idx,:]


    WRF_DUST=np.delete(WRF_DUST, 0, axis=0)

    WRF_DUST=np.flipud(WRF_DUST)

    #converting to kg/kg
    WRF_DUST=WRF_DUST*1e-9


    WRF_LOAD=WRF_DELP*WRF_DUST/g
    WRF_LOAD=np.sum(WRF_LOAD, axis=0)




    ash_map.drawcoastlines(linewidth=1)
    ash_map.drawmapboundary(linewidth=0.25)

    clevs =np.linspace(0, 5e-3,num=100, endpoint=True)
    cs = ash_map.contourf(x,y,WRF_LOAD,clevs,cmap=plt.cm.Spectral_r)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,60.,10.)
    ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

	#cs = ash_map.contourf(x,y,aod,100,cmap=plt.cm.Spectral_r)

    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("wrfoutput dust loading (kg m-2)")
    cbar.formatter.set_powerlimits((0, 0))
    cbar.update_ticks()

    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlabel('Longitude',fontsize=15)
    plt.ylabel('Lattitude',fontsize=15)


    plt.title("%s on %s" % ("WRF output Total dust mass Loading (kg m-2)", ''.join(times[time_idx])))

#    plt.show()
    print 'processing wrfout_loading_%d.png'%time_idx
    plt.savefig('wrfout_loading_%d.png'%time_idx)
    plt.clf()

plt.close()
nc_fid.close()
