# MiniCFD

## Build instructions
```bash
mkdir build
cd build
cmake ..
make
```
To enable trace logging, pass `-DENABLE_TRACE_LOG=ON` to CMake. (Note, that you also need to set the correct logging level when calling the executable.)

## Run instructions
```bash
./minicfd -h # print help about command-line arguments
```

### Benchmark-friendly runs
Use `--disable-output` to avoid file I/O during timing and profiling runs:
```bash
OMP_NUM_THREADS=16 ./minicfd -d 100 -e 6 -s 0.4 --disable-output
```

### Visualization runs 
A good size for trying out the simulation and generating data for visualization is 64x64x64 grid cells.
```bash
OMP_NUM_THREADS=8 ./minicfd -d 64 -e 5 -s 0.4
```

### Benchmarking runs
To conduct performance measurements, use a larger simulation setup:
```bash
time OMP_NUM_THREADS=16 ./minicfd -d 100 -e 6 -s 0.4
```

## Visualization
The `visualize.py` script can be used to render a specific frame of the simulation with [Paraview](https://www.paraview.org/).
To use it, first install Paraview via your system's package manager.
See `python visualize.py -h` for available parameters.

### Run visualization
```bash
pvpython visualize.py "<simulation_dir>/fields.csv.*" --animate --size 64
```
Make sure to match the `-size` parameter to the grid size (`-d`) from the simulation call.

To encode the resulting PNG files into an MP4-file, FFmpeg can be used:
```bash
ffmpeg -framerate 20 -i anim.%04d.png -c:v libx264 -pix_fmt yuv420p -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" out.mp4
```

## Tests
To run the tests, first enable their compilation at configure time by passing `-DBUILD_TESTS=ON` to CMake.
Then, run:
```bash
tests/unittests
tests/integrationtests
```

## Lichtenberg workflow
The repository contains a small automation layer for the seminar workflow:

- `scripts/build_cluster.sh`: build the named cluster configurations
- `configs/*.json`: example benchmark/profiling campaign definitions
- `scripts/generate_campaign.py`: validate a config and generate a submit script
- `scripts/run_campaign.slurm`: generic Slurm entry point for timing campaigns
- `scripts/run_hpctoolkit.slurm`: generic Slurm entry point for HPCToolkit runs
- `scripts/collect_results.py`: normalize raw run folders into one CSV file
- `scripts/aggregate_results.py`: compute grouped statistics, speedup, and efficiency
- `scripts/plot_*.py`: generate paper-ready figures from the CSV files

Use the cluster paths like this:

- keep the repository in `$HOME`, for example `$HOME/minicfd`
- keep large raw outputs in `$HPC_SCRATCH/minicfd`
- submit jobs from the login node, but do not use login-node runs as benchmark data

Typical usage on Lichtenberg:
```bash
cd $HOME/minicfd
bash scripts/build_cluster.sh baseline-build
python3 scripts/generate_campaign.py --config configs/pilot.json --output-dir scripts/generated/pilot
bash scripts/generated/pilot/submit.sh
python3 scripts/collect_results.py --input $HPC_SCRATCH/minicfd --output results/summary/pilot.csv
python3 scripts/aggregate_results.py --input results/summary/pilot.csv --output results/summary/pilot_aggregated.csv
```

Minimal first workflow:

1. Build once in `$HOME/minicfd`
2. Submit the pilot campaign with Slurm
3. Wait for the Slurm job to finish
4. Collect the raw results from `$HPC_SCRATCH/minicfd` into CSV
5. Only after that move on to placement, scaling, and HPCToolkit
