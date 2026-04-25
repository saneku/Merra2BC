[![DOI](https://zenodo.org/badge/183694240.svg)](https://zenodo.org/badge/latestdoi/183694240)

# Merra2BC

<p align="center">
  <img src="doc/repo_logo.png" alt="Merra2BC logo" width="240"/>
</p>

Merra2BC interpolates MERRA-2 chemical species to model grids and updates:
- WRF-Chem initial and boundary conditions (`wrfinput_d01`, `wrfbdy_d01`)
- MPAS-A initial conditions (`*.init.nc`) and, for regional runs, time-varying lateral boundary files (`lbc.*.nc`)

![Merra2BC workflow thumbnail](doc/repo_thumbnail.svg)

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
Defaults are defined in `src/config.py`:
- target model (`--target`, default: `wrfchem`)
- species mapping profile (`--mapping_profile`)
- file paths and filename masks
- whether to process IC/BC by default (`do_IC`, `do_BC`)

Mapping profiles live under `maps/`:
- `maps/wrfchem.map` (current production workflow)
- `maps/mpasa.map` (CheMPAS-A starter profile)
- In `maps/mpasa.map`, `co` includes `Mw(CO)/Mw(air)=28.01/28.97` to convert MERRA-2 `CO` (`mol/mol`) to MPAS `co` (`kg/kg`).

Format for each mapping line:
```text
<OUT_VAR> -> <coef>*[<MERRA_VAR>] [+ <coef>*[<MERRA_VAR>] ...] ; <out_multiplier>
```

At runtime, command-line flags can override these defaults without editing source files.

## Quick Start
1. Run `real.exe` with `chem_in_opt = 0` to generate `wrfinput_d01` and `wrfbdy_d01`.
2. Download required MERRA-2 collections:
   - [M2I3NVAER_5.12.4](https://disc.gsfc.nasa.gov/datasets/M2I3NVAER_5.12.4/summary)
   - [M2I3NVCHM_5.12.4](https://disc.gsfc.nasa.gov/datasets/M2I3NVCHM_5.12.4/summary)
3. Update `src/config.py` defaults (especially `spc_map`, paths, and masks).
4. Zero relevant chemistry fields before interpolation:
   ```bash
   python3 zero_fields.py --do_IC=true --do_BC=true
   ```
5. Run interpolation:
   ```bash
   python3 main.py
   ```
6. Before running `wrf.exe`, in `namelist.input` under `&chem` set:
   - `have_bcs_chem = .true.` for boundary conditions
   - `chem_in_opt = 1` for initial conditions
7. Run `wrf.exe`.

## Command-line Interface
Print all options:

```bash
python3 main.py --help
```

`main.py` supported options:
- `--wrf_input_file` (full path to `wrfinput_d01`)
- `--wrf_bdy_file` (full path to `wrfbdy_d01`)
- `--wrf_met_files` (full-path glob mask for `met_em` files)
- `--merra2_files` (full-path glob mask for MERRA2 files)
- `--mpas_init_file` (full path to MPAS init file, required for `--target mpasa`)
- `--mpas_lbc_files` (glob mask for MPAS `lbc.*.nc`; required only when `--target mpasa --do_BC=true`)
- `--do_IC=true|false`
- `--do_BC=true|false`
- `--init_co2_ch4=true|false` (default `false`; input values are `co2=400 ppmv`, `ch4=1.7 ppmv`; WRF writes ppmv and zeroes BC tendencies, MPAS writes constant `co2/ch4` and `lbc_co2/lbc_ch4` with unit-aware conversion)
- `--target=wrfchem|mpasa`
- `--mapping_profile=/path/to/profile.map` (optional; defaults to `maps/<target>.map`)

Example (explicit paths, process both IC and BC):

```bash
python3 main.py \
  --wrf_input_file /path/to/wrf/run/wrfinput_d01 \
  --wrf_bdy_file /path/to/wrf/run/wrfbdy_d01 \
  --wrf_met_files '/path/to/wps/run/met_em.d01.2010-*' \
  --merra2_files '/path/to/merra/MERRA2_*.nc4' \
  --do_IC=true --do_BC=true \
  --init_co2_ch4=false
```

Example (boundary conditions only):

```bash
python3 main.py --do_IC=false --do_BC=true
```

`zero_fields.py` uses a fixed zero value (`1e-16`) and supports shared config overrides (including WRF and MPAS file arguments). The fields zeroed should be the same mapped output fields that are updated later by `main.py` (based on the active `spc_map`).

```bash
python3 zero_fields.py \
   --wrf_input_file /path/to/wrf/run/wrfinput_d01 \
   --do_IC=true

OR

python3 zero_fields.py \
   --wrf_bdy_file /path/to/wrf/run/wrfbdy_d01 \
   --do_BC=true
```

MPAS examples:

Global run (IC only):
```bash
python3 zero_fields.py \
  --target mpasa \
  --mpas_init_file /path/to/x1.4002.init.nc \
  --do_IC=true --do_BC=false

python3 main.py \
  --target mpasa \
  --mpas_init_file /path/to/x1.4002.init.nc \
  --merra2_files '/path/to/merra/MERRA2_*.nc4' \
  --do_IC=true --do_BC=false
```

Regional run (IC + time-varying LBC):
```bash
python3 zero_fields.py \
  --target mpasa \
  --mpas_init_file /path/to/MiddleEastRegional.init.nc \
  --mpas_lbc_files '/path/to/lbc.*.nc' \
  --do_IC=true --do_BC=true

python3 main.py \
  --target mpasa \
  --mpas_init_file /path/to/MiddleEastRegional.init.nc \
  --mpas_lbc_files '/path/to/lbc.*.nc' \
  --merra2_files '/path/to/merra/MERRA2_*.nc4' \
  --do_IC=true --do_BC=true
```

## Notes
- Interpolated values are added to existing WRF-Chem fields.
- Running `zero_fields.py` before `main.py` is recommended to avoid double counting.
- For `--target mpasa`, interpolated values are added to MPAS chemistry fields in init/lbc files.
- For `--target mpasa --init_co2_ch4=true`, constants are derived from ppmv and converted by target-variable units (`kg kg^-1`, `mol mol^-1`, or `ppmv`).
- MPAS pressure for vertical interpolation is used from `pressure`/`lbc_pressure` if present. If not present, it is reconstructed from `rho/theta/qv` (or `lbc_rho/lbc_theta/lbc_qv`).
- Global MPAS runs typically use IC only (`--do_BC=false` and no `--mpas_lbc_files`).

## Citation
If this utility is useful in your research, please cite:

Ukhov, A., Ahmadov, R., Grell, G., and Stenchikov, G.: Improving dust simulations in WRF-Chem v4.1.3 coupled with the GOCART aerosol module, Geosci. Model Dev., 14, 473–493, https://doi.org/10.5194/gmd-14-473-2021, 2021.
