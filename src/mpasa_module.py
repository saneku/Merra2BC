from . import config
from . import utils
import os
import re
import glob
from netCDF4 import Dataset
import numpy as np


mpas_init_vars = []
mpas_lbc_vars = []

mpas_cell_lons = np.array([])
mpas_cell_lats = np.array([])

mpas_init_time = ""
mpas_lbc_times = {}  # map between time and lbc file path
mpas_lbc_files = []

n_cells = 0
n_vert_levels = 0


P0 = 100000.0
RD = 287.0
CP = 1004.5
RV = 461.6
KAPPA = RD / CP
GAMMA = 1.0 / (1.0 - KAPPA)
EPS = RD / RV

MOLAR_MASS_DRY_AIR = 28.97
MOLAR_MASS = {"co2": 44.01, "ch4": 16.04}


def _decode_nc_chars(char_array):
    data = np.asarray(char_array)
    if data.dtype.kind in ("S", "U"):
        text = data.tobytes().decode("utf-8", errors="ignore")
        return text.replace("\x00", "").strip()
    return str(data).strip()


def _normalize_time(text):
    match = re.search(
        r"(\d{4})-(\d{2})-(\d{2})[_ ](\d{2})[:._](\d{2})[:._](\d{2})",
        str(text),
    )
    if not match:
        raise ValueError("Could not parse MPAS time: " + str(text))
    return "{}-{}-{}_{}:{}:{}".format(*match.groups())


def _extract_lbc_time_from_name(file_path):
    basename = os.path.basename(file_path)
    match = re.search(
        r"lbc\.(\d{4})-(\d{2})-(\d{2})_(\d{2})\.(\d{2})\.(\d{2})", basename
    )
    if not match:
        return None
    return "{}-{}-{}_{}:{}:{}".format(*match.groups())


def _get_var_case_insensitive(nc_file, var_name):
    if var_name in nc_file.variables:
        return nc_file.variables[var_name]

    target = var_name.lower()
    for key in nc_file.variables:
        if key.lower() == target:
            return nc_file.variables[key]

    return None


def _extract_time_from_init(init_file):
    if "xtime" in init_file.variables:
        xtime = init_file.variables["xtime"][:]
        if len(xtime) > 0:
            return _normalize_time(_decode_nc_chars(xtime[0]))

    if "initial_time" in init_file.variables:
        return _normalize_time(_decode_nc_chars(init_file.variables["initial_time"][:]))

    if "Time" in init_file.variables and hasattr(init_file.variables["Time"], "units"):
        units = str(init_file.variables["Time"].units)
        match = re.search(r"since\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})", units)
        if match:
            return "{}_{}:{}:{}".format(match.group(1), match.group(2), match.group(3), match.group(4))

    utils.error_message("Could not determine init time from MPAS init file.")


def _extract_time_from_lbc_file(file_path):
    from_name = _extract_lbc_time_from_name(file_path)
    if from_name is not None:
        return from_name

    lbc_file = Dataset(file_path, "r")
    if "xtime" not in lbc_file.variables:
        lbc_file.close()
        utils.error_message(
            "Could not parse time from lbc file name and xtime is missing: " + str(file_path)
        )

    xtime = lbc_file.variables["xtime"][:]
    if len(xtime) == 0:
        lbc_file.close()
        utils.error_message("xtime is empty in lbc file: " + str(file_path))

    parsed = _normalize_time(_decode_nc_chars(xtime[0]))
    lbc_file.close()
    return parsed


def _sorted_lbc_files_with_times(file_mask):
    matched = glob.glob(file_mask)
    if not matched:
        return []

    decorated = []
    for file_path in matched:
        time_key = _extract_time_from_lbc_file(file_path)
        decorated.append((time_key, file_path))

    decorated.sort(key=lambda pair: pair[0])
    return decorated


