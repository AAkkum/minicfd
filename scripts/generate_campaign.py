#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from common import ensure_dir, load_config, write_json


def validate_benchmark(config: dict) -> None:
    benchmark = config["benchmark"]
    required = [
        "executable",
        "domain_sizes",
        "end_times",
        "step_size",
        "preconditioner",
        "threads",
        "omp_places",
        "omp_proc_binds",
        "repetitions",
    ]
    for key in required:
        if key not in benchmark:
            raise ValueError(f"benchmark config missing key: {key}")


def validate_hpctoolkit(config: dict) -> None:
    profile = config["hpctoolkit"]
    if "cases" not in profile or not profile["cases"]:
        raise ValueError("hpctoolkit config requires at least one case")


def validate(config: dict) -> None:
    required = ["campaign_name", "campaign_kind", "repo_root", "build_name", "raw_results_root", "slurm"]
    for key in required:
        if key not in config:
            raise ValueError(f"campaign config missing key: {key}")

    if config["campaign_kind"] == "benchmark":
        validate_benchmark(config)
    elif config["campaign_kind"] == "hpctoolkit":
        validate_hpctoolkit(config)
    else:
        raise ValueError(f"unsupported campaign kind: {config['campaign_kind']}")


def build_submit_script(config_path: Path, config: dict) -> str:
    repo_root = config["repo_root"]
    raw_root = config["raw_results_root"]
    slurm = config["slurm"]
    script_name = (
        "run_hpctoolkit.slurm" if config["campaign_kind"] == "hpctoolkit" else "run_campaign.slurm"
    )
    slurm_script = Path(repo_root) / "scripts" / script_name
    build_name = config["build_name"]

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'REPO_ROOT={json.dumps(repo_root)}',
        f'RAW_RESULTS_ROOT={json.dumps(raw_root)}',
        f'CONFIG_PATH={json.dumps(str(config_path))}',
        f'BUILD_NAME={json.dumps(build_name)}',
        "cd \"$REPO_ROOT\"",
        "EXPORTS=\"ALL,"
        "MINICFD_REPO_ROOT=${REPO_ROOT},"
        "MINICFD_RAW_RESULTS_ROOT=${RAW_RESULTS_ROOT},"
        "MINICFD_CONFIG_PATH=${CONFIG_PATH},"
        "MINICFD_BUILD_NAME=${BUILD_NAME}\"",
        f"sbatch -J {json.dumps(slurm['job_name'])} -t {json.dumps(slurm['time'])} "
        "--export=\"$EXPORTS\" "
        f"{json.dumps(str(slurm_script))}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a campaign config and generate a submit wrapper.")
    parser.add_argument("--config", required=True, help="Path to campaign JSON config.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for the expanded config and submit wrapper.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    validate(config)

    output_dir = ensure_dir(Path(args.output_dir).resolve())
    expanded_config_path = output_dir / f"{config['campaign_name']}.expanded.json"
    write_json(expanded_config_path, config)

    submit_path = output_dir / "submit.sh"
    submit_path.write_text(
        build_submit_script(expanded_config_path, config),
        encoding="utf-8",
    )

    try:
        submit_path.chmod(0o755)
    except OSError:
        pass

    original_copy = output_dir / config_path.name
    if original_copy != expanded_config_path:
        original_copy.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote expanded config: {expanded_config_path}")
    print(f"Wrote submit wrapper: {submit_path}")


if __name__ == "__main__":
    main()
