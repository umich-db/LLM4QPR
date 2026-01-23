"""
Analyze error percentiles by metric buckets for specific LLM models.

This script:
1. For three specific models (google-gemma-3-4b-pt, meta-llama-Llama-3.1-8B, Qwen-Qwen3-Embedding-8B)
2. For every dataset and task
3. Groups query plans by every metric into n buckets
4. Calculates 50th, 90th, 95th, and max error in every bucket
5. Uses Huber regression to describe how these error percentiles change with bucket index
6. Does this for every model separately and also overall (averaging errors across models)
7. Draws figures for the overall results
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import r2_score
from scipy import stats

try:
    from statsmodels.robust.robust_linear_model import RLM
    from statsmodels.robust.norms import HuberT
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    try:
        from sklearn.linear_model import HuberRegressor
        HAS_SKLEARN = True
    except ImportError:
        HAS_SKLEARN = False

from plan_structural_metrics import PlanStructuralSummary, summarise_plan_structure

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
VERBOSE_ROOT_DEFAULT = EXPERIMENTS_DIR / "verbose"
OUT_DIR = Path(__file__).resolve().parent / "metric_bucket_results"

# Models to analyze
TARGET_MODELS = [
    "google-gemma-3-4b-pt",
    "meta-llama-Llama-3.1-8B",
    "Qwen-Qwen3-Embedding-8B",
]

# Non-LLM algorithms to analyze
NON_LLM_ALGOS = ["bao", "aimai", "qf", "e2e_cost"]

# All structural metrics to analyze
STRUCT_METRICS = [
    "num_tables",
    "num_columns",
    "num_joins",
    "num_filters",
    "longest_path_len",
    "num_nodes",
    "join_tree_diameter",
    "num_blocking_ops",
    "num_nested_loop",
    "max_est_join_input_rows",
    "sum_est_join_input_rows",
    "num_highly_selective_filters",
    "log_filter_selectivity_product",
    "optimizer_est_cost_root",
    "log_max_est_rows",
    "log_sum_est_rows",
    "max_log_card_error",
    "plan_string_length",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze error percentiles by metric buckets for specific LLM models."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Dataset name (e.g., 'stats', 'job'). If not specified, processes all datasets.",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        choices=["card", "time"],
        help="Task type ('card' or 'time'). If not specified, processes all tasks.",
    )
    parser.add_argument(
        "--num_buckets",
        type=int,
        default=10,
        help="Number of buckets to split each metric into",
    )
    parser.add_argument(
        "--verbose_root",
        type=Path,
        default=VERBOSE_ROOT_DEFAULT,
        help="Verbose root directory",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to filter verbose CSVs",
    )
    parser.add_argument(
        "--ngram_n",
        type=int,
        default=3,
        help="n for path n-grams (default: 3)",
    )
    parser.add_argument(
        "--plan_cache_limit",
        type=int,
        default=0,
        help="Optional cap on number of rows (0 = all). Applied after sorting by idx.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug output (e.g., [METRIC_BUCKET] messages).",
    )
    parser.add_argument(
        "--target",
        type=str,
        choices=["llm", "baseline", "both"],
        default="both",
        help="Which targets to process: 'llm' for LLM models only, 'baseline' for non-LLM algorithms only, 'both' for all (default: both)",
    )
    return parser.parse_args()


def extract_first_nonempty(series: pd.Series) -> Path:
    """Extract first non-empty path from a series."""
    filled = series.replace("", pd.NA).ffill().dropna()
    if filled.empty:
        raise ValueError("No path found in verbose CSV column.")
    rel_path = filled.iloc[0]
    path = (EXPERIMENTS_DIR / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def load_embeddings(embedding_path: Path) -> pd.DataFrame:
    """Load embeddings from CSV file."""
    df = pd.read_csv(embedding_path)
    if "idx" in df.columns:
        feat_cols = [c for c in df.columns if c != "idx"]
        return df.set_index("idx")[feat_cols]
    df = df.reset_index().rename(columns={"index": "idx"})
    return df.set_index("idx")


def cosine_distance_matrix(vectors: np.ndarray) -> np.ndarray:
    """Compute cosine distance matrix between all pairs of vectors."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    Z = vectors / norms
    sim = np.clip(Z @ Z.T, -1.0, 1.0)
    dist = 1.0 - sim
    np.fill_diagonal(dist, 0.0)
    return dist


def compute_mean_embedding_distances(vectors: np.ndarray) -> np.ndarray:
    """
    For each plan, compute mean embedding distance to all other plans.
    Same as grand_analysis.py to ensure consistent data alignment.
    """
    D_emb = cosine_distance_matrix(vectors)
    n = D_emb.shape[0]
    # Mean distance excluding self (diagonal is 0, so we can use mean)
    mean_dists = D_emb.mean(axis=1)
    return mean_dists


def _collect_verbose_csvs(dataset_dir: Path, task: str, seed: int, target: str = "llm") -> List[Tuple[Path, str]]:
    """
    Collect verbose CSV files for target models or non-LLM algorithms matching the task and seed.
    
    Args:
        target: "llm" for LLM models, "baseline" for non-LLM algorithms, "both" for all
    
    Returns:
        List of tuples: (csv_path, identifier) where identifier is model name for LLM or algo name for baseline
    """
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
        # Exclude ablation study files (with _rm- suffix)
        if "_rm-" in entry.name:
            continue
        if "lora" in entry.name:
            continue
        if "last" in entry.name:
            continue
        # Exclude downstream task files
        if "downstream" in entry.name:
            continue
        
        stem = entry.stem
        identifier = None
        
        # Check for LLM files
        if stem.startswith(f"{prefix}llm_") and target in ["llm", "both"]:
            # Extract model name between "h2048_" (or "h" followed by digits) and "_emb"
            match = re.search(r'_h\d+_(.+?)_emb\d+', stem)
            if match:
                identifier = match.group(1)
            else:
                match = re.search(r'_h\d+_(.+?)_emb', stem)
                if match:
                    identifier = match.group(1)
                else:
                    identifier = "unknown"
            
            # Only include target models
            if identifier in TARGET_MODELS:
                results.append((entry, identifier))
        
        # Check for non-LLM algorithm files
        elif target in ["baseline", "both"]:
            for algo in NON_LLM_ALGOS:
                if stem.startswith(f"{prefix}{algo}_"):
                    identifier = algo
                    results.append((entry, identifier))
                    break
    
    return results


