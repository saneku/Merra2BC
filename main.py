#TODO if there is a dublicate in WRF scpes in spc_map
#TODO if there is a dublicate in MERRA specs in spc_map

import sys
from src import config
import time
start_time = time.time()
from src import merra2_module
from src import wrf_module
from src import mpasa_module
from src import merra2wrf_mapper
from src import utils
from netCDF4 import Dataset
import numpy as np
from datetime import datetime


def _cli_option_provided(option_name):
    return any(
        arg == option_name or arg.startswith(option_name + "=")
        for arg in sys.argv[1:]
    )


def _require_merra_species_available():
    available = set(str(name).lower() for name in merra2_module.merra_vars)
    for var in merra2wrf_mapper.get_merra_vars():
        if str(var).lower() not in available:
            utils.error_message(
                "Could not find variable "
                + str(var)
                + " in MERRA2 files. Exiting..."
            )


def _sort_unique_times(time_keys):
    uniq = sorted(set(time_keys), key=lambda x: time.mktime(time.strptime(x, "%Y-%m-%d_%H:%M:%S")))
    return uniq


def _print_missing_times(required_times, available_times):
    missing = [time_key for time_key in required_times if time_key not in available_times]
    if missing:
        print("These datetimes are missing in MERRA2 dataset:")
        for item in missing:
            print(item)
    return missing


def _align_periodic_lons_to_source_range(target_lons, source_lons):
    target_lons = np.asarray(target_lons, dtype=np.float64)
    source_lons = np.asarray(source_lons, dtype=np.float64)

    min_lon = float(np.min(source_lons))
    max_lon = float(np.max(source_lons))
    center = 0.5 * (min_lon + max_lon)

    candidates = np.stack((target_lons, target_lons - 360.0, target_lons + 360.0), axis=0)
    idx = np.argmin(np.abs(candidates - center), axis=0)
    aligned = np.take_along_axis(candidates, idx[np.newaxis, :], axis=0)[0]

    return np.clip(aligned, min_lon, max_lon)


def _vertical_interpolate_columns(src_field, src_pressure, dst_pressure):
    src_field = np.asarray(src_field)
    src_pressure = np.asarray(src_pressure)
    dst_pressure = np.asarray(dst_pressure)

    if src_field.shape != src_pressure.shape:
        raise ValueError(
            "Source field/pressure shape mismatch: "
            + str(src_field.shape)
            + " vs "
            + str(src_pressure.shape)
        )

    if src_field.ndim != 2 or dst_pressure.ndim != 2:
        raise ValueError("Vertical interpolation expects 2D [nLev, nPoint] arrays.")

    n_dst_lev = dst_pressure.shape[0]
    n_points = dst_pressure.shape[1]

    if src_field.shape[1] != n_points:
        raise ValueError(
            "Point-count mismatch between source and destination columns: "
            + str(src_field.shape[1])
            + " vs "
            + str(n_points)
        )

    out = np.zeros([n_dst_lev, n_points], dtype=np.float64)

    for i in range(0, n_points):
        xp = np.asarray(src_pressure[:, i], dtype=np.float64)
        fp = np.asarray(src_field[:, i], dtype=np.float64)
        x = np.asarray(dst_pressure[:, i], dtype=np.float64)

        valid = np.isfinite(xp) & np.isfinite(fp)
        if np.count_nonzero(valid) < 2:
            fallback = 0.0
            if np.count_nonzero(valid) == 1:
                fallback = fp[valid][0]
            out[:, i] = fallback
            continue

        xp = xp[valid]
        fp = fp[valid]

        order = np.argsort(xp)
        xp = xp[order]
        fp = fp[order]

        xp, unique_idx = np.unique(xp, return_index=True)
        fp = fp[unique_idx]

        if xp.size < 2:
            out[:, i] = fp[0]
            continue

        x_safe = x.copy()
        finite_dst = np.isfinite(x_safe)
        if not np.any(finite_dst):
            out[:, i] = fp[0]
            continue

        x_safe[~finite_dst] = xp[0]
        interpolated = np.interp(x_safe, xp, fp, left=fp[0], right=fp[-1])
        interpolated[~finite_dst] = fp[0]
        out[:, i] = interpolated

    return out