def _get_3d_time_slice(var_obj):
    data = np.asarray(var_obj[:])
    dims = tuple(str(name).lower() for name in var_obj.dimensions)

    if data.ndim == 3:
        if len(dims) != 3:
            raise ValueError("Unexpected dimension metadata for " + str(var_obj.name))

        if "time" in dims[0]:
            sliced = data[0, :, :]
            spatial_dims = dims[1:]
        else:
            sliced = data[:, :, :]
            spatial_dims = dims

        if "ncells" in spatial_dims and "nvertlevels" in spatial_dims:
            cell_axis = spatial_dims.index("ncells")
            lev_axis = spatial_dims.index("nvertlevels")
            if (cell_axis, lev_axis) != (0, 1):
                sliced = np.transpose(sliced, (cell_axis, lev_axis))
            return sliced

        return sliced

    if data.ndim == 2:
        if len(dims) == 2 and "ncells" in dims and "nvertlevels" in dims:
            cell_axis = dims.index("ncells")
            lev_axis = dims.index("nvertlevels")
            if (cell_axis, lev_axis) != (0, 1):
                return np.transpose(data, (cell_axis, lev_axis))
        return data[:, :]

    raise ValueError(
        "Unsupported variable rank for "
        + str(var_obj.name)
        + ": "
        + str(data.ndim)
        + ". Expected 2D or 3D."
    )


def _reconstruct_pressure_from_state(rho, theta, qv):
    # MPAS dry-air state relation:
    # p = p0 * (rho * Rd * theta_m / p0)^(cp/cv), theta_m = theta*(1 + qv/eps)
    theta_m = theta * (1.0 + qv / EPS)
    ratio = (rho * RD * theta_m) / P0
    ratio = np.maximum(ratio, 1.0e-12)
    return P0 * np.power(ratio, GAMMA)


def get_init_time():
    return mpas_init_time


def get_lbc_times_ordered():
    return sorted(mpas_lbc_times.keys())


def has_lbc_files():
    return len(mpas_lbc_files) > 0


def get_lbc_file_by_time(time_key):
    return mpas_lbc_times.get(time_key)


def _find_matching_var_name(var_names, requested_name):
    target = requested_name.lower()
    for name in var_names:
        if name.lower() == target:
            return name
    return None


def has_init_var(var_name):
    return _find_matching_var_name(mpas_init_vars, var_name) is not None


def has_lbc_var(var_name):
    return _find_matching_var_name(mpas_lbc_vars, var_name) is not None


def resolve_init_var_name(var_name):
    return _find_matching_var_name(mpas_init_vars, var_name)


def resolve_lbc_var_name(var_name):
    return _find_matching_var_name(mpas_lbc_vars, var_name)


def get_init_pressure(init_file):
    pressure_var = _get_var_case_insensitive(init_file, "pressure")
    if pressure_var is not None:
        return _get_3d_time_slice(pressure_var)

    rho_var = _get_var_case_insensitive(init_file, "rho")
    theta_var = _get_var_case_insensitive(init_file, "theta")
    qv_var = _get_var_case_insensitive(init_file, "qv")

    if rho_var is None or theta_var is None:
        utils.error_message(
            "Could not build MPAS init pressure: need either pressure or rho/theta in init file."
        )

    rho = _get_3d_time_slice(rho_var)
    theta = _get_3d_time_slice(theta_var)
    qv = np.zeros_like(theta)
    if qv_var is not None:
        qv = _get_3d_time_slice(qv_var)

    return _reconstruct_pressure_from_state(rho, theta, qv)


def get_lbc_pressure(lbc_file):
    pressure_var = _get_var_case_insensitive(lbc_file, "lbc_pressure")
    if pressure_var is not None:
        return _get_3d_time_slice(pressure_var)

    rho_var = _get_var_case_insensitive(lbc_file, "lbc_rho")
    theta_var = _get_var_case_insensitive(lbc_file, "lbc_theta")
    qv_var = _get_var_case_insensitive(lbc_file, "lbc_qv")

    if rho_var is None or theta_var is None:
        utils.error_message(
            "Could not build MPAS LBC pressure: need either lbc_pressure or lbc_rho/lbc_theta."
        )

    rho = _get_3d_time_slice(rho_var)
    theta = _get_3d_time_slice(theta_var)
    qv = np.zeros_like(theta)
    if qv_var is not None:
        qv = _get_3d_time_slice(qv_var)

    return _reconstruct_pressure_from_state(rho, theta, qv)


