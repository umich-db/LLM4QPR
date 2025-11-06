#!/usr/bin/env python3
"""
Analyze relative error impact of field removals (`rm-card`, `rm-cond`, `rm-cost-meta`)
for LLM algorithms across specified datasets.

For each dataset (syn, job, stats), this script looks inside:
  results/results_Train_{dataset}_Test_{dataset}_ours/
and loads the file:
  quantile_table_results_results_Train_{dataset}_Test_{dataset}_ours_card.csv

For every LLM model that has the following variants:
  1. baseline (no `_rm-` suffix)
  2. `_rm-card`
  3. `_rm-cond`
  4. `_rm-cost-meta`

the script computes the relative error of each removal compared to the baseline
at all evaluation points (50, 90, 95, max).

Usage:
    python card_rm_analysis.py --datasets syn job stats
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Supported datasets that have cardinality measurements
SUPPORTED_DATASETS = {"syn", "job", "stats"}

# Required ablation suffixes (exact string in column names)
REQUIRED_ABLATIONS = ["_rm-card", "_rm-cond", "_rm-cost-meta"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze LLM field removal impact on cardinality metrics.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        required=True,
        choices=sorted(SUPPORTED_DATASETS),
        help="Datasets to include in the analysis (choose one or more of: syn, job, stats).",
    )
    parser.add_argument(
        "--results_root",
        type=str,
        default="results",
        help="Root directory containing the per-dataset results (default: results).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write the aggregated relative-error table as CSV.",
    )
    parser.add_argument(
        "--average_by",
        nargs="+",
        choices=["dataset", "model"],
        default=None,
        help="Optional fields to average relative errors across (choose any combination of 'dataset' and 'model').",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Optional list of LLM model identifiers to include (matches on extracted model string). "
             "If omitted, all models are analyzed.",
    )
    return parser.parse_args()


def split_column(column_name: str) -> Tuple[str, Optional[str]]:
    """
    Split a column name into its baseline portion and optional ablation suffix.
    Returns (base_name, suffix) where suffix is None for baseline.
    """
    if "_rm-" not in column_name:
        return column_name, None
    idx = column_name.index("_rm-")
    return column_name[:idx], column_name[idx:]


def extract_model_identifier(column_name: str) -> str:
    """
    Attempt to extract the core model identifier from a full LLM column name.
    Falls back to the original column name if parsing fails.
    """
    match = re.search(r"card_llm_pretrained-[^_]*_[^_]*_cdf_[^_]*_[^_]*_[^_]*_(.+?)_emb", column_name)
    if match:
        return match.group(1)
    return column_name


def load_dataset_table(results_root: Path, dataset: str) -> pd.DataFrame:
    """
    Load the quantile table for the given dataset.
    """
    csv_path = (
        results_root
        / f"results_Train_{dataset}_Test_{dataset}_ours"
        / f"quantile_table_results_results_Train_{dataset}_Test_{dataset}_ours_card.csv"
    )
    if not csv_path.exists():
        raise FileNotFoundError(f"Expected file not found for dataset '{dataset}': {csv_path}")
    # First column is the evaluation point; use it as index
    df = pd.read_csv(csv_path, index_col=0)
    return df


def gather_llm_columns(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Build a mapping from baseline column name to its variants (baseline + ablations).
    Returns dict: {base_name: {'baseline': col_name, '_rm-card': col_name, ...}}
    """
    llm_columns: Dict[str, Dict[str, str]] = {}
    for col in df.columns:
        if not col.startswith("card_llm"):
            continue
        base_name, suffix = split_column(col)
        entry = llm_columns.setdefault(base_name, {})
        if suffix is None:
            entry["baseline"] = col
        else:
            entry[suffix] = col
    return llm_columns


def compute_relative_errors(
    df: pd.DataFrame, dataset: str, allowed_models: Optional[List[str]] = None
) -> List[Dict[str, object]]:
    """
    Compute relative errors for all LLM models in the dataframe that have the required ablations.
    Returns a list of dictionaries with the results.
    """
    results: List[Dict[str, object]] = []
    llm_columns = gather_llm_columns(df)

    for base_name, variants in llm_columns.items():
        baseline_col = variants.get("baseline")
        if baseline_col is None:
            continue

        # Ensure all required ablation variants are present
        if not all(ab_suffix in variants for ab_suffix in REQUIRED_ABLATIONS):
            continue

        model_id = extract_model_identifier(base_name)
        if allowed_models is not None and model_id not in allowed_models:
            continue

        baseline_values = df[baseline_col]

        for ab_suffix in REQUIRED_ABLATIONS:
            ablation_col = variants[ab_suffix]
            ablation_values = df[ablation_col]

            # Relative error = ablation / baseline (element-wise)
            relative_series = ablation_values / baseline_values

            for metric, rel_error in relative_series.items():
                results.append(
                    {
                        "dataset": dataset,
                        "model": model_id,
                        "ablation": ab_suffix.replace("_rm-", ""),
                        "metric": metric,
                        "baseline_error": baseline_values.loc[metric],
                        "ablation_error": ablation_values.loc[metric],
                        "relative_error": rel_error,
                    }
                )

    return results


