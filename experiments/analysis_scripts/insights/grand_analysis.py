"""
Grand analysis: Spearman correlation between structural metrics and q_error, true_label, embedding.

For each dataset/task/seed, this script:
  - Collects all verbose CSV files (all algo/model combinations)
  - Extracts structural metrics for each query plan
  - Computes Spearman correlations between each metric and:
      * q_error
      * true_label
      * mean embedding distance (to all other plans)
  - Aggregates results across all algo/model combinations
  - Determines type_number based on positive *** significant correlations
  - Outputs a CSV with metrics as rows and columns: error, true_label, embedding, type_number
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
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
OUT_DIR = Path(__file__).resolve().parent / "grand_analysis_results"

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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grand analysis: correlations between metrics and error/label/embedding."
    )
    parser.add_argument("--dataset", required=True, help="Dataset (e.g., job_full).")
    parser.add_argument("--task", required=True, choices=["card", "time"], help="Task type.")
    parser.add_argument("--seed", type=int, default=42, help="Seed to filter verbose CSVs.")
    parser.add_argument("--verbose_root", type=Path, default=VERBOSE_ROOT_DEFAULT, help="Verbose root.")
    parser.add_argument("--ngram_n", type=int, default=3, help="n for path n-grams (default: 3).")
    parser.add_argument(
        "--plan_cache_limit",
        type=int,
        default=0,
        help="Optional cap on number of rows (0 = all). Applied after sorting by idx.",
    )
    return parser.parse_args()


def _collect_verbose_csvs(dataset_dir: Path, task: str, seed: int) -> List[Tuple[Path, str, str | None]]:
    """
    Collect all verbose CSV files matching the task and seed, and extract algo/model combinations.
    
    Returns:
        List of tuples: (csv_path, algo, model) where model is None for non-LLM algorithms.
    """
    prefix = f"{task}_"
    seed_token = f"seed{seed}"
    results: List[Tuple[Path, str, str | None]] = []
    
    # Known non-LLM algorithms
    non_llm_algos = ["bao", "aimai", "qf", "e2e_cost", "postgres"]
    
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
        # Exclude downstream task files
        if "downstream" in entry.name:
            continue
        
        stem = entry.stem
        algo = None
        model = None
        
        # Check for LLM first (files starting with {task}_llm_)
        if stem.startswith(f"{prefix}llm_"):
            algo = "llm"
            # Extract model name between "h2048_" (or "h" followed by digits) and "_emb" (or "_emb" followed by digits)
            # Pattern: ..._h2048_<MODEL_NAME>_emb1000_...
            # Look for pattern: h<digits>_<model>_emb<digits>
            match = re.search(r'_h\d+_(.+?)_emb\d+', stem)
            if match:
                model = match.group(1)
            else:
                # Fallback: try to find between any "h" followed by digits and "_emb"
                match = re.search(r'_h\d+_(.+?)_emb', stem)
                if match:
                    model = match.group(1)
                else:
                    model = "unknown"
        else:
            # Check for non-LLM algorithms
            for non_llm_algo in non_llm_algos:
                if stem.startswith(f"{prefix}{non_llm_algo}_"):
                    algo = non_llm_algo
                    break
        
        if algo:
            results.append((entry, algo, model))
    
    return results


def extract_first_nonempty(series: pd.Series) -> Path:
    filled = series.replace("", pd.NA).ffill().dropna()
    if filled.empty:
        raise ValueError("No path found in verbose CSV column.")
    rel_path = filled.iloc[0]
    path = (EXPERIMENTS_DIR / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def load_embeddings(embedding_path: Path) -> pd.DataFrame:
    df = pd.read_csv(embedding_path)
    if "idx" in df.columns:
        feat_cols = [c for c in df.columns if c != "idx"]
        return df.set_index("idx")[feat_cols]
    df = df.reset_index().rename(columns={"index": "idx"})
    return df.set_index("idx")


def cosine_distance_matrix(vectors: np.ndarray) -> np.ndarray:
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
    """
    D_emb = cosine_distance_matrix(vectors)
    n = D_emb.shape[0]
    # Mean distance excluding self (diagonal is 0, so we can use mean)
    mean_dists = D_emb.mean(axis=1)
    return mean_dists


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


