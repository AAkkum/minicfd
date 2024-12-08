#!/bin/bash
### General information about the job you want to submit
#SBATCH -J PEng_MiniCFD
##SBATCH --mail-type=FAIL
#SBATCH -t 00:30:00

### Which kind of compute node do you want to allocate
#SBATCH --mem-per-cpu=3000
#SBATCH -N 1
#SBATCH -n 104
#SBATCH -c 1
#SBATCH -C avx512
#SBATCH -C i02
##SBATCH --exclusive

### Frequency pinning
#SBATCH --cpu-freq=High-High

### Data for our project
#SBATCH -p kurs00089
#SBATCH -A kurs00089
#SBATCH --reservation=kurs00089

module purge
ml gcc/13

srun -n 1 lscpu | grep MHz
cd build
srun -n 1 --cpus-per-task=16 /usr/bin/time ./minicfd -d 100 -e 6 -s 0.4
srun -n 1 --cpus-per-task=16 /usr/bin/time ./minicfd -d 100 -e 6 -s 0.4
srun -n 1 --cpus-per-task=16 /usr/bin/time ./minicfd -d 100 -e 6 -s 0.4