def main():
    args = parse_args()
    results_root = Path(args.results_root)

    all_results: List[Dict[str, object]] = []

    for dataset in args.datasets:
        df = load_dataset_table(results_root, dataset)
        dataset_results = compute_relative_errors(df, dataset, allowed_models=args.models)
        if not dataset_results:
            print(f"[WARN] No complete LLM baseline/ablation sets found for dataset '{dataset}'.")
        all_results.extend(dataset_results)

    if not all_results:
        print("No relative error data was produced. Check datasets or available ablation variants.")
        return

    results_df = pd.DataFrame(all_results)
    # Sort for readability
    results_df.sort_values(by=["dataset", "model", "ablation", "metric"], inplace=True)

    # Display summary
    print("\nRelative error of field removals compared to baseline (ablation / baseline):")
    print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # Optional averaging across specified fields
    if args.average_by:
        # Determine which dimensions to KEEP (those not averaged across)
        total_dims = ["dataset", "model"]
        keep_dims = [dim for dim in total_dims if dim not in args.average_by]

        if len(keep_dims) < len(total_dims):
            group_cols = keep_dims + ["ablation", "metric"]

            avg_df = (
                results_df.groupby(group_cols, as_index=False)
                .agg(
                    baseline_error=("baseline_error", "mean"),
                    ablation_error=("ablation_error", "mean"),
                    relative_error=("relative_error", "mean"),
                )
            )
            report_df = avg_df

            averaged_dims = [dim for dim in args.average_by if dim in total_dims]
            print(
                "\nAverage relative errors aggregated across "
                f"{', '.join(averaged_dims)} (mean over specified dimensions):"
            )
            print(report_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

            # Compare ablations relative to 'cond' baseline per metric
            comparison_records = []
            if keep_dims:
                group_iterable = report_df.groupby(keep_dims)
            else:
                group_iterable = [((), report_df)]

            for group_key, group_df in group_iterable:
                if not isinstance(group_key, tuple):
                    group_key = (group_key,)
                group_label = dict(zip(keep_dims, group_key)) if keep_dims else {}

                for metric, metric_df in group_df.groupby("metric"):
                    cond_rows = metric_df[metric_df["ablation"] == "cond"]
                    if cond_rows.empty:
                        continue
                    cond_value = cond_rows["relative_error"].iloc[0]

                    # Always record cond as baseline (ratio 1.0 if finite)
                    cond_record = {
                        "metric": metric,
                        "ablation": "cond",
                        "relative_to_cond": 1.0,
                        "cond_relative_error": cond_value,
                        "ablation_relative_error": cond_value,
                    }
                    cond_record.update(group_label)
                    comparison_records.append(cond_record)

                    for ablation in ["card", "cost-meta"]:
                        ab_rows = metric_df[metric_df["ablation"] == ablation]
                        if ab_rows.empty:
                            continue
                        ab_value = ab_rows["relative_error"].iloc[0]
                        if cond_value == 0:
                            rel_ratio = float("inf")
                        else:
                            rel_ratio = ab_value / cond_value

                        record = {
                            "metric": metric,
                            "ablation": ablation,
                            "relative_to_cond": rel_ratio,
                            "cond_relative_error": cond_value,
                            "ablation_relative_error": ab_value,
                        }
                        record.update(group_label)
                        comparison_records.append(record)

            if comparison_records:
                comparison_df = pd.DataFrame(comparison_records)
                print("\nRelative-to-cond comparison (ablation_relative_error / cond_relative_error):")
                print(comparison_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

                summary_group_cols = list(keep_dims) + ["ablation"]
                ratio_summary = (
                    comparison_df.groupby(summary_group_cols, as_index=False)["relative_to_cond"]
                    .mean()
                    .rename(columns={"relative_to_cond": "mean_relative_to_cond"})
                )
                print("\nAverage relative-to-cond ratio across metrics:")
                print(ratio_summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
            else:
                print("\n[INFO] No relative-to-cond comparison could be computed (missing 'cond' baseline).")
        else:
            print(
                "\n[WARN] --average_by did not match any supported dimensions (dataset, model)."
            )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(output_path, index=False)
        print(f"\nResults written to: {output_path}")


if __name__ == "__main__":
    main()

