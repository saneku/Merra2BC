import argparse
import os


wrf_input_file = "/home/WRFV4.1.3/run_tutorial/wrfinput_d01"
wrf_bdy_file = "/home/WRFV4.1.3/run_tutorial/wrfbdy_d01"
wrf_met_files = "/home/WPSV4.1.3/run_tutorial/met_em.d01.2010*"
merra2_files = "/home/Merra2_data/svc_MERRA2_300.inst3_3d_aer_Nv.2010*"
mpas_init_file = ""
mpas_lbc_files = ""

do_IC = False
do_BC = False
init_co2_ch4 = False

# Runtime targets:
# - wrfchem: IC + BC in wrfinput/wrfbdy
# - mpasa: IC in init file and BC in lbc files (regional runs)
target = "wrfchem"
mapping_profile = ""


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _default_mapping_profile_for_target(model_target):
    return os.path.join(_repo_root(), "maps", model_target + ".map")


def _fallback_species_map_for_target(model_target):
    if model_target == "mpasa":
        return [
            "so2 -> 1.0*[so2];1.0",
            "o3 -> 1.0*[o3];1.0",
            "co -> 1.0*[co];0.966862271",
            "dust_1 -> 1.0*[du001];1.0",
        ]

    # wrfchem default (legacy hardcoded map kept for backwards compatibility)
    return [
        "DUST_1 -> 1.0*[du001];1.e9",
        "DUST_2 -> 1.0*[du002];1.e9",
        "DUST_3 -> 1.0*[du003];1.e9",
        "DUST_4 -> 1.0*[du004];1.e9",
        "DUST_5 -> 1.0*[du005];1.e9",
        "SEAS_1 -> 1.0*[ss002];1.e9",
        "SEAS_2 -> 1.0*[ss003];1.e9",
        "SEAS_3 -> 1.0*[ss004];1.e9",
        "SEAS_4 -> 1.0*[ss005];1.e9",
        "so2 -> 0.453*[so2];1.e6",
        "sulf -> 0.302*[so4];1.e6",
        "BC1 -> 1.0*[bcphobic];1.e9",
        "BC2 -> 1.0*[bcphilic];1.e9",
        "OC1 -> 1.0*[ocphobic];1.e9",
        "OC2 -> 1.0*[ocphilic];1.e9",
        "dms -> 0.467*[dms];1.e6",
        "msa -> 0.302*[msa];1.e6",
        "nh3 -> 1.701*[nh3];1.e6",
        "co2 -> 1.0*[co2];1.e6",
    ]


def _load_species_map_lines(map_file):
    mapping_lines = []
    with open(map_file, "r", encoding="utf-8") as stream:
        for raw_line in stream:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            mapping_lines.append(stripped)
    return mapping_lines


def _resolve_species_map(model_target, map_file):
    if map_file and os.path.isfile(map_file):
        loaded = _load_species_map_lines(map_file)
        if loaded:
            return loaded

    if map_file:
        print(
            "WARNING: mapping profile file was not found or empty: "
            + str(map_file)
            + ". Falling back to built-in mapping."
        )
    return _fallback_species_map_for_target(model_target)


def _apply_cli_overrides():
    global wrf_input_file, wrf_bdy_file
    global wrf_met_files
    global merra2_files
    global mpas_init_file, mpas_lbc_files
    global do_IC, do_BC, init_co2_ch4
    global target, mapping_profile

    parser = argparse.ArgumentParser(
        description="MERRA2 chemistry interpolator settings"
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
        "--mpas_init_file",
        default=mpas_init_file,
        type=str,
        help="Full path to MPAS init file (required for --target mpasa)",
    )
    parser.add_argument(
        "--mpas_lbc_files",
        default=mpas_lbc_files,
        type=str,
        help="Path mask for MPAS lbc files (glob; required when --target mpasa and --do_BC=true)",
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
    parser.add_argument(
        "--target",
        default=target,
        type=str.lower,
        choices=("wrfchem", "mpasa"),
        help="Output model target",
    )
    parser.add_argument(
        "--mapping_profile",
        default=mapping_profile,
        type=str,
        help="Path to species mapping profile (.map). If omitted, uses maps/<target>.map",
    )

    args, _ = parser.parse_known_args()

    wrf_input_file = args.wrf_input_file
    wrf_bdy_file = args.wrf_bdy_file
    wrf_met_files = args.wrf_met_files
    merra2_files = args.merra2_files
    mpas_init_file = args.mpas_init_file
    mpas_lbc_files = args.mpas_lbc_files
    do_IC = args.do_IC == "true"
    do_BC = args.do_BC == "true"
    init_co2_ch4 = args.init_co2_ch4 == "true"

    target = args.target
    if args.mapping_profile:
        mapping_profile = args.mapping_profile
    else:
        mapping_profile = _default_mapping_profile_for_target(target)


_apply_cli_overrides()

spc_map = _resolve_species_map(target, mapping_profile)