def huber_regression_multivariate(X: np.ndarray, y: np.ndarray, metric_names: List[str]) -> Dict[str, Tuple[float, float]]:
    """
    Perform multivariate Huber regression: y ~ X (all metrics simultaneously)
    Features are z-score normalized (mean=0, std=1) for comparability.
    Returns: Dict[metric_name, (coefficient, p_value)]
    Positive coefficient means error increases as metric increases (per standard deviation).
    """
    # Remove rows with any NaN
    valid_mask = ~(np.isnan(y) | np.any(np.isnan(X), axis=1))
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]
    
    if len(X_clean) < len(metric_names) + 1:  # Need at least n_features + 1 samples
        return {metric: (float("nan"), float("nan")) for metric in metric_names}
    
    # Normalize features (z-score: mean=0, std=1)
    # This makes coefficients comparable across metrics with different scales
    X_mean = np.mean(X_clean, axis=0, keepdims=True)
    X_std = np.std(X_clean, axis=0, keepdims=True)
    # Avoid division by zero for constant features
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


def format_coefficient(value: float, p_value: float) -> str:
    """
    Format coefficient with significance stars, avoiding 0.0000***.
    Uses scientific notation for very small numbers.
    """
    if np.isnan(value):
        return "NaN"
    
    stars = significance_stars(p_value)
    abs_value = abs(value)
    
    # If value is exactly zero or rounds to zero with 4 decimals, use more precision
    if abs_value == 0.0:
        # Exactly zero - show as 0.0
        formatted = "0.0"
    elif abs_value < 0.0001:
        # Very small: use scientific notation or more precision
        if abs_value < 1e-6:
            # Extremely small: use scientific notation
            formatted = f"{value:.2e}"
        else:
            # Small but not extremely: use more decimal places
            formatted = f"{value:.8f}".rstrip('0').rstrip('.')
            # If still shows as 0 after stripping, use scientific notation
            if formatted == "0" or formatted == "-0":
                formatted = f"{value:.2e}"
    elif abs_value > 10000:
        # Very large: use scientific notation
        formatted = f"{value:.2e}"
    else:
        # Normal range: use 4 decimal places, but ensure we show non-zero if value is non-zero
        formatted = f"{value:.4f}".rstrip('0').rstrip('.')
        # If it rounded to 0, use more precision
        if formatted == "0" or formatted == "-0":
            formatted = f"{value:.8f}".rstrip('0').rstrip('.')
            if formatted == "0" or formatted == "-0":
                formatted = f"{value:.2e}"
    
    return f"{formatted}{stars}"


