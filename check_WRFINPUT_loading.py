#comparing total dust loading with computed based on MERRA2 data
#as it is IC take only first time

import pathes
import time
import wrf_module
start_time = time.time()

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np

g=9.81

#dust bins from wrfinput
dust_array=['DUST_1','DUST_2','DUST_3','DUST_4','DUST_5']

wrf_module.initialise()

'''
wrfinput=Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r')
wrf_p_top=wrfinput.variables['P_TOP'][:]
znu=wrfinput.variables['ZNU'][:]
xlon=wrfinput.variables['XLONG'][0,:]
xlat=wrfinput.variables['XLAT'][0,:]

cur_time=''.join(wrfinput.variables['Times'][0])

nx=wrfinput.dimensions['west_east'].size
ny=wrfinput.dimensions['south_north'].size
nz=wrfinput.dimensions['bottom_top'].size
'''

cur_time=wrf_module.start_time

#total dust contains sum of all dust bins from wrfinput
wrfinput = Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r')
WRF_DUST = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
for dust in dust_array:
    WRF_DUST=WRF_DUST+wrfinput.variables[dust][0,:]


metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
WRF_Pres=wrf_module.get_pressure_from_metfile(metfile)

'''
#Restoring pressure from wrfinput
WRF_PSFC=wrfinput.variables['PSFC'][:]


WRF_Pres = np.zeros([nz,ny,nx])
for z_level in reversed(range(nz)):
    WRF_Pres[nz-1-z_level,:]=WRF_PSFC*znu[0,z_level]+ (1.0 - znu[0,z_level])*wrf_p_top
'''

WRF_DELP=np.diff(WRF_Pres,axis=0)
WRF_DUST=np.delete(WRF_DUST, 0, axis=0)

WRF_DUST=np.flipud(WRF_DUST)

WRF_LOAD=WRF_DELP*WRF_DUST/g
WRF_LOAD=np.sum(WRF_LOAD, axis=0)


fig = plt.figure(figsize=(20,20))
ash_map = Basemap(width=4400000,height=4400000,resolution='l',area_thresh=100.,projection='lcc', lat_1=30.,lat_2=40,lat_0=35,lon_0=25)
ash_map.drawcoastlines(linewidth=1)
ash_map.drawmapboundary(linewidth=0.25)
x, y = ash_map(wrf_module.xlon, wrf_module.xlat)
clevs =np.linspace(0, 5e-3,num=100, endpoint=True)
cs = ash_map.contourf(x,y,WRF_LOAD,clevs,cmap=plt.cm.Spectral_r)

# draw parallels.
parallels = np.arange(0.,90,10.)
ash_map.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
# draw meridians
meridians = np.arange(0.,60.,10.)
ash_map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

#TODO do we need xpt ypt?
xpt,ypt = ash_map(wrf_module.xlon,wrf_module.xlat)
ash_map.plot(xpt,ypt,'k.', ms=1,alpha=.25)

cbar = plt.colorbar(cs, orientation='horizontal')
cbar.set_label("dust loading (kg m-2)")
cbar.formatter.set_powerlimits((0, 0))
cbar.update_ticks()

plt.gca().set_aspect('equal', adjustable='box')
plt.xlabel('Longitude',fontsize=15)
plt.ylabel('Lattitude',fontsize=15)
plt.title("WRF IC. Total dust mass Loading (kg m-2) at %s"%cur_time)

plt.show()
plt.close()


wrfinput.close()


print("--- %s seconds ---" % (time.time() - start_time))
