import argparse

wrf_dir="/lustre2/project/k10022/ukhova/WRF-Climate/run_microphysics/"
wrf_input_file="wrfinput_d01"
wrf_bdy_file="wrfbdy_d01"
wrf_emis_file="wrfqnainp_d01"

wrf_met_dir="/lustre2/project/k10022/ukhova/WPS-4.5/AirQuality_100km/"
wrf_met_files="met_em.d01.*"

#for IC and BC
mera_dir="/scratch/ukhova/merra2/ICBC/"
mera_files="MERRA2_400.inst3_3d_aer_Nv.2016*"

#for emissions
mera_dir="/scratch/ukhova/merra2/emissions/"
mera_files="MERRA2_400.tavg1_2d_adg_Nx.2016*"

do_IC=False
do_BC=False
do_emissions=True

parser = argparse.ArgumentParser(description='Argument parser to preset paramters needed for interpolator')
input_args = parser.add_argument_group('Input arguments')
input_args.add_argument('--wrf_dir', metavar='dir',default=wrf_dir, type=str,  help='WRF dir')
input_args.add_argument('--wrf_input_file', default=wrf_input_file, type=str, help='WRF input file')
input_args.add_argument('--wrf_bdy_file', default=wrf_bdy_file, type=str, help='WRF bdy file')
input_args.add_argument('--wrf_emis_file', default=wrf_emis_file, type=str, help='WRF emission file')

input_args.add_argument('--wrf_met_dir', metavar='dir', default=wrf_met_dir, type=str, help='Met files dir')
input_args.add_argument('--wrf_met_files', default=wrf_met_files, type=str, help='Met files mask')

input_args.add_argument('--mera_dir', metavar='dir', default=mera_dir, type=str, help='Dir with Merra2 files')
input_args.add_argument('--mera_files', default=mera_files, type=str, help='Merra2 files mask')

input_args.add_argument('--do_IC', action='store_true', help='add if initial conditions needs to be updated')
input_args.add_argument('--do_BC', action='store_true', help='add if boundary conditions needs to be updated')
input_args.add_argument('--do_emissions', action='store_true', help='add if emissions needs to be updated')


#Output arguments
#output_args = parser.add_argument_group('Output arguments')
#output_args.add_argument('--solution_dir', metavar='dir', default=solution_dir, type=str,  help='Specify directory to store the pre/post processing and solution')

# Parse the command-line arguments
args = parser.parse_args()

# Iterate through the arguments and assign values to variables using exec
for arg in vars(args):
    value = getattr(args, arg)
    if value is not None:
        exec(f'{arg} = {repr(value)}')

#for Thompson microphysics option mp_physics=28
# !!!!! dust_emis should be 0 !!!!! because we take dust emissions from the MERRA-2
#DU001 "kg kg-1"
#QNIFA "# kg-1"
#QNWFA "# kg-1"

den_dust=[2500.,2650.,2650.,2650.,2650.] #kg/m3
den_dust = [d * 1.0e-3 for d in den_dust]      #in g/cm3
reff_dust=[0.64,1.34,2.32,4.2,7.75]            #microns
diam_dust= [r * 2 * 1.0e-4 for r in reff_dust] #cm

reff_salt=[0.08,0.27,1.05,2.50,7.48]
den_salt=[2200.,2200.,2200.,2200.,2200.]
den_salt = [d * 1.0e-3 for d in den_salt]       #in g/cm3
diam_salt= [r * 2 * 1.0e-4 for r in reff_salt]  #cm

dustmas = [0.001 * (3.141592/6.) * den_dust[i] * diam_dust[i]**3 for i in range(5)] # mass of particle in kg
saltmas = [0.001 * (3.141592/6.) * den_salt[i] * diam_salt[i]**3 for i in range(5)] # mass of particle in kg

###################################
#from table 2 in "Tropospheric Aerosol Optical Thickness from the GOCART Model and Comparisons with Satellite and Sun Photometer Measurements" by M. Chin
#from  supplementary of Randles 2017, The MERRA-2 Aerosol Reanalysis, 1980 Onward. Part I: System Description and Data Assimilation Evaluation 
dens_sulf = 1.8 * 1.0e-3 #in g/cm3
diam_sulf = 0.16*2 * 1.0e-4 # cm
sulfmass = 0.001 * (3.141592/6.) * dens_sulf * diam_sulf**3 #kg

dens_oc = 1.8 * 1.0e-3 #in g/cm3
diam_oc = 0.09 * 2 * 1.0e-4 # cm
ocmass = 0.001 * (3.141592/6.) * dens_oc * diam_oc**3 #kg

dens_bc = 1.0 * 1.0e-3 #in g/cm3
diam_bc = 0.04 * 2 * 1.0e-4 # cm
bcmass = 0.001 * (3.141592/6.) * dens_bc * diam_bc**3 #kg
###################################

#spc_map = [f'QNIFA->{1./dustmas[0]}*[DU001]+{1./dustmas[1]}*[DU002]+{1./dustmas[2]}*[DU003]+{1./dustmas[3]}*[DU004]+{1./dustmas[4]}*[DU005]+{1./bcmass}*[BCPHOBIC]+{1./ocmass}*[OCPHOBIC];1',
#           f'QNWFA->{1./saltmas[0]}*[SS001]+{1./saltmas[1]}*[SS002]+{1./saltmas[2]}*[SS003]+{1./saltmas[3]}*[SS004]+{1./saltmas[4]}*[SS005]+{1./bcmass}*[BCPHILIC]+{1./ocmass}*[OCPHILIC]+{1.0/sulfmass}*[SO4];1']



#https://gmao.gsfc.nasa.gov/pubs/docs/Bosilovich785.pdf
#DUEM001:units = "kg m-2 s-1" ;
#QNWFA2D:units = "kg-1 s-1" ;
air_density=1.2 #kg/m3
dz=130          #height of the 1st layer, meters
coef = 1.0/(dz*air_density)
spc_map = [f'QNIFA2D->{1./dustmas[0]}*[DUEM001]+{1./dustmas[1]}*[DUEM002]+{1./dustmas[2]}*[DUEM003]+{1./dustmas[3]}*[DUEM004]+{1./dustmas[4]}*[DUEM005];{coef}',
           f'QNWFA2D->{1./saltmas[0]}*[SSEM001]+{1./saltmas[1]}*[SSEM002]+{1./saltmas[2]}*[SSEM003]+{1./saltmas[3]}*[SSEM004]+{1./saltmas[4]}*[SSEM005]+{1./bcmass}*[BCEM001]+{1./ocmass}*[OCEM001]+{1.0/sulfmass}*[SUEM001];{coef}']

'''
FOR EMISSIONS
dsrc in kg
! convert dust flux to number concentration (#/kg/s)
! nifa2d = dsrc/dt / dustParticle_mas /cell_air_mass
nifa2d(i,j) = nifa2d(i,j) + dsrc/dt * 1000.0/dustmas/airmas
'''


print (wrf_dir)
print(wrf_input_file)
print(wrf_bdy_file)
print(wrf_emis_file)

print(wrf_met_dir)
print(wrf_met_files)

print(mera_dir)
print(mera_files)

print(do_IC)
print(do_BC)
print(do_emissions)


#exit()
