import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from insights.embedding_geometry import GeometryConfig, run_geometry_metric
from insights.plan_structural_metrics import PlanStructuralSummary, summarise_plan_structure


SUPPORTED_ANALYSES = ["top_q_error", "embedding_geometry"]
EXPERIMENTS_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_RESULTS_DIR = EXPERIMENTS_ROOT / "analysis_scripts" / "insights" / "geometry_results"

GEOMETRY_TITLES = {
    "g1": "Mean Cosine",
    "g2": "Top-Component Dominance",
    "g3": "Uniformity",
    "g4": "Hubness",
    "g5": "Norm Sanity",
}

GEOMETRY_GUIDANCE = {
    "g1": "Mean cosine should stay near 0 (smaller absolute value better); std should not collapse to 0.",
    "g2": "Lower MCC/EVR1 indicate less collapse; higher effective_rank indicates more isotropy.",
    "g3": "Lower uniformity implies embeddings are more evenly spread.",
    "g4": "Lower hubness_gini (and tighter counts spread) means fewer universal neighbours.",
    "g5": "Post-norm mean≈1 with low std; large spread hints at unstable scaling.",
}

PRINTABLE_GEOMETRY_KEYS = {
    "g1": ["mean_cosine"],
    "g2": ["MCC", "EVR1", "effective_rank"],
    "g4": ["hubness_gini"],
}

GEOMETRY_TABLE_ROWS = [
    ("g1", "mean_cosine"),
    ("g2", "MCC"),
    ("g2", "EVR1"),
    ("g2", "effective_rank"),
    ("g4", "hubness_gini"),
]
GEOMETRY_TABLE_LABELS = [f"{metric.upper()}_{key}" for metric, key in GEOMETRY_TABLE_ROWS] + [
    "CKA_metrics_embeddings",
    "CKA_embeddings_true_label",
    "CKA_embeddings_est_label",
]

GEOMETRY_KEY_ORDER = {
    "g1": ["mean_cosine", "std_cosine", "num_pairs"],
    "g2": ["MCC", "EVR1", "effective_rank"],
    "g3": ["uniformity", "t", "num_pairs"],
    "g4": ["hubness_gini", "k", "n_eval", "counts_mean", "counts_std", "counts_min", "counts_max"],
    "g5": [
        "pre_norm_mean",
        "pre_norm_std",
        "pre_norm_min",
        "pre_norm_max",
        "post_norm_mean",
        "post_norm_std",
        "post_norm_min",
        "post_norm_max",
    ],
}


def resolve_verbose_directory(dataset: str, custom_root: Path | None = None) -> Path:
    """
    Resolve the directory containing verbose CSV files for the given dataset.
    """
    root = custom_root if custom_root is not None else Path(__file__).resolve().parent.parent / "verbose"
    target_dir = root / f"verbose_Train_{dataset}_Test_{dataset}_ours"
    if not target_dir.exists():
        raise FileNotFoundError(f"Verbose directory not found for dataset '{dataset}': {target_dir}")
    return target_dir


def discover_datasets(verbose_root: Path | None = None) -> list[str]:
    """
    Discover all available datasets from the verbose directory structure.
    
    Returns:
        List of dataset names found in verbose directories.
    """
    root = verbose_root if verbose_root is not None else Path(__file__).resolve().parent.parent / "verbose"
    if not root.exists():
        return []
    
    datasets = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        # Pattern: verbose_Train_{dataset}_Test_{dataset}_ours
        if entry.name.startswith("verbose_Train_") and entry.name.endswith("_ours"):
            # Extract dataset name: verbose_Train_{dataset}_Test_{dataset}_ours
            parts = entry.name.replace("verbose_Train_", "").replace("_Test_", "_").replace("_ours", "").split("_")
            if len(parts) >= 2 and parts[0] == parts[1]:  # Train and Test dataset should match
                dataset = parts[0]
                if dataset not in datasets:
                    datasets.append(dataset)
    
    return sorted(datasets)


