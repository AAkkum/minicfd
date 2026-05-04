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
