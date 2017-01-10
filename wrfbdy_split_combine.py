import config
from netCDF4 import Dataset
import numpy as np
import os

#from parutils import pprint
from mpi4py import MPI
comm = MPI.COMM_WORLD

def split_wrfbdy(size):
    wrf_times=[]
    wrfbddy = Dataset(pathes.wrf_dir+"/"+pathes.wrf_bdy_file,'r')
    for i in range(0,len(wrfbddy.variables['Times'][:]),1):
        wrf_times.append(''.join(wrfbddy.variables['Times'][i]))
    wrfbddy.close()

    index=0
    for i in np.array_split(range(len(wrf_times)),size):
        print "Creating temps wrfbdy's"+pathes.wrf_dir+"/"+pathes.wrf_bdy_file+"_"+str(index)
        os.system("ncks -d Time,"+str(i[0])+","+str(i[len(i)-1])+" "+pathes.wrf_dir+"/"+pathes.wrf_bdy_file+" "+pathes.wrf_dir+"/"+pathes.wrf_bdy_file+"_"+str(index))
        index=index+1

def concat_wrfbdy(size):
    command="ncrcat -h "
    for index in range(size):
        command=command+pathes.wrf_dir+pathes.wrf_bdy_file+"_"+str(index)+" "
        print "Combining temps "+pathes.wrf_dir+pathes.wrf_bdy_file+"_"+str(index)
    command=command+pathes.wrf_dir+pathes.wrf_bdy_file+"_int"
    print command
    os.system(command)

    command="rm "
    for index in range(size):
        command=command+pathes.wrf_dir+pathes.wrf_bdy_file+"_"+str(index)+" "
        print "Cleaning temps "+pathes.wrf_dir+pathes.wrf_bdy_file+"_"+str(index)
    print command
    os.system(command)
#

comm.Barrier()
#start = MPI.Wtime()

size=comm.size
rank=comm.rank

print(" Rank [%d] from %d running in total..." % (comm.rank, comm.size))

if rank==0:
    split_wrfbdy(size)

comm.Barrier()
#changing wrfbdy filename
pathes.wrf_bdy_file=pathes.wrf_bdy_file+"_"+str(rank)
#print "["+str(rank)+"]"
print "Working with "+pathes.wrf_bdy_file


#if rank==0:
#    concat_wrfbdy(size)


#mpirun -np 2 --output-filename Proc python ./main.py &
