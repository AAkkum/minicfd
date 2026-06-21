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
    parser = argparse.ArgumentParser(description="Plot speedup and efficiency from aggregated CSV.")
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
    speedup = [float(row["speedup_vs_1thread"] or 0.0) for row in rows]
    efficiency = [float(row["efficiency_vs_1thread"] or 0.0) for row in rows]

    figure, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].plot(threads, speedup, marker="o")
    axes[0].plot(threads, threads, linestyle="--", linewidth=1, label="Ideal")
    axes[0].set_xlabel("Threads")
    axes[0].set_ylabel("Speedup")
    axes[0].set_title("Speedup vs. Threads")
    axes[0].grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    axes[0].legend()

    axes[1].plot(threads, efficiency, marker="o")
    axes[1].axhline(1.0, linestyle="--", linewidth=1, label="Ideal")
    axes[1].set_xlabel("Threads")
    axes[1].set_ylabel("Efficiency")
    axes[1].set_title("Efficiency vs. Threads")
    axes[1].grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    axes[1].legend()

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)


if __name__ == "__main__":
    main()
