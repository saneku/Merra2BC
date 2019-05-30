# Merra2BC
Merra2BC interpolator creates time-varying chemical boundary conditions based on MERRA-2 reanalysis for a WRF-Chem simulation by interpolating chemical species mixing ratios defined on the MERRA-2 grid to the WRF-Chem grid for initial conditions (IC) and boundary conditions (BC).

This utility is written on Python and requires:
NetCDF4 interface to work with [netCDF](https://github.com/Unidata/netcdf4-python) files and (SciPy](https://github.com/scipy/scipy) interpolation package.


# Workflow

1. run *real.exe*, which will produce wrfinput and wrfbdy files
2. download required MERRA-2 collections from https://disc.gsfc.nasa.gov/daac-bin/FTPSubset2.pl
3. edit *config.py*
4. run *python zero_fields.py* to zero required fields
5. run *python main.py*
6. modify *namelist.input* file at section *&chem* (*have_bcs_chem = .true.* for BC *chem_in_opt = 1* for IC )
7. run *wrf.exe*
