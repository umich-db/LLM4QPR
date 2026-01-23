#!/usr/bin/env python3
"""
Analyze query plans in high (90-100%) and low (0-50%) error ranges.

For each dataset/task and the three target models:
1. Find query plans in 90-100% error range (high error)
2. Find query plans in 0-50% error range (low error)
3. Find common query plans across the three models in each range
4. Compare metrics between high and low error ranges
5. Report cases where high-error plans have larger metric values than low-error plans
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from plan_structural_metrics import PlanStructuralSummary, summarise_plan_structure

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
VERBOSE_ROOT_DEFAULT = EXPERIMENTS_DIR / "verbose"
INSIGHTS_DIR = Path(__file__).resolve().parent
OUT_DIR = INSIGHTS_DIR / "error_range_analysis_results"

# Target models
TARGET_MODELS = [
    "google-gemma-3-1b-pt",
    "meta-llama-Llama-3.1-8B",
    "Qwen-Qwen3-Embedding-8B",
]

# Metrics to analyze for time task
TIME_METRICS = [
    "num_tables",
    "num_columns",
    "num_joins",
    "num_filters",
    "longest_path_len",
    "num_nodes",
    "join_tree_diameter",
    "num_nested_loop",
    "max_log_card_error",
]

# Metrics to analyze for card task
CARD_METRICS = [
    "num_tables",
    "num_columns",
    "num_joins",
    "num_filters",
    "longest_path_len",
    "num_nodes",
    "num_nested_loop",
    "num_highly_selective_filters",
    "max_log_card_error",
]


def extract_first_nonempty(series: pd.Series) -> Path:
    """Extract first non-empty path from a series."""
    filled = series.replace("", pd.NA).ffill().dropna()
    if filled.empty:
        raise ValueError("No path found in verbose CSV column.")
    rel_path = filled.iloc[0]
    return Path(rel_path)


def _collect_verbose_csvs(dataset_dir: Path, task: str, seed: int) -> List[Tuple[Path, str]]:
    """Collect verbose CSV files for target models."""
    import re
    
    prefix = f"{task}_"
    seed_token = f"seed{seed}"
    results: List[Tuple[Path, str]] = []
    
    for entry in sorted(dataset_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".csv":
            continue
        if not entry.name.startswith(prefix):
            continue
        if seed_token not in entry.stem:
            continue
        # Exclude ablation study files and downstream files
        if "_rm-" in entry.name or "downstream" in entry.name:
            continue
        
        stem = entry.stem
        model = None
        
        # Check for LLM files
        if stem.startswith(f"{prefix}llm_"):
            # Extract model name between "h2048_" (or "h" followed by digits) and "_emb"
            match = re.search(r'_h\d+_(.+?)_emb\d+', stem)
            if match:
                model = match.group(1)
            else:
                match = re.search(r'_h\d+_(.+?)_emb', stem)
                if match:
                    model = match.group(1)
                else:
                    model = "unknown"
            
            # Only include target models
            if model in TARGET_MODELS:
                results.append((entry, model))
    
    return results


def get_error_percentiles(q_errors: np.ndarray) -> Tuple[float, float, float, float]:
    """Get percentile thresholds for error ranges."""
    p0 = np.percentile(q_errors, 0)
    p50 = np.percentile(q_errors, 50)
    p90 = np.percentile(q_errors, 90)
    p100 = np.percentile(q_errors, 100)
    return p0, p50, p90, p100


def find_plans_in_range(
    vdf: pd.DataFrame,
    plan_df: pd.DataFrame,
    error_range: Tuple[float, float],
    summaries: Dict[int, PlanStructuralSummary],
) -> Dict[str, Tuple[float, Dict[str, float], int]]:
    """
    Find query plans in a specific error range.
    
    Returns:
        Dict mapping plan_json to (error, metrics_dict, idx)
    """
    q_errors = vdf["q_error"].to_numpy(dtype=float)
    min_error, max_error = error_range
    
    results: Dict[str, Tuple[float, Dict[str, float], int]] = {}
    
    for idx in range(min(len(vdf), len(plan_df))):
        error = q_errors[idx]
        if min_error <= error <= max_error:
            plan_json = plan_df.iloc[idx]["json"]
            if idx in summaries:
                summary = summaries[idx]
                metrics = {
                    "num_tables": summary.num_tables,
                    "num_columns": summary.num_columns,
                    "num_joins": summary.num_joins,
                    "num_filters": summary.num_filters,
                    "longest_path_len": summary.longest_path_len,
                    "num_nodes": summary.num_nodes,
                    "join_tree_diameter": summary.join_tree_diameter,
                    "num_blocking_ops": summary.num_blocking_ops,
                    "num_nested_loop": summary.num_nested_loop,
                    "max_est_join_input_rows": summary.max_est_join_input_rows,
                    "sum_est_join_input_rows": summary.sum_est_join_input_rows,
                    "num_highly_selective_filters": summary.num_highly_selective_filters,
                    "log_filter_selectivity_product": summary.log_filter_selectivity_product,
                    "optimizer_est_cost_root": summary.optimizer_est_cost_root,
                    "log_max_est_rows": summary.log_max_est_rows,
                    "log_sum_est_rows": summary.log_sum_est_rows,
                    "max_log_card_error": summary.max_log_card_error,
                }
                # If same plan appears multiple times, keep the one with the error closest to the range center
                if plan_json not in results or abs(error - (min_error + max_error) / 2) < abs(results[plan_json][0] - (min_error + max_error) / 2):
                    results[plan_json] = (error, metrics, idx)
    
    return results


def process_dataset_task(dataset: str, task: str, seed: int = 42) -> None:
    """Process a single dataset/task combination."""
    dataset_dir = VERBOSE_ROOT_DEFAULT / f"verbose_Train_{dataset}_Test_{dataset}_ours"
    
    if not dataset_dir.exists():
        print(f"Warning: Dataset directory {dataset_dir} does not exist. Skipping.")
        return
    
    # Collect verbose CSV files for target models
    csv_files = _collect_verbose_csvs(dataset_dir, task, seed)
    
    if len(csv_files) != len(TARGET_MODELS):
        print(f"Warning: Expected {len(TARGET_MODELS)} files for {dataset}/{task}, found {len(csv_files)}. Skipping.")
        return
    
    print(f"\nProcessing {dataset}/{task}...")
    
    # Determine metrics to analyze
    metrics_to_analyze = TIME_METRICS if task == "time" else CARD_METRICS
    
    # Process each model
    model_data: Dict[str, Dict[str, Dict[str, Tuple[float, Dict[str, float], int]]]] = {}
    
    for csv_path, model in csv_files:
        print(f"  Loading {model}...")
        
        vdf = pd.read_csv(csv_path)
        required_cols = {"q_error", "plan_file"}
        if not required_cols.issubset(vdf.columns):
            print(f"    Warning: Missing required columns. Skipping.")
            continue
        
        # Load plan data
        plan_path = extract_first_nonempty(vdf["plan_file"])
        plan_df = pd.read_csv(plan_path)
        if "json" not in plan_df.columns:
            print(f"    Warning: 'json' column not found. Skipping.")
            continue
        
        plan_df = plan_df.reset_index(drop=True)
        
        # Extract structural metrics
        summaries: Dict[int, PlanStructuralSummary] = {}
        for idx in range(min(len(vdf), len(plan_df))):
            raw = plan_df.iloc[idx]["json"]
            try:
                obj = json.loads(raw)
                summ = summarise_plan_structure(obj, ngram_n=3)
                summaries[idx] = summ
            except Exception:
                continue
        
        # Get error percentiles
        q_errors = vdf["q_error"].to_numpy(dtype=float)
        p0, p50, p90, p100 = get_error_percentiles(q_errors)
        
        # For job_full, use 70-100% instead of 90-100% for high error range
        if dataset == "job_full":
            p70 = np.percentile(q_errors, 70)
            high_error_threshold = p70
        else:
            high_error_threshold = p90
        
        # Find plans in low error range (0-50%)
        low_range_plans = find_plans_in_range(vdf, plan_df, (p0, p50), summaries)
        
        # Find plans in high error range (70-100% for job_full, 90-100% for others)
        high_range_plans = find_plans_in_range(vdf, plan_df, (high_error_threshold, p100), summaries)
        
        model_data[model] = {
            "low": low_range_plans,
            "high": high_range_plans,
        }
        
        range_label = "70-100%" if dataset == "job_full" else "90-100%"
        print(f"    Low range (0-50%): {len(low_range_plans)} plans")
        print(f"    High range ({range_label}): {len(high_range_plans)} plans")
    
    # Find common plans across all three models
    if len(model_data) != len(TARGET_MODELS):
        print(f"  Warning: Not all models processed. Skipping common plan analysis.")
        return
    
    # Get plan JSONs for each range
    low_plan_jsons = [set(model_data[m]["low"].keys()) for m in TARGET_MODELS]
    high_plan_jsons = [set(model_data[m]["high"].keys()) for m in TARGET_MODELS]
    
    # Find intersection (common plans)
    common_low_plans = set.intersection(*low_plan_jsons) if low_plan_jsons else set()
    common_high_plans = set.intersection(*high_plan_jsons) if high_plan_jsons else set()
    
    print(f"  Common plans in low range: {len(common_low_plans)}")
    print(f"  Common plans in high range: {len(common_high_plans)}")
    
    # Build dictionaries mapping plan_json to (error, metrics, idx) for each model
    low_plan_data: Dict[str, Dict[str, Tuple[float, Dict[str, float], int]]] = {}
    high_plan_data: Dict[str, Dict[str, Tuple[float, Dict[str, float], int]]] = {}
    
    for model in TARGET_MODELS:
        for plan_json in common_low_plans:
            if plan_json in model_data[model]["low"]:
                if plan_json not in low_plan_data:
                    low_plan_data[plan_json] = {}
                low_plan_data[plan_json][model] = model_data[model]["low"][plan_json]
        
        for plan_json in common_high_plans:
            if plan_json in model_data[model]["high"]:
                if plan_json not in high_plan_data:
                    high_plan_data[plan_json] = {}
                high_plan_data[plan_json][model] = model_data[model]["high"][plan_json]
    
    # Pre-compute average metrics for all plans
    high_plan_metrics_all: Dict[str, Dict[str, float]] = {}
    low_plan_metrics_all: Dict[str, Dict[str, float]] = {}
    
    for plan_json in common_high_plans:
        if plan_json not in high_plan_data:
            continue
        metrics_avg = {}
        for model in TARGET_MODELS:
            if model in high_plan_data[plan_json]:
                _, metrics, _ = high_plan_data[plan_json][model]
                for metric in metrics_to_analyze:
                    if metric not in metrics_avg:
                        metrics_avg[metric] = []
                    metrics_avg[metric].append(metrics.get(metric, 0.0))
        # Average across models
        for metric in metrics_avg:
            metrics_avg[metric] = np.mean(metrics_avg[metric])
        high_plan_metrics_all[plan_json] = metrics_avg
    
    for plan_json in common_low_plans:
        if plan_json not in low_plan_data:
            continue
        metrics_avg = {}
        for model in TARGET_MODELS:
            if model in low_plan_data[plan_json]:
                _, metrics, _ = low_plan_data[plan_json][model]
                for metric in metrics_to_analyze:
                    if metric not in metrics_avg:
                        metrics_avg[metric] = []
                    metrics_avg[metric].append(metrics.get(metric, 0.0))
        # Average across models
        for metric in metrics_avg:
            metrics_avg[metric] = np.mean(metrics_avg[metric])
        low_plan_metrics_all[plan_json] = metrics_avg
    
    # Helper function to compute relative value for a plan pair
    def compute_pair_relative_value(
        high_plan_json: str,
        low_plan_json: str,
        high_metrics: Dict[str, float],
        low_metrics: Dict[str, float],
        high_plan_data_entry: Dict[str, Tuple[float, Dict[str, float], int]],
        low_plan_data_entry: Dict[str, Tuple[float, Dict[str, float], int]],
    ) -> Tuple[float, Dict]:
        """Compute average relative value across all metrics for a plan pair."""
        relative_values = []
        for metric in metrics_to_analyze:
            high_val = high_metrics.get(metric, 0.0)
            low_val = low_metrics.get(metric, 0.0)
            if high_val > 0:
                relative_values.append(low_val / high_val)
            elif low_val > 0:
                # If high_val is 0 but low_val > 0, use a very small relative value
                relative_values.append(1e-10)  # Use very small number
        
        avg_relative = np.mean(relative_values) if relative_values else 0.0
        
        # Get error and idx information
        high_errors = []
        high_indices = []
        for model in TARGET_MODELS:
            if model in high_plan_data_entry:
                error, _, idx = high_plan_data_entry[model]
                high_errors.append(error)
                high_indices.append(idx)
        
        low_errors = []
        low_indices = []
        for model in TARGET_MODELS:
            if model in low_plan_data_entry:
                error, _, idx = low_plan_data_entry[model]
                low_errors.append(error)
                low_indices.append(idx)
        
        avg_high_error = np.mean(high_errors) if high_errors else 0.0
        avg_low_error = np.mean(low_errors) if low_errors else 0.0
        high_idx = max(set(high_indices), key=high_indices.count) if high_indices else -1
        low_idx = max(set(low_indices), key=low_indices.count) if low_indices else -1
        
        pair_info = {
            "high_plan_json": high_plan_json,
            "low_plan_json": low_plan_json,
            "high_metrics": high_metrics,
            "low_metrics": low_metrics,
            "high_errors": high_errors,
            "low_errors": low_errors,
            "avg_high_error": avg_high_error,
            "avg_low_error": avg_low_error,
            "high_idx": high_idx,
            "low_idx": low_idx,
        }
        
        return (avg_relative, pair_info)
    
    # Generate all plan pairs with their data
    all_pairs_data = []
    for high_plan_json in common_high_plans:
        if high_plan_json not in high_plan_data or high_plan_json not in high_plan_metrics_all:
            continue
        for low_plan_json in common_low_plans:
            if low_plan_json not in low_plan_data or low_plan_json not in low_plan_metrics_all:
                continue
            all_pairs_data.append((
                high_plan_json,
                low_plan_json,
                high_plan_metrics_all[high_plan_json],
                low_plan_metrics_all[low_plan_json],
                high_plan_data[high_plan_json],
                low_plan_data[low_plan_json],
            ))
    
    print(f"  Computing relative values for {len(all_pairs_data)} plan pairs...")
    
    # Compute relative values in parallel
    pair_scores: List[Tuple[float, Dict]] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(compute_pair_relative_value, h, l, hm, lm, hd, ld): (h, l)
            for h, l, hm, lm, hd, ld in all_pairs_data
        }
        for future in as_completed(futures):
            try:
                score, pair_info = future.result()
                if score > 0 and not np.isinf(score):  # Only keep pairs with valid relative values
                    pair_scores.append((score, pair_info))
            except Exception as e:
                print(f"    Warning: Error computing pair: {e}")
                continue
    
    # Sort by average relative value (ascending) and take bottom 10 (lowest values)
    pair_scores.sort(key=lambda x: x[0], reverse=False)
    top_pairs = pair_scores[:10]
    
    print(f"  Selected top {len(top_pairs)} plan pairs by average relative value")
    
    # Generate findings for top pairs
    findings: List[Dict] = []
    for avg_relative, pair_info in top_pairs:
        high_metrics = pair_info["high_metrics"]
        low_metrics = pair_info["low_metrics"]
        
        # For each metric, check if high > low
        for metric in metrics_to_analyze:
            high_val = high_metrics.get(metric, 0.0)
            low_val = low_metrics.get(metric, 0.0)
            
            if high_val > low_val:
                findings.append({
                    "metric": metric,
                    "high_error_plan": pair_info["high_plan_json"][:100] + "..." if len(pair_info["high_plan_json"]) > 100 else pair_info["high_plan_json"],
                    "low_error_plan": pair_info["low_plan_json"][:100] + "..." if len(pair_info["low_plan_json"]) > 100 else pair_info["low_plan_json"],
                    "high_error_avg": pair_info["avg_high_error"],
                    "low_error_avg": pair_info["avg_low_error"],
                    "high_metric_value": high_val,
                    "low_metric_value": low_val,
                    "high_plan_errors": pair_info["high_errors"],
                    "low_plan_errors": pair_info["low_errors"],
                    "high_plan_metrics": {m: high_metrics.get(m, 0.0) for m in metrics_to_analyze},
                    "low_plan_metrics": {m: low_metrics.get(m, 0.0) for m in metrics_to_analyze},
                    "high_plan_idx": pair_info["high_idx"],
                    "low_plan_idx": pair_info["low_idx"],
                    "avg_relative_value": avg_relative,
                })
    
    # Save results
    if findings:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUT_DIR / f"{dataset}_{task}_findings.json"
        
        with open(output_file, "w") as f:
            json.dump(findings, f, indent=2)
        
        print(f"  Found {len(findings)} cases where high-error plans have larger metrics")
        print(f"  Saved to {output_file}")
        
        # Also create a summary CSV
        # Group findings by plan pair (high_plan_idx, low_plan_idx, avg_relative_value)
        pair_groups: Dict[Tuple[int, int, float], List[Dict]] = {}
        for finding in findings:
            key = (
                finding["high_plan_idx"],
                finding["low_plan_idx"],
                finding.get("avg_relative_value", 0.0),
            )
            if key not in pair_groups:
                pair_groups[key] = []
            pair_groups[key].append(finding)
        
        # Create summary rows, grouping by pair
        summary_rows = []
        for (high_idx, low_idx, avg_rel), group_findings in pair_groups.items():
            # Sort metrics within each group
            group_findings.sort(key=lambda x: x["metric"])
            for finding in group_findings:
                summary_rows.append({
                    "metric": finding["metric"],
                    "high_error_avg": finding["high_error_avg"],
                    "low_error_avg": finding["low_error_avg"],
                    "high_metric_value": finding["high_metric_value"],
                    "low_metric_value": finding["low_metric_value"],
                    "difference": finding["high_metric_value"] - finding["low_metric_value"],
                    "high_plan_idx": finding["high_plan_idx"],
                    "low_plan_idx": finding["low_plan_idx"],
                    "avg_relative_value": finding.get("avg_relative_value", 0.0),
                })
        
        if summary_rows:
            df = pd.DataFrame(summary_rows)
            # Sort by plan pair (high_plan_idx, low_plan_idx) first, then by metric
            # This groups all metrics from the same plan pair together
            df = df.sort_values(by=["high_plan_idx", "low_plan_idx", "metric"], ascending=[True, True, True])
            csv_file = OUT_DIR / f"{dataset}_{task}_summary.csv"
            df.to_csv(csv_file, index=False)
            print(f"  Summary saved to {csv_file}")
    else:
        print(f"  No cases found where high-error plans have larger metrics")


def main() -> None:
    """Main function."""
    datasets = ["job", "job_full", "stats", "syn", "tpch", "tpcds"]
    tasks = ["card", "time"]
    seed = 42
    
    print("=" * 80)
    print("Analyzing query plans in error ranges")
    print("=" * 80)
    
    for dataset in datasets:
        for task in tasks:
            try:
                process_dataset_task(dataset, task, seed)
            except Exception as e:
                print(f"Error processing {dataset}/{task}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print("\n" + "=" * 80)
    print("Completed!")
    print(f"Results saved to {OUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()

