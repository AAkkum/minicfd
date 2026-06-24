#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "usage: $0 <baseline-build|opt-a-build|opt-b-build|opt-c-build|opt-d-build|vec-report-build> [repo-root]" >&2
    exit 1
fi

build_name=$1
repo_root=${2:-$(pwd)}
build_dir="${repo_root}/build/${build_name}"

case "${build_name}" in
    baseline-build|opt-a-build|opt-b-build|opt-c-build|opt-d-build)
        cmake_args=(
            -S "${repo_root}"
            -B "${build_dir}"
            -DCMAKE_BUILD_TYPE=RelWithDebInfo
            -DBUILD_TESTS=ON
        )
        ;;
    vec-report-build)
        cmake_args=(
            -S "${repo_root}"
            -B "${build_dir}"
            -DCMAKE_BUILD_TYPE=RelWithDebInfo
            -DBUILD_TESTS=ON
            -DCMAKE_CXX_FLAGS=-fopt-info-vec-optimized\ -fopt-info-vec-missed
        )
        ;;
    *)
        echo "unknown build name: ${build_name}" >&2
        exit 1
        ;;
esac

mkdir -p "${build_dir}"
cmake "${cmake_args[@]}"
cmake --build "${build_dir}" -j

if [[ "${build_name}" == "vec-report-build" ]]; then
    echo "Vectorization diagnostics are emitted during the compiler invocation."
    echo "Re-run with: cmake --build \"${build_dir}\" -j 2>&1 | tee \"${build_dir}/vectorization.log\""
fi
