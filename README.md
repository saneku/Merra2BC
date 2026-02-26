[![DOI](https://zenodo.org/badge/183694240.svg)](https://zenodo.org/badge/latestdoi/183694240)

# Merra2BC
Merra2BC interpolates MERRA-2 chemical species to the WRF-Chem grid and updates:
- initial conditions (`wrfinput_d01`)
- time-varying boundary conditions (`wrfbdy_d01`)

## Requirements
- Python 3
- [`numpy`](https://numpy.org/)
- [`scipy`](https://scipy.org/)
- [`netCDF4`](https://github.com/Unidata/netcdf4-python)
- WRF/WPS outputs from your case setup:
  - `wrfinput_d01`
  - `wrfbdy_d01`
  - `met_em.d01.*.nc`
- MERRA-2 files covering the full simulation period and spatial domain

Install Python dependencies (pip):

```bash
python3 -m pip install -r requirements.txt
```

Or create a Conda environment from the included file:

```bash
conda env create -f environment.yml
conda activate merra2bc
```

## Configuration Model
Defaults are defined in `config.py`:
- species mapping (`spc_map`)
- file paths and filename masks
- whether to process IC/BC by default (`do_IC`, `do_BC`)

At runtime, command-line flags can override these defaults without editing the file.

## Quick Start
1. Run `real.exe` to generate `wrfinput_d01` and `wrfbdy_d01`.
2. Download required MERRA-2 collections:
   - [M2I3NVAER_5.12.4](https://disc.gsfc.nasa.gov/datasets/M2I3NVAER_5.12.4/summary)
   - [M2I3NVCHM_5.12.4](https://disc.gsfc.nasa.gov/datasets/M2I3NVCHM_5.12.4/summary)
3. Update `config.py` defaults (especially `spc_map`, paths, and masks).
4. Zero relevant chemistry fields before interpolation:
   ```bash
   python3 zero_fields.py
   ```
5. Run interpolation:
   ```bash
   python3 main.py
   ```
6. In `namelist.input` under `&chem`, enable updated chemistry fields:
   - `have_bcs_chem = .true.` for boundary conditions
   - `chem_in_opt = 1` for initial conditions
7. Run `wrf.exe`.

## Command-line Interface
Print all options:

```bash
python3 main.py --help
```

Supported options:
- `--wrf_dir`
- `--wrf_input_file`
- `--wrf_bdy_file`
- `--wrf_met_dir`
- `--wrf_met_files`
- `--mera_dir`
- `--mera_files`
- `--do_IC` / `--no_do_IC`
- `--do_BC` / `--no_do_BC`

Example (explicit paths, process both IC and BC):

```bash
python3 main.py \
  --wrf_dir /path/to/wrf/run \
  --wrf_met_dir /path/to/wps/run \
  --mera_dir /path/to/merra \
  --do_IC --do_BC
```

Example (boundary conditions only):

```bash
python3 main.py --no_do_IC --do_BC
```

## Notes
- Interpolated values are added to existing WRF-Chem fields.
- Running `zero_fields.py` before `main.py` is recommended to avoid double counting.

## Citation
If this utility is useful in your research, please cite:

Ukhov, A., Ahmadov, R., Grell, G., and Stenchikov, G.: Improving dust simulations in WRF-Chem v4.1.3 coupled with the GOCART aerosol module, Geosci. Model Dev., 14, 473–493, https://doi.org/10.5194/gmd-14-473-2021, 2021.
