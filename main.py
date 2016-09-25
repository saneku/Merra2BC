#TODO if there is a dublicate in WRF scpes in spc_map
#TODO if there is a dublicate in MERRA specs in spc_map
#TODO draw map according to domain dimensions
import pathes
import time
start_time = time.time()
import merra2_module
import wrf_module
import merra2wrf_mapper
import utils
from netCDF4 import Dataset
import numpy as np
from datetime import datetime
import multiprocessing

#modules initialisation
merra2_module.initialise()
wrf_module.initialise()
merra2wrf_mapper.initialise()

if pathes.enable_threading:
    print "Multiprocessing is active. "+str(pathes.number_of_workers)+" threads out of "+str(multiprocessing.cpu_count())+" will be used."

#-----------------------------
#Sanity checks:
#check species availability in wrf and in merra files
for var in merra2wrf_mapper.get_merra_vars():
    if var not in merra2_module.merra_vars:
        utils.error_message("Could not find variable "+var+" in MERRA2 file. Exiting...")

for var in merra2wrf_mapper.get_wrf_vars():
    if var not in wrf_module.wrf_vars:
        utils.error_message("Could not find variable "+var+" in WRF input file. Exiting...")

#check that spatial dimensions are covered
if((min(wrf_module.wrf_lons)<min(merra2_module.mera_lon))|(max(wrf_module.wrf_lons)>max(merra2_module.mera_lon))|(min(wrf_module.wrf_lats)<min(merra2_module.mera_lat))|(max(wrf_module.wrf_lats)>max(merra2_module.mera_lat))):
    utils.error_message("WRF area is not fully covered by MERRA2 area. Exiting...")
#-----------------------------

time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()

#check that wrf time is covered by merra2 time
if(len(time_intersection)!=len(wrf_module.wrf_times)):
    utils.error_message("WRF time range is not fully covered by MERRA2 time range. Exiting...")

#sorting times for processing
time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))


if pathes.do_IC:
    print "START INITIAL CONDITIONS"
    cur_time=time_intersection[0]
    index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
    print "Opening mera file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" with initial time: "+cur_time
    merra_f = Dataset(pathes.mera_dir+"/"+merra2_module.get_file_name_by_index(index_of_opened_mera_file),'r')
    MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)


    if pathes.enable_threading:
        #Threaded Horizontal interpolation of Merra pressure on WRF horizontal grid
        MER_HOR_PRES=merra2_module.threaded_hor_interpolate_3dfield_on_wrf_grid(MERA_PRES,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)
    else:
        #Horizontal interpolation of Merra pressure on WRF horizontal grid
        MER_HOR_PRES=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MERA_PRES,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)


    print "Opening metfile: "+wrf_module.get_met_file_by_time(cur_time)
    metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
    WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)

    print "Opening wrfintput: "+pathes.wrf_input_file
    wrfinput_f=Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r+')

    for merra_specie in merra2wrf_mapper.get_merra_vars():
        print "\t\t - Reading "+merra_specie+" field from Merra2."
        MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

        print "\t\t - Horisontal interpolation of "+merra_specie+" on WRF horizontal grid"

        if pathes.enable_threading:
            #Threaded Horizontal interpolation of Merra specie on WRF horizontal grid
            MER_HOR_SPECIE=merra2_module.threaded_hor_interpolate_3dfield_on_wrf_grid(MER_SPECIE,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)
        else:
            #Horizontal interpolation of Merra specie on WRF horizontal grid
            MER_HOR_SPECIE=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MER_SPECIE,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)


        #Vertical interpolation of MER_HOR_SPECIE on WRF vertical grid
        print "\t\t - Vertical interpolation of "+merra_specie+" on WRF vertical grid"
        WRF_SPECIE=merra2_module.ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE,MER_HOR_PRES,WRF_PRES,wrf_module.nz,wrf_module.ny,wrf_module.nx)
        WRF_SPECIE=np.flipud(WRF_SPECIE)

        for wrf_name_and_coef in merra2wrf_mapper.get_list_of_wrf_spec_by_merra_var(merra_specie):
            wrf_spec=wrf_name_and_coef[0]
            coef=wrf_name_and_coef[1]
            wrf_mult=merra2wrf_mapper.coefficients[wrf_spec]
            print "\t\t - Updating wrfinput field "+wrf_spec+"[0]="+wrf_spec+"[0]+"+merra_specie+"*"+str(coef)+"*"+str(wrf_mult)+"\n"
            wrfinput_f.variables[wrf_spec][0,:]=wrfinput_f.variables[wrf_spec][0,:]+WRF_SPECIE*coef*wrf_mult


    print "Closing wrfintput: "+pathes.wrf_input_file
    wrfinput_f.close()

    print "Closing mera file "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)
    merra_f.close()

    print "Closing metfile file "+wrf_module.get_met_file_by_time(cur_time)
    metfile.close()

    print "FINISH INITIAL CONDITIONS"


