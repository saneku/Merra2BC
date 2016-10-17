#comparing total dust loading with computed based on MERRA2 data
#as it is IC take only first time

import pathes
import time
import wrf_module
import merra2_module
start_time = time.time()

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np

g=9.81

gas_spec_array=['so2','sulf']
molar_mass_map={'air':29.0,'so2':64.0,'sulf':96.0}  #g mole-1

merra2_module.initialise()
wrf_module.initialise()
time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()
#sorting times for processing
time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))

cur_time=time_intersection[0]

wrfinput = Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r')

metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
WRF_Pres=wrf_module.get_pressure_from_metfile(metfile)

WRF_DELP=np.diff(WRF_Pres,axis=0)

fig = plt.figure(figsize=(20,20))
ash_map = Basemap(width=wrf_module.dx*wrf_module.nx,height=wrf_module.dy*wrf_module.ny,resolution='l',area_thresh=100.,projection=wrf_module.get_BaseMapProjectionByWrfProjection(), lat_1=wrf_module.true_lat1,lat_2=wrf_module.true_lat2,lat_0=wrf_module.cen_lat,lon_0=wrf_module.cen_lon)

for gas in gas_spec_array:
    #WRF_GAS = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
    WRF_GAS=wrfinput.variables[gas][0,:]

    WRF_GAS=np.delete(WRF_GAS, 0, axis=0)

    WRF_GAS=np.flipud(WRF_GAS)

    #converting to kg/kg from ppmv
    WRF_GAS=WRF_GAS*1e-6*molar_mass_map[gas]/molar_mass_map['air']


    WRF_LOAD=WRF_DELP*WRF_GAS/g
    WRF_LOAD=np.sum(WRF_LOAD, axis=0)

    ash_map.drawcoastlines(linewidth=1)
    ash_map.drawmapboundary(linewidth=0.25)

    x, y = ash_map(wrf_module.xlon, wrf_module.xlat)
    clevs =np.linspace(0, 7e-5,num=100, endpoint=True)
    cs = ash_map.contourf(x,y,WRF_LOAD,clevs,cmap=plt.cm.Spectral_r)
    ash_map.plot(x,y,'k.', ms=1,alpha=0.1)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,180.,10.)
    ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("dust loading (kg m-2)")
    cbar.formatter.set_powerlimits((0, 0))
    cbar.update_ticks()

    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlabel('Longitude',fontsize=15)
    plt.ylabel('Lattitude',fontsize=15)
    plt.title("WRF IC. "+gas+" mass Loading (kg m-2) at %s"%cur_time)

    #plt.show()
    print 'processing wrfinput_'+gas+'_loading.png'
    plt.savefig('wrfinput_'+gas+'_loading.png')
    plt.clf()

plt.close()

metfile.close()
wrfinput.close()


print("--- %s seconds ---" % (time.time() - start_time))