def find_verbose_file(
    dataset_dir: Path,
    task: str,
    algo: str,
    seed: int,
    model: str | None = None,
) -> Path:
    """
    Locate a verbose CSV file that matches the requested configuration.
    """
    prefix = f"{task}_{algo}"
    matches = []

    for entry in dataset_dir.iterdir():
        if not entry.is_file() or not entry.name.endswith(".csv"):
            continue
        name = entry.name
        if not name.startswith(prefix):
            continue
        if f"seed{seed}" not in name:
            continue
        if algo == "llm":
            if model is None:
                raise ValueError("Argument '--model' is required when '--algo llm' is selected.")
            if model not in name:
                continue
        matches.append(entry)

    if not matches:
        model_msg = f" and model '{model}'" if (algo == "llm" and model) else ""
        raise FileNotFoundError(
            f"No verbose CSV found for task '{task}', algo '{algo}'{model_msg}, seed {seed} in {dataset_dir}"
        )

    if len(matches) > 1 and algo == "llm":
        baseline_matches = [entry for entry in matches if "_rm-" not in entry.name]
        if baseline_matches:
            if len(baseline_matches) == 1:
                return baseline_matches[0]
            matches = baseline_matches

    if len(matches) > 1:
        match_list = "\n  - ".join(str(m.name) for m in matches)
        raise RuntimeError(
            "Multiple verbose CSV files matched the provided arguments. "
            "Please refine your inputs (e.g., specify a more precise model string).\n"
            f"Matches:\n  - {match_list}"
        )

    return matches[0]


def analyse_top_q_error(csv_path: Path, topk: int) -> None:
    """
    Report the rows with the largest q_error values, including their idx.
    """
    df = pd.read_csv(csv_path)
    if "q_error" not in df.columns:
        raise KeyError(f"'q_error' column not found in {csv_path}")
    if "idx" not in df.columns:
        raise KeyError(f"'idx' column not found in {csv_path}")

    topk = max(1, topk)
    subset = df.nlargest(topk, "q_error")[["idx", "q_error", "true_label", "est_label"]]

    print(f"Top {len(subset)} q_error rows in {csv_path.name}:")
    for _, row in subset.iterrows():
        idx = int(row["idx"])
        q_err = row["q_error"]
        true_val = row.get("true_label", float("nan"))
        est_val = row.get("est_label", float("nan"))
        print(
            f"  idx={idx:<6} q_error={q_err:.6f} "
            f"true_label={true_val:.6f} est_label={est_val:.6f}"
        )


def _resolve_embedding_path(df: pd.DataFrame, verbose_csv: Path) -> Path:
    if "embedding_file" not in df.columns:
        raise KeyError(f"'embedding_file' column not found in {verbose_csv}")

    candidates = [
        Path(str(path).strip())
        for path in df["embedding_file"].dropna()
        if isinstance(path, str) and path.strip()
    ]
    if not candidates:
        raise RuntimeError(
            "No embedding file path found in the verbose CSV. "
            "Ensure the verbose run recorded embedding_file entries."
        )

    rel_path = candidates[0]
    embed_path = rel_path if rel_path.is_absolute() else (EXPERIMENTS_ROOT / rel_path).resolve()
    if not embed_path.exists():
        raise FileNotFoundError(f"Embedding file not found: {embed_path}")
    return embed_path


def _load_embeddings_matrix(embed_path: Path) -> np.ndarray:
    df = pd.read_csv(embed_path)
    
    # Exclude known non-embedding columns
    excluded_cols = {"idx", "costs", "cards", "lengths"}
    for col in excluded_cols:
        if col in df.columns:
            df = df.drop(columns=col)
    
    # Get embedding columns: columns with integer names (string representation of integer)
    embedding_cols = []
    for col in df.columns:
        if col in excluded_cols:
            continue
        # Check if column name is an integer (string representation of integer)
        if str(col).isdigit():
            embedding_cols.append(col)
    
    if not embedding_cols:
        raise ValueError(f"No embedding columns found in {embed_path} (only excluded columns)")
    
    Z = df[embedding_cols].to_numpy(dtype=float)
    if Z.ndim != 2 or Z.shape[0] < 1:
        raise ValueError(f"Unexpected embedding shape {Z.shape} from {embed_path}")
    
    # Handle NaN values: replace with 0
    Z = np.where(np.isnan(Z), 0.0, Z)
    
    return Z


