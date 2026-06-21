#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from common import mean, median, stddev, write_csv


GROUP_FIELDS = [
    "campaign_name",
    "campaign_kind",
    "build_name",
    "threads",
    "omp_places",
    "omp_proc_bind",
    "domain_size",
    "end_time",
    "step_size",
    "preconditioner",
    "output_disabled",
]

OUTPUT_FIELDS = GROUP_FIELDS + [
    "sample_count",
    "mean_wall_time_sec",
    "median_wall_time_sec",
    "stddev_wall_time_sec",
    "relative_stddev_percent",
    "speedup_vs_1thread",
    "efficiency_vs_1thread",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate collected run CSV data.")
    parser.add_argument("--input", required=True, help="Input CSV from collect_results.py.")
    parser.add_argument("--output", required=True, help="Output aggregated CSV.")
    args = parser.parse_args()

    rows = load_rows(Path(args.input).resolve())
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if not row.get("wall_time_sec"):
            continue
        key = tuple(row[field] for field in GROUP_FIELDS)
        grouped[key].append(row)

    grouped_results = []
    by_baseline_key: dict[tuple[str, ...], float] = {}
    for key, samples in grouped.items():
        wall_times = [float(sample["wall_time_sec"]) for sample in samples]
        group_row = {field: key[index] for index, field in enumerate(GROUP_FIELDS)}
        med = median(wall_times)
        avg = mean(wall_times)
        sd = stddev(wall_times)
        group_row.update(
            {
                "sample_count": len(wall_times),
                "mean_wall_time_sec": f"{avg:.9f}",
                "median_wall_time_sec": f"{med:.9f}",
                "stddev_wall_time_sec": f"{sd:.9f}",
                "relative_stddev_percent": f"{(sd / avg * 100.0) if avg else 0.0:.6f}",
                "speedup_vs_1thread": "",
                "efficiency_vs_1thread": "",
            }
        )
        grouped_results.append(group_row)

        baseline_key = tuple(
            group_row[field]
            for field in GROUP_FIELDS
            if field != "threads"
        )
        if group_row["threads"] == "1":
            by_baseline_key[baseline_key] = med

    for group_row in grouped_results:
        baseline_key = tuple(
            group_row[field]
            for field in GROUP_FIELDS
            if field != "threads"
        )
        baseline = by_baseline_key.get(baseline_key)
        if baseline is None:
            continue
        threads = int(group_row["threads"])
        median_runtime = float(group_row["median_wall_time_sec"])
        if median_runtime == 0.0:
            continue
        speedup = baseline / median_runtime
        group_row["speedup_vs_1thread"] = f"{speedup:.6f}"
        group_row["efficiency_vs_1thread"] = f"{(speedup / threads):.6f}"

    grouped_results.sort(
        key=lambda row: (
            row["campaign_name"],
            row["domain_size"],
            row["end_time"],
            row["omp_proc_bind"],
            int(row["threads"]),
        )
    )
    write_csv(Path(args.output).resolve(), grouped_results, OUTPUT_FIELDS)
    print(f"Wrote {len(grouped_results)} aggregated rows to {args.output}")


if __name__ == "__main__":
    main()