if pathes.do_BC:
    print "\n\nSTART BOUNDARY CONDITIONS"

    print "Opening "+pathes.wrf_bdy_file
    wrfbdy_f=Dataset(pathes.wrf_dir+"/"+pathes.wrf_bdy_file,'r+')

    #difference betweeen two given times
    dt=(datetime.strptime(time_intersection[1], '%Y-%m-%d_%H:%M:%S')-datetime.strptime(time_intersection[0], '%Y-%m-%d_%H:%M:%S')).total_seconds()

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


        print "\n\tCur_time="+cur_time
        print "\tReading MERRA Pressure at index "+str(merra2_module.get_index_in_file_by_time(cur_time))
        MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)

        print "\tHorizontal interpolation of MERRA Pressure on WRF boundary"
        if pathes.enable_threading:
            MER_HOR_PRES_BND=merra2_module.threaded_hor_interpolate_3dfield_on_wrf_boubdary(MERA_PRES,len(wrf_module.wrf_lons),wrf_module.wrf_lons,wrf_module.wrf_lats)
        else:
            MER_HOR_PRES_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MERA_PRES,len(wrf_module.wrf_lons),wrf_module.wrf_lons,wrf_module.wrf_lats)


        print "\tReading WRF Pressure from: "+wrf_module.get_met_file_by_time(cur_time)
        metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
        WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)
        WRF_PRES_BND=np.concatenate((WRF_PRES[:,:,0],WRF_PRES[:,wrf_module.ny-1,:],WRF_PRES[:,:,wrf_module.nx-1],WRF_PRES[:,0,:]), axis=1)
        #TODO UNCOMMENT IT
        metfile.close()

        time_index=wrf_module.get_index_in_file_by_time(cur_time)
        for merra_specie in merra2wrf_mapper.get_merra_vars():
            print "\n\t\t - Reading "+merra_specie+" field from MERRA."
            MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

            print "\t\tHorizontal interpolation of "+merra_specie+" on WRF boundary"
            if pathes.enable_threading:
                MER_HOR_SPECIE_BND=merra2_module.threaded_hor_interpolate_3dfield_on_wrf_boubdary(MER_SPECIE,len(wrf_module.wrf_lons),wrf_module.wrf_lons,wrf_module.wrf_lats)
            else:
                MER_HOR_SPECIE_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MER_SPECIE,len(wrf_module.wrf_lons),wrf_module.wrf_lons,wrf_module.wrf_lats)


            print "\t\tVertical interpolation of "+merra_specie+" on WRF boundary"
            WRF_SPECIE_BND=merra2_module.ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_module.nz,len(wrf_module.wrf_lons))
            WRF_SPECIE_BND=np.flipud(WRF_SPECIE_BND)

            for wrf_name_and_coef in merra2wrf_mapper.get_list_of_wrf_spec_by_merra_var(merra_specie):
                wrf_spec=wrf_name_and_coef[0]
                coef=wrf_name_and_coef[1]
                wrf_mult=merra2wrf_mapper.coefficients[wrf_spec]
                print "\n\t\t - Updating wrfbdy field: "+wrf_spec+"["+str(time_index)+"]="+wrf_spec+"["+str(time_index)+"]+"+merra_specie+"*"+str(coef)+"*"+str(wrf_mult)
                WRF_SPECIE_BND=WRF_SPECIE_BND*coef*wrf_mult
                wrf_module.update_boundaries(WRF_SPECIE_BND,wrfbdy_f,wrf_spec,time_index)

        wrf_sp_index=0
        for wrf_spec in merra2wrf_mapper.get_wrf_vars():
            wrf_module.update_tendency_boundaries(wrfbdy_f,wrf_spec,time_index,dt,wrf_sp_index)
            wrf_sp_index=wrf_sp_index+1


        print("--- %s seconds ---" % (time.time() - start_time))

    print "Closing prev. opened MERRA2 file with index "+str(index_of_opened_mera_file)
    merra_f.close()

    print "Closing "+pathes.wrf_bdy_file
    wrfbdy_f.close()

    print "FINISH BOUNDARY CONDITIONS"


print("--- %s seconds ---" % (time.time() - start_time))