def compute_correlations_for_file(
    csv_path: Path, ngram_n: int, plan_cache_limit: int
) -> Dict[str, Dict[str, Tuple[float, float]]]:
    """
    Compute Spearman correlations for each metric with error, true_label, and embedding.
    
    Returns:
        Dict[metric_name, Dict[target, (rho, p_value)]]
        where target is one of "error", "true_label", "embedding"
    """
    print(f"\n[GRAND_ANALYSIS] ===== Processing {csv_path.name} =====")
    
    vdf = pd.read_csv(csv_path)
    print(f"[GRAND_ANALYSIS] Milestone 1: Loaded vdf, shape={vdf.shape}")
    if plan_cache_limit > 0:
        vdf = vdf.iloc[:plan_cache_limit]
        print(f"[GRAND_ANALYSIS] Milestone 1b: After plan_cache_limit, shape={vdf.shape}")
    
    required_cols = {"q_error", "plan_file", "embedding_file"}
    if not required_cols.issubset(vdf.columns):
        missing = required_cols - set(vdf.columns)
        raise KeyError(f"Verbose file {csv_path} missing columns: {missing}")
    
    plan_path = extract_first_nonempty(vdf["plan_file"])
    emb_path = extract_first_nonempty(vdf["embedding_file"])
    print(f"[GRAND_ANALYSIS] Milestone 2: Extracted paths, plan_path={plan_path}, emb_path={emb_path}")
    
    # Load embeddings
    emb_df = load_embeddings(emb_path)
    print(f"[GRAND_ANALYSIS] Milestone 3: Loaded embeddings, emb_df.shape={emb_df.shape}, vdf.shape={vdf.shape}")
    if "idx" in vdf.columns and emb_df.index.name == "idx":
        valid_mask = vdf["idx"].isin(emb_df.index)
        vdf = vdf[valid_mask].reset_index(drop=True)
        vectors = emb_df.loc[vdf["idx"]].to_numpy(dtype=float)
        print(f"[GRAND_ANALYSIS] Milestone 3b: After embedding filter, vdf.shape={vdf.shape}, vectors.shape={vectors.shape}")
    else:
        vectors = emb_df.to_numpy(dtype=float)
        vectors = vectors[:len(vdf)]
        print(f"[GRAND_ANALYSIS] Milestone 3b: After embedding filter (no idx), vdf.shape={vdf.shape}, vectors.shape={vectors.shape}")
    
    # Compute mean embedding distances
    mean_emb_dists = compute_mean_embedding_distances(vectors)
    print(f"[GRAND_ANALYSIS] Milestone 4: Computed mean_emb_dists, shape={mean_emb_dists.shape}, first 5 values={mean_emb_dists[:5]}")
    
    # Load plan data
    plan_df = pd.read_csv(plan_path)
    if "json" not in plan_df.columns:
        raise KeyError(f"'json' column not found in plan file: {plan_path}")
    plan_df = plan_df.reset_index(drop=True)
    print(f"[GRAND_ANALYSIS] Milestone 5: Loaded plan_df, shape={plan_df.shape}")
    
    # Extract structural metrics
    summaries: List[PlanStructuralSummary] = []
    cache: Dict[str, PlanStructuralSummary] = {}
    indices = list(range(len(vdf)))
    
    for idx in indices:
        if idx >= len(plan_df):
            continue
        raw = plan_df.iloc[idx]["json"]
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
    
    print(f"[GRAND_ANALYSIS] Milestone 6: Extracted summaries, len={len(summaries)}")
    
    # Extract metric values
    metric_values: Dict[str, np.ndarray] = {}
    for metric in STRUCT_METRICS:
        values = []
        for s in summaries:
            if hasattr(s, metric):
                values.append(getattr(s, metric))
            else:
                values.append(0.0)
        metric_values[metric] = np.array(values, dtype=float)
    
    print(f"[GRAND_ANALYSIS] Milestone 7: Extracted metric_values, num_metrics={len(metric_values)}, first metric (num_tables) shape={metric_values['num_tables'].shape}, first 5 values={metric_values['num_tables'][:5]}")
    
    # Extract target values
    q_errors = vdf["q_error"].to_numpy(dtype=float)
    true_labels = vdf["true_label"].to_numpy(dtype=float) if "true_label" in vdf.columns else None
    print(f"[GRAND_ANALYSIS] Milestone 8: Extracted q_errors, shape={q_errors.shape}, first 5 values={q_errors[:5]}, true_labels={true_labels is not None}")
    
    # Align lengths
    min_len = min(len(q_errors), len(mean_emb_dists), len(summaries))
    if true_labels is not None:
        min_len = min(min_len, len(true_labels))
    print(f"[GRAND_ANALYSIS] Milestone 9: Aligning lengths: len(q_errors)={len(q_errors)}, len(mean_emb_dists)={len(mean_emb_dists)}, len(summaries)={len(summaries)}, len(true_labels)={len(true_labels) if true_labels is not None else 'N/A'}, min_len={min_len}")
    
    q_errors = q_errors[:min_len]
    mean_emb_dists = mean_emb_dists[:min_len]
    if true_labels is not None:
        true_labels = true_labels[:min_len]
    
    for metric in STRUCT_METRICS:
        metric_values[metric] = metric_values[metric][:min_len]
    
    print(f"[GRAND_ANALYSIS] Milestone 10: After alignment, q_errors shape={q_errors.shape}, metric_values['num_tables'] shape={metric_values['num_tables'].shape}, first 5 values={metric_values['num_tables'][:5]}")
    
    # Prepare feature matrix for multivariate Huber regression
    X_matrix = np.column_stack([metric_values[metric] for metric in STRUCT_METRICS])
    print(f"[GRAND_ANALYSIS] Milestone 11: Prepared X_matrix, shape={X_matrix.shape}, q_errors shape={q_errors.shape}")
    print(f"[GRAND_ANALYSIS] Milestone 11b: X_matrix first row (first 5 metrics)={X_matrix[0, :5]}")
    print(f"[GRAND_ANALYSIS] Milestone 11c: q_errors first 5={q_errors[:5]}")
    
    # Compute multivariate Huber regression for error (all metrics at once)
    error_coefs = huber_regression_multivariate(X_matrix, q_errors, STRUCT_METRICS)
    print(f"[GRAND_ANALYSIS] Milestone 12: Computed error_coefs")
    for metric in ['num_tables', 'num_columns', 'num_joins']:
        coef, p = error_coefs.get(metric, (float("nan"), float("nan")))
        print(f"[GRAND_ANALYSIS]   {metric}: coef={coef:.10f}, p={p:.10f}")
    
    # Compute correlations
    results: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for metric in STRUCT_METRICS:
        metric_vals = metric_values[metric]
        results[metric] = {}
        
        # Error: use coefficient from multivariate Huber regression
        coef, p = error_coefs.get(metric, (float("nan"), float("nan")))
        results[metric]["error"] = (float(coef), float(p))
        
        # Correlation with true_label
        if true_labels is not None:
            valid_mask = ~(np.isnan(true_labels) | np.isnan(metric_vals))
            if valid_mask.sum() >= 3:
                rho, p = stats.spearmanr(true_labels[valid_mask], metric_vals[valid_mask])
                results[metric]["true_label"] = (float(rho), float(p))
            else:
                results[metric]["true_label"] = (float("nan"), float("nan"))
        else:
            results[metric]["true_label"] = (float("nan"), float("nan"))
        
        # Correlation with embedding
        valid_mask = ~(np.isnan(mean_emb_dists) | np.isnan(metric_vals))
        if valid_mask.sum() >= 3:
            rho, p = stats.spearmanr(mean_emb_dists[valid_mask], metric_vals[valid_mask])
            results[metric]["embedding"] = (float(rho), float(p))
        else:
            results[metric]["embedding"] = (float("nan"), float("nan"))
    
    return results


