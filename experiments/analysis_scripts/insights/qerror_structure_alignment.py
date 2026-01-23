"""
Analyze the relationship between structural plan metrics and q_error per verbose file.

For each verbose CSV (per algo/model), this script:
  * Loads the referenced plan file and extracts structural metrics
    (number of tables, columns, joins, filters).
  * Aligns these metrics with q_error entries (by row index).
  * Computes Pearson correlations and p-values between q_error and each metric.
  * Outputs a table where each column corresponds to a verbose CSV (algo/model)
    and each row is a structural metric. Values are formatted as
        "{correlation:.4f}{stars}"
    where stars denote statistical significance (* for p<0.05, ** for p<0.01, *** for p<0.001).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats

from plan_structural_metrics import PlanStructuralSummary, summarise_plan_structure


EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
VERBOSE_ROOT_DEFAULT = EXPERIMENTS_DIR / "verbose"
OUTPUT_DIR = Path(__file__).resolve().parent / "structure_qerror_results"

STRUCT_METRICS = [
    ("num_tables", "Tables"),
    ("num_columns", "Columns"),
    ("num_joins", "Joins"),
    ("num_filters", "Filters"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Correlate q_error with plan structural metrics."
    )
    parser.add_argument("--dataset", required=True, help="Dataset identifier (e.g., job_full).")
    parser.add_argument(
        "--task",
        required=True,
        choices=["card", "time"],
        help="Task type represented in verbose filenames.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed to filter verbose CSVs.")
    parser.add_argument(
        "--verbose_root",
        type=Path,
        default=VERBOSE_ROOT_DEFAULT,
        help="Root folder containing verbose directories.",
    )
    parser.add_argument(
        "--ngram_n",
        type=int,
        default=3,
        help="Path n-gram length for structural summaries (passed through for consistency).",
    )
    parser.add_argument(
        "--plan_cache_limit",
        type=int,
        default=0,
        help="Optional number of rows to sample (0 means use all rows).",
    )
    return parser.parse_args()


def significance_stars(p_value: float) -> str:
    if np.isnan(p_value):
        return ""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""


def extract_plan_path(series: pd.Series) -> Path:
    filled = series.replace("", pd.NA).ffill().dropna()
    if filled.empty:
        raise ValueError("No plan_file paths found in verbose CSV.")
    rel_path = filled.iloc[0]
    path = (EXPERIMENTS_DIR / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {path}")
    return path


def load_plan_dataframe(plan_path: Path) -> pd.DataFrame:
    df = pd.read_csv(plan_path)
    if "json" not in df.columns:
        raise KeyError(f"'json' column not found in plan file: {plan_path}")
    return df.reset_index(drop=True)


def summarise_plans(plan_df: pd.DataFrame, indices: List[int], ngram_n: int) -> Dict[int, PlanStructuralSummary]:
    summaries: Dict[int, PlanStructuralSummary] = {}
    cache: Dict[str, PlanStructuralSummary] = {}
    for idx in indices:
        if idx in summaries:
            continue
        if idx >= len(plan_df):
            raise IndexError(f"Plan idx {idx} out of bounds for plan file with {len(plan_df)} rows.")
        raw_json = plan_df.iloc[idx]["json"]
        if raw_json in cache:
            summaries[idx] = cache[raw_json]
            continue
        plan_obj = json.loads(raw_json)
        summary = summarise_plan_structure(plan_obj, ngram_n=ngram_n)
        summaries[idx] = summary
        cache[raw_json] = summary
    return summaries


def compute_correlations(csv_path: Path, args: argparse.Namespace) -> Dict[str, str]:
    verbose_df = pd.read_csv(csv_path)
    required_cols = {"idx", "q_error", "plan_file"}
    if not required_cols.issubset(verbose_df.columns):
        missing = required_cols - set(verbose_df.columns)
        raise KeyError(f"Verbose file {csv_path} missing columns: {missing}")

    plan_path = extract_plan_path(verbose_df["plan_file"])
    plan_df = load_plan_dataframe(plan_path)

    if args.plan_cache_limit > 0:
        verbose_df = verbose_df.iloc[: args.plan_cache_limit]

    indices = verbose_df["idx"].tolist()
    q_errors = verbose_df["q_error"].to_numpy(dtype=float)

    summaries_map = summarise_plans(plan_df, indices, args.ngram_n)
    metrics = {
        metric_key: np.array([summaries_map[idx].__dict__[metric_key] for idx in indices], dtype=float)
        for metric_key, _ in STRUCT_METRICS
    }

    results: Dict[str, str] = {}
    for metric_key, row_label in STRUCT_METRICS:
        values = metrics[metric_key]
        valid_mask = ~np.isnan(q_errors) & ~np.isnan(values)
        if valid_mask.sum() < 3:
            corr = np.nan
            p_value = np.nan
        else:
            corr, p_value = stats.pearsonr(q_errors[valid_mask], values[valid_mask])
        formatted = f"{corr:.4f}{significance_stars(p_value)}" if not np.isnan(corr) else "NaN"
        results[row_label] = formatted
    return results


def main() -> None:
    args = parse_args()
    dataset_dir = args.verbose_root / f"verbose_Train_{args.dataset}_Test_{args.dataset}_ours"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Verbose directory not found: {dataset_dir}")

    pattern = f"{args.task}_*_seed{args.seed}.csv"
    csv_files = sorted(dataset_dir.glob(pattern))
    if not csv_files:
        raise FileNotFoundError(f"No verbose CSV files matched pattern '{pattern}' in {dataset_dir}")

    table = pd.DataFrame(index=[label for _, label in STRUCT_METRICS])
    for csv_path in csv_files:
        print(f"Processing {csv_path.name} ...")
        column_results = compute_correlations(csv_path, args)
        column_label = csv_path.stem
        table[column_label] = [column_results[label] for label in table.index]

    dataset_dir = OUTPUT_DIR / args.dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    out_path = dataset_dir / f"struct_vs_qerror_{args.dataset}_{args.task}_seed{args.seed}.csv"
    table.to_csv(out_path)
    print(f"Saved structural correlation table to {out_path}")


if __name__ == "__main__":
    main()

