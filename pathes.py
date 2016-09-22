wrf_dir="/home/ukhova/Downloads/"
wrf_input_file="wrfinput_d01"
wrf_bdy_file="wrfbdy_d01"

wrf_met_dir="/home/ukhova/Downloads/"
wrf_met_files="met_em.d01.2010*"

mera_dir="/home/ukhova/Downloads/Merra2ForVISUVI/"
mera_files="svc_MERRA2_300.inst3_3d_aer_Nv.20100*"

number_of_workers=18
enable_threading=True

do_IC=True
do_BC=True


#mapping between MERRA2 species and WRF species
#chem_map      ={'DU001':'DUST_1','DU002':'DUST_2','DU003':'DUST_3','DU004':'DUST_4','DU005':'DUST_5'}
#coefficients  ={'DU001':1e9,'DU002':1e9,'DU003':1e9,'DU004':1e9,'DU005':1e9}


'''
spec=[
'num_a01 -> 1.*OC1+3.59e17*OC2+3.11e18*SOA+8.51e17*CB1+2.51e17*CB2+3.65e16*SO4+3.04e16*NH4NO3+6.86e15*NH4;1.0',
'num_a02->1.20e17*OC1+1.20e17*OC2+1.44e18*SOA+1.47e17*CB1+1.47e17*CB2+6.70e16*SO4+5.59e16*NH4NO3+1.26e16*NH4+3.62e17*SA1+7.13e17*[DUST1];1',
'num_a08->6.22e08*OC1+6.22e08*OC2+7.46e09*SOA+2.65e04*CB1+2.65e04*CB2+4.12e10*SO4+3.43e10*NH4NO3+7.74e09*NH4+2.40e13*[DUST4];1',
'OC2 -> .4143*OC2;1.e9',
'DUST_1 -> 1.1738*[DUST1];1.e9',
'DUST_2 -> .939*[DUST2];1.e9',
'DUST_3 -> .2348*[DUST2]+.939*[DUST3];1.e9',
'DUST_5 -> .5869*[DUST4];1.e9',
'SEAS_1 -> 2.*SA1;1.e9',
]
'''

#FOR GOCART DUST ONLY
spc_map = [ 'DUST_1 -> 1*[DU001];1.e9',
            'DUST_2 -> 1*[DU002];1.e9',
            'DUST_3 -> 1.*[DU003];1.e9',
            'DUST_4 -> 1*[DU004];1.e9',
            'DUST_5 -> 1.0*[DU005];1.e9']
