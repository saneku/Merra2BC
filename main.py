
import time
start_time = time.time()
import merra2_module
import wrf_module
import utils

#print merra2_module.get_ordered_mera_files_in_mera_dir()

#print wrf_module.get_ordered_met_files()



merra2_module.initialise()
wrf_module.initialise()


'''
print merra2_module.mera_times
print "\n"
print wrf_module.wrf_times
print "\n"
'''


time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()

if(len(time_intersection)!=len(wrf_module.wrf_times)):
    utils.error_message("WRF time range is not fully covered by MERRA2 time range. Exiting...")

#sorting times for processing
time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))


print "START INITIAL CONDITIONS"
cur_time=time_intersection[0]
index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
print "Opening mera file "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" with initial time: "+cur_time
print "Opening wrfinput"
print "INTERPOLATION"
print "Closing prev. opened mera file "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)
print "Saving wrfinput"
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
