# -*- coding: utf-8 -*-
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import time

import pathes
#pathes.mera_dir="/home/ukhova/Downloads/Merra2ForVISUVI_data/"
#pathes.mera_files="svc_MERRA2_300.inst3_3d_aer*"

start_time = time.time()
import merra2_module
#modules initialisation
merra2_module.initialise()

Ptop_mera=1 #Pa   (=0.01 hPa)

molar_mass_map={'air':29.0,'SO2':64.0,'SO4':96.0,'O3':48.0,'CO':28}  #g mole-1
gas_spec_array=['O3','CO','SO2','SO4']

x_limit={'SO2':0.0020,'SO4':0.0020,'O3':10.0,'CO':0.2}

fig = plt.figure(figsize=(20,20))

file_index=0
merra_files = merra2_module.get_ordered_mera_files_in_mera_dir()
for mf in merra_files:

    print "Processing MERRA2 file: " + mf
    merra_file = Dataset(pathes.mera_dir+"/"+mf,'r')

    mera_start_time=merra_file.RangeBeginningDate
    mera_start_time=datetime.strptime(mera_start_time, '%Y-%m-%d')
    mera_times =merra_file.variables['time'][:] #time in minutes since mera_start_time

    for mera_time_idx in range(0,len(mera_times),1):

        mera_cur_time=str(mera_start_time+timedelta(minutes=mera_times[mera_time_idx]))

        #------------------------------
        #Read Merra Pressure at given time index
        #print "\tReading MERRA2 at: " +mera_cur_time+ " ("+ str(mera_time_idx)+" index in Merra file)"

        #Read Merra Pressure at given time index
        print "\tReading MERRA pressure at: " +mera_cur_time+ " ("+ str(mera_time_idx)+" index in Merra file)"
        MER_Pres = np.zeros([merra2_module.mer_number_of_z_points,merra2_module.mer_number_of_y_points,merra2_module.mer_number_of_x_points])

        #filling top layer with Ptop_mera
        MER_Pres[0,:]=Ptop_mera
        # Extract delta P from NetCDF file
        DELP = merra_file.variables['DELP'][mera_time_idx,:]  #Pa

        for z_level in range(merra2_module.mer_number_of_z_points-1):
            MER_Pres[z_level+1,:]=MER_Pres[z_level,:]+DELP[z_level]

        MER_Pres=(MER_Pres/100.0)  #convert to hPa, 1 hPa = 100 Pa
####
        for merra_specie in gas_spec_array:
            GAS=merra_file.variables[merra_specie][mera_time_idx,:]
            #converting to ppmv
            GAS= 1e6*GAS*(molar_mass_map['air']/molar_mass_map[merra_specie])

            plt.gca().invert_yaxis()

            #plt.gca().set_xlim([0,0.10])
            #plt.gca().set_ylim([0,1000])
            plt.plot(np.mean(GAS, axis=(1,2)),np.mean(MER_Pres, axis=(1,2)),'-o',label=merra_specie+' profile')

            '''
            a=np.empty(72);
            a.fill(5)
            plt.plot(a,np.mean(MER_Pres, axis=(1,2)),'-o')
            '''

            plt.ylabel('Pressure, hPa',fontsize=15)
            plt.xlabel(merra_specie+', ppmv',fontsize=15)
            plt.yscale('log')

            #x1,x2,y1,y2 = plt.axis()
            #print x1,x2,y1,y2

            #x1,x2,y1,y2 = plt.axis()
            #plt.axis((x1,x2,1000,0.01))
            plt.axis((0,x_limit.get(merra_specie),1000,0.01))


            plt.title("Averaged Merra "+merra_specie+" profile (ppmv) at %s"%mera_cur_time)

            #plt.show()
            #OR

            plt.savefig('merra_'+merra_specie+'_profile_%d.png'%(file_index))
            plt.clf()
####
        file_index=file_index+1

    merra_file.close()
    print "\n"


plt.close()
print("--- %s seconds ---" % (time.time() - start_time))
