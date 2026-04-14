import argparse

wrf_input_file="/home/WRFV4.1.3/run_tutorial/wrfinput_d01"
wrf_bdy_file="/home/WRFV4.1.3/run_tutorial/wrfbdy_d01"

wrf_met_files="/home/WPSV4.1.3/run_tutorial/met_em.d01.2010*"

merra2_files="/home/Merra2_data/svc_MERRA2_300.inst3_3d_aer_Nv.2010*"

do_IC=False
do_BC=False
init_co2_ch4=False


def _apply_cli_overrides():
    global wrf_input_file, wrf_bdy_file
    global wrf_met_files
    global merra2_files
    global do_IC, do_BC, init_co2_ch4

    parser = argparse.ArgumentParser(
        description="MERRA2 to WRF boundary/initial condition interpolator settings"
    )

    parser.add_argument(
        "--wrf_input_file",
        default=wrf_input_file,
        type=str,
        help="Full path to wrfinput file",
    )
    parser.add_argument(
        "--wrf_bdy_file",
        default=wrf_bdy_file,
        type=str,
        help="Full path to wrfbdy file",
    )
    parser.add_argument(
        "--wrf_met_files",
        default=wrf_met_files,
        type=str,
        help="Path mask for met_em files (glob)",
    )
    parser.add_argument(
        "--merra2_files",
        default=merra2_files,
        type=str,
        help="Path mask for MERRA2 files (glob)",
    )

    parser.add_argument(
        "--do_IC",
        default=str(do_IC).lower(),
        type=str.lower,
        choices=("true", "false"),
        metavar="{true,false}",
        help="Enable/disable initial-condition update (true/false)",
    )
    parser.add_argument(
        "--do_BC",
        default=str(do_BC).lower(),
        type=str.lower,
        choices=("true", "false"),
        metavar="{true,false}",
        help="Enable/disable boundary-condition update (true/false)",
    )
    parser.add_argument(
        "--init_co2_ch4",
        default=str(init_co2_ch4).lower(),
        type=str.lower,
        choices=("true", "false"),
        metavar="{true,false}",
        help="Set fixed CO2/CH4 ppmv fields in IC/BC (true/false)",
    )

    args, _ = parser.parse_known_args()

    wrf_input_file = args.wrf_input_file
    wrf_bdy_file = args.wrf_bdy_file
    wrf_met_files = args.wrf_met_files
    merra2_files = args.merra2_files
    do_IC = args.do_IC == "true"
    do_BC = args.do_BC == "true"
    init_co2_ch4 = args.init_co2_ch4 == "true"


_apply_cli_overrides()

###########################################
#MAPPING FROM GEOS-FP to GOCART
spc_map = [ 'DUST_1 -> 1.0*[du001];1.e9',
            'DUST_2 -> 1.0*[du002];1.e9',
            'DUST_3 -> 1.0*[du003];1.e9',
            'DUST_4 -> 1.0*[du004];1.e9',
            'DUST_5 -> 1.0*[du005];1.e9',
            'SEAS_1 -> 1.0*[ss002];1.e9',
            'SEAS_2 -> 1.0*[ss003];1.e9',
            'SEAS_3 -> 1.0*[ss004];1.e9',
            'SEAS_4 -> 1.0*[ss005];1.e9',
            'so2 -> 0.453*[so2];1.e6',
            'sulf -> 0.302*[so4];1.e6',
            'BC1 -> 1.0*[bcphobic];1.e9',
            'BC2 -> 1.0*[bcphilic];1.e9',
            'OC1 -> 1.0*[ocphobic];1.e9', 
            'OC2 -> 1.0*[ocphilic];1.e9',
            'dms -> 0.467*[dms];1.e6',
            'msa -> 0.302*[msa];1.e6',
            'nh3 -> 1.701*[nh3];1.e6',
            'co2 -> 1.0*[co2];1.e6']

#MERRA2_400.inst3_3d_chm_Nv.*
#spc_map = [ 'o3 -> 0.604*[O3];1.e6','co -> 1.0*[CO];1.e6']