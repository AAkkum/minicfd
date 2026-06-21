#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
import inspect
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
    parser = argparse.ArgumentParser(description="Plot runtime variation from raw collected CSV.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--filter", action="append", default=[], help="Filter rows via key=value.")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for plotting") from exc

    rows = apply_filters(load_rows(Path(args.input).resolve()), args.filter)
    if not rows:
        raise SystemExit("no rows matched the requested filters")

    grouped: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        if not row.get("wall_time_sec"):
            continue
        grouped[int(row["threads"])].append(float(row["wall_time_sec"]))

    threads = sorted(grouped)
    samples = [grouped[thread] for thread in threads]

    figure, axis = plt.subplots(figsize=(7, 4))
    label_kw = "tick_labels" if "tick_labels" in inspect.signature(axis.boxplot).parameters else "labels"
    axis.boxplot(samples, **{label_kw: [str(thread) for thread in threads]})
    axis.set_xlabel("Threads")
    axis.set_ylabel("Runtime [s]")
    axis.set_title("Runtime Variation by Thread Count")
    axis.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)


if __name__ == "__main__":
    main()