def run_wrfchem():
    if not _cli_option_provided("--wrf_input_file"):
        utils.error_message(
            "Argument --wrf_input_file is required for main.py, even when --do_IC=false."
        )

    merra2_module.initialise()
    wrf_module.initialise()
    merra2wrf_mapper.initialise()

    #check species availability in wrf and in merra files
    for var in merra2wrf_mapper.get_merra_vars():
        if var not in merra2_module.merra_vars:
            utils.error_message("Could not find variable "+var+" in MERRA2 file. Exiting...")

    for var in merra2wrf_mapper.get_wrf_vars():
        if var not in wrf_module.wrf_vars:
            utils.error_message("Could not find variable "+var+" in WRF input file. Exiting...")

    #check that spatial dimensions are covered
    if((min(wrf_module.wrf_bnd_lons)<min(merra2_module.mera_lon))|(max(wrf_module.wrf_bnd_lons)>max(merra2_module.mera_lon))|(min(wrf_module.wrf_bnd_lats)<min(merra2_module.mera_lat))|(max(wrf_module.wrf_bnd_lats)>max(merra2_module.mera_lat))):
        utils.error_message("WRF area is not fully covered by MERRA2 area. Exiting...")

    if sys.version_info[0] < 3:
        time_intersection=wrf_module.wrf_times.viewkeys() & merra2_module.mera_times.viewkeys()
    else:
        time_intersection=wrf_module.wrf_times.keys() & merra2_module.mera_times.keys()

    #check that merra2 time is covered by wrf time
    if(len(time_intersection)!=len(wrf_module.wrf_times)):
        print('These datetimes are missing in MERRA2 dataset:')
        time_intersection = dict.fromkeys(time_intersection, 0)
        for key in wrf_module.wrf_times.keys():
            if not key in time_intersection:
                print (key)
        utils.error_message("WRF time range is not fully covered by MERRA2 time range. Exiting...")

    #sorting times for processing
    time_intersection=sorted(time_intersection, key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d_%H:%M:%S")))

    print ("\nTimes for processing:")
    for i in time_intersection:
        print (i)

    if config.do_IC:
        print ("START INITIAL CONDITIONS")
        cur_time=time_intersection[0]
        index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
        print ("Opening mera file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" with initial time: "+cur_time)
        print (merra2_module.get_file_path_by_index(index_of_opened_mera_file))
        merra_f = Dataset(merra2_module.get_file_path_by_index(index_of_opened_mera_file),'r')
        MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)

        #Horizontal interpolation of Merra pressure on WRF horizontal grid
        MER_HOR_PRES=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MERA_PRES,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)

        print ("Opening metfile: "+wrf_module.get_met_file_by_time(cur_time))
        metfile= Dataset(wrf_module.get_met_file_by_time(cur_time),'r')
        WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)

        print ("Opening wrfintput: "+config.wrf_input_file)
        wrfinput_f=Dataset(config.wrf_input_file,'r+')

        for merra_specie in merra2wrf_mapper.get_merra_vars():
            print ("\t\t - Reading "+merra_specie+" field from Merra2.")
            MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

            print ("\t\t - Horisontal interpolation of "+merra_specie+" on WRF horizontal grid")
            MER_HOR_SPECIE=merra2_module.hor_interpolate_3dfield_on_wrf_grid(MER_SPECIE,wrf_module.ny,wrf_module.nx,wrf_module.xlon,wrf_module.xlat)

            print ("\t\t - Vertical interpolation of "+merra_specie+" on WRF vertical grid")
            WRF_SPECIE=merra2_module.ver_interpolate_3dfield_on_wrf_grid(MER_HOR_SPECIE,MER_HOR_PRES,WRF_PRES,wrf_module.nz,wrf_module.ny,wrf_module.nx)
            WRF_SPECIE=np.flipud(WRF_SPECIE)

            for wrf_name_and_coef in merra2wrf_mapper.get_list_of_wrf_spec_by_merra_var(merra_specie):
                wrf_spec=wrf_name_and_coef[0]
                coef=wrf_name_and_coef[1]
                wrf_mult=merra2wrf_mapper.coefficients[wrf_spec]
                print ("\t\t - Updating wrfinput field "+wrf_spec+"[0]="+wrf_spec+"[0]+"+merra_specie+"*"+str(coef)+"*"+str(wrf_mult))
                wrfinput_f.variables[wrf_spec][0,:]=wrfinput_f.variables[wrf_spec][0,:]+WRF_SPECIE*coef*wrf_mult

        if config.init_co2_ch4:
            wrf_module.init_co2_ch4_ic(wrfinput_f)

        print ("Closing wrfintput: "+config.wrf_input_file)
        wrfinput_f.close()

        print ("Closing mera file "+merra2_module.get_file_name_by_index(index_of_opened_mera_file))
        merra_f.close()

        print ("Closing metfile "+wrf_module.get_met_file_by_time(cur_time))
        metfile.close()

        print ("FINISH INITIAL CONDITIONS")


    if config.do_BC:
        print ("\n\nSTART BOUNDARY CONDITIONS")

        print ("Opening "+config.wrf_bdy_file)
        wrfbdy_f=Dataset(config.wrf_bdy_file,'r+')

        #difference betweeen two given times
        dt=(datetime.strptime(time_intersection[1], '%Y-%m-%d_%H:%M:%S')-datetime.strptime(time_intersection[0], '%Y-%m-%d_%H:%M:%S')).total_seconds()

        cur_time=time_intersection[0]
        index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
        print ("\nOpening MERRA2 file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" file which has index "+str(index_of_opened_mera_file))
        merra_f = Dataset(merra2_module.get_file_path_by_index(index_of_opened_mera_file),'r')

        for cur_time in time_intersection:
            if (merra2_module.get_file_index_by_time(cur_time)!=index_of_opened_mera_file):
                print ("Closing prev. opened MERRA2 file with index "+str(index_of_opened_mera_file))
                merra_f.close()

                index_of_opened_mera_file=merra2_module.get_file_index_by_time(cur_time)
                print ("\nOpening MERRA2 file: "+merra2_module.get_file_name_by_index(index_of_opened_mera_file)+" file which has index "+str(index_of_opened_mera_file))
                merra_f = Dataset(merra2_module.get_file_path_by_index(index_of_opened_mera_file),'r')


            print ("\n\tCur_time="+cur_time)
            print ("\tReading MERRA Pressure at index "+str(merra2_module.get_index_in_file_by_time(cur_time)))
            MERA_PRES=merra2_module.get_pressure_by_time(cur_time,merra_f)

            print ("\tHorizontal interpolation of MERRA Pressure on WRF boundary")
            MER_HOR_PRES_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MERA_PRES,len(wrf_module.wrf_bnd_lons),wrf_module.wrf_bnd_lons,wrf_module.wrf_bnd_lats)

            print ("\tReading WRF Pressure from: "+wrf_module.get_met_file_by_time(cur_time))
            metfile= Dataset(wrf_module.get_met_file_by_time(cur_time),'r')
            WRF_PRES=wrf_module.get_pressure_from_metfile(metfile)
            WRF_PRES_BND=np.concatenate((WRF_PRES[:,:,0],WRF_PRES[:,wrf_module.ny-1,:],WRF_PRES[:,:,wrf_module.nx-1],WRF_PRES[:,0,:]), axis=1)
            metfile.close()

            time_index=wrf_module.get_index_in_file_by_time(cur_time)
            for merra_specie in merra2wrf_mapper.get_merra_vars():
                print ("\n\t\t - Reading "+merra_specie+" field from MERRA.")
                MER_SPECIE=merra2_module.get_3dfield_by_time(cur_time,merra_f,merra_specie)

                print ("\t\tHorizontal interpolation of "+merra_specie+" on WRF boundary")
                MER_HOR_SPECIE_BND=merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(MER_SPECIE,len(wrf_module.wrf_bnd_lons),wrf_module.wrf_bnd_lons,wrf_module.wrf_bnd_lats)

                print ("\t\tVertical interpolation of "+merra_specie+" on WRF boundary")
                WRF_SPECIE_BND=merra2_module.ver_interpolate_3dfield_on_wrf_boubdary(MER_HOR_SPECIE_BND,MER_HOR_PRES_BND,WRF_PRES_BND,wrf_module.nz,len(wrf_module.wrf_bnd_lons))
                WRF_SPECIE_BND=np.flipud(WRF_SPECIE_BND)

                for wrf_name_and_coef in merra2wrf_mapper.get_list_of_wrf_spec_by_merra_var(merra_specie):
                    wrf_spec=wrf_name_and_coef[0]
                    coef=wrf_name_and_coef[1]
                    wrf_mult=merra2wrf_mapper.coefficients[wrf_spec]
                    print ("\t\t - Updating wrfbdy field: "+wrf_spec+"["+str(time_index)+"]="+wrf_spec+"["+str(time_index)+"]+"+merra_specie+"*"+str(coef)+"*"+str(wrf_mult))
                    wrf_module.update_boundaries(WRF_SPECIE_BND*coef*wrf_mult,wrfbdy_f,wrf_spec,time_index)

            wrf_sp_index=0
            for wrf_spec in merra2wrf_mapper.get_wrf_vars():
                wrf_module.update_tendency_boundaries(wrfbdy_f,wrf_spec,time_index,dt,wrf_sp_index)
                wrf_sp_index=wrf_sp_index+1

            #print("--- %s seconds ---" % (time.time() - start_time))

        print ("Closing prev. opened MERRA2 file with index "+str(index_of_opened_mera_file))
        merra_f.close()

        if config.init_co2_ch4:
            wrf_module.init_co2_ch4_bc(wrfbdy_f)

        print ("Closing "+config.wrf_bdy_file)
        wrfbdy_f.close()

        print("FINISH BOUNDARY CONDITIONS")


