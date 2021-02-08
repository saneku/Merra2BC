# Merra2BC
Merra2BC is an interpolation utility, which creates for a WRF-Chem simulation initial and time-varying chemical boundary conditions (IC&BC) based on MERRA-2 reanalysis.

Merra2BC is written on Python and requires:
NetCDF4 interface to work with [netCDF](https://github.com/Unidata/netcdf4-python) files and [SciPy](https://github.com/scipy/scipy) interpolation package.


## Workflow

1. run *real.exe*, which will produce wrfinput and wrfbdy files
2. download required [MERRA-2](https://disc.gsfc.nasa.gov/daac-bin/FTPSubset2.pl) collections
3. run *git clone https://github.com/saneku/Merra2BC.git*
4. edit *config.py*
5. run *python zero_fields.py* to zero required fields (since utility will add values to the existing)
6. run *python main.py* or python *./main.py >& output.log &* to run in background
7. modify *namelist.input* file at section *&chem* (*have_bcs_chem = .true.* for BC *chem_in_opt = 1* for IC )
8. run *wrf.exe*


## How to cite
If you find this code useful in your research, please consider citing:

Ukhov, A., Ahmadov, R., Grell, G., and Stenchikov, G.: Improving dust simulations in WRF-Chem v4.1.3 coupled with the GOCART aerosol module, Geosci. Model Dev., 14, 473–493, https://doi.org/10.5194/gmd-14-473-2021, 2021.