def linear_cka(Z: np.ndarray, M: np.ndarray) -> float:
    """
    Linear CKA between two representations Z and M.

    Z: (n_samples, d_z)  – e.g., LLM embeddings
    M: (n_samples, d_m)  – e.g., metric vectors

    Returns:
        scalar in [0, 1]-ish range (higher = more similar structure).
    """
    assert Z.shape[0] == M.shape[0], "Z and M must have same number of samples"

    # Handle NaN values: replace with 0
    Z = np.where(np.isnan(Z), 0.0, Z)
    M = np.where(np.isnan(M), 0.0, M)

    # Center features (columns) by subtracting mean over samples
    Zc = Z - Z.mean(axis=0, keepdims=True)
    Mc = M - M.mean(axis=0, keepdims=True)

    # Cross-covariance-like term
    ZtM = Zc.T @ Mc  # (d_z, d_m)

    numerator = np.linalg.norm(ZtM, ord="fro") ** 2
    denom = (
        np.linalg.norm(Zc.T @ Zc, ord="fro")
        * np.linalg.norm(Mc.T @ Mc, ord="fro")
    )
    if denom == 0:
        return 0.0

    return numerator / denom


def _extract_structural_metrics_from_verbose(
    csv_path: Path, embed_path: Path, ngram_n: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract structural metrics and align them with embeddings by idx.

    Returns:
        (Z, M) where Z is (n_samples, d_z) embeddings and M is (n_samples, d_m) metrics
    """
    # Load verbose CSV
    vdf = pd.read_csv(csv_path)
    
    # Load embeddings - use the embedding file from the verbose CSV, not the passed embed_path
    # This ensures we use the correct embedding file for each model
    actual_embed_path = _resolve_embedding_path(vdf, csv_path)
    embed_df = pd.read_csv(actual_embed_path)
    embed_has_idx = "idx" in embed_df.columns
    if embed_has_idx:
        embed_df = embed_df.set_index("idx")
    
    # Get embedding columns: columns with integer names (string representation of integer)
    # Exclude known non-embedding columns: costs, cards, lengths, idx
    excluded_cols = {"costs", "cards", "lengths", "idx"}
    embedding_cols = []
    for col in embed_df.columns:
        if col in excluded_cols:
            continue
        # Check if column name is an integer (string representation of integer)
        if str(col).isdigit():
            embedding_cols.append(col)
    
    if not embedding_cols:
        raise ValueError(f"No embedding columns found in {actual_embed_path} (only excluded columns)")
    
    # Load plan data
    if "plan_file" not in vdf.columns:
        raise KeyError(f"'plan_file' column not found in {csv_path}")
    plan_path = vdf["plan_file"].dropna().iloc[0] if not vdf["plan_file"].dropna().empty else None
    if plan_path is None:
        raise ValueError(f"No plan_file found in {csv_path}")
    
    plan_path = Path(plan_path)
    if not plan_path.is_absolute():
        plan_path = (EXPERIMENTS_ROOT / plan_path).resolve()
    
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    
    plan_df = pd.read_csv(plan_path)
    if "json" not in plan_df.columns:
        raise KeyError(f"'json' column not found in plan file: {plan_path}")
    plan_has_idx = "idx" in plan_df.columns
    
    # Align by idx if available in all three
    if "idx" in vdf.columns and embed_has_idx and plan_has_idx:
        # Filter to rows that have both embeddings and plans
        vdf_indices = set(vdf["idx"].dropna().astype(int))
        embed_indices = set(embed_df.index.astype(int))
        plan_indices = set(plan_df["idx"].dropna().astype(int))
        
        common_indices = sorted(list(vdf_indices & embed_indices & plan_indices))
        if not common_indices:
            raise ValueError(f"No common indices found between verbose, embeddings, and plans")
        
        # Get embeddings (use only embedding columns)
        Z = embed_df.loc[common_indices][embedding_cols].to_numpy(dtype=float)
        # Handle NaN values: replace with 0
        Z = np.where(np.isnan(Z), 0.0, Z)
        
        # Get plans (sorted by idx to match embedding order)
        plan_subset = plan_df[plan_df["idx"].isin(common_indices)].sort_values("idx")
    else:
        # Fallback: align by position
        min_len = min(len(vdf), len(embed_df), len(plan_df))
        vdf = vdf.iloc[:min_len]
        Z = embed_df.iloc[:min_len][embedding_cols].to_numpy(dtype=float)
        # Handle NaN values: replace with 0
        Z = np.where(np.isnan(Z), 0.0, Z)
        plan_subset = plan_df.iloc[:min_len]
    
    # Extract structural metrics
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
    
    M_rows = []
    cache = {}
    for _, row in plan_subset.iterrows():
        raw_json = row["json"]
        if raw_json in cache:
            summary = cache[raw_json]
        else:
            try:
                obj = json.loads(raw_json)
                summary = summarise_plan_structure(obj, ngram_n=ngram_n)
                cache[raw_json] = summary
            except Exception as e:
                # Create dummy summary with zeros
                from collections import Counter
                summary = PlanStructuralSummary(
                    num_tables=0, num_columns=0, num_joins=0, num_filters=0,
                    operator_histogram=Counter(), path_ngrams=Counter(),
                    longest_path_len=0, num_nodes=0, join_tree_diameter=0,
                    num_blocking_ops=0, num_nested_loop=0, max_est_join_input_rows=0.0,
                    sum_est_join_input_rows=0.0, num_highly_selective_filters=0,
                    log_filter_selectivity_product=0.0, optimizer_est_cost_root=0.0,
                    log_max_est_rows=0.0, log_sum_est_rows=0.0, max_log_card_error=0.0
                )
        
        metric_row = [getattr(summary, metric, 0.0) for metric in STRUCT_METRICS]
        M_rows.append(metric_row)
    
    M = np.array(M_rows, dtype=float)
    
    # Ensure Z and M have the same number of samples
    min_samples = min(Z.shape[0], M.shape[0])
    Z = Z[:min_samples]
    M = M[:min_samples]
    
    return Z, M


def _geometry_row_label(metric: str, key: str) -> str:
    return f"{metric.upper()}_{key}"


def _compute_geometry_table_rows(
    Z: np.ndarray, 
    cfg: GeometryConfig, 
    M: np.ndarray | None = None,
    true_labels: np.ndarray | None = None,
    est_labels: np.ndarray | None = None,
) -> dict[str, float]:
    metrics_data: dict[str, float] = {}
    for metric, key in GEOMETRY_TABLE_ROWS:
        results = run_geometry_metric(Z, metric, cfg)
        value = results.get(key, math.nan)
        metrics_data[_geometry_row_label(metric, key)] = abs(value) if isinstance(value, (int, float)) else math.nan
    
    # Compute CKA if metrics are provided
    if M is not None and Z.shape[0] == M.shape[0] and M.shape[0] > 0:
        try:
            cka_value = linear_cka(Z, M)
            metrics_data["CKA_metrics_embeddings"] = cka_value
        except Exception as e:
            print(f"Warning: Failed to compute CKA with metrics: {e}")
            metrics_data["CKA_metrics_embeddings"] = math.nan
    else:
        metrics_data["CKA_metrics_embeddings"] = math.nan
    
    # Compute CKA with true_label (treat as 1-D representation)
    if true_labels is not None and Z.shape[0] == len(true_labels) and len(true_labels) > 0:
        try:
            # Reshape labels to (n_samples, 1) to treat as 1-D representation
            labels_2d = true_labels.reshape(-1, 1)
            cka_true = linear_cka(Z, labels_2d)
            metrics_data["CKA_embeddings_true_label"] = cka_true
        except Exception as e:
            print(f"Warning: Failed to compute CKA with true_label: {e}")
            metrics_data["CKA_embeddings_true_label"] = math.nan
    else:
        metrics_data["CKA_embeddings_true_label"] = math.nan
    
    # Compute CKA with est_label (treat as 1-D representation)
    if est_labels is not None and Z.shape[0] == len(est_labels) and len(est_labels) > 0:
        try:
            # Reshape labels to (n_samples, 1) to treat as 1-D representation
            labels_2d = est_labels.reshape(-1, 1)
            cka_est = linear_cka(Z, labels_2d)
            metrics_data["CKA_embeddings_est_label"] = cka_est
        except Exception as e:
            print(f"Warning: Failed to compute CKA with est_label: {e}")
            metrics_data["CKA_embeddings_est_label"] = math.nan
    else:
        metrics_data["CKA_embeddings_est_label"] = math.nan
    
    return metrics_data


def _load_embeddings_from_verbose(csv_path: Path) -> tuple[np.ndarray, Path]:
    df_verbose = pd.read_csv(csv_path)
    embed_path = _resolve_embedding_path(df_verbose, csv_path)
    Z = _load_embeddings_matrix(embed_path)
    return Z, embed_path


def _collect_verbose_csvs(dataset_dir: Path, task: str, seed: int) -> list[Path]:
    prefix = f"{task}_"
    seed_token = f"seed{seed}"
    csvs: list[Path] = []
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
        csvs.append(entry)
    return csvs


def _write_geometry_table(
    dataset: str,
    task: str,
    seed: int,
    csv_files: list[Path],
    cfg: GeometryConfig,
) -> Path:
    if not csv_files:
        raise FileNotFoundError(
            f"No verbose CSV files found for dataset '{dataset}', task '{task}', seed {seed}"
        )

    table = pd.DataFrame(index=GEOMETRY_TABLE_LABELS)
    for csv_path in csv_files:
        Z, embed_path = _load_embeddings_from_verbose(csv_path)
        column_label = csv_path.stem
        
        # Load verbose CSV to get labels
        vdf = pd.read_csv(csv_path)
        true_labels = None
        est_labels = None
        
        if "true_label" in vdf.columns:
            true_labels = vdf["true_label"].fillna(0.0).to_numpy(dtype=float)
        if "est_label" in vdf.columns:
            est_labels = vdf["est_label"].fillna(0.0).to_numpy(dtype=float)
        
        # Align labels with embeddings by idx if available
        if "idx" in vdf.columns:
            embed_df = pd.read_csv(embed_path)
            if "idx" in embed_df.columns:
                embed_df = embed_df.set_index("idx")
                vdf_indices = set(vdf["idx"].dropna().astype(int))
                embed_indices = set(embed_df.index.astype(int))
                common_indices = sorted(list(vdf_indices & embed_indices))
                
                if common_indices and len(common_indices) == len(Z):
                    # Align labels to match embedding order
                    vdf_aligned = vdf[vdf["idx"].isin(common_indices)].set_index("idx").loc[common_indices]
                    if "true_label" in vdf_aligned.columns:
                        true_labels = vdf_aligned["true_label"].fillna(0.0).to_numpy(dtype=float)
                    if "est_label" in vdf_aligned.columns:
                        est_labels = vdf_aligned["est_label"].fillna(0.0).to_numpy(dtype=float)
        
        # Ensure labels match embedding length
        min_len = Z.shape[0]
        if true_labels is not None and len(true_labels) != min_len:
            min_len = min(min_len, len(true_labels))
        if est_labels is not None and len(est_labels) != min_len:
            min_len = min(min_len, len(est_labels))
        
        # Truncate to common length
        Z = Z[:min_len]
        if true_labels is not None:
            true_labels = true_labels[:min_len]
        if est_labels is not None:
            est_labels = est_labels[:min_len]
        
        # Compute geometry metrics on all embeddings
        metrics_data = _compute_geometry_table_rows(Z, cfg, M=None, true_labels=true_labels, est_labels=est_labels)
        
        # Try to extract structural metrics for CKA calculation
        # CKA requires aligned embeddings and metrics
        # Note: _extract_structural_metrics_from_verbose will use the embedding file from csv_path,
        # not the embed_path we loaded earlier, to ensure we use the correct embeddings for each model
        try:
            Z_aligned, M = _extract_structural_metrics_from_verbose(csv_path, embed_path, ngram_n=3)
            # Align Z_aligned with Z if they differ in length
            if Z_aligned.shape[0] != Z.shape[0]:
                min_align_len = min(Z_aligned.shape[0], Z.shape[0])
                Z_aligned = Z_aligned[:min_align_len]
                M = M[:min_align_len]
            
            # Compute CKA on aligned data
            if Z_aligned.shape[0] == M.shape[0] and M.shape[0] > 0:
                cka_value = linear_cka(Z_aligned, M)
                metrics_data["CKA_metrics_embeddings"] = cka_value
                # Debug: print embedding stats to verify they're different
                print(f"  CKA={cka_value:.10f} (Z shape: {Z_aligned.shape}, M shape: {M.shape}, "
                      f"Z mean norm: {np.linalg.norm(Z_aligned.mean(axis=0)):.6f}, "
                      f"Z std: {Z_aligned.std():.6f})")
            else:
                metrics_data["CKA_metrics_embeddings"] = math.nan
        except Exception as e:
            print(f"Warning: Could not compute CKA with metrics for {column_label}: {e}")
            metrics_data["CKA_metrics_embeddings"] = math.nan
        
        table[column_label] = [metrics_data.get(row, math.nan) for row in GEOMETRY_TABLE_LABELS]
        print(f"Computed geometry metrics for {column_label} (embedding {embed_path})")

    dataset_dir = GEOMETRY_RESULTS_DIR / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    output_path = dataset_dir / f"geometry_table_{dataset}_{task}_seed{seed}.csv"
    table.to_csv(output_path)
    return output_path


def _print_geometry_block(metric: str, results: dict) -> None:
    metric = metric.lower()
    if metric not in PRINTABLE_GEOMETRY_KEYS:
        return
    title = GEOMETRY_TITLES.get(metric, metric.upper())
    guidance = GEOMETRY_GUIDANCE.get(metric, "Interpretation guidance unavailable.")
    print(f"\n{metric.upper()} – {title}")
    print(f"  Guidance: {guidance}")
    for key in PRINTABLE_GEOMETRY_KEYS[metric]:
        value = results.get(key)
        if value is None:
            continue
        print(f"    {key}: {abs(value)}")


def analyse_embedding_geometry(
    csv_path: Path,
    metric: str,
    num_pairs: int,
    uniformity_t: float,
    knn_k: int,
    max_samples: int,
    seed: int,
    center: bool,
    l2: bool,
) -> None:
    Z, embed_path = _load_embeddings_from_verbose(csv_path)

    cfg = GeometryConfig(
        num_pairs=num_pairs,
        uniformity_t=uniformity_t,
        knn_k=knn_k,
        max_samples_for_knn=max_samples,
        seed=seed,
        center=center,
        l2=l2,
    )
    metrics = ["g1", "g2", "g3", "g4", "g5"] if metric == "all" else [metric]

    print(f"Geometry analysis for embeddings: {embed_path}")
    print(f"  Samples: {Z.shape[0]}  Dim: {Z.shape[1]}")

    for single_metric in metrics:
        results = run_geometry_metric(Z, single_metric, cfg)
        _print_geometry_block(single_metric, results)


def analyse_all_embedding_geometries(
    dataset_dir: Path,
    dataset_name: str,
    task: str,
    seed: int,
    cfg: GeometryConfig,
) -> None:
    csv_files = _collect_verbose_csvs(dataset_dir, task, seed)
    output_path = _write_geometry_table(dataset_name, task, seed, csv_files, cfg)
    print(f"\nAggregated geometry table saved to {output_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyse verbose outputs for specific algorithms and datasets."
    )
    parser.add_argument(
        "--algo",
        default=None,
        help="Algorithm name (e.g., llm, bao, aimai). Optional for geometry analysis when "
        "aggregating over all algorithms/models.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model identifier (required when algo is 'llm', ignored otherwise).",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Dataset identifier as used in verbose directory names (e.g., stats, job, syn). "
             "Optional for embedding_geometry analysis when processing all datasets.",
    )
    parser.add_argument(
        "--task",
        default=None,
        choices=["card", "time"],
        help="Task type to analyse (card or time). "
             "Optional for embedding_geometry analysis when processing all tasks.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed of the verbose run (default: 42).")
    parser.add_argument(
        "--analysis_type",
        required=True,
        choices=SUPPORTED_ANALYSES,
        help="Type of analysis to perform on the verbose file.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=10,
        help="Number of rows to report for analyses that support ranking (default: 10).",
    )
    parser.add_argument(
        "--verbose_root",
        default=None,
        help="Optional override for the verbose directory root. "
             "If omitted, the script assumes experiments/verbose relative to this file.",
    )
    parser.add_argument(
        "--geometry_metric",
        choices=["g1", "g2", "g3", "g4", "g5", "all"],
        default="all",
        help="Geometry diagnostic to run when analysis_type=embedding_geometry.",
    )
    parser.add_argument(
        "--geometry_num_pairs",
        type=int,
        default=200_000,
        help="Number of sampled pairs for cosine/uniformity metrics (G1/G3).",
    )
    parser.add_argument(
        "--geometry_uniformity_t",
        type=float,
        default=2.0,
        help="Temperature parameter t for G3 uniformity.",
    )
    parser.add_argument(
        "--geometry_knn_k",
        type=int,
        default=10,
        help="k for hubness metric G4.",
    )
    parser.add_argument(
        "--geometry_max_samples",
        type=int,
        default=5000,
        help="Subsample size for hubness metric G4.",
    )
    parser.add_argument(
        "--geometry_seed",
        type=int,
        default=0,
        help="Random seed for pair sampling and subsampling.",
    )
    parser.add_argument(
        "--geometry_disable_center",
        action="store_false",
        dest="geometry_center",
        help="Disable mean-centering before geometry metrics.",
    )
    parser.add_argument(
        "--geometry_disable_l2",
        action="store_false",
        dest="geometry_l2",
        help="Disable L2 normalisation before geometry metrics.",
    )
    parser.set_defaults(geometry_center=True, geometry_l2=True)

    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    geometry_mode = args.analysis_type == "embedding_geometry"
    multi_geometry = geometry_mode and args.algo is None and args.model is None

    if args.algo is None and not multi_geometry:
        raise ValueError("Argument '--algo' is required unless aggregating all geometries.")
    if not multi_geometry and args.algo == "llm" and args.model is None:
        raise ValueError("Argument '--model' is required when '--algo llm' is selected.")
    if args.model is not None and (args.algo is None or args.algo != "llm"):
        print("Warning: '--model' is ignored for non-LLM algorithms.", file=sys.stderr)

    verbose_root = Path(args.verbose_root) if args.verbose_root else None
    
    # For embedding_geometry, allow processing all datasets and tasks if not specified
    if geometry_mode and multi_geometry:
        # Determine datasets and tasks to process
        if args.dataset is None:
            datasets = discover_datasets(verbose_root)
            if not datasets:
                raise FileNotFoundError(
                    f"No datasets found in verbose directory: "
                    f"{verbose_root if verbose_root else Path(__file__).resolve().parent.parent / 'verbose'}"
                )
            print(f"Discovered {len(datasets)} dataset(s): {', '.join(datasets)}")
        else:
            datasets = [args.dataset]
        
        if args.task is None:
            tasks = ["card", "time"]
            print(f"Processing all tasks: {', '.join(tasks)}")
        else:
            tasks = [args.task]
        
        # Process each dataset and task combination
        cfg = GeometryConfig(
            num_pairs=args.geometry_num_pairs,
            uniformity_t=args.geometry_uniformity_t,
            knn_k=args.geometry_knn_k,
            max_samples_for_knn=args.geometry_max_samples,
            seed=args.geometry_seed,
            center=args.geometry_center,
            l2=args.geometry_l2,
        )
        
        total = len(datasets) * len(tasks)
        current = 0
        for dataset in datasets:
            for task in tasks:
                current += 1
                print(f"\n{'='*60}")
                print(f"Processing {current}/{total}: {dataset}/{task}")
                print(f"{'='*60}")
                try:
                    dataset_dir = resolve_verbose_directory(dataset, verbose_root)
                    analyse_all_embedding_geometries(dataset_dir, dataset, task, args.seed, cfg)
                except FileNotFoundError as e:
                    print(f"Warning: {e}. Skipping {dataset}/{task}.")
                    continue
                except Exception as e:
                    print(f"Error processing {dataset}/{task}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        return
    
    # For non-geometry or single-file geometry analysis, dataset and task are required
    if args.dataset is None:
        raise ValueError("Argument '--dataset' is required for this analysis type.")
    if args.task is None:
        raise ValueError("Argument '--task' is required for this analysis type.")
    
    dataset_dir = resolve_verbose_directory(args.dataset, verbose_root)
    csv_path = None
    if not multi_geometry:
        csv_path = find_verbose_file(dataset_dir, args.task, args.algo, args.seed, args.model)

    if args.analysis_type == "top_q_error":
        if csv_path is None:
            raise RuntimeError("Internal error: csv_path missing for top_q_error analysis.")
        analyse_top_q_error(csv_path, args.topk)
        return

    if geometry_mode:
        cfg = GeometryConfig(
            num_pairs=args.geometry_num_pairs,
            uniformity_t=args.geometry_uniformity_t,
            knn_k=args.geometry_knn_k,
            max_samples_for_knn=args.geometry_max_samples,
            seed=args.geometry_seed,
            center=args.geometry_center,
            l2=args.geometry_l2,
        )
        if multi_geometry:
            analyse_all_embedding_geometries(dataset_dir, args.dataset, args.task, args.seed, cfg)
        else:
            analyse_embedding_geometry(
                csv_path=csv_path,
                metric=args.geometry_metric,
                num_pairs=args.geometry_num_pairs,
                uniformity_t=args.geometry_uniformity_t,
                knn_k=args.geometry_knn_k,
                max_samples=args.geometry_max_samples,
                seed=args.geometry_seed,
                center=args.geometry_center,
                l2=args.geometry_l2,
            )
        return

    raise NotImplementedError(f"Unsupported analysis type: {args.analysis_type}")


if __name__ == "__main__":
    main(sys.argv[1:])