def compute_bucket_percentiles(
    metric_values: np.ndarray,
    errors: np.ndarray,
    num_buckets: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into equal-sized buckets (quantile-based) based on metric values, then compute percentiles.
    Each bucket will have approximately the same number of data points.
    
    Returns:
        (bucket_indices, bucket_centers, bucket_mins, bucket_maxs, medians, p90s, p95s, max_errors)
        All arrays have shape (num_buckets,)
    """
    # Remove NaN values
    valid_mask = ~(np.isnan(metric_values) | np.isnan(errors))
    metric_clean = metric_values[valid_mask]
    errors_clean = errors[valid_mask]
    
    if len(metric_clean) == 0:
        return (
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
        )
    
    # Sort by metric values to create equal-sized buckets
    sort_indices = np.argsort(metric_clean)
    metric_sorted = metric_clean[sort_indices]
    errors_sorted = errors_clean[sort_indices]
    
    n = len(metric_sorted)
    if n == 0:
        return (
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
        )
    
    # Calculate bucket sizes (approximately equal)
    bucket_size = n / num_buckets
    
    bucket_indices = []
    bucket_centers = []
    bucket_mins = []
    bucket_maxs = []
    medians = []
    p90s = []
    p95s = []
    max_errors = []
    
    # For each bucket, collect points and compute percentiles
    for i in range(num_buckets):
        start_idx = int(i * bucket_size)
        end_idx = int((i + 1) * bucket_size) if i < (num_buckets - 1) else n
        
        if start_idx >= end_idx:
            continue
        
        # Get data points for this bucket
        errors_bucket = errors_sorted[start_idx:end_idx]
        metric_bucket = metric_sorted[start_idx:end_idx]
        
        # Calculate bucket center (median of metric values in this bucket)
        center = np.median(metric_bucket)
        # Calculate bucket min and max (range of metric values in this bucket)
        bucket_min = np.min(metric_bucket)
        bucket_max = np.max(metric_bucket)
        
        # Calculate percentiles of errors in this bucket
        median_val = np.percentile(errors_bucket, 50)
        p90_val = np.percentile(errors_bucket, 90)
        p95_val = np.percentile(errors_bucket, 95)
        max_val = np.max(errors_bucket)
        
        bucket_indices.append(i)
        bucket_centers.append(center)
        bucket_mins.append(bucket_min)
        bucket_maxs.append(bucket_max)
        medians.append(median_val)
        p90s.append(p90_val)
        p95s.append(p95_val)
        max_errors.append(max_val)
    
    return (
        np.array(bucket_indices),
        np.array(bucket_centers),
        np.array(bucket_mins),
        np.array(bucket_maxs),
        np.array(medians),
        np.array(p90s),
        np.array(p95s),
        np.array(max_errors),
    )


def process_single_file(
    csv_path: Path,
    num_buckets: int,
    ngram_n: int,
    plan_cache_limit: int,
    debug: bool = False,
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Process a single verbose CSV file and compute bucket percentiles for all metrics.
    
    Returns:
        Dict[metric_name, Dict[stat_name, array]]
        where stat_name is one of: "bucket_indices", "bucket_centers", "medians", "p90s", "p95s", "max_errors"
    """
    if debug:
        print(f"\n[METRIC_BUCKET] ===== Processing {csv_path.name} =====")
    
    vdf = pd.read_csv(csv_path)
    if debug:
        print(f"[METRIC_BUCKET] Milestone 1: Loaded vdf, shape={vdf.shape}")
    if plan_cache_limit > 0:
        vdf = vdf.iloc[:plan_cache_limit]
        if debug:
            print(f"[METRIC_BUCKET] Milestone 1b: After plan_cache_limit, shape={vdf.shape}")
    
    required_cols = {"q_error", "plan_file"}
    if not required_cols.issubset(vdf.columns):
        missing = required_cols - set(vdf.columns)
        raise KeyError(f"Verbose file {csv_path} missing columns: {missing}")
    
    # Filter vdf based on embeddings if available (same logic as grand_analysis.py)
    # This ensures we use the same dataset for consistent regression coefficients
    mean_emb_dists = None
    if "embedding_file" in vdf.columns:
        emb_path = extract_first_nonempty(vdf["embedding_file"])
        emb_df = load_embeddings(emb_path)
        if debug:
            print(f"[METRIC_BUCKET] Milestone 2: Loaded embeddings, emb_df.shape={emb_df.shape}, vdf.shape={vdf.shape}")
        if "idx" in vdf.columns and emb_df.index.name == "idx":
            valid_mask = vdf["idx"].isin(emb_df.index)
            vdf = vdf[valid_mask].reset_index(drop=True)
            vectors = emb_df.loc[vdf["idx"]].to_numpy(dtype=float)
            if debug:
                print(f"[METRIC_BUCKET] Milestone 2b: After embedding filter, vdf.shape={vdf.shape}, vectors.shape={vectors.shape}")
        else:
            vectors = emb_df.to_numpy(dtype=float)
            vectors = vectors[:len(vdf)]
            if debug:
                print(f"[METRIC_BUCKET] Milestone 2b: After embedding filter (no idx), vdf.shape={vdf.shape}, vectors.shape={vectors.shape}")
        
        # Compute mean embedding distances (same as grand_analysis.py)
        # This is needed for proper alignment
        mean_emb_dists = compute_mean_embedding_distances(vectors)
        if debug:
            print(f"[METRIC_BUCKET] Milestone 3: Computed mean_emb_dists, shape={mean_emb_dists.shape}, first 5 values={mean_emb_dists[:5]}")
    else:
        if debug:
            print(f"[METRIC_BUCKET] Milestone 2: No embedding_file column")
    
    plan_path = extract_first_nonempty(vdf["plan_file"])
    if debug:
        print(f"[METRIC_BUCKET] Milestone 4: Extracted plan_path={plan_path}")
    
    # Load plan data
    plan_df = pd.read_csv(plan_path)
    if "json" not in plan_df.columns:
        raise KeyError(f"'json' column not found in plan file: {plan_path}")
    plan_df = plan_df.reset_index(drop=True)
    if debug:
        print(f"[METRIC_BUCKET] Milestone 5: Loaded plan_df, shape={plan_df.shape}")
    
    # Extract structural metrics
    summaries: List[PlanStructuralSummary] = []
    plan_string_lengths: List[int] = []  # Store plan string lengths separately
    cache: Dict[str, PlanStructuralSummary] = {}
    
    for idx in range(len(vdf)):
        if idx >= len(plan_df):
            # Skip if plan not available, but ensure we still have matching lengths
            # by not appending to either list
            continue
        raw = plan_df.iloc[idx]["json"]
        # Store plan string length (in bytes)
        plan_string_lengths.append(len(raw.encode('utf-8')))
        
        if raw in cache:
            summaries.append(cache[raw])
        else:
            try:
                obj = json.loads(raw)
                summ = summarise_plan_structure(obj, ngram_n=ngram_n)
                summaries.append(summ)
                cache[raw] = summ
            except Exception as e:
                print(f"Warning: Failed to parse plan at idx {idx}: {e}")
                # Create a dummy summary with zeros
                # Note: plan_string_lengths was already appended above, so lengths stay aligned
                dummy = PlanStructuralSummary(
                    num_tables=0, num_columns=0, num_joins=0, num_filters=0,
                    operator_histogram=Counter(), path_ngrams=Counter(),
                    longest_path_len=0, num_nodes=0, join_tree_diameter=0,
                    num_blocking_ops=0, num_nested_loop=0, max_est_join_input_rows=0.0,
                    sum_est_join_input_rows=0.0, num_highly_selective_filters=0,
                    log_filter_selectivity_product=0.0, optimizer_est_cost_root=0.0,
                    log_max_est_rows=0.0, log_sum_est_rows=0.0, max_log_card_error=0.0
                )
                summaries.append(dummy)
    
    if debug:
        print(f"[METRIC_BUCKET] Milestone 6: Extracted summaries, len={len(summaries)}")
    
    # Extract metric values and errors
    q_errors = vdf["q_error"].to_numpy(dtype=float)
    if debug:
        print(f"[METRIC_BUCKET] Milestone 7: Extracted q_errors, shape={q_errors.shape}, first 5 values={q_errors[:5]}")
    
    # Align lengths (same logic as grand_analysis.py)
    # This ensures we use exactly the same data
    if mean_emb_dists is not None:
        min_len = min(len(q_errors), len(mean_emb_dists), len(summaries), len(plan_string_lengths))
        if debug:
            print(f"[METRIC_BUCKET] Milestone 8: Aligning lengths (with mean_emb_dists): len(q_errors)={len(q_errors)}, len(mean_emb_dists)={len(mean_emb_dists)}, len(summaries)={len(summaries)}, len(plan_string_lengths)={len(plan_string_lengths)}, min_len={min_len}")
    else:
        min_len = min(len(q_errors), len(summaries), len(plan_string_lengths))
        if debug:
            print(f"[METRIC_BUCKET] Milestone 8: Aligning lengths (no mean_emb_dists): len(q_errors)={len(q_errors)}, len(summaries)={len(summaries)}, len(plan_string_lengths)={len(plan_string_lengths)}, min_len={min_len}")
    q_errors = q_errors[:min_len]
    plan_string_lengths = plan_string_lengths[:min_len]
    
    # Extract metric values
    metric_values: Dict[str, np.ndarray] = {}
    for metric in STRUCT_METRICS:
        values = []
        if metric == "plan_string_length":
            # Special handling for plan_string_length
            values = plan_string_lengths
        else:
            for s in summaries[:min_len]:
                if hasattr(s, metric):
                    values.append(getattr(s, metric))
                else:
                    values.append(0.0)
        metric_values[metric] = np.array(values, dtype=float)
    
    if debug:
        print(f"[METRIC_BUCKET] Milestone 9: Extracted metric_values, num_metrics={len(metric_values)}, first metric (num_tables) shape={metric_values['num_tables'].shape}, first 5 values={metric_values['num_tables'][:5]}")
    
    # Compute multivariate Huber regression (all metrics together)
    X_matrix = np.column_stack([metric_values[metric] for metric in STRUCT_METRICS])
    if debug:
        print(f"[METRIC_BUCKET] Milestone 10: Prepared X_matrix, shape={X_matrix.shape}, q_errors shape={q_errors.shape}")
        print(f"[METRIC_BUCKET] Milestone 10b: X_matrix first row (first 5 metrics)={X_matrix[0, :5]}")
        print(f"[METRIC_BUCKET] Milestone 10c: q_errors first 5={q_errors[:5]}")
        print(f"[METRIC_BUCKET] Milestone 10d: X_matrix stats - mean={np.mean(X_matrix, axis=0)[:3]}, std={np.std(X_matrix, axis=0)[:3]}")
        print(f"[METRIC_BUCKET] Milestone 10e: q_errors stats - mean={np.mean(q_errors)}, std={np.std(q_errors)}, min={np.min(q_errors)}, max={np.max(q_errors)}")
        print(f"[METRIC_BUCKET] Milestone 10f: X_matrix has NaN: {np.any(np.isnan(X_matrix))}, q_errors has NaN: {np.any(np.isnan(q_errors))}")
    
    multivariate_coefs = huber_regression_multivariate(X_matrix, q_errors, STRUCT_METRICS)
    if debug:
        print(f"[METRIC_BUCKET] Milestone 11: Computed multivariate_coefs")
        for metric in ['num_tables', 'num_columns', 'num_joins']:
            coef, p = multivariate_coefs.get(metric, (float("nan"), float("nan")))
            is_sig = not np.isnan(p) and p < 0.001 and abs(coef) > 0.1
            sig_str = "*** SIGNIFICANT" if is_sig else "not significant"
            print(f"[METRIC_BUCKET]   {metric}: coef={coef:.10f}, p={p:.10f} ({sig_str})")
    
    # Compute univariate Huber regression for each metric
    univariate_coefs: Dict[str, Tuple[float, float]] = {}
    for metric in STRUCT_METRICS:
        coef, p_value = huber_regression_univariate(metric_values[metric], q_errors)
        univariate_coefs[metric] = (coef, p_value)
    
    # Print significance summary for multivariate and univariate
    if debug:
        print(f"[METRIC_BUCKET] Significance summary:")
        sig_multivariate = []
        sig_univariate = []
        for metric in STRUCT_METRICS:
            mult_coef, mult_p = multivariate_coefs.get(metric, (float("nan"), float("nan")))
            univ_coef, univ_p = univariate_coefs.get(metric, (float("nan"), float("nan")))
            
            mult_sig = not np.isnan(mult_p) and mult_p < 0.001 and abs(mult_coef) > 0.1
            univ_sig = not np.isnan(univ_p) and univ_p < 0.001 and abs(univ_coef) > 0.1
            
            if mult_sig:
                sig_multivariate.append(f"{metric} ({mult_coef:+.4f})")
            if univ_sig:
                sig_univariate.append(f"{metric} ({univ_coef:+.4f})")
        
        print(f"  Multivariate significant (|coef|>0.1, p<0.001): {len(sig_multivariate)} metrics")
        if sig_multivariate:
            print(f"    {', '.join(sig_multivariate[:5])}{'...' if len(sig_multivariate) > 5 else ''}")
        print(f"  Univariate significant (|coef|>0.1, p<0.001): {len(sig_univariate)} metrics")
        if sig_univariate:
            print(f"    {', '.join(sig_univariate[:5])}{'...' if len(sig_univariate) > 5 else ''}")
    
    # Compute bucket percentiles for each metric
    results: Dict[str, Dict[str, np.ndarray]] = {}
    for metric in STRUCT_METRICS:
        bucket_indices, bucket_centers, bucket_mins, bucket_maxs, medians, p90s, p95s, max_errors = compute_bucket_percentiles(
            metric_values[metric],
            q_errors,
            num_buckets,
        )
        mult_coef, mult_p = multivariate_coefs.get(metric, (float("nan"), float("nan")))
        univ_coef, univ_p = univariate_coefs.get(metric, (float("nan"), float("nan")))
        results[metric] = {
            "bucket_indices": bucket_indices,
            "bucket_centers": bucket_centers,
            "bucket_mins": bucket_mins,
            "bucket_maxs": bucket_maxs,
            "medians": medians,
            "p90s": p90s,
            "p95s": p95s,
            "max_errors": max_errors,
            "multivariate_coef": mult_coef,
            "multivariate_p": mult_p,
            "univariate_coef": univ_coef,
            "univariate_p": univ_p,
        }
    
    return results


def fit_huber_regression(
    bucket_indices: np.ndarray,
    values: np.ndarray,
) -> Tuple[HuberRegressor, float]:
    """Fit Huber regression and return model and R² score."""
    if len(bucket_indices) < 2:
        return None, 0.0
    
    X = bucket_indices.reshape(-1, 1)
    y = values
    
    # Remove NaN values only
    valid_mask = ~(np.isnan(X.flatten()) | np.isnan(y))
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]
    
    if len(X_clean) < 2:
        return None, 0.0
    
    # Fit Huber regression on all data (including outliers)
    reg = HuberRegressor()
    reg.fit(X_clean, y_clean)
    
    y_pred = reg.predict(X_clean)
    r2 = r2_score(y_clean, y_pred)
    
    return reg, r2


