#TODO check that spatial dimensions are covered
#TODO add coefficients
#TODO check species correspondance

import pathes
import time
start_time = time.time()
import merra2_module
import wrf_module
import utils
from netCDF4 import Dataset
import numpy as np

#modules initialisation
merra2_module.initialise()
wrf_module.initialise()

time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()

if(len(time_intersection)!=len(wrf_module.wrf_times)):
    utils.error_message("WRF time range is not fully covered by MERRA2 time range. Exiting...")

#sorting times for processing
time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))


print "START INITIAL CONDITIONS"
cur_time=time_intersection[0]
index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
print "Opening mera file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" with initial time: "+cur_time
merra_f = Dataset(pathes.mera_dir+"/"+merra2_module.get_file_name_by_index(index_of_opened_mera_file),'r')
MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)


#Threaded Horizontal interpolation of Merra pressure on WRF horizontal grid
MER_HOR_PRES=merra2_module.threaded_hor_interpolate_3dfield_on_wrf_grid(MERA_PRES,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)

#Horizontal interpolation of Merra pressure on WRF horizontal grid
#MER_HOR_PRES=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MERA_PRES,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)


print "Opening metfile: "+wrf_module.get_met_file_by_time(cur_time)
metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)

print "Opening wrfintput: "+pathes.wrf_input_file
wrfinput_f=Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r+')

for merra_specie in pathes.chem_map:
    print "\t\t - Reading "+merra_specie+" field from Merra2. It corresponds to "+pathes.chem_map[merra_specie]+" in WRF."
    MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

    #Horizontal interpolation of Merra specie on WRF horizontal grid
    print "\t\t - Horisontal interpolation of "+merra_specie+" on WRF horizontal grid"
    #MER_HOR_SPECIE=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MER_SPECIE,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)

    #Threaded Horizontal interpolation of Merra specie on WRF horizontal grid
    MER_HOR_SPECIE=merra2_module.threaded_hor_interpolate_3dfield_on_wrf_grid(MER_SPECIE,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)

    #Vertical interpolation of MER_HOR_SPECIE on WRF vertical grid
    print "\t\t - Vertical interpolation of "+merra_specie+" on WRF vertical grid"
    WRF_SPECIE=merra2_module.ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE,MER_HOR_PRES,WRF_PRES,wrf_module.nz,wrf_module.ny,wrf_module.nx)
    WRF_SPECIE=np.flipud(WRF_SPECIE)

    print "\t\t - Updating wrfinput by "+merra_specie+" from MERRA2\n"
    wrfinput_f.variables[pathes.chem_map[merra_specie]][0,:]=WRF_SPECIE

print "Closing wrfintput: "+pathes.wrf_input_file
wrfinput_f.close()

print "Closing mera file "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)
merra_f.close()

print "Closing metfile file "+wrf_module.get_met_file_by_time(cur_time)
metfile.close()

print "FINISH INITIAL CONDITIONS"

'''


print "\n\nSTART BOUNDARY CONDITIONS"

print "Opening "+pathes.wrf_bdy_file
wrfbdy_f=Dataset(pathes.wrf_dir+"/"+pathes.wrf_bdy_file,'r+')


cur_time=time_intersection[0]
index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
print "\nOpening MERRA2 file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" file which has index "+str(index_of_opened_mera_file)
merra_f = Dataset(pathes.mera_dir+"/"+merra2_module.get_file_name_by_index(index_of_opened_mera_file),'r')

for cur_time in time_intersection:
    if (merra2_module.get_file_index_by_time(cur_time)!=index_of_opened_mera_file):
        print "Closing prev. opened MERRA2 file with index "+str(index_of_opened_mera_file)
        merra_f.close()

        index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
        print "\nOpening MERRA2 file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" file which has index "+str(index_of_opened_mera_file)
        merra_f = Dataset(pathes.mera_dir+"/"+merra2_module.get_file_name_by_index(index_of_opened_mera_file),'r')

#************
    print "\n\tCur_time="+cur_time
    print "\tReading MERRA Pressure at index "+str(merra2_module.get_index_in_file_by_time(cur_time))
    MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)
    print "\tHorizontal interpolation of MERRA Pressure on WRF boundary"
    MER_HOR_PRES_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MERA_PRES,len(wrf_module.wrf_lons),wrf_module.wrf_lons,wrf_module.wrf_lats)

    print "\tReading WRF Pressure from: "+wrf_module.get_met_file_by_time(cur_time)
    metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
    WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)
    WRF_PRES_BND=np.concatenate((WRF_PRES[:,:,0],WRF_PRES[:,wrf_module.ny-1,:],WRF_PRES[:,:,wrf_module.nx-1],WRF_PRES[:,0,:]), axis=1)
    #TODO UNCOMMENT IT
    metfile.close()

    sp_index=0
    for merra_specie in pathes.chem_map:
        print "\n\t\t - Reading "+merra_specie+" field from MERRA."# It corresponds to "+pathes.chem_map[merra_specie]+" in WRF."
        MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

        print "\t\tHorizontal interpolation of "+merra_specie+" on WRF boundary"
        MER_HOR_SPECIE_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MER_SPECIE,len(wrf_module.wrf_lons),wrf_module.wrf_lons,wrf_module.wrf_lats)

        print "\t\tVertical interpolation of "+merra_specie+" on WRF boundary"
        WRF_SPECIE_BND=merra2_module.ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_module.nz,len(wrf_module.wrf_lons))
        WRF_SPECIE_BND=np.flipud(WRF_SPECIE_BND)

        WRF_SPECIE_LEFT_BND  =WRF_SPECIE_BND[:,0:wrf_module.ny]
        WRF_SPECIE_TOP_BND   =WRF_SPECIE_BND[:,wrf_module.ny:wrf_module.ny+wrf_module.nx]
        WRF_SPECIE_RIGHT_BND =WRF_SPECIE_BND[:,wrf_module.ny+wrf_module.nx:2*wrf_module.ny+wrf_module.nx]
        WRF_SPECIE_BOT_BND   =WRF_SPECIE_BND[:,2*wrf_module.ny+wrf_module.nx:2*wrf_module.ny+2*wrf_module.nx]

        wrfxs=np.repeat(WRF_SPECIE_LEFT_BND[np.newaxis,:,:], wrf_module.nw, axis=0)
        wrfye=np.repeat(WRF_SPECIE_TOP_BND[np.newaxis,:,:], wrf_module.nw, axis=0)
        wrfxe=np.repeat(WRF_SPECIE_RIGHT_BND[np.newaxis,:,:], wrf_module.nw, axis=0)
        wrfys=np.repeat(WRF_SPECIE_BOT_BND[np.newaxis,:,:], wrf_module.nw, axis=0)

        print "\t\t - Updating "+pathes.chem_map[merra_specie]+" in wrfbdy at index "+str(wrf_module.get_index_in_file_by_time(cur_time))
        wrf_module.update_boundaries(wrfxs,wrfye,wrfxe,wrfys,wrfbdy_f,pathes.chem_map[merra_specie],wrf_module.get_index_in_file_by_time(cur_time),sp_index)
        sp_index=sp_index+1


    print("--- %s seconds ---" % (time.time() - start_time))
#************************


print "Closing prev. opened MERRA2 file with index "+str(index_of_opened_mera_file)
merra_f.close()

print "Closing "+pathes.wrf_bdy_file
wrfbdy_f.close()

print "FINISH BOUNDARY CONDITIONS"
'''

print("--- %s seconds ---" % (time.time() - start_time))
