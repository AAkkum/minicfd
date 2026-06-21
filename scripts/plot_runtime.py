#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def apply_filters(rows: list[dict[str, str]], filters: list[str]) -> list[dict[str, str]]:
    for item in filters:
        key, _, value = item.partition("=")
        rows = [row for row in rows if row.get(key) == value]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot runtime vs. threads from aggregated CSV.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--filter", action="append", default=[], help="Filter rows via key=value.")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for plotting") from exc

    rows = apply_filters(load_rows(Path(args.input).resolve()), args.filter)
    rows.sort(key=lambda row: int(row["threads"]))
    if not rows:
        raise SystemExit("no rows matched the requested filters")

    threads = [int(row["threads"]) for row in rows]
    medians = [float(row["median_wall_time_sec"]) for row in rows]
    deviations = [float(row["stddev_wall_time_sec"]) for row in rows]

    figure, axis = plt.subplots(figsize=(7, 4))
    axis.errorbar(threads, medians, yerr=deviations, marker="o", capsize=4)
    axis.set_xlabel("Threads")
    axis.set_ylabel("Median runtime [s]")
    axis.set_title("MiniCFD Runtime Scaling")
    axis.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)


if __name__ == "__main__":
    main()
