wrf_dir="/home/ukhova/Downloads/"
wrf_input_file="wrfinput_d01"
wrf_bdy_file="wrfbdy_d01"

wrf_met_dir="/home/ukhova/Downloads/"
wrf_met_files="met_em.d01.2010*"

mera_dir="/home/ukhova/Downloads/Merra2ForVISUVI_data/"
mera_files="svc_MERRA2_300.inst3_3d_aer_Nv.20100*"

number_of_workers=18 #depending on the number of availble cores recomended values are: 2,4,6,8,12,18,24
enable_threading=False

do_IC=True
do_BC=True

#GOCART DUST ONLY
spc_map = [ 'DUST_1 -> 1*[DU001];1.e9',
            'DUST_2 -> 1*[DU002];1.e9',
            'DUST_3 -> 1.*[DU003];1.e9',
            'DUST_4 -> 1*[DU004];1.e9',
            'DUST_5 -> 1.0*[DU005];1.e9']


#CBMZ-MOSAIC_8bins  DUST only
spc_map =['oin_a02->4.92e-4*[DU001];1.e9',
          'oin_a03->8.94e-3*[DU001];1.e9',
          'oin_a04->0.14300*[DU001];1.e9',
          'oin_a05->0.84740*[DU001]+0.1520*[DU002];1.e9',
          'oin_a06->0.84800*[DU002]+0.4055*[DU003];1.e9',
          'oin_a07->0.59450*[DU003]+0.4480*[DU004];1.e9',
          'oin_a08->0.55200*[DU004]+1*[DU005];1.e9',

          'num_a02->0.213e14*[DU001];1',
          'num_a03->0.598e14*[DU001];1',
          'num_a04->1.192e14*[DU001];1',
          'num_a05->1.434e14*[DU001]+0.948e13*[DU002];1',
          'num_a06->2.086e13*[DU002]+0.358e13*[DU003];1',
          'num_a07->0.255e13*[DU003]+0.592e12*[DU004];1',
          'num_a08->0.296e12*[DU004]+1.655e11*[DU005];1']