def huber_regression_multivariate(X: np.ndarray, y: np.ndarray, metric_names: List[str]) -> Dict[str, Tuple[float, float]]:
    """
    Perform multivariate Huber regression: y ~ X (all metrics simultaneously)
    Features are z-score normalized (mean=0, std=1) for comparability.
    Returns: Dict[metric_name, (coefficient, p_value)]
    """
    # Remove rows with any NaN
    valid_mask = ~(np.isnan(y) | np.any(np.isnan(X), axis=1))
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]
    
    if len(X_clean) < len(metric_names) + 1:
        return {metric: (float("nan"), float("nan")) for metric in metric_names}
    
    # Normalize features (z-score: mean=0, std=1)
    X_mean = np.mean(X_clean, axis=0, keepdims=True)
    X_std = np.std(X_clean, axis=0, keepdims=True)
    X_std = np.where(X_std < 1e-10, 1.0, X_std)
    X_normalized = (X_clean - X_mean) / X_std
    
    results = {}
    
    if HAS_STATSMODELS:
        # Use statsmodels for proper p-values
        try:
            model = RLM(y_clean, X_normalized, M=HuberT())
            result = model.fit()
            coefs = result.params
            p_values = result.pvalues
            
            for i, metric in enumerate(metric_names):
                if i < len(coefs):
                    results[metric] = (float(coefs[i]), float(p_values[i]))
                else:
                    results[metric] = (float("nan"), float("nan"))
            return results
        except Exception as e:
            print(f"Warning: statsmodels RLM failed, falling back to sklearn: {e}")
            # Fall through to sklearn
    
    if HAS_SKLEARN:
        # Use sklearn HuberRegressor
        try:
            reg = HuberRegressor(epsilon=1.35, max_iter=200, alpha=0.0)
            reg.fit(X_normalized, y_clean)
            coefs = reg.coef_
            
            # Calculate p-values using standard errors
            y_pred = reg.predict(X_normalized)
            residuals = y_clean - y_pred
            n, p = X_normalized.shape
            
            if n > p + 1:
                # Mean squared error
                mse = np.sum(residuals ** 2) / (n - p - 1)
                
                # Calculate standard errors for each coefficient
                # Using the covariance matrix approximation
                # X_normalized is already centered (mean=0), so we can use it directly
                try:
                    # Covariance matrix of coefficients
                    cov_matrix = mse * np.linalg.inv(X_normalized.T @ X_normalized)
                    se_coefs = np.sqrt(np.diag(cov_matrix))
                    
                    # t-statistics and p-values
                    for i, metric in enumerate(metric_names):
                        if i < len(coefs):
                            coef = float(coefs[i])
                            se = float(se_coefs[i]) if i < len(se_coefs) and se_coefs[i] > 0 else float("nan")
                            if not np.isnan(se) and se > 0:
                                t_stat = coef / se
                                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - p - 1))
                            else:
                                p_value = float("nan")
                            results[metric] = (coef, p_value)
                        else:
                            results[metric] = (float("nan"), float("nan"))
                except np.linalg.LinAlgError:
                    # Singular matrix, can't compute p-values
                    for i, metric in enumerate(metric_names):
                        if i < len(coefs):
                            results[metric] = (float(coefs[i]), float("nan"))
                        else:
                            results[metric] = (float("nan"), float("nan"))
            else:
                # Not enough samples for p-value calculation
                for i, metric in enumerate(metric_names):
                    if i < len(coefs):
                        results[metric] = (float(coefs[i]), float("nan"))
                    else:
                        results[metric] = (float("nan"), float("nan"))
            
            return results
        except Exception as e:
            print(f"Warning: sklearn HuberRegressor failed: {e}")
            return {metric: (float("nan"), float("nan")) for metric in metric_names}
    
    # Fallback: use individual Spearman correlations
    print("Warning: Neither statsmodels nor sklearn available. Using Spearman correlation for error.")
    results = {}
    for i, metric in enumerate(metric_names):
        if i < X_clean.shape[1]:
            rho, p = stats.spearmanr(X_clean[:, i], y_clean)
            results[metric] = (float(rho), float(p))
        else:
            results[metric] = (float("nan"), float("nan"))
    return results


