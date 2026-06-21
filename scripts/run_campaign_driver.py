#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

from common import (
    build_metadata,
    campaign_run_name,
    ensure_dir,
    git_commit,
    hostname,
    load_config,
    run_timed_command,
    shell_join,
    slurm_job_id,
    utc_now,
    write_json,
)


def build_command(executable: Path, benchmark: dict, domain_size: int, end_time: float) -> list[str]:
    command = [
        str(executable),
        "-d",
        str(domain_size),
        "-e",
        str(end_time),
        "-s",
        str(benchmark["step_size"]),
        "-p",
        benchmark["preconditioner"],
    ]
    log_level = benchmark.get("log_level")
    if log_level:
        command.extend(["-l", log_level])
    if benchmark.get("disable_output", False):
        command.append("--disable-output")
    command.extend(str(arg) for arg in benchmark.get("extra_args", []))
    return command


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute a benchmark campaign sequentially.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--build-name", required=True)
    args = parser.parse_args()

    config = load_config(Path(args.config))
    repo_root = Path(args.repo_root).resolve()
    raw_root = Path(args.raw_root).resolve()
    build_dir = repo_root / "build" / args.build_name
    executable = build_dir / config["benchmark"].get("executable", "minicfd")

    benchmark = config["benchmark"]
    build_info = build_metadata(build_dir)
    campaign_dir = ensure_dir(
        raw_root / config["campaign_name"] / utc_now().replace(":", "-")
    )
    runs_dir = ensure_dir(campaign_dir / "runs")

    manifest = {
        "campaign_name": config["campaign_name"],
        "campaign_kind": config["campaign_kind"],
        "started_at": utc_now(),
        "repo_root": str(repo_root),
        "build_dir": str(build_dir),
        "executable": str(executable),
        "git_commit": git_commit(repo_root),
        "node_name": hostname(),
        "job_id": slurm_job_id(),
        "config": config,
        "build_metadata": build_info,
    }
    write_json(campaign_dir / "campaign_manifest.json", manifest)

    run_index = 0
    for domain_size in benchmark["domain_sizes"]:
        for end_time in benchmark["end_times"]:
            for omp_proc_bind in benchmark["omp_proc_binds"]:
                for threads in benchmark["threads"]:
                    for repetition in range(1, benchmark["repetitions"] + 1):
                        run_index += 1
                        run_name = campaign_run_name(
                            run_index,
                            domain_size=domain_size,
                            end_time=end_time,
                            threads=threads,
                            bind=omp_proc_bind,
                            repetition=repetition,
                        )
                        run_dir = ensure_dir(runs_dir / run_name)
                        stdout_path = run_dir / "stdout.log"
                        stderr_path = run_dir / "stderr.log"
                        time_path = run_dir / "time.txt"

                        command = build_command(executable, benchmark, domain_size, end_time)
                        env = os.environ.copy()
                        env["OMP_NUM_THREADS"] = str(threads)
                        env["OMP_PLACES"] = benchmark["omp_places"]
                        env["OMP_PROC_BIND"] = omp_proc_bind

                        exit_code = run_timed_command(
                            command,
                            cwd=repo_root,
                            env=env,
                            stdout_path=stdout_path,
                            stderr_path=stderr_path,
                            time_path=time_path,
                        )

                        metadata = {
                            "timestamp": utc_now(),
                            "campaign_name": config["campaign_name"],
                            "campaign_kind": config["campaign_kind"],
                            "git_commit": manifest["git_commit"],
                            "build_name": args.build_name,
                            "compiler": build_info["compiler"],
                            "compiler_version": build_info["compiler_version"],
                            "cmake_build_type": build_info["cmake_build_type"],
                            "cxx_flags": build_info["cxx_flags"],
                            "node_name": manifest["node_name"],
                            "job_id": manifest["job_id"],
                            "threads": threads,
                            "omp_places": benchmark["omp_places"],
                            "omp_proc_bind": omp_proc_bind,
                            "domain_size": domain_size,
                            "end_time": end_time,
                            "step_size": benchmark["step_size"],
                            "preconditioner": benchmark["preconditioner"],
                            "output_disabled": bool(benchmark.get("disable_output", False)),
                            "repetition": repetition,
                            "exit_code": exit_code,
                            "stdout_path": str(stdout_path),
                            "stderr_path": str(stderr_path),
                            "time_path": str(time_path),
                            "command": shell_join(command),
                        }
                        write_json(run_dir / "metadata.json", metadata)

                        if exit_code != 0:
                            raise SystemExit(f"benchmark run failed in {run_dir}")


if __name__ == "__main__":
    main()
