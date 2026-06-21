#!/usr/bin/env python3

import csv
import json
import os
import resource
import shlex
import shutil
import socket
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TIME_FORMAT = "\n".join(
    [
        "wall_time_sec=%e",
        "user_time_sec=%U",
        "sys_time_sec=%S",
        "max_rss_kb=%M",
        "exit_status=%x",
    ]
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def expand_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: expand_env(val) for key, val in value.items()}
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, str):
        return os.path.expanduser(os.path.expandvars(value))
    return value


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return expand_env(json.load(handle))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_kv_file(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            parsed[key] = value
    return parsed


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def git_commit(repo_root: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                text=True,
            )
            .strip()
        )
    except subprocess.CalledProcessError:
        return "unknown"


def read_cmake_cache(cache_path: Path) -> dict[str, str]:
    cache: dict[str, str] = {}
    if not cache_path.exists():
        return cache
    with cache_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            key_part, _, value = line.partition("=")
            key, _, _type = key_part.partition(":")
            cache[key] = value
    return cache


def build_metadata(build_dir: Path) -> dict[str, str]:
    cache = read_cmake_cache(build_dir / "CMakeCache.txt")
    compiler = cache.get("CMAKE_CXX_COMPILER", "unknown")
    compiler_version = "unknown"
    if compiler != "unknown":
        try:
            compiler_version = (
                subprocess.check_output([compiler, "--version"], text=True)
                .splitlines()[0]
                .strip()
            )
        except (FileNotFoundError, subprocess.CalledProcessError, IndexError):
            compiler_version = "unknown"

    build_type = cache.get("CMAKE_BUILD_TYPE", "unknown")
    cxx_flags = " ".join(
        part
        for part in [
            cache.get("CMAKE_CXX_FLAGS", "").strip(),
            cache.get(f"CMAKE_CXX_FLAGS_{build_type.upper()}", "").strip(),
        ]
        if part
    )

    return {
        "compiler": Path(compiler).name if compiler != "unknown" else compiler,
        "compiler_version": compiler_version,
        "cmake_build_type": build_type,
        "cxx_flags": cxx_flags,
    }


def run_timed_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    time_path: Path,
) -> int:
    time_binary = shutil.which("time")
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        if time_binary is not None:
            timed_command = [time_binary, "-f", TIME_FORMAT, "-o", str(time_path), *command]
            completed = subprocess.run(
                timed_command,
                cwd=str(cwd),
                env=env,
                stdout=stdout_handle,
                stderr=stderr_handle,
                check=False,
            )
            return completed.returncode

        usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            check=False,
        )
        wall_time = time.perf_counter() - start
        usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)

    user_time = usage_after.ru_utime - usage_before.ru_utime
    sys_time = usage_after.ru_stime - usage_before.ru_stime
    max_rss_kb = usage_after.ru_maxrss
    time_path.write_text(
        "\n".join(
            [
                f"wall_time_sec={wall_time:.9f}",
                f"user_time_sec={user_time:.9f}",
                f"sys_time_sec={sys_time:.9f}",
                f"max_rss_kb={max_rss_kb}",
                f"exit_status={completed.returncode}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return completed.returncode


def hostname() -> str:
    return socket.gethostname()


def slurm_job_id() -> str:
    return os.environ.get("SLURM_JOB_ID", "")


def campaign_run_name(index: int, *, domain_size: int, end_time: float, threads: int, bind: str, repetition: int) -> str:
    return (
        f"run_{index:04d}_d{domain_size}_e{end_time:g}_t{threads}"
        f"_bind-{bind}_r{repetition:02d}"
    )


def median(values: list[float]) -> float:
    return statistics.median(values)


def mean(values: list[float]) -> float:
    return statistics.fmean(values)


def stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