def determine_type_number(
    error_coef: float, error_p: float,
    label_rho: float, label_p: float,
    emb_rho: float, emb_p: float
) -> int:
    """
    Determine type_number based on *** significant correlations/coefficients.
    
    For error: yes = |coefficient| > 0.1 AND p < 0.001
    For label/embedding: yes = positive Spearman correlation AND p < 0.001
    """
    error_yes = not np.isnan(error_coef) and abs(error_coef) > 0.1 and error_p < 0.001
    label_yes = not np.isnan(label_rho) and label_rho > 0 and label_p < 0.001
    emb_yes = not np.isnan(emb_rho) and emb_rho > 0 and emb_p < 0.001
    
    if error_yes and label_yes and not emb_yes:
        return 1
    elif error_yes and label_yes and emb_yes:
        return 2
    elif not error_yes and label_yes and emb_yes:
        return 3
    elif not error_yes and label_yes and not emb_yes:
        return 4
    elif not error_yes and not label_yes and emb_yes:
        return 5
    elif not error_yes and not label_yes and not emb_yes:
        return 6
    elif error_yes and not label_yes and emb_yes:
        return 7
    elif error_yes and not label_yes and not emb_yes:
        return 8
    else:
        return 6  # Default fallback


def process_single_grand_analysis(
    csv_path: Path,
    args: argparse.Namespace,
    algo: str,
    model: str | None,
) -> None:
    """
    Process a single grand analysis for a given verbose CSV file.
    """
    print(f"Processing: {csv_path.name} (algo={algo}, model={model})")
    try:
        correlations = compute_correlations_for_file(csv_path, args.ngram_n, args.plan_cache_limit)
    except Exception as e:
        print(f"Error processing {csv_path.name}: {e}")
        return
    
    # Build output table
    output_data = []
    for metric in STRUCT_METRICS:
        if metric not in correlations:
            # No data for this metric
            error_coef, error_p = float("nan"), float("nan")
            label_rho, label_p = float("nan"), float("nan")
            emb_rho, emb_p = float("nan"), float("nan")
        else:
            error_coef, error_p = correlations[metric].get("error", (float("nan"), float("nan")))
            label_rho, label_p = correlations[metric].get("true_label", (float("nan"), float("nan")))
            emb_rho, emb_p = correlations[metric].get("embedding", (float("nan"), float("nan")))
        
        # Format with significance stars
        error_str = format_coefficient(error_coef, error_p)
        label_str = f"{label_rho:.4f}{significance_stars(label_p)}" if not np.isnan(label_rho) else "NaN"
        emb_str = f"{emb_rho:.4f}{significance_stars(emb_p)}" if not np.isnan(emb_rho) else "NaN"
        
        # Determine type_number
        type_num = determine_type_number(error_coef, error_p, label_rho, label_p, emb_rho, emb_p)
        
        output_data.append({
            "metric": metric,
            "error": error_str,
            "true_label": label_str,
            "embedding": emb_str,
            "type_number": type_num,
        })
    
    # Save to CSV
    df = pd.DataFrame(output_data)
    df = df.set_index("metric")
    
    dataset_dir_out = OUT_DIR / args.dataset
    dataset_dir_out.mkdir(parents=True, exist_ok=True)
    algo_tag = algo
    model_tag = model if (algo == "llm" and model) else "none"
    out_name = f"grand_analysis_{args.dataset}_{args.task}_seed{args.seed}_{algo_tag}_{model_tag}.csv"
    out_path = dataset_dir_out / out_name
    df.to_csv(out_path)
    print(f"Saved grand analysis results to {out_path}")