def huber_regression_univariate(X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Perform univariate Huber regression: y ~ X (single metric)
    Returns: (coefficient, p_value)
    """
    # Remove NaN values
    valid_mask = ~(np.isnan(X.flatten()) | np.isnan(y))
    X_clean = X[valid_mask].reshape(-1, 1)
    y_clean = y[valid_mask]
    
    if len(X_clean) < 2:
        return (float("nan"), float("nan"))
    
    # Normalize feature (z-score)
    X_mean = np.mean(X_clean)
    X_std = np.std(X_clean)
    if X_std < 1e-10:
        X_std = 1.0
    X_normalized = (X_clean - X_mean) / X_std
    
    # Fit Huber regression
    reg = HuberRegressor(epsilon=1.35, max_iter=200, alpha=0.0)
    reg.fit(X_normalized, y_clean)
    coef = float(reg.coef_[0])
    
    # Calculate p-value
    y_pred = reg.predict(X_normalized)
    residuals = y_clean - y_pred
    n = len(y_clean)
    
    if n > 2:
        mse = np.sum(residuals ** 2) / (n - 2)
        try:
            se_coef = np.sqrt(mse / np.sum((X_normalized - np.mean(X_normalized)) ** 2))
            if se_coef > 0:
                t_stat = coef / se_coef
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                p_value = float("nan")
        except Exception:
            p_value = float("nan")
    else:
        p_value = float("nan")
    
    return (coef, p_value)


def process_dataset_task(
    dataset: str,
    task: str,
    args: argparse.Namespace,
) -> None:
    """Process all files for a dataset/task combination."""
    dataset_dir = args.verbose_root / f"verbose_Train_{dataset}_Test_{dataset}_ours"
    if not dataset_dir.exists():
        print(f"Warning: Dataset directory {dataset_dir} does not exist. Skipping.")
        return
    
    # Collect verbose CSV files for target models or non-LLM algorithms
    csv_files = _collect_verbose_csvs(dataset_dir, task, args.seed, args.target)
    if not csv_files:
        print(f"Warning: No verbose CSV files found for {dataset}/{task}. Skipping.")
        return
    
    print(f"\nProcessing {dataset}/{task}: {len(csv_files)} files")
    
    # Process each model/algorithm separately
    # Group files by identifier (since there may be multiple files per model/algo with different suffixes)
    # We'll process all files for each identifier, but only keep the last one (matching grand_analysis.py behavior)
    identifier_results: Dict[str, Dict[str, Dict[str, np.ndarray]]] = {}
    identifier_file_map: Dict[str, Path] = {}  # Track which file was used for each identifier
    
    for csv_path, identifier in csv_files:
        print(f"  Processing {identifier} from {csv_path.name}...")
        try:
            results = process_single_file(
                csv_path,
                args.num_buckets,
                args.ngram_n,
                args.plan_cache_limit,
                args.debug,
            )
            # Overwrite previous results for this identifier (last file wins, matching grand_analysis.py)
            identifier_results[identifier] = results
            identifier_file_map[identifier] = csv_path
        except Exception as e:
            print(f"    Error processing {csv_path.name}: {e}")
            continue
    
    if not identifier_results:
        print(f"  No valid results for {dataset}/{task}")
        return
    
    # Create output directory
    dataset_task_dir = OUT_DIR / dataset / task
    dataset_task_dir.mkdir(parents=True, exist_ok=True)
    
    # Save per-identifier results
    for identifier, results in identifier_results.items():
        identifier_safe = identifier.replace("/", "_").replace("\\", "_")
        
        # For each metric, save bucket data and fit Huber regression
        metric_data = []
        for metric in STRUCT_METRICS:
            if metric not in results:
                continue
            
            data = results[metric]
            bucket_indices = data["bucket_indices"]
            bucket_centers = data["bucket_centers"]
            bucket_mins = data["bucket_mins"]
            bucket_maxs = data["bucket_maxs"]
            medians = data["medians"]
            p90s = data["p90s"]
            p95s = data["p95s"]
            max_errors = data["max_errors"]
            
            # Get multivariate and univariate coefficients and p-values
            multivariate_coef = data.get("multivariate_coef", float("nan"))
            multivariate_p = data.get("multivariate_p", float("nan"))
            univariate_coef = data.get("univariate_coef", float("nan"))
            univariate_p = data.get("univariate_p", float("nan"))
            
            # Fit Huber regression for each percentile
            reg_med, r2_med = fit_huber_regression(bucket_indices, medians)
            reg_p90, r2_p90 = fit_huber_regression(bucket_indices, p90s)
            reg_p95, r2_p95 = fit_huber_regression(bucket_indices, p95s)
            reg_max, r2_max = fit_huber_regression(bucket_indices, max_errors)
            
            metric_data.append({
                "metric": metric,
                "error_vs_metric_multivariate": multivariate_coef,
                "error_vs_metric_multivariate_p": multivariate_p,
                "error_vs_metric_univariate": univariate_coef,
                "error_vs_metric_univariate_p": univariate_p,
                "huber_med_slope": reg_med.coef_[0] if reg_med else None,
                "huber_p90_slope": reg_p90.coef_[0] if reg_p90 else None,
                "huber_p95_slope": reg_p95.coef_[0] if reg_p95 else None,
                "huber_max_slope": reg_max.coef_[0] if reg_max else None,
                "bucket_index": bucket_indices.tolist(),
                "bucket_center": bucket_centers.tolist(),
                "bucket_min": bucket_mins.tolist(),
                "bucket_max": bucket_maxs.tolist(),
                "median": medians.tolist(),
                "p90": p90s.tolist(),
                "p95": p95s.tolist(),
                "max_error": max_errors.tolist(),
                "huber_med_intercept": reg_med.intercept_ if reg_med else None,
                "huber_med_r2": r2_med,
                "huber_p90_intercept": reg_p90.intercept_ if reg_p90 else None,
                "huber_p90_r2": r2_p90,
                "huber_p95_intercept": reg_p95.intercept_ if reg_p95 else None,
                "huber_p95_r2": r2_p95,
                "huber_max_intercept": reg_max.intercept_ if reg_max else None,
                "huber_max_r2": r2_max,
            })
        
        # Save to CSV
        df = pd.DataFrame(metric_data)
        output_path = dataset_task_dir / f"bucket_analysis_{identifier_safe}.csv"
        df.to_csv(output_path, index=False)
        print(f"    Saved {identifier} results to {output_path}")
    
    # Separate identifiers into LLM models and non-LLM algorithms
    llm_identifiers = [id for id in identifier_results.keys() if id in TARGET_MODELS]
    baseline_identifiers = [id for id in identifier_results.keys() if id in NON_LLM_ALGOS]
    
    # Compute overall results separately for LLM models and non-LLM algorithms
    def compute_overall_results(identifiers_to_use: List[str], suffix: str) -> None:
        """Compute and save overall results for a subset of identifiers."""
        if not identifiers_to_use:
            return
        
        print(f"  Computing overall results for {suffix} (averaging across {len(identifiers_to_use)} identifiers)...")
        overall_results: Dict[str, Dict[str, np.ndarray]] = {}
        
        for metric in STRUCT_METRICS:
            # Collect all bucket data for this metric across identifiers
            all_bucket_indices = []
            all_bucket_centers = []
            all_bucket_mins = []
            all_bucket_maxs = []
            all_medians = []
            all_p90s = []
            all_p95s = []
            all_max_errors = []
            all_multivariate_coefs = []
            all_multivariate_ps = []
            all_univariate_coefs = []
            all_univariate_ps = []
            
            for identifier in identifiers_to_use:
                if identifier not in identifier_results:
                    continue
                results = identifier_results[identifier]
                if metric not in results:
                    continue
                data = results[metric]
                all_bucket_indices.append(data["bucket_indices"])
                all_bucket_centers.append(data["bucket_centers"])
                all_bucket_mins.append(data["bucket_mins"])
                all_bucket_maxs.append(data["bucket_maxs"])
                all_medians.append(data["medians"])
                all_p90s.append(data["p90s"])
                all_p95s.append(data["p95s"])
                all_max_errors.append(data["max_errors"])
                all_multivariate_coefs.append(data.get("multivariate_coef", float("nan")))
                all_multivariate_ps.append(data.get("multivariate_p", float("nan")))
                all_univariate_coefs.append(data.get("univariate_coef", float("nan")))
                all_univariate_ps.append(data.get("univariate_p", float("nan")))
            
            if not all_bucket_indices:
                continue
            
            # Find common bucket indices (union of all models)
            all_indices = set()
            for indices in all_bucket_indices:
                all_indices.update(indices.tolist())
            common_indices = sorted(all_indices)
            
            # Average values for each bucket index
            avg_medians = []
            avg_p90s = []
            avg_p95s = []
            avg_max_errors = []
            avg_centers = []
            avg_mins = []
            avg_maxs = []
            
            for idx in common_indices:
                medians_at_idx = []
                p90s_at_idx = []
                p95s_at_idx = []
                max_errors_at_idx = []
                centers_at_idx = []
                mins_at_idx = []
                maxs_at_idx = []
                
                for i, model_indices in enumerate(all_bucket_indices):
                    if idx in model_indices:
                        pos = np.where(model_indices == idx)[0][0]
                        medians_at_idx.append(all_medians[i][pos])
                        p90s_at_idx.append(all_p90s[i][pos])
                        p95s_at_idx.append(all_p95s[i][pos])
                        max_errors_at_idx.append(all_max_errors[i][pos])
                        centers_at_idx.append(all_bucket_centers[i][pos])
                        mins_at_idx.append(all_bucket_mins[i][pos])
                        maxs_at_idx.append(all_bucket_maxs[i][pos])
                
                if medians_at_idx:
                    avg_medians.append(np.mean(medians_at_idx))
                    avg_p90s.append(np.mean(p90s_at_idx))
                    avg_p95s.append(np.mean(p95s_at_idx))
                    avg_max_errors.append(np.mean(max_errors_at_idx))
                    avg_centers.append(np.mean(centers_at_idx))
                    avg_mins.append(np.mean(mins_at_idx))
                    avg_maxs.append(np.mean(maxs_at_idx))
            
            if avg_medians:
                # Average multivariate and univariate coefficients across models
                multivariate_coefs_clean = [c for c in all_multivariate_coefs if not np.isnan(c)]
                multivariate_ps_clean = [p for i, p in enumerate(all_multivariate_ps) if not np.isnan(all_multivariate_coefs[i])]
                univariate_coefs_clean = [c for c in all_univariate_coefs if not np.isnan(c)]
                univariate_ps_clean = [p for i, p in enumerate(all_univariate_ps) if not np.isnan(all_univariate_coefs[i])]
                
                avg_multivariate_coef = np.mean(multivariate_coefs_clean) if multivariate_coefs_clean else float("nan")
                # For p-values, use the minimum (most significant) if any are significant, otherwise average
                if multivariate_ps_clean:
                    avg_multivariate_p = min(multivariate_ps_clean) if any(p < 0.001 for p in multivariate_ps_clean) else np.mean(multivariate_ps_clean)
                else:
                    avg_multivariate_p = float("nan")
                
                avg_univariate_coef = np.mean(univariate_coefs_clean) if univariate_coefs_clean else float("nan")
                if univariate_ps_clean:
                    avg_univariate_p = min(univariate_ps_clean) if any(p < 0.001 for p in univariate_ps_clean) else np.mean(univariate_ps_clean)
                else:
                    avg_univariate_p = float("nan")
                
                overall_results[metric] = {
                    "bucket_indices": np.array(common_indices[:len(avg_medians)]),
                    "bucket_centers": np.array(avg_centers),
                    "bucket_mins": np.array(avg_mins),
                    "bucket_maxs": np.array(avg_maxs),
                    "medians": np.array(avg_medians),
                    "p90s": np.array(avg_p90s),
                    "p95s": np.array(avg_p95s),
                    "max_errors": np.array(avg_max_errors),
                    "multivariate_coef": avg_multivariate_coef,
                    "multivariate_p": avg_multivariate_p,
                    "univariate_coef": avg_univariate_coef,
                    "univariate_p": avg_univariate_p,
                }
        
        # Save overall results
        overall_data = []
        for metric in STRUCT_METRICS:
            if metric not in overall_results:
                continue
            
            data = overall_results[metric]
            bucket_indices = data["bucket_indices"]
            medians = data["medians"]
            p90s = data["p90s"]
            p95s = data["p95s"]
            max_errors = data["max_errors"]
            
            # Get multivariate and univariate coefficients (averaged across identifiers)
            multivariate_coef = data.get("multivariate_coef", float("nan"))
            multivariate_p = data.get("multivariate_p", float("nan"))
            univariate_coef = data.get("univariate_coef", float("nan"))
            univariate_p = data.get("univariate_p", float("nan"))
            
            # Fit Huber regression on bucket_indices (consistent with CSV)
            reg_med, r2_med = fit_huber_regression(bucket_indices, medians)
            reg_p90, r2_p90 = fit_huber_regression(bucket_indices, p90s)
            reg_p95, r2_p95 = fit_huber_regression(bucket_indices, p95s)
            reg_max, r2_max = fit_huber_regression(bucket_indices, max_errors)
            
            overall_data.append({
                "metric": metric,
                "error_vs_metric_multivariate": multivariate_coef,
                "error_vs_metric_multivariate_p": multivariate_p,
                "error_vs_metric_univariate": univariate_coef,
                "error_vs_metric_univariate_p": univariate_p,
                "huber_med_slope": reg_med.coef_[0] if reg_med else None,
                "huber_p90_slope": reg_p90.coef_[0] if reg_p90 else None,
                "huber_p95_slope": reg_p95.coef_[0] if reg_p95 else None,
                "huber_max_slope": reg_max.coef_[0] if reg_max else None,
                "bucket_index": bucket_indices.tolist(),
                "bucket_center": data["bucket_centers"].tolist(),
                "bucket_min": data["bucket_mins"].tolist(),
                "bucket_max": data["bucket_maxs"].tolist(),
                "median": medians.tolist(),
                "p90": p90s.tolist(),
                "p95": p95s.tolist(),
                "max_error": max_errors.tolist(),
                "huber_med_intercept": reg_med.intercept_ if reg_med else None,
                "huber_med_r2": r2_med,
                "huber_p90_intercept": reg_p90.intercept_ if reg_p90 else None,
                "huber_p90_r2": r2_p90,
                "huber_p95_intercept": reg_p95.intercept_ if reg_p95 else None,
                "huber_p95_r2": r2_p95,
                "huber_max_intercept": reg_max.intercept_ if reg_max else None,
                "huber_max_r2": r2_max,
            })
        
        df_overall = pd.DataFrame(overall_data)
        overall_path = dataset_task_dir / f"bucket_analysis_overall_{suffix}.csv"
        df_overall.to_csv(overall_path, index=False)
        print(f"  Saved overall results to {overall_path}")
        
        # Generate plots only for LLM models
        if suffix == "llm":
            print(f"  Generating plots for {suffix}...")
            plot_dir = dataset_task_dir / "plots"
            plot_dir.mkdir(exist_ok=True)
            
            for metric in STRUCT_METRICS:
                if metric not in overall_results:
                    continue
                
                data = overall_results[metric]
                bucket_indices = data["bucket_indices"]
                bucket_centers = data["bucket_centers"]
                medians = data["medians"]
                p90s = data["p90s"]
                p95s = data["p95s"]
                max_errors = data["max_errors"]
                
                # Fit Huber regression on bucket_indices (x-axis will be bucket index)
                reg_med, _ = fit_huber_regression(bucket_indices, medians)
                reg_p90, _ = fit_huber_regression(bucket_indices, p90s)
                reg_p95, _ = fit_huber_regression(bucket_indices, p95s)
                reg_max, _ = fit_huber_regression(bucket_indices, max_errors)
                
                # Create smooth line using bucket_indices for x-axis
                if len(bucket_indices) > 0:
                    x_line = np.linspace(
                        bucket_indices.min(),
                        bucket_indices.max(),
                        200
                    ).reshape(-1, 1)
                    y_line_med = reg_med.predict(x_line) if reg_med else None
                    y_line_p90 = reg_p90.predict(x_line) if reg_p90 else None
                    y_line_p95 = reg_p95.predict(x_line) if reg_p95 else None
                    y_line_max = reg_max.predict(x_line) if reg_max else None
                else:
                    x_line = np.array([])
                    y_line_med = None
                    y_line_p90 = None
                    y_line_p95 = None
                    y_line_max = None
                
                # Plot
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Ensure arrays are 1D and non-empty
                if len(bucket_centers) == 0 or len(medians) == 0:
                    print(f"    Warning: Empty data for {metric}, skipping plot")
                    plt.close(fig)
                    continue
                
                # Scatter points (use bucket_indices for x-axis)
                ax.scatter(
                    bucket_indices.flatten() if bucket_indices.ndim > 1 else bucket_indices,
                    medians.flatten() if medians.ndim > 1 else medians,
                    s=50,
                    color="tab:blue",
                    marker="o",
                    label="50th percentile"
                )
                ax.scatter(
                    bucket_indices.flatten() if bucket_indices.ndim > 1 else bucket_indices,
                    p90s.flatten() if p90s.ndim > 1 else p90s,
                    s=50,
                    color="tab:orange",
                    marker="s",
                    label="90th percentile"
                )
                ax.scatter(
                    bucket_indices.flatten() if bucket_indices.ndim > 1 else bucket_indices,
                    p95s.flatten() if p95s.ndim > 1 else p95s,
                    s=50,
                    color="tab:green",
                    marker="^",
                    label="95th percentile"
                )
                ax.scatter(
                    bucket_indices.flatten() if bucket_indices.ndim > 1 else bucket_indices,
                    max_errors.flatten() if max_errors.ndim > 1 else max_errors,
                    s=50,
                    color="tab:red",
                    marker="v",
                    label="Max error"
                )
                
                # Huber-fitted lines (all solid lines, not dotted)
                if y_line_med is not None and x_line is not None:
                    ax.plot(
                        x_line.flatten(),
                        y_line_med,
                        color="tab:blue",
                        linestyle="-",  # Solid line
                        linewidth=2.0,
                        label="Huber fit (50th)"
                    )
                if y_line_p90 is not None and x_line is not None:
                    ax.plot(
                        x_line.flatten(),
                        y_line_p90,
                        color="tab:orange",
                        linestyle="-",  # Solid line (not dotted)
                        linewidth=2.0,
                        label="Huber fit (90th)"
                    )
                if y_line_p95 is not None and x_line is not None:
                    ax.plot(
                        x_line.flatten(),
                        y_line_p95,
                        color="tab:green",
                        linestyle="-",  # Solid line (not dotted)
                        linewidth=2.0,
                        label="Huber fit (95th)"
                    )
                if y_line_max is not None and x_line is not None:
                    ax.plot(
                        x_line.flatten(),
                        y_line_max,
                        color="tab:red",
                        linestyle="-",
                        linewidth=2.0,
                        label="Huber fit (max)"
                    )
                
                ax.set_xlabel("Bucket Index", fontweight='bold', fontsize=14)
                ax.set_ylabel("Q-Error", fontweight='bold', fontsize=14)
                ax.set_title(f"{metric} - {dataset}/{task}", fontsize=14)
                ax.grid(True)
                ax.legend(fontsize=10, loc="upper left")
                
                # Handle outliers: set reasonable y-axis limits
                # Collect all y-values to determine limits
                all_y_values = np.concatenate([medians, p90s, p95s, max_errors])
                all_y_values = all_y_values[~np.isnan(all_y_values)]
                all_y_values = all_y_values[all_y_values > 0]  # Only positive values
                
                if len(all_y_values) > 0:
                    # Use IQR method to detect outliers for y-axis limits only
                    q1 = np.percentile(all_y_values, 25)
                    q3 = np.percentile(all_y_values, 75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # Find non-outlier values
                    non_outliers = all_y_values[(all_y_values >= lower_bound) & (all_y_values <= upper_bound)]
                    
                    if len(non_outliers) > 0:
                        # Set y-axis limits based on non-outliers, with some padding
                        y_min = max(0, np.min(non_outliers) * 0.9)  # Don't go below 0
                        y_max = np.max(non_outliers) * 1.1
                        
                        # If there are outliers, cap the y-axis at a reasonable value
                        # This prevents the plot from being squeezed by outliers
                        if np.any(all_y_values > upper_bound):
                            # Cap y-axis at reasonable value (2x upper_bound or 95th percentile * 1.5)
                            y_max_capped = min(y_max * 2, np.percentile(all_y_values, 95) * 1.5)
                            ax.set_ylim(y_min, y_max_capped)
                            
                            # Add text annotation for extreme outliers that are above the y-axis limit
                            for i, (x, y) in enumerate(zip(bucket_indices, max_errors)):
                                if y > y_max_capped:  # Very extreme outliers above the y-axis limit
                                    ax.annotate(
                                        f'{y:.1f}',
                                        xy=(x, y_max_capped),  # Place annotation at the top of the plot
                                        xytext=(5, 5),
                                        textcoords='offset points',
                                        fontsize=8,
                                        color='red',
                                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5),
                                        arrowprops=dict(arrowstyle='->', color='red', lw=1)
                                    )
                        else:
                            # No outliers, use standard limits
                            ax.set_ylim(y_min, y_max)
                    else:
                        # Fallback: use percentile-based limits
                        y_min = max(0, np.percentile(all_y_values, 5))
                        y_max = np.percentile(all_y_values, 95) * 1.2
                        ax.set_ylim(y_min, y_max)
                
                metric_safe = metric.replace("/", "_").replace("\\", "_")
                plot_path = plot_dir / f"{metric_safe}.png"
                fig.tight_layout()
                fig.savefig(plot_path, dpi=300, bbox_inches="tight")
                plt.close(fig)
            
            print(f"  Saved plots to {plot_dir}")
    
    # Call the function for LLM models and non-LLM algorithms separately
    if llm_identifiers:
        compute_overall_results(llm_identifiers, "llm")
    if baseline_identifiers:
        compute_overall_results(baseline_identifiers, "baseline")


def classify_error_coefficient(coef: float, p_value: float) -> int:
    """
    Classify error coefficient into -1, 0, or 1.
    
    Returns:
        - 1 if coefficient is positive, significant (p < 0.001), and |coef| > 0.1
        - -1 if coefficient is negative, significant (p < 0.001), and |coef| > 0.1
        - 0 otherwise
    """
    if np.isnan(coef) or np.isnan(p_value):
        return 0
    
    if p_value >= 0.001:
        return 0
    
    if abs(coef) <= 0.1:
        return 0
    
    if coef > 0:
        return 1
    else:
        return -1


def classify_huber_slopes(med_slope: float, p90_slope: float, p95_slope: float, max_slope: float) -> int:
    """
    Classify Huber slopes into -1, 0, or 1 based on majority direction.
    
    Args:
        med_slope: Huber regression slope for median error
        p90_slope: Huber regression slope for 90th percentile error
        p95_slope: Huber regression slope for 95th percentile error
        max_slope: Huber regression slope for max error
    
    Returns:
        - 1 if at least 3 of the 4 slopes are positive
        - -1 if at least 3 of the 4 slopes are negative
        - 0 otherwise
    """
    slopes = [med_slope, p90_slope, p95_slope, max_slope]
    
    # Count positive and negative slopes (excluding NaN)
    positive_count = sum(1 for s in slopes if not np.isnan(s) and s > 0)
    negative_count = sum(1 for s in slopes if not np.isnan(s) and s < 0)
    
    if positive_count >= 3:
        return 1
    elif negative_count >= 3:
        return -1
    else:
        return 0


def classify_error_coefficient_simple(coef: float) -> int:
    """
    Simple classification of error coefficient based only on sign.
    No requirement for significance or absolute value threshold.
    
    Returns:
        - 1 if coefficient is positive
        - -1 if coefficient is negative
        - 0 if coefficient is NaN or zero
    """
    if np.isnan(coef):
        return 0
    
    if coef > 0:
        return 1
    elif coef < 0:
        return -1
    else:
        return 0


def collect_bucket_analysis_files() -> Dict[Tuple[str, str, str], Path]:
    """
    Collect all bucket_analysis files for target models.
    
    Returns:
        Dict mapping (dataset, task, model) -> file path
    """
    files_map: Dict[Tuple[str, str, str], Path] = {}
    
    if not OUT_DIR.exists():
        print(f"Warning: Output directory {OUT_DIR} does not exist.")
        return files_map
    
    # Iterate through all dataset/task/model combinations
    for dataset_dir in OUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue
        
        dataset = dataset_dir.name
        
        for task_dir in dataset_dir.iterdir():
            if not task_dir.is_dir():
                continue
            
            task = task_dir.name
            
            # Look for bucket_analysis files for target models
            for file_path in task_dir.glob("bucket_analysis_*.csv"):
                # Skip overall files
                if "overall" in file_path.name:
                    continue
                
                # Extract model name from filename: bucket_analysis_{model}.csv
                stem = file_path.stem
                model = stem.replace("bucket_analysis_", "")
                
                # Only include target models
                if model in TARGET_MODELS:
                    files_map[(dataset, task, model)] = file_path
    
    return files_map


def generate_error_coefficient_analysis(processed_datasets_tasks: set[tuple[str, str]] | None = None) -> None:
    """
    Generate error coefficient analysis files similar to analyze_error_coefficients.py.
    Uses multivariate coefficients from bucket_analysis files.
    Also generates Huber slope analysis files.
    """
    print("\n" + "=" * 80)
    print("Generating error coefficient analysis files...")
    print("=" * 80)
    
    files_map = collect_bucket_analysis_files()
    
    # Filter to only include datasets/tasks that were processed in the current run
    if processed_datasets_tasks is not None:
        files_map = {
            (dataset, task, model): file_path
            for (dataset, task, model), file_path in files_map.items()
            if (dataset, task) in processed_datasets_tasks
        }
    
    if not files_map:
        print("Warning: No bucket_analysis files found for target models.")
        return
    
    print(f"Found {len(files_map)} bucket_analysis files:")
    for (dataset, task, model), file_path in sorted(files_map.items()):
        print(f"  {dataset}/{task}/{model}: {file_path.name}")
    
    # Get all tasks
    tasks = sorted(set(task for (_, task, _) in files_map.keys()))
    
    # Process each task (aggregated across all models)
    for task in tasks:
        print(f"\nProcessing task: {task} (aggregated)")
        
        # Collect data: metric -> dataset -> list of classification values (one per model)
        metric_data: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        
        # Get all datasets for this task
        datasets = sorted(set(dataset for (dataset, file_task, _) in files_map.keys() if file_task == task))
        
        # Process each file
        for (dataset, file_task, model), file_path in files_map.items():
            if file_task != task:
                continue
            
            try:
                df = pd.read_csv(file_path)
                if "error_vs_metric_multivariate" not in df.columns:
                    print(f"Warning: {file_path.name} does not have 'error_vs_metric_multivariate' column. Skipping.")
                    continue
                
                # Process each metric
                for _, row in df.iterrows():
                    metric = row["metric"]
                    if metric not in STRUCT_METRICS:
                        continue
                    
                    coef = row["error_vs_metric_multivariate"]
                    p_value = row.get("error_vs_metric_multivariate_p", float("nan"))
                    
                    # Always try to get p-value from grand_analysis file (more reliable)
                    # The bucket_analysis p-values might not be accurate
                    grand_analysis_dir = OUT_DIR.parent / "grand_analysis_results" / dataset
                    pattern = f"grand_analysis_{dataset}_{task}_seed*_llm_{model}.csv"
                    grand_files = list(grand_analysis_dir.glob(pattern))
                    if grand_files:
                        try:
                            grand_df = pd.read_csv(grand_files[0], index_col=0)
                            if metric in grand_df.index and "error" in grand_df.columns:
                                # Parse the formatted error string to get p-value
                                error_str = str(grand_df.loc[metric, "error"])
                                # Extract p-value from formatted string (has *** if p < 0.001)
                                if "***" in error_str:
                                    p_value = 0.0005  # p < 0.001
                                elif "**" in error_str:
                                    p_value = 0.005  # p < 0.01
                                elif "*" in error_str:
                                    p_value = 0.05  # p < 0.05
                                else:
                                    p_value = 1.0  # Not significant
                        except Exception:
                            pass
                    
                    classification = classify_error_coefficient(coef, p_value)
                    metric_data[metric][dataset].append(classification)
                    
            except Exception as e:
                print(f"Warning: Failed to process {file_path.name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Build result table
        result_rows = []
        for metric in STRUCT_METRICS:
            row = {"metric": metric}
            for dataset in datasets:
                values = metric_data[metric][dataset]
                if values:
                    # Sum across the three models for this dataset
                    row[dataset] = sum(values)
                else:
                    row[dataset] = 0
            result_rows.append(row)
        
        # Create DataFrame
        df_result = pd.DataFrame(result_rows)
        df_result = df_result.set_index("metric")
        
        # Add sum column (sum across datasets for each metric)
        df_result["sum"] = df_result.sum(axis=1)
        
        # Save to CSV
        output_path = OUT_DIR.parent / "grand_analysis_results" / f"error_coefficient_analysis_{task}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_result.to_csv(output_path)
        print(f"Saved aggregated analysis to {output_path}")
        print(f"Shape: {df_result.shape}")
        
        # Also generate simple classification (no significance or threshold requirement)
        print(f"\nProcessing task: {task} (aggregated) - Simple classification")
        metric_data_simple: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        
        # Process each file again for simple classification
        for (dataset, file_task, model), file_path in files_map.items():
            if file_task != task:
                continue
            
            try:
                df = pd.read_csv(file_path)
                if "error_vs_metric_multivariate" not in df.columns:
                    continue
                
                # Process each metric
                for _, row in df.iterrows():
                    metric = row["metric"]
                    if metric not in STRUCT_METRICS:
                        continue
                    
                    coef = row["error_vs_metric_multivariate"]
                    classification = classify_error_coefficient_simple(coef)
                    metric_data_simple[metric][dataset].append(classification)
                    
            except Exception as e:
                continue
        
        # Build result table for simple classification
        result_rows_simple = []
        for metric in STRUCT_METRICS:
            row = {"metric": metric}
            for dataset in datasets:
                values = metric_data_simple[metric][dataset]
                if values:
                    row[dataset] = sum(values)
                else:
                    row[dataset] = 0
            result_rows_simple.append(row)
        
        # Create DataFrame
        df_result_simple = pd.DataFrame(result_rows_simple)
        df_result_simple = df_result_simple.set_index("metric")
        
        # Add sum column
        df_result_simple["sum"] = df_result_simple.sum(axis=1)
        
        # Save to CSV
        output_path_simple = OUT_DIR.parent / "grand_analysis_results" / f"error_coefficient_analysis_simple_{task}.csv"
        output_path_simple.parent.mkdir(parents=True, exist_ok=True)
        df_result_simple.to_csv(output_path_simple)
        print(f"Saved aggregated simple analysis to {output_path_simple}")
        print(f"Shape: {df_result_simple.shape}")
    
    # Process each task for each model separately
    for task in tasks:
        for model in TARGET_MODELS:
            print(f"\nProcessing task: {task}, model: {model}")
            
            # Collect data: metric -> dataset -> classification value
            metric_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            
            # Get all datasets for this task and model
            datasets = sorted(set(
                dataset for (dataset, file_task, file_model) in files_map.keys()
                if file_task == task and file_model == model
            ))
            
            # Process each file for this model
            for (dataset, file_task, file_model), file_path in files_map.items():
                if file_task != task or file_model != model:
                    continue
                
                try:
                    df = pd.read_csv(file_path)
                    if "error_vs_metric_multivariate" not in df.columns:
                        print(f"Warning: {file_path.name} does not have 'error_vs_metric_multivariate' column. Skipping.")
                        continue
                    
                    # Process each metric
                    for _, row in df.iterrows():
                        metric = row["metric"]
                        if metric not in STRUCT_METRICS:
                            continue
                        
                        coef = row["error_vs_metric_multivariate"]
                        p_value = row.get("error_vs_metric_multivariate_p", float("nan"))
                        
                        # Always try to get p-value from grand_analysis file (more reliable)
                        grand_analysis_dir = OUT_DIR.parent / "grand_analysis_results" / dataset
                        pattern = f"grand_analysis_{dataset}_{task}_seed*_llm_{model}.csv"
                        grand_files = list(grand_analysis_dir.glob(pattern))
                        if grand_files:
                            try:
                                grand_df = pd.read_csv(grand_files[0], index_col=0)
                                if metric in grand_df.index and "error" in grand_df.columns:
                                    error_str = str(grand_df.loc[metric, "error"])
                                    if "***" in error_str:
                                        p_value = 0.0005  # p < 0.001
                                    elif "**" in error_str:
                                        p_value = 0.005  # p < 0.01
                                    elif "*" in error_str:
                                        p_value = 0.05  # p < 0.05
                                    else:
                                        p_value = 1.0  # Not significant
                            except Exception:
                                pass
                        
                        classification = classify_error_coefficient(coef, p_value)
                        metric_data[metric][dataset] = classification
                        
                except Exception as e:
                    print(f"Warning: Failed to process {file_path.name}: {e}")
                    continue
            
            # Build result table
            result_rows = []
            for metric in STRUCT_METRICS:
                row = {"metric": metric}
                for dataset in datasets:
                    classification = metric_data[metric][dataset]
                    row[dataset] = classification
                result_rows.append(row)
            
            # Create DataFrame
            df_result = pd.DataFrame(result_rows)
            df_result = df_result.set_index("metric")
            
            if df_result.empty:
                print(f"  No data found for {model} in task {task}")
                continue
            
            # Add sum column (sum across datasets for each metric)
            df_result["sum"] = df_result.sum(axis=1)
            
            # Create a safe filename from model name
            model_safe = model.replace("/", "_").replace("\\", "_")
            output_path = OUT_DIR.parent / "grand_analysis_results" / f"error_coefficient_analysis_{task}_{model_safe}.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df_result.to_csv(output_path)
            print(f"Saved model-specific analysis to {output_path}")
            print(f"Shape: {df_result.shape}")
            
            # Also generate simple classification for this model
            print(f"\nProcessing task: {task}, model: {model} - Simple classification")
            metric_data_simple: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            
            # Process each file for this model
            for (dataset, file_task, file_model), file_path in files_map.items():
                if file_task != task or file_model != model:
                    continue
                
                try:
                    df = pd.read_csv(file_path)
                    if "error_vs_metric_multivariate" not in df.columns:
                        continue
                    
                    # Process each metric
                    for _, row in df.iterrows():
                        metric = row["metric"]
                        if metric not in STRUCT_METRICS:
                            continue
                        
                        coef = row["error_vs_metric_multivariate"]
                        classification = classify_error_coefficient_simple(coef)
                        metric_data_simple[metric][dataset] = classification
                        
                except Exception as e:
                    continue
            
            # Build result table for simple classification
            result_rows_simple = []
            for metric in STRUCT_METRICS:
                row = {"metric": metric}
                for dataset in datasets:
                    classification = metric_data_simple[metric][dataset]
                    row[dataset] = classification
                result_rows_simple.append(row)
            
            # Create DataFrame
            df_result_simple = pd.DataFrame(result_rows_simple)
            df_result_simple = df_result_simple.set_index("metric")
            
            if df_result_simple.empty:
                continue
            
            # Add sum column
            df_result_simple["sum"] = df_result_simple.sum(axis=1)
            
            # Save to CSV
            output_path_simple = OUT_DIR.parent / "grand_analysis_results" / f"error_coefficient_analysis_simple_{task}_{model_safe}.csv"
            output_path_simple.parent.mkdir(parents=True, exist_ok=True)
            df_result_simple.to_csv(output_path_simple)
            print(f"Saved model-specific simple analysis to {output_path_simple}")
            print(f"Shape: {df_result_simple.shape}")
    
    # Generate Huber slope analysis files
    print("\n" + "=" * 80)
    print("Generating Huber slope analysis files...")
    print("=" * 80)
    
    # Process each task (aggregated across all models) for slopes
    for task in tasks:
        print(f"\nProcessing task: {task} (aggregated) - Huber slopes")
        
        # Collect data: metric -> dataset -> list of classification values (one per model)
        metric_data: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        
        # Get all datasets for this task
        datasets = sorted(set(dataset for (dataset, file_task, _) in files_map.keys() if file_task == task))
        
        # Process each file
        for (dataset, file_task, model), file_path in files_map.items():
            if file_task != task:
                continue
            
            try:
                df = pd.read_csv(file_path)
                required_cols = ["huber_med_slope", "huber_p90_slope", "huber_p95_slope", "huber_max_slope"]
                if not all(col in df.columns for col in required_cols):
                    print(f"Warning: {file_path.name} missing slope columns. Skipping.")
                    continue
                
                # Process each metric
                for _, row in df.iterrows():
                    metric = row["metric"]
                    if metric not in STRUCT_METRICS:
                        continue
                    
                    med_slope = row.get("huber_med_slope", float("nan"))
                    p90_slope = row.get("huber_p90_slope", float("nan"))
                    p95_slope = row.get("huber_p95_slope", float("nan"))
                    max_slope = row.get("huber_max_slope", float("nan"))
                    
                    classification = classify_huber_slopes(med_slope, p90_slope, p95_slope, max_slope)
                    metric_data[metric][dataset].append(classification)
                    
            except Exception as e:
                print(f"Warning: Failed to process {file_path.name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Build result table
        result_rows = []
        for metric in STRUCT_METRICS:
            row = {"metric": metric}
            for dataset in datasets:
                values = metric_data[metric][dataset]
                if values:
                    # Sum across the three models for this dataset
                    row[dataset] = sum(values)
                else:
                    row[dataset] = 0
            result_rows.append(row)
        
        # Create DataFrame
        df_result = pd.DataFrame(result_rows)
        df_result = df_result.set_index("metric")
        
        # Add sum column (sum across datasets for each metric)
        df_result["sum"] = df_result.sum(axis=1)
        
        # Save to CSV
        output_path = OUT_DIR.parent / "grand_analysis_results" / f"huber_slope_analysis_{task}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_result.to_csv(output_path)
        print(f"Saved aggregated slope analysis to {output_path}")
        print(f"Shape: {df_result.shape}")
    
    # Process each task for each model separately for slopes
    for task in tasks:
        for model in TARGET_MODELS:
            print(f"\nProcessing task: {task}, model: {model} - Huber slopes")
            
            # Collect data: metric -> dataset -> classification value
            metric_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            
            # Get all datasets for this task and model
            datasets = sorted(set(
                dataset for (dataset, file_task, file_model) in files_map.keys()
                if file_task == task and file_model == model
            ))
            
            # Process each file for this model
            for (dataset, file_task, file_model), file_path in files_map.items():
                if file_task != task or file_model != model:
                    continue
                
                try:
                    df = pd.read_csv(file_path)
                    required_cols = ["huber_med_slope", "huber_p90_slope", "huber_p95_slope", "huber_max_slope"]
                    if not all(col in df.columns for col in required_cols):
                        print(f"Warning: {file_path.name} missing slope columns. Skipping.")
                        continue
                    
                    # Process each metric
                    for _, row in df.iterrows():
                        metric = row["metric"]
                        if metric not in STRUCT_METRICS:
                            continue
                        
                        med_slope = row.get("huber_med_slope", float("nan"))
                        p90_slope = row.get("huber_p90_slope", float("nan"))
                        p95_slope = row.get("huber_p95_slope", float("nan"))
                        max_slope = row.get("huber_max_slope", float("nan"))
                        
                        classification = classify_huber_slopes(med_slope, p90_slope, p95_slope, max_slope)
                        metric_data[metric][dataset] = classification
                        
                except Exception as e:
                    print(f"Warning: Failed to process {file_path.name}: {e}")
                    continue
            
            # Build result table
            result_rows = []
            for metric in STRUCT_METRICS:
                row = {"metric": metric}
                for dataset in datasets:
                    classification = metric_data[metric][dataset]
                    row[dataset] = classification
                result_rows.append(row)
            
            # Create DataFrame
            df_result = pd.DataFrame(result_rows)
            df_result = df_result.set_index("metric")
            
            if df_result.empty:
                print(f"  No data found for {model} in task {task}")
                continue
            
            # Add sum column (sum across datasets for each metric)
            df_result["sum"] = df_result.sum(axis=1)
            
            # Create a safe filename from model name
            model_safe = model.replace("/", "_").replace("\\", "_")
            output_path = OUT_DIR.parent / "grand_analysis_results" / f"huber_slope_analysis_{task}_{model_safe}.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df_result.to_csv(output_path)
            print(f"Saved model-specific slope analysis to {output_path}")
            print(f"Shape: {df_result.shape}")


def collect_baseline_bucket_analysis_files() -> Dict[Tuple[str, str, str], Path]:
    """
    Collect all bucket_analysis files for non-LLM algorithms.
    
    Returns:
        Dict mapping (dataset, task, algo) -> file path
    """
    files_map: Dict[Tuple[str, str, str], Path] = {}
    
    if not OUT_DIR.exists():
        print(f"Warning: Output directory {OUT_DIR} does not exist.")
        return files_map
    
    # Iterate through all dataset/task/algo combinations
    for dataset_dir in OUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue
        
        dataset = dataset_dir.name
        
        for task_dir in dataset_dir.iterdir():
            if not task_dir.is_dir():
                continue
            
            task = task_dir.name
            
            # Look for bucket_analysis files for non-LLM algorithms
            for file_path in task_dir.glob("bucket_analysis_*.csv"):
                # Skip overall files
                if "overall" in file_path.name:
                    continue
                
                # Extract algo name from filename: bucket_analysis_{algo}.csv
                stem = file_path.stem
                algo = stem.replace("bucket_analysis_", "")
                
                # Only include non-LLM algorithms
                if algo in NON_LLM_ALGOS:
                    files_map[(dataset, task, algo)] = file_path
    
    return files_map


def generate_baseline_huber_slope_analysis() -> None:
    """
    Generate Huber slope analysis files for non-LLM algorithms.
    Similar to generate_error_coefficient_analysis but for baselines.
    """
    print("\n" + "=" * 80)
    print("Generating Huber slope analysis for non-LLM algorithms...")
    print("=" * 80)
    
    files_map = collect_baseline_bucket_analysis_files()
    
    if not files_map:
        print("Warning: No bucket analysis files found for non-LLM algorithms.")
        print("You may need to run metric_bucket_analysis.py for non-LLM algorithms first.")
        return
    
    # Get all unique tasks and algorithms
    tasks = sorted(set(task for (_, task, _) in files_map.keys()))
    algos = sorted(set(algo for (_, _, algo) in files_map.keys()))
    
    print(f"Found {len(files_map)} bucket analysis files")
    print(f"Tasks: {tasks}")
    print(f"Algorithms: {algos}")
    
    # Process each task for each algorithm separately for slopes
    for task in tasks:
        for algo in algos:
            print(f"\nProcessing task: {task}, algorithm: {algo} - Huber slopes")
            
            # Collect data: metric -> dataset -> classification value
            metric_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            
            # Get all datasets for this task and algorithm
            datasets = sorted(set(
                dataset for (dataset, file_task, file_algo) in files_map.keys()
                if file_task == task and file_algo == algo
            ))
            
            # Process each file for this algorithm
            for (dataset, file_task, file_algo), file_path in files_map.items():
                if file_task != task or file_algo != algo:
                    continue
                
                try:
                    df = pd.read_csv(file_path)
                    required_cols = ["huber_med_slope", "huber_p90_slope", "huber_p95_slope", "huber_max_slope"]
                    if not all(col in df.columns for col in required_cols):
                        print(f"Warning: {file_path.name} missing slope columns. Skipping.")
                        continue
                    
                    # Process each metric
                    for _, row in df.iterrows():
                        metric = row["metric"]
                        if metric not in STRUCT_METRICS:
                            continue
                        
                        med_slope = row.get("huber_med_slope", float("nan"))
                        p90_slope = row.get("huber_p90_slope", float("nan"))
                        p95_slope = row.get("huber_p95_slope", float("nan"))
                        max_slope = row.get("huber_max_slope", float("nan"))
                        
                        classification = classify_huber_slopes(med_slope, p90_slope, p95_slope, max_slope)
                        metric_data[metric][dataset] = classification
                        
                except Exception as e:
                    print(f"Warning: Failed to process {file_path.name}: {e}")
                    continue
            
            # Build result table
            result_rows = []
            for metric in STRUCT_METRICS:
                row = {"metric": metric}
                for dataset in datasets:
                    classification = metric_data[metric][dataset]
                    row[dataset] = classification
                result_rows.append(row)
            
            # Create DataFrame
            df_result = pd.DataFrame(result_rows)
            df_result = df_result.set_index("metric")
            
            if df_result.empty:
                print(f"  No data found for {algo} in task {task}")
                continue
            
            # Add sum column (sum across datasets for each metric)
            df_result["sum"] = df_result.sum(axis=1)
            
            # Create output directory for baselines
            baseline_dir = OUT_DIR.parent / "grand_analysis_results" / "huber_slope_baselines"
            baseline_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a safe filename from algorithm name
            algo_safe = algo.replace("/", "_").replace("\\", "_")
            output_path = baseline_dir / f"huber_slope_analysis_{task}_{algo_safe}.csv"
            df_result.to_csv(output_path)
            print(f"Saved baseline slope analysis to {output_path}")
            print(f"Shape: {df_result.shape}")


def main() -> None:
    args = parse_args()
    
    # Determine which datasets and tasks to process
    all_datasets = ["job", "job_full", "stats", "syn", "tpch", "tpcds"]
    all_tasks = ["card", "time"]
    
    if args.dataset:
        if args.dataset not in all_datasets:
            raise ValueError(
                f"Unknown dataset: {args.dataset}. "
                f"Valid options: {', '.join(all_datasets)}"
            )
        datasets = [args.dataset]
    else:
        datasets = all_datasets
    
    if args.task:
        tasks = [args.task]
    else:
        tasks = all_tasks
    
    total = len(datasets) * len(tasks)
    current = 0
    processed_datasets_tasks: set[tuple[str, str]] = set()
    
    for dataset in datasets:
        for task in tasks:
            current += 1
            print(f"\n{'='*60}")
            print(f"Processing {current}/{total}: {dataset}/{task}")
            print(f"{'='*60}")
            try:
                # Check if any files were actually processed
                dataset_dir = args.verbose_root / f"verbose_Train_{dataset}_Test_{dataset}_ours"
                csv_files = _collect_verbose_csvs(dataset_dir, task, args.seed)
                if csv_files:
                    process_dataset_task(dataset, task, args)
                    processed_datasets_tasks.add((dataset, task))
                else:
                    print(f"Warning: No verbose CSV files found for {dataset}/{task}. Skipping.")
            except Exception as e:
                print(f"Error processing {dataset}/{task}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print(f"\n{'='*60}")
    print(f"Completed! Results saved to {OUT_DIR}")
    print(f"{'='*60}")
    
    # Generate error coefficient analysis files (only for datasets/tasks that were actually processed)
    if args.target in ["llm", "both"]:
        generate_error_coefficient_analysis(processed_datasets_tasks)
    
    # Generate Huber slope analysis for non-LLM algorithms
    if args.target in ["baseline", "both"]:
        generate_baseline_huber_slope_analysis()


if __name__ == "__main__":
    main()

