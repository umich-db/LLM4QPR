#!/usr/bin/env python3
"""
Utility script to verify that result CSV files exist for all expected seeds.

The script walks the `results` directory (configurable via `--results_root`) and
checks every CSV whose filename contains the pattern `_seedXX`. For each
directory and base filename (with the seed number removed), it verifies that
files exist for the expected seeds (default: 42, 43, 44). Missing seeds are
reported to stdout.
"""

import argparse
from collections import defaultdict
from pathlib import Path
import re
from typing import Dict, List, Set, Tuple

SEED_REGEX = re.compile(r"^(?P<prefix>.*_seed)(?P<seed>\d+)(?P<suffix>.*\.csv)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that result CSV files exist for all expected seeds."
    )
    parser.add_argument(
        "--results_root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "results",
        help="Root directory containing result CSV files (default: experiments/results).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42, 43, 44],
        help="Seed numbers that must be present for each result file group.",
    )
    return parser.parse_args()


def collect_seed_files(
    root: Path, expected_seeds: Set[int]
) -> Dict[Tuple[Path, str], Dict[str, Set[int]]]:
    """
    Walk `root` and collect CSV files grouped by (directory, base_key).

    The base key is derived by removing the seed number from the filename, so
    files like `..._seed42.csv`, `..._seed43.csv` belong to the same group.
    """
    groups: Dict[Tuple[Path, str], Dict[str, Set[int]]] = defaultdict(
        lambda: {"seeds": set(), "paths": set()}
    )

    for csv_path in root.rglob("*.csv"):
        match = SEED_REGEX.match(csv_path.name)
        if not match:
            continue
        prefix = match.group("prefix")
        seed_str = match.group("seed")
        suffix = match.group("suffix")

        try:
            seed = int(seed_str)
        except ValueError:
            continue

        if expected_seeds and seed not in expected_seeds:
            # Ignore seeds outside the expected list
            continue

        base_key = f"{prefix}{suffix}"
        key = (csv_path.parent, base_key)
        groups[key]["seeds"].add(seed)
        groups[key]["paths"].add(csv_path.name)

    return groups


def report_missing(groups, expected_seeds: Set[int], root: Path) -> List[str]:
    missing_reports: List[str] = []
    for (directory, base_key), info in sorted(groups.items()):
        missing = sorted(expected_seeds - info["seeds"])
        if missing:
            rel_dir = directory.relative_to(root)
            missing_str = ", ".join(str(seed) for seed in missing)
            sample_files = ", ".join(sorted(info["paths"]))
            report = (
                f"[{rel_dir}] {base_key} -> missing seeds: {missing_str} "
                # f"(present files: {sample_files})"
            )
            missing_reports.append(report)
    return missing_reports


def main() -> None:
    args = parse_args()
    results_root = args.results_root.resolve()
    expected_seeds = set(args.seeds)

    if not results_root.exists():
        raise FileNotFoundError(f"Results root does not exist: {results_root}")

    groups = collect_seed_files(results_root, expected_seeds)
    missing_reports = report_missing(groups, expected_seeds, results_root)

    if not missing_reports:
        print(
            f"All CSV groups under {results_root} contain the expected seeds: "
            f"{', '.join(str(seed) for seed in sorted(expected_seeds))}"
        )
        return

    print("Missing seed files detected:")
    for line in missing_reports:
        print(f"  - {line}")


if __name__ == "__main__":
    main()