def _coerce_added_shape(added_field, target_shape, field_name):
    data = np.asarray(added_field)

    if data.shape == target_shape:
        return data

    if data.ndim == 2 and data.T.shape == target_shape:
        return data.T

    raise ValueError(
        "Shape mismatch for "
        + str(field_name)
        + ": target "
        + str(target_shape)
        + ", got "
        + str(data.shape)
        + "."
    )


def _normalize_units_text(units):
    return str(units).strip().lower().replace(" ", "")


def _ppmv_to_kgkg(ppmv, species_name):
    key = str(species_name).lower()
    if key not in MOLAR_MASS:
        utils.error_message("Missing molar mass for species: " + str(species_name))
    return float(ppmv) * 1.0e-6 * MOLAR_MASS[key] / MOLAR_MASS_DRY_AIR


def _co2_ch4_value_for_variable_units(var_obj, species_name, ppmv_value):
    units_attr = getattr(var_obj, "units", None)
    if units_attr is None:
        print(
            "WARNING: units attribute missing for "
            + str(var_obj.name)
            + "; assuming kg kg^-1 for "
            + str(species_name)
        )
        return _ppmv_to_kgkg(ppmv_value, species_name), "kg kg^-1 (assumed)"

    units_norm = _normalize_units_text(units_attr)

    if units_norm in {"kgkg-1", "kgkg^{-1}", "kg/kg"}:
        return _ppmv_to_kgkg(ppmv_value, species_name), str(units_attr)

    if units_norm in {"molmol-1", "molmol^{-1}", "mol/mol", "1"}:
        return float(ppmv_value) * 1.0e-6, str(units_attr)

    if "ppmv" in units_norm or units_norm == "ppm":
        return float(ppmv_value), str(units_attr)

    utils.error_message(
        "Unsupported units for "
        + str(var_obj.name)
        + ": "
        + str(units_attr)
        + ". Supported: kg kg^-1, mol mol^-1, or ppmv."
    )


def _set_var_constant(var_obj, value):
    if var_obj.ndim == 3:
        var_obj[:, :, :] = value
        return

    if var_obj.ndim == 2:
        var_obj[:, :] = value
        return

    if var_obj.ndim == 1:
        var_obj[:] = value
        return

    utils.error_message(
        "Unsupported rank for variable " + str(var_obj.name) + ": " + str(var_obj.ndim)
    )


def _require_var_case_insensitive(nc_file, var_name, file_label):
    resolved = _find_matching_var_name(nc_file.variables.keys(), var_name)
    if resolved is None:
        utils.error_message("Could not find variable " + str(var_name) + " in " + str(file_label))
    return resolved, nc_file.variables[resolved]


def init_co2_ch4_ic(init_file, co2_ppmv=400.0, ch4_ppmv=1.7):
    for species_name, ppmv_value in [("co2", co2_ppmv), ("ch4", ch4_ppmv)]:
        resolved, var_obj = _require_var_case_insensitive(init_file, species_name, "MPAS init file")
        value, units_label = _co2_ch4_value_for_variable_units(var_obj, species_name, ppmv_value)
        print(
            "\t\t - Setting MPAS init field "
            + str(resolved)
            + " to "
            + str(value)
            + " ["
            + str(units_label)
            + "] from "
            + str(ppmv_value)
            + " ppmv"
        )
        _set_var_constant(var_obj, value)


def init_co2_ch4_lbc(lbc_file, co2_ppmv=400.0, ch4_ppmv=1.7):
    for species_name, ppmv_value in [("co2", co2_ppmv), ("ch4", ch4_ppmv)]:
        var_name = "lbc_" + str(species_name)
        resolved, var_obj = _require_var_case_insensitive(lbc_file, var_name, "MPAS lbc file")
        value, units_label = _co2_ch4_value_for_variable_units(var_obj, species_name, ppmv_value)
        print(
            "\t\t - Setting MPAS lbc field "
            + str(resolved)
            + " to "
            + str(value)
            + " ["
            + str(units_label)
            + "] from "
            + str(ppmv_value)
            + " ppmv"
        )
        _set_var_constant(var_obj, value)


