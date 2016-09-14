#TODO check that spatial dimensions are covered


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


#for cur_time in time_intersection:
    #print "Cur_time="+cur_time+ "\t corresponding metfile: "+wrf_module.get_met_file_by_time(cur_time)
    #print "Opening metfile: "+wrf_module.get_met_file_by_time(cur_time)
    #print wrf_module.get_sfcp_from_met_file(wrf_module.get_met_file_by_time(cur_time))



print "START INITIAL CONDITIONS"
cur_time=time_intersection[0]
index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
print "Opening mera file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" with initial time: "+cur_time
merra_f = Dataset(pathes.mera_dir+"/"+merra2_module.get_file_name_by_index(index_of_opened_mera_file),'r')
MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)


#************************
'''
#left boundary
MER_HOR_PRES_LEFT=merra2_module.hor_interpolate_3dfield_on_wrf_left_and_right_boubdary(MERA_PRES,wrf_module.ny,1,wrf_module.xlon[:,0],wrf_module.xlat[:,0])
#right boubdary
MER_HOR_PRES_RIGHT=merra2_module.hor_interpolate_3dfield_on_wrf_left_and_right_boubdary(MERA_PRES,wrf_module.ny,1,wrf_module.xlon[:,wrf_module.nx-1],wrf_module.xlat[:,wrf_module.nx-1])

#bottom boubdary
MER_HOR_PRES_BOT=merra2_module.hor_interpolate_3dfield_on_wrf_top_and_bottom_boubdary(MERA_PRES,1,wrf_module.nx,wrf_module.xlon[0,:],wrf_module.xlat[0,:])

#top boubdary
MER_HOR_PRES_TOP=merra2_module.hor_interpolate_3dfield_on_wrf_top_and_bottom_boubdary(MERA_PRES,1,wrf_module.nx,wrf_module.xlon[wrf_module.ny-1,:],wrf_module.xlat[wrf_module.ny-1,:])
'''

#left+top+right+bottom boundaries
wrf_lons=np.concatenate((wrf_module.xlon[:,0],wrf_module.xlon[wrf_module.ny-1,:],wrf_module.xlon[:,wrf_module.nx-1],wrf_module.xlon[0,:]), axis=0)
wrf_lats=np.concatenate((wrf_module.xlat[:,0],wrf_module.xlat[wrf_module.ny-1,:],wrf_module.xlat[:,wrf_module.nx-1],wrf_module.xlat[0,:]), axis=0)

MER_HOR_PRES_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MERA_PRES,len(wrf_lons),wrf_lons,wrf_lats)
#MER_HOR_PRES_LEFT  =MER_HOR_PRES_BND[:,0:wrf_module.ny]
#MER_HOR_PRES_TOP   =MER_HOR_PRES_BND[:,wrf_module.ny:wrf_module.ny+wrf_module.nx]
#MER_HOR_PRES_RIGHT =MER_HOR_PRES_BND[:,wrf_module.ny+wrf_module.nx:2*wrf_module.ny+wrf_module.nx]
#MER_HOR_PRES_BOT   =MER_HOR_PRES_BND[:,2*wrf_module.ny+wrf_module.nx:2*wrf_module.ny+2*wrf_module.nx]
#************************


#Horizontal interpolation of Merra pressure on WRF horizontal grid
MER_HOR_PRES=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MERA_PRES,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)
#print "MER_HOR_PRES="
#print MER_HOR_PRES[:,1,1]


print "Opening metfile: "+wrf_module.get_met_file_by_time(cur_time)
metfile= Dataset(pathes.wrf_met_dir+"/"+wrf_module.get_met_file_by_time(cur_time),'r')
WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)
#print "WRF_PRES="
#print WRF_PRES[:,1,1]

print "Opening wrfintput: "+pathes.wrf_input_file
wrfinput_f=Dataset(pathes.wrf_dir+"/"+pathes.wrf_input_file,'r+')

for merra_specie in pathes.chem_map:
    print "\t\t - Reading "+merra_specie+" field from Merra2. It corresponds to "+pathes.chem_map[merra_specie]+" in WRF."
    MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)
    #print "MER_SPECIE="
    #print MER_SPECIE[:,1,1]


    #************************
    WRF_PRES_BND=np.concatenate((WRF_PRES[:,:,0],WRF_PRES[:,wrf_module.ny-1,:],WRF_PRES[:,:,wrf_module.nx-1],WRF_PRES[:,0,:]), axis=1)
    MER_HOR_SPECIE_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MER_SPECIE,len(wrf_lons),wrf_lons,wrf_lats)
    WRF_SPECIE_BND=merra2_module.ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_module.nz,len(wrf_lons))
    #WRF_SPECIE_BND=np.flipud(WRF_SPECIE_BND)

    WRF_SPECIE_LEFT_BND  =WRF_SPECIE_BND[:,0:wrf_module.ny]
    WRF_SPECIE_TOP_BND   =WRF_SPECIE_BND[:,wrf_module.ny:wrf_module.ny+wrf_module.nx]
    WRF_SPECIE_RIGHT_BND =WRF_SPECIE_BND[:,wrf_module.ny+wrf_module.nx:2*wrf_module.ny+wrf_module.nx]
    WRF_SPECIE_BOT_BND   =WRF_SPECIE_BND[:,2*wrf_module.ny+wrf_module.nx:2*wrf_module.ny+2*wrf_module.nx]



    #************************

    #Horizontal interpolation of Merra specie on WRF horizontal grid
    print "\t\t - Horisontal interpolation of "+merra_specie+" on WRF horizontal grid"
    MER_HOR_SPECIE=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MER_SPECIE,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)
    #MER_HOR_SPECIE=np.flipud(MER_HOR_SPECIE)
    #print "MER_HOR_SPECIE="
    #print MER_HOR_SPECIE[:,1,1]

    #Vertical interpolation of MER_HOR_SPECIE on WRF vertical grid
    print "\t\t - Vertical interpolation of "+merra_specie+" on WRF vertical grid"
    WRF_SPECIE=merra2_module.ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE,MER_HOR_PRES,WRF_PRES,wrf_module.nz,wrf_module.ny,wrf_module.nx)
    WRF_SPECIE=np.flipud(WRF_SPECIE)
    #print "WRF_SPECIE="
    #print WRF_SPECIE[:,1,1]

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

print "Opening wrfbdy"
index_of_opened_mera_file=-1
for cur_time in time_intersection:
    print "\n\tCur_time="+cur_time
#    print "Opening MERRA2 file index "+str(merra2_module.get_file_index_by_time(cur_time))+" for reading at index "+str(merra2_module.get_index_in_file_by_time(cur_time))

    if (merra2_module.get_file_index_by_time(cur_time)==index_of_opened_mera_file):
        print "\tReading mera at index "+str(merra2_module.get_index_in_file_by_time(cur_time))
    else:
        print "Closing prev. opened mera file with index "+str(index_of_opened_mera_file)
        index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
        print "Opening "+merra2_module.get_file_name_by_index(merra2_module.get_file_index_by_time(cur_time))+" file which has index "+str(merra2_module.get_file_index_by_time(cur_time))
        print "\tReading mera at index "+str(merra2_module.get_index_in_file_by_time(cur_time))

    print "\tWriting to wrfbdy at index "+str(wrf_module.get_index_in_file_by_time(cur_time))

print "Closing prev. opened mera file with index "+str(index_of_opened_mera_file)
print "Closing wrfbdy"
print "FINISH BOUNDARY CONDITIONS"
'''

print("--- %s seconds ---" % (time.time() - start_time))
