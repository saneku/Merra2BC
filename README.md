# Merra2bc
Merra2BC interpolator creates time-varying chemical boundary conditions based on MERRA-2 reanalysis for a WRF-Chem simulation by interpolating chemical species mixing ratios defined on the MERRA-2 grid to the WRF-Chem grid for initial conditions (IC) and boundary conditions (BC).

The utility requires:
NetCDF4 interface to work with netCDF files and SciPy's interpolation package.
- netcdf4 (https://github.com/Unidata/netcdf4-python)
- SciPy (https://github.com/scipy/scipy)

#Workflow

1. run real.exe, which will produce wrfinput and wrfbdy files
2. edit config.py
3. run python zero_fields.py to zero required fields
4. run python main.py
5. modify namelist.input file at section &chem (have_bcs_chem = .true. for BC chem_in_opt = 1 for IC )
6. run wrf.exe