def run_mpasa():
    merra2_module.initialise()
    mpasa_module.initialise()
    merra2wrf_mapper.initialise()

    _require_merra_species_available()

    for var in merra2wrf_mapper.get_wrf_vars():
        if config.do_IC and (not mpasa_module.has_init_var(var)):
            utils.error_message(
                "Could not find variable "
                + str(var)
                + " in MPAS init file "
                + str(config.mpas_init_file)
                + ". Exiting..."
            )

        lbc_name = "lbc_" + str(var)
        if config.do_BC and (not mpasa_module.has_lbc_var(lbc_name)):
            utils.error_message(
                "Could not find variable "
                + str(lbc_name)
                + " in MPAS lbc files. Exiting..."
            )

    merra_lons = np.asarray(merra2_module.mera_lon, dtype=np.float64)
    merra_lats = np.asarray(merra2_module.mera_lat, dtype=np.float64)
    lon_step = float(np.median(np.abs(np.diff(np.sort(merra_lons))))) if merra_lons.size > 1 else 1.0
    lat_step = float(np.median(np.abs(np.diff(np.sort(merra_lats))))) if merra_lats.size > 1 else 1.0
    lon_tol = max(1.0e-6, lon_step)
    lat_tol = max(1.0e-6, lat_step)

    mpas_lons_for_merra = _align_periodic_lons_to_source_range(mpasa_module.mpas_cell_lons, merra_lons)
    mpas_lats_for_merra = np.asarray(mpasa_module.mpas_cell_lats, dtype=np.float64)

    if (
        (min(mpas_lons_for_merra) < min(merra_lons) - lon_tol)
        or (max(mpas_lons_for_merra) > max(merra_lons) + lon_tol)
        or (min(mpas_lats_for_merra) < min(merra_lats) - lat_tol)
        or (max(mpas_lats_for_merra) > max(merra_lats) + lat_tol)
    ):
        utils.error_message("MPAS area is not fully covered by MERRA2 area. Exiting...")

    requested_times = []
    if config.do_IC:
        requested_times.append(mpasa_module.get_init_time())
    if config.do_BC:
        requested_times.extend(mpasa_module.get_lbc_times_ordered())
    requested_times = _sort_unique_times(requested_times)

    if not requested_times:
        print("Nothing to do: both --do_IC and --do_BC are false.")
        return

    missing = _print_missing_times(requested_times, merra2_module.mera_times)
    if missing:
        utils.error_message("Requested MPAS times are not fully covered by MERRA2 time range. Exiting...")

    print("\nTimes for processing:")
    for item in requested_times:
        print(item)

    index_of_opened_mera_file = None
    merra_f = None

    def _open_merra_for_time(time_key):
        nonlocal index_of_opened_mera_file
        nonlocal merra_f

        needed_index = merra2_module.get_file_index_by_time(time_key)
        if needed_index is None:
            utils.error_message("Could not resolve MERRA2 file for time " + str(time_key))

        if index_of_opened_mera_file == needed_index and merra_f is not None:
            return

        if merra_f is not None:
            print("Closing prev. opened MERRA2 file with index " + str(index_of_opened_mera_file))
            merra_f.close()

        index_of_opened_mera_file = needed_index
        print(
            "Opening MERRA2 file: "
            + merra2_module.get_file_name_by_index(index_of_opened_mera_file)
            + " file which has index "
            + str(index_of_opened_mera_file)
        )
        merra_f = Dataset(merra2_module.get_file_path_by_index(index_of_opened_mera_file), "r")

    if config.do_IC:
        cur_time = mpasa_module.get_init_time()
        print("\nSTART MPAS INITIAL CONDITIONS")
        print("Cur_time=" + str(cur_time))
        _open_merra_for_time(cur_time)

        print("\tReading MERRA pressure")
        MERA_PRES = merra2_module.get_pressure_by_time(cur_time, merra_f)
        print("\tHorizontal interpolation of MERRA pressure on MPAS cells")
        MER_HOR_PRES = merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(
            MERA_PRES,
            mpasa_module.n_cells,
            mpas_lons_for_merra,
            mpas_lats_for_merra,
        )

        print("Opening MPAS init file: " + str(config.mpas_init_file))
        init_f = Dataset(config.mpas_init_file, "r+")
        MPAS_PRES = mpasa_module.get_init_pressure(init_f).T

        for merra_specie in merra2wrf_mapper.get_merra_vars():
            print("\t\t - Reading " + str(merra_specie) + " field from MERRA2")
            MER_SPECIE = merra2_module.get_3dfield_by_time(cur_time, merra_f, merra_specie)

            print("\t\t - Horizontal interpolation of " + str(merra_specie) + " on MPAS cells")
            MER_HOR_SPECIE = merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(
                MER_SPECIE,
                mpasa_module.n_cells,
                mpas_lons_for_merra,
                mpas_lats_for_merra,
            )

            print("\t\t - Vertical interpolation of " + str(merra_specie) + " on MPAS levels")
            MPAS_SPECIE = _vertical_interpolate_columns(MER_HOR_SPECIE, MER_HOR_PRES, MPAS_PRES)

            for out_name_and_coef in merra2wrf_mapper.get_list_of_wrf_spec_by_merra_var(merra_specie):
                out_var = out_name_and_coef[0]
                coef = out_name_and_coef[1]
                out_mult = merra2wrf_mapper.coefficients[out_var]
                print(
                    "\t\t - Updating MPAS init field "
                    + str(out_var)
                    + " = "
                    + str(out_var)
                    + " + "
                    + str(merra_specie)
                    + " * "
                    + str(coef)
                    + " * "
                    + str(out_mult)
                )
                mpasa_module.update_init_field(init_f, out_var, MPAS_SPECIE * coef * out_mult)

        if config.init_co2_ch4:
            mpasa_module.init_co2_ch4_ic(init_f)

        init_f.close()
        print("FINISH MPAS INITIAL CONDITIONS")

    if config.do_BC:
        print("\n\nSTART MPAS BOUNDARY CONDITIONS")
        for cur_time in mpasa_module.get_lbc_times_ordered():
            lbc_path = mpasa_module.get_lbc_file_by_time(cur_time)
            if lbc_path is None:
                utils.error_message("Could not resolve MPAS lbc file for time " + str(cur_time))

            print("\n\tCur_time=" + str(cur_time))
            print("\tOpening MPAS lbc file: " + str(lbc_path))
            lbc_f = Dataset(lbc_path, "r+")
            _open_merra_for_time(cur_time)

            print("\tReading MERRA pressure")
            MERA_PRES = merra2_module.get_pressure_by_time(cur_time, merra_f)
            print("\tHorizontal interpolation of MERRA pressure on MPAS cells")
            MER_HOR_PRES = merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(
                MERA_PRES,
                mpasa_module.n_cells,
                mpas_lons_for_merra,
                mpas_lats_for_merra,
            )

            MPAS_PRES = mpasa_module.get_lbc_pressure(lbc_f).T

            for merra_specie in merra2wrf_mapper.get_merra_vars():
                print("\t\t - Reading " + str(merra_specie) + " field from MERRA2")
                MER_SPECIE = merra2_module.get_3dfield_by_time(cur_time, merra_f, merra_specie)

                print("\t\t - Horizontal interpolation of " + str(merra_specie) + " on MPAS cells")
                MER_HOR_SPECIE = merra2_module.hor_interpolate_3dfield_on_wrf_boubdary(
                    MER_SPECIE,
                    mpasa_module.n_cells,
                    mpas_lons_for_merra,
                    mpas_lats_for_merra,
                )

                print("\t\t - Vertical interpolation of " + str(merra_specie) + " on MPAS levels")
                MPAS_SPECIE = _vertical_interpolate_columns(MER_HOR_SPECIE, MER_HOR_PRES, MPAS_PRES)

                for out_name_and_coef in merra2wrf_mapper.get_list_of_wrf_spec_by_merra_var(merra_specie):
                    out_var = out_name_and_coef[0]
                    coef = out_name_and_coef[1]
                    out_mult = merra2wrf_mapper.coefficients[out_var]
                    lbc_var = "lbc_" + str(out_var)
                    print(
                        "\t\t - Updating MPAS lbc field "
                        + str(lbc_var)
                        + " = "
                        + str(lbc_var)
                        + " + "
                        + str(merra_specie)
                        + " * "
                        + str(coef)
                        + " * "
                        + str(out_mult)
                    )
                    mpasa_module.update_lbc_field(lbc_f, lbc_var, MPAS_SPECIE * coef * out_mult)

            if config.init_co2_ch4:
                mpasa_module.init_co2_ch4_lbc(lbc_f)

            lbc_f.close()

        print("FINISH MPAS BOUNDARY CONDITIONS")

    if merra_f is not None:
        print("Closing prev. opened MERRA2 file with index " + str(index_of_opened_mera_file))
        merra_f.close()


if config.target == "wrfchem":
    run_wrfchem()
elif config.target == "mpasa":
    run_mpasa()
else:
    utils.error_message("Unknown --target value: " + str(config.target))


print("--- %s seconds ---" % (time.time() - start_time))