def update_init_field(init_file, var_name, added_field):
    resolved = _find_matching_var_name(init_file.variables.keys(), var_name)
    if resolved is None:
        utils.error_message("Could not find init variable: " + str(var_name))

    var_obj = init_file.variables[resolved]
    if var_obj.ndim == 3:
        target = var_obj[0, :, :]
        increment = _coerce_added_shape(added_field, target.shape, resolved)
        var_obj[0, :, :] = target + increment
        return

    if var_obj.ndim == 2:
        target = var_obj[:, :]
        increment = _coerce_added_shape(added_field, target.shape, resolved)
        var_obj[:, :] = target + increment
        return

    utils.error_message(
        "Unsupported rank for init variable " + str(resolved) + ": " + str(var_obj.ndim)
    )


def update_lbc_field(lbc_file, var_name, added_field):
    resolved = _find_matching_var_name(lbc_file.variables.keys(), var_name)
    if resolved is None:
        utils.error_message("Could not find lbc variable: " + str(var_name))

    var_obj = lbc_file.variables[resolved]
    if var_obj.ndim == 3:
        target = var_obj[0, :, :]
        increment = _coerce_added_shape(added_field, target.shape, resolved)
        var_obj[0, :, :] = target + increment
        return

    if var_obj.ndim == 2:
        target = var_obj[:, :]
        increment = _coerce_added_shape(added_field, target.shape, resolved)
        var_obj[:, :] = target + increment
        return

    utils.error_message(
        "Unsupported rank for lbc variable " + str(resolved) + ": " + str(var_obj.ndim)
    )


def initialise():
    global mpas_init_vars, mpas_lbc_vars
    global mpas_cell_lons, mpas_cell_lats
    global mpas_init_time, mpas_lbc_times, mpas_lbc_files
    global n_cells, n_vert_levels

    mpas_lbc_times = {}
    mpas_lbc_files = []
    mpas_lbc_vars = []

    if not config.mpas_init_file:
        utils.error_message("Argument --mpas_init_file is required for --target mpasa.")

    if not os.path.isfile(config.mpas_init_file):
        utils.error_message("MPAS init file not found: " + str(config.mpas_init_file))

    init_file = Dataset(config.mpas_init_file, "r")
    mpas_init_vars = [var for var in init_file.variables]

    if "latCell" not in init_file.variables or "lonCell" not in init_file.variables:
        init_file.close()
        utils.error_message("MPAS init file must contain latCell/lonCell.")

    mpas_cell_lats = np.asarray(init_file.variables["latCell"][:]) * 180.0 / np.pi
    mpas_cell_lons = np.asarray(init_file.variables["lonCell"][:]) * 180.0 / np.pi
    mpas_cell_lons = ((mpas_cell_lons + 180.0) % 360.0) - 180.0

    if "nCells" not in init_file.dimensions or "nVertLevels" not in init_file.dimensions:
        init_file.close()
        utils.error_message("MPAS init dimensions nCells/nVertLevels are missing.")

    n_cells = len(init_file.dimensions["nCells"])
    n_vert_levels = len(init_file.dimensions["nVertLevels"])
    mpas_init_time = _extract_time_from_init(init_file)
    init_file.close()

    if config.mpas_lbc_files:
        lbc_with_times = _sorted_lbc_files_with_times(config.mpas_lbc_files)
        mpas_lbc_files = [pair[1] for pair in lbc_with_times]
        for pair in lbc_with_times:
            mpas_lbc_times.update({pair[0]: pair[1]})

        if mpas_lbc_files:
            lbc_file = Dataset(mpas_lbc_files[0], "r")
            mpas_lbc_vars = [var for var in lbc_file.variables]
            lbc_file.close()

    if config.do_BC and not mpas_lbc_files:
        utils.error_message(
            "--do_BC=true for --target mpasa requires --mpas_lbc_files pointing to lbc.*.nc files."
        )

    print(
        "MPAS dimensions: [nVertLevels]="
        + str(n_vert_levels)
        + " [nCells]="
        + str(n_cells)
        + " [lbc files]="
        + str(len(mpas_lbc_files))
    )
    print("MPAS init time: " + str(mpas_init_time))
