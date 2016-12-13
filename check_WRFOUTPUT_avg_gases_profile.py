# -*- coding: utf-8 -*-
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
import wrf_module


#molar_mass_map={'air':29.0,'so2':64.0,'sulf':96.0,'o3':48.0,'co':28}  #g mole-1
gas_spec_array=['o3','co','so2','sulf']#,'ho']
x_limit={'so2':0.0020,'sulf':0.0020,'o3':10.0,'co':0.2}

wrf_module.wrf_dir="/home/ukhova/Apps/WRF/V3.7.1/WRFV3.7.1/run_visuvi_tutorial/with_BCS"
wrf_module.initialise()

nc_fid = nc.MFDataset(wrf_module.wrf_dir+'/wrfout*')
times =nc_fid.variables['Times'][:]
znu=nc_fid.variables['ZNU'][0,:]
wrf_p_top=nc_fid.variables['P_TOP'][0]


fig = plt.figure(figsize=(8,8))

for time_idx in range(0,len(times),3):
    cur_time=''.join(times[time_idx])
    print "\tReconstructing WRF pressure at: " +cur_time+ " ("+ str(time_idx)+" index in WRFOUT files)"
    PSFC=nc_fid.variables['PSFC'][time_idx,:]
    WRF_Pres = np.zeros([wrf_module.nz,wrf_module.ny,wrf_module.nx])
    for z_level in reversed(range(wrf_module.nz)):
        WRF_Pres[wrf_module.nz-1-z_level,:]=PSFC*wrf_module.znu[0,z_level]+ (1.0 - wrf_module.znu[0,z_level])*wrf_p_top

    WRF_Pres=(WRF_Pres/100.0)  #convert to hPa, 1 hPa = 100 Pa

    for wrf_specie in gas_spec_array:
        GAS=nc_fid.variables[wrf_specie][time_idx,:]
        GAS=np.flipud(GAS)
        plt.gca().invert_yaxis()

        #plt.gca().set_ylim([0,1000])
        plt.plot(np.mean(GAS, axis=(1,2)),np.mean(WRF_Pres, axis=(1,2)),'-o',label=wrf_specie+' profile')

        '''
        a=np.empty(wrf_module.nz);
        a.fill(5)
        plt.plot(a,np.mean(WRF_Pres, axis=(1,2)),'-o')
        '''
        plt.ylabel('Pressure, hPa',fontsize=15)
        plt.xlabel(wrf_specie+', ppmv',fontsize=15)
        plt.yscale('log')

        plt.title("Averaged WRFOUT "+wrf_specie+" profile (ppmv) at %s"%cur_time)

        #x1,x2,y1,y2 = plt.axis()
        plt.axis((0,x_limit.get(wrf_specie),1000,0.01))


        #plt.show()
        #OR
    #    plt.show()
        print 'processing wrfout_'+wrf_specie+'_%d.png'%time_idx
        plt.savefig('wrfout_'+wrf_specie+'_profile_%d.png'%time_idx)
        plt.clf()
        ####

plt.close()
nc_fid.close()
