#!/usr/bin/env python3

import argparse
from pathlib import Path

from common import parse_kv_file, read_json, write_csv


FIELDNAMES = [
    "timestamp",
    "campaign_name",
    "campaign_kind",
    "case_label",
    "git_commit",
    "build_name",
    "compiler",
    "compiler_version",
    "cmake_build_type",
    "cxx_flags",
    "node_name",
    "job_id",
    "threads",
    "omp_places",
    "omp_proc_bind",
    "domain_size",
    "end_time",
    "step_size",
    "preconditioner",
    "output_disabled",
    "repetition",
    "wall_time_sec",
    "user_time_sec",
    "sys_time_sec",
    "max_rss_kb",
    "exit_code",
    "stdout_path",
    "stderr_path",
    "time_path",
    "measurements_dir",
    "database_dir",
    "command",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect benchmark or profiler run folders into one CSV file.")
    parser.add_argument("--input", required=True, help="Raw result root to scan recursively.")
    parser.add_argument("--output", required=True, help="Output CSV path.")
    args = parser.parse_args()

    raw_root = Path(args.input).resolve()
    rows = []
    for metadata_path in sorted(raw_root.rglob("metadata.json")):
        metadata = read_json(metadata_path)
        timing = parse_kv_file(Path(metadata["time_path"]))
        row = {field: "" for field in FIELDNAMES}
        row.update(metadata)
        row["case_label"] = metadata.get("case_label", "")
        row["measurements_dir"] = metadata.get("measurements_dir", "")
        row["database_dir"] = metadata.get("database_dir", "")
        row["wall_time_sec"] = timing.get("wall_time_sec", "")
        row["user_time_sec"] = timing.get("user_time_sec", "")
        row["sys_time_sec"] = timing.get("sys_time_sec", "")
        row["max_rss_kb"] = timing.get("max_rss_kb", "")
        row["exit_code"] = metadata.get("exit_code", timing.get("exit_status", ""))
        rows.append(row)

    write_csv(Path(args.output).resolve(), rows, FIELDNAMES)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
