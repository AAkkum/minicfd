#!/usr/bin/env python3

import argparse
import os
import subprocess
from pathlib import Path

from common import (
    build_metadata,
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


def base_command(executable: Path, case: dict) -> list[str]:
    command = [
        str(executable),
        "-d",
        str(case["domain_size"]),
        "-e",
        str(case["end_time"]),
        "-s",
        str(case["step_size"]),
        "-p",
        case["preconditioner"],
    ]
    if case.get("log_level"):
        command.extend(["-l", case["log_level"]])
    if case.get("disable_output", True):
        command.append("--disable-output")
    command.extend(str(arg) for arg in case.get("extra_args", []))
    return command


def run_command(command: list[str], *, cwd: Path, env: dict[str, str], stdout_path: Path, stderr_path: Path) -> int:
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            check=False,
        )
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute an HPCToolkit campaign.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--build-name", required=True)
    args = parser.parse_args()

    config = load_config(Path(args.config))
    repo_root = Path(args.repo_root).resolve()
    raw_root = Path(args.raw_root).resolve()
    build_dir = repo_root / "build" / args.build_name
    executable = build_dir / config["hpctoolkit"].get("executable", "minicfd")
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

    for case_index, case in enumerate(config["hpctoolkit"]["cases"], start=1):
        case_name = case.get("label", f"case-{case_index:02d}")
        repetitions = int(case.get("repetitions", 1))
        for repetition in range(1, repetitions + 1):
            run_dir = ensure_dir(runs_dir / f"{case_name}_r{repetition:02d}")
            measurements_dir = run_dir / "measurements"
            database_dir = run_dir / "database"
            stdout_path = run_dir / "stdout.log"
            stderr_path = run_dir / "stderr.log"
            time_path = run_dir / "time.txt"
            hpcstruct_stdout = run_dir / "hpcstruct.stdout.log"
            hpcstruct_stderr = run_dir / "hpcstruct.stderr.log"
            hpcprof_stdout = run_dir / "hpcprof.stdout.log"
            hpcprof_stderr = run_dir / "hpcprof.stderr.log"

            command = base_command(executable, case)
            hpcrun_command = ["hpcrun", "-o", str(measurements_dir), *command]

            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = str(case["threads"])
            env["OMP_PLACES"] = case["omp_places"]
            env["OMP_PROC_BIND"] = case["omp_proc_bind"]

            exit_code = run_timed_command(
                hpcrun_command,
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
                "case_label": case_name,
                "git_commit": manifest["git_commit"],
                "build_name": args.build_name,
                "compiler": build_info["compiler"],
                "compiler_version": build_info["compiler_version"],
                "cmake_build_type": build_info["cmake_build_type"],
                "cxx_flags": build_info["cxx_flags"],
                "node_name": manifest["node_name"],
                "job_id": manifest["job_id"],
                "threads": case["threads"],
                "omp_places": case["omp_places"],
                "omp_proc_bind": case["omp_proc_bind"],
                "domain_size": case["domain_size"],
                "end_time": case["end_time"],
                "step_size": case["step_size"],
                "preconditioner": case["preconditioner"],
                "output_disabled": bool(case.get("disable_output", True)),
                "repetition": repetition,
                "exit_code": exit_code,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "time_path": str(time_path),
                "measurements_dir": str(measurements_dir),
                "database_dir": str(database_dir),
                "command": shell_join(command),
            }
            write_json(run_dir / "metadata.json", metadata)

            if exit_code != 0:
                raise SystemExit(f"hpcrun failed for {case_name}")

            hpcstruct_exit = run_command(
                ["hpcstruct", str(measurements_dir)],
                cwd=repo_root,
                env=os.environ.copy(),
                stdout_path=hpcstruct_stdout,
                stderr_path=hpcstruct_stderr,
            )
            if hpcstruct_exit != 0:
                raise SystemExit(f"hpcstruct failed for {case_name}")

            hpcprof_exit = run_command(
                ["hpcprof", "-o", str(database_dir), str(measurements_dir)],
                cwd=repo_root,
                env=os.environ.copy(),
                stdout_path=hpcprof_stdout,
                stderr_path=hpcprof_stderr,
            )
            if hpcprof_exit != 0:
                raise SystemExit(f"hpcprof failed for {case_name}")


if __name__ == "__main__":
    main()
