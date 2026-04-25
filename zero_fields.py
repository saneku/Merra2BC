# -*- coding: utf-8 -*-
from src import config
from src import merra2wrf_mapper
from src import utils
import time
import glob
import re

from netCDF4 import Dataset

start_time = time.time()


zero = 1e-16


def _find_var_case_insensitive(var_names, wanted_name):
    target = str(wanted_name).lower()
    for name in var_names:
        if str(name).lower() == target:
            return name
    return None


def _extract_lbc_time_from_name(file_path):
    basename = file_path.split("/")[-1]
    match = re.search(
        r"lbc\.(\d{4})-(\d{2})-(\d{2})_(\d{2})\.(\d{2})\.(\d{2})", basename
    )
    if not match:
        return basename
    return "{}-{}-{}_{}:{}:{}".format(*match.groups())


merra2wrf_mapper.initialise()
fields_to_zero = sorted(list(merra2wrf_mapper.get_wrf_vars()))
if not fields_to_zero:
    utils.error_message("Species mapping is empty; nothing to zero.")

if not config.do_IC and not config.do_BC:
    print("Nothing to do: both --do_IC and --do_BC are false.")
    print("--- %s seconds ---" % (time.time() - start_time))
    raise SystemExit(0)

if config.target == "wrfchem":
    if config.do_IC:
        print("SETTING TO ZERO INITIAL CONDITIONS")
        wrfinput_path = config.wrf_input_file
        print("Processing wrfinput:", wrfinput_path)
        wrfinput = Dataset(wrfinput_path, "r+")
        for field in fields_to_zero:
            if field not in wrfinput.variables:
                print("Skipping IC field (not found):", field)
                continue
            print("Setting to zero IC for", field)
            wrfinput.variables[field][:] = zero
        wrfinput.close()

    if config.do_BC:
        print("\n\nSETTING TO ZERO BOUNDARY CONDITIONS AND TENDENCIES")
        wrfbdy_path = config.wrf_bdy_file
        print("Processing wrfbdy:", wrfbdy_path)
        wrfbddy = Dataset(wrfbdy_path, "r+")
        for field in fields_to_zero:
            required = [
                field + "_BXS",
                field + "_BXE",
                field + "_BYS",
                field + "_BYE",
                field + "_BTXS",
                field + "_BTXE",
                field + "_BTYS",
                field + "_BTYE",
            ]
            missing = [name for name in required if name not in wrfbddy.variables]
            if missing:
                print("Skipping BC field (missing vars):", field, "->", ",".join(missing))
                continue
            print("Setting to zero BC for", field)
            wrfbddy.variables[field + "_BXS"][:] = zero
            wrfbddy.variables[field + "_BXE"][:] = zero
            wrfbddy.variables[field + "_BYS"][:] = zero
            wrfbddy.variables[field + "_BYE"][:] = zero

            print("Setting to zero Tendency BC for", field)
            wrfbddy.variables[field + "_BTXS"][:] = zero
            wrfbddy.variables[field + "_BTXE"][:] = zero
            wrfbddy.variables[field + "_BTYS"][:] = zero
            wrfbddy.variables[field + "_BTYE"][:] = zero
        wrfbddy.close()

elif config.target == "mpasa":
    if config.do_IC:
        if not config.mpas_init_file:
            utils.error_message(
                "Argument --mpas_init_file is required for --target mpasa when --do_IC=true."
            )
        print("SETTING TO ZERO MPAS INITIAL CONDITIONS")
        print("Processing MPAS init:", config.mpas_init_file)
        init_f = Dataset(config.mpas_init_file, "r+")
        for field in fields_to_zero:
            resolved = _find_var_case_insensitive(init_f.variables.keys(), field)
            if resolved is None:
                print("Skipping MPAS IC field (not found):", field)
                continue
            print("Setting to zero MPAS IC for", resolved)
            init_f.variables[resolved][:] = zero
        init_f.close()

    if config.do_BC:
        if not config.mpas_lbc_files:
            utils.error_message(
                "Argument --mpas_lbc_files is required for --target mpasa when --do_BC=true."
            )

        lbc_files = sorted(glob.glob(config.mpas_lbc_files), key=_extract_lbc_time_from_name)
        if not lbc_files:
            utils.error_message("No lbc files matched mask: " + str(config.mpas_lbc_files))

        print("\n\nSETTING TO ZERO MPAS BOUNDARY CONDITIONS")
        for lbc_path in lbc_files:
            print("Processing MPAS lbc:", lbc_path)
            lbc_f = Dataset(lbc_path, "r+")
            for field in fields_to_zero:
                lbc_name = "lbc_" + str(field)
                resolved = _find_var_case_insensitive(lbc_f.variables.keys(), lbc_name)
                if resolved is None:
                    print("Skipping MPAS BC field (not found):", lbc_name)
                    continue
                print("Setting to zero MPAS BC for", resolved)
                lbc_f.variables[resolved][:] = zero
            lbc_f.close()
else:
    utils.error_message("Unknown --target value: " + str(config.target))

print("--- %s seconds ---" % (time.time() - start_time))