def generate_type_number_summary(args: argparse.Namespace) -> None:
    """
    Generate a summary table counting type_numbers and calculating Spearman correlation
    between true_label and embedding for each algo/model combination.
    """
    dataset_dir_out = OUT_DIR / args.dataset
    if not dataset_dir_out.exists():
        print(f"Warning: Output directory {dataset_dir_out} does not exist. Cannot generate summary.")
        return
    
    # Find all grand analysis CSV files for this dataset/task/seed
    pattern = f"grand_analysis_{args.dataset}_{args.task}_seed{args.seed}_*.csv"
    csv_files = sorted(dataset_dir_out.glob(pattern))
    
    if not csv_files:
        print(f"Warning: No grand analysis files found matching pattern {pattern}")
        return
    
    # Also need to access verbose files to calculate true_label vs embedding correlation
    dataset_dir = args.verbose_root / f"verbose_Train_{args.dataset}_Test_{args.dataset}_ours"
    if not dataset_dir.exists():
        print(f"Warning: Verbose directory {dataset_dir} does not exist. Cannot calculate true_label vs embedding correlation.")
        return
    
    # Collect verbose CSV files
    csv_combinations = _collect_verbose_csvs(dataset_dir, args.task, args.seed)
    verbose_file_map = {}
    for csv_path, algo, model in csv_combinations:
        if algo == "llm" and model:
            row_label = f"{algo}_{model}"
        else:
            row_label = f"{algo}_none" if model is None else f"{algo}_{model}"
        verbose_file_map[row_label] = csv_path
    
    # Collect data for each algo/model combination
    summary_data = {}
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, index_col=0)
            if "type_number" not in df.columns:
                print(f"Warning: {csv_file.name} does not have 'type_number' column. Skipping.")
                continue
            
            # Extract algo and model from filename
            # Pattern: grand_analysis_{dataset}_{task}_seed{seed}_{algo}_{model}.csv
            stem = csv_file.stem
            parts = stem.replace(f"grand_analysis_{args.dataset}_{args.task}_seed{args.seed}_", "").split("_", 1)
            if len(parts) == 2:
                algo = parts[0]
                model = parts[1] if parts[1] != "none" else None
            else:
                algo = parts[0]
                model = None
            
            # Create row label
            if algo == "llm" and model:
                row_label = f"{algo}_{model}"
            else:
                row_label = f"{algo}_none" if model is None else f"{algo}_{model}"
            
            # Count type_numbers
            type_counts = df["type_number"].value_counts().to_dict()
            
            # Calculate Spearman correlation between true_label and embedding
            label_emb_corr = "NaN"
            est_label_emb_corr = "NaN"
            if row_label in verbose_file_map:
                try:
                    verbose_csv = verbose_file_map[row_label]
                    vdf = pd.read_csv(verbose_csv)
                    
                    if "embedding_file" in vdf.columns:
                        # Load embeddings
                        emb_path = extract_first_nonempty(vdf["embedding_file"])
                        emb_df = load_embeddings(emb_path)
                        
                        # Compute mean embedding distances
                        if "idx" in vdf.columns and emb_df.index.name == "idx":
                            valid_mask = vdf["idx"].isin(emb_df.index)
                            vdf_aligned = vdf[valid_mask].reset_index(drop=True)
                            vectors = emb_df.loc[vdf_aligned["idx"]].to_numpy(dtype=float)
                        else:
                            vectors = emb_df.to_numpy(dtype=float)
                            vectors = vectors[:len(vdf)]
                            vdf_aligned = vdf.iloc[:len(vectors)].reset_index(drop=True)
                        
                        mean_emb_dists = compute_mean_embedding_distances(vectors)
                        
                        # Calculate Spearman correlation with true_label
                        if "true_label" in vdf_aligned.columns:
                            true_labels = vdf_aligned["true_label"].to_numpy(dtype=float)
                            
                            # Align lengths
                            min_len = min(len(true_labels), len(mean_emb_dists))
                            true_labels = true_labels[:min_len]
                            mean_emb_dists_aligned = mean_emb_dists[:min_len]
                            
                            # Calculate Spearman correlation
                            valid_mask = ~(np.isnan(true_labels) | np.isnan(mean_emb_dists_aligned))
                            if valid_mask.sum() >= 3:
                                rho, p = stats.spearmanr(true_labels[valid_mask], mean_emb_dists_aligned[valid_mask])
                                label_emb_corr = f"{rho:.4f}{significance_stars(p)}"
                        
                        # Calculate Spearman correlation with est_label
                        if "est_label" in vdf_aligned.columns:
                            est_labels = vdf_aligned["est_label"].to_numpy(dtype=float)
                            
                            # Align lengths
                            min_len = min(len(est_labels), len(mean_emb_dists))
                            est_labels = est_labels[:min_len]
                            mean_emb_dists_aligned = mean_emb_dists[:min_len]
                            
                            # Calculate Spearman correlation
                            valid_mask = ~(np.isnan(est_labels) | np.isnan(mean_emb_dists_aligned))
                            if valid_mask.sum() >= 3:
                                rho, p = stats.spearmanr(est_labels[valid_mask], mean_emb_dists_aligned[valid_mask])
                                est_label_emb_corr = f"{rho:.4f}{significance_stars(p)}"
                except Exception as e:
                    print(f"Warning: Failed to calculate label vs embedding correlation for {row_label}: {e}")
            
            # Store all data
            summary_data[row_label] = {
                "type_counts": type_counts,
                "label_emb_corr": label_emb_corr,
                "est_label_emb_corr": est_label_emb_corr,
            }
            
        except Exception as e:
            print(f"Warning: Failed to process {csv_file.name} for summary: {e}")
            continue
    
    if not summary_data:
        print("Warning: No valid data found for summary generation.")
        return
    
    # Build summary table
    all_type_numbers = list(range(1, 9))  # 1-8
    summary_rows = []
    
    for row_label in sorted(summary_data.keys()):
        data = summary_data[row_label]
        counts = data["type_counts"]
        row_dict = {"algo_model": row_label}
        
        # Add type_number counts
        for tn in all_type_numbers:
            row_dict[f"type_{tn}"] = counts.get(tn, 0)
        
        # Add Spearman correlation between true_label and embedding
        row_dict["true_label_vs_embedding_spearman"] = data["label_emb_corr"]
        
        # Add Spearman correlation between est_label and embedding
        row_dict["est_label_vs_embedding_spearman"] = data["est_label_emb_corr"]
        
        summary_rows.append(row_dict)
    
    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.set_index("algo_model")
    
    # Save summary
    summary_path = dataset_dir_out / f"grand_analysis_summary_{args.dataset}_{args.task}_seed{args.seed}.csv"
    summary_df.to_csv(summary_path)
    print(f"\nSaved type_number summary to {summary_path}")


def main() -> None:
    args = parse_args()
    dataset_dir = args.verbose_root / f"verbose_Train_{args.dataset}_Test_{args.dataset}_ours"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Verbose directory not found: {dataset_dir}")
    
    # Collect all verbose CSV files
    csv_combinations = _collect_verbose_csvs(dataset_dir, args.task, args.seed)
    if not csv_combinations:
        raise FileNotFoundError(
            f"No verbose CSV files found for task '{args.task}', seed {args.seed} in {dataset_dir}"
        )
    
    print(f"Processing {len(csv_combinations)} verbose files...")
    
    # Process each file individually
    for csv_path, algo, model in csv_combinations:
        process_single_grand_analysis(csv_path, args, algo, model)
    
    print(f"\nCompleted processing {len(csv_combinations)} grand analyses.")
    
    # Generate summary of type_number counts
    generate_type_number_summary(args)


if __name__ == "__main__":
    main()

