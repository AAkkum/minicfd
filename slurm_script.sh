#!/bin/bash
### General information about the job you want to submit
#SBATCH -J PEng_MiniCFD
##SBATCH --mail-type=FAIL
#SBATCH -t 00:30:00

### Which kind of compute node do you want to allocate
#SBATCH --mem-per-cpu=3000
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 96
#SBATCH -C avx512
#SBATCH -C i01
##SBATCH --exclusive

### Frequency pinning
#SBATCH --cpu-freq=HighM1

### Data for our project
#SBATCH -p kurs00095
#SBATCH -A kurs00095
#SBATCH --reservation=kurs00095

# Switch to custom Spack installation and enable prepared environment
export SPACK_USER_CACHE_PATH=${HOME}/.pengspack
export SPACK_USER_CONFIG_PATH=${HOME}/.pengspack
source /work/home/kurse/kurs00095/pengspack/share/spack/setup-env.sh
spack env activate /work/home/kurse/kurs00095/task3-spackenv

srun bash -c "sleep 2 && lscpu -e"

cd build
srun --cpus-per-task=16 /usr/bin/time ./minicfd -d 100 -e 6 -s 0.4
srun --cpus-per-task=16 /usr/bin/time ./minicfd -d 100 -e 6 -s 0.4
srun --cpus-per-task=16 /usr/bin/time ./minicfd -d 100 -e 6 -s 0.4
