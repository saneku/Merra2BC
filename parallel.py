# -*- coding: utf-8 -*-

from mpi4py import MPI

import re
import os

wrf_out_files_mask="wrfout_d01_2010-0*"
number_of_hours_per_wrfout=72


numbers = re.compile(r'(\d+)')
def numericalSort1(value):
    parts = numbers.split(value)
    return int(parts[3]+parts[5]+parts[7]+parts[9])

def get_wrfout_files(wrf_out_files_mask,wrf_dir):

    comm = MPI.COMM_WORLD
    rank=comm.rank
    size=comm.size

    wrfout_files = None
    chunks = None

    if rank == 0:
        wrfout_files=sorted([f for f in os.listdir(wrf_dir) if re.match(wrf_out_files_mask, f)], key=numericalSort1)
        #print "[%d]: Total number of wrfout-files is %s"% (comm.rank, str(len(wrfout_files)))

        file_indexes = [i for i in range(len(wrfout_files))]
        # dividing data into chunks
        chunks = [[] for _ in range(size)]
        for i, chunk in enumerate(file_indexes):
            chunks[i % size].append(chunk)

    all_wrfout_files = comm.bcast(wrfout_files, root=0)
    wrf_out_files_indexes = comm.scatter(chunks, root=0)

    wrf_out_files={}
    for r in xrange(size):
        if rank == r:
            print "[%d]: %s" % (comm.rank, wrf_out_files_indexes)
            for i in wrf_out_files_indexes:
                #print all_wrfout_files[i]
                wrf_out_files[i]=all_wrfout_files[i]
        #comm.Barrier()

    #wrf_out_files=list(wrf_out_files.values())

    print wrf_out_files_indexes

    return wrf_out_files
