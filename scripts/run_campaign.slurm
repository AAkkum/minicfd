#!/bin/bash -l
### Generic benchmark campaign entry point
#SBATCH -J PEng_MiniCFD
#SBATCH -t 02:00:00
#SBATCH --mem-per-cpu=3000
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 104
#SBATCH -C avx512
#SBATCH -C i02
#SBATCH --cpu-freq=HighM1
#SBATCH -A kurs00102
#SBATCH -p kurs00102
#SBATCH --reservation=kurs00102

set -euo pipefail

: "${MINICFD_REPO_ROOT:?MINICFD_REPO_ROOT is required}"
: "${MINICFD_RAW_RESULTS_ROOT:?MINICFD_RAW_RESULTS_ROOT is required}"
: "${MINICFD_CONFIG_PATH:?MINICFD_CONFIG_PATH is required}"
: "${MINICFD_BUILD_NAME:?MINICFD_BUILD_NAME is required}"

spack env activate /work/home/kurse/kurs00102/common/spenv

cd "${MINICFD_REPO_ROOT}"
python3 scripts/run_campaign_driver.py \
    --config "${MINICFD_CONFIG_PATH}" \
    --repo-root "${MINICFD_REPO_ROOT}" \
    --raw-root "${MINICFD_RAW_RESULTS_ROOT}" \
    --build-name "${MINICFD_BUILD_NAME}"
