"""
Case study: Per-anchor Spearman alignment for selected percentile plans.

For a given verbose CSV (algo/model), this script:
  - Selects four anchors by q_error: 50th, 90th, 95th percentile, and max.
  - Builds embedding distance matrix D_emb (1 - cosine on L2-normalized embeddings).
  - Builds structural distance matrices for:
      num_tables, num_columns, num_joins, num_filters, longest_path_len,
      operator_multiset (L1), path_ngrams (cosine distance on TF).
  - For each anchor, computes Spearman rank correlation between the anchor's
    row of D_emb and each structural distance row (excluding self).
  - Writes a CSV whose rows are [q50, q90, q95, qmax] and columns are metrics.

Output filename includes algo and model to disambiguate runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from plan_structural_metrics import (
    PlanStructuralSummary,
    operator_multiset_distance,
    path_ngram_distance,
    summarise_plan_structure,
)


EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
VERBOSE_ROOT_DEFAULT = EXPERIMENTS_DIR / "verbose"
OUT_DIR = Path(__file__).resolve().parent / "case_study_results"

STRUCT_SCALAR_KEYS = [
    ("num_tables", "num_tables"),
    ("num_columns", "num_columns"),
    ("num_joins", "num_joins"),
    ("num_filters", "num_filters"),
    ("longest_path_len", "longest_path"),
]
STRUCT_COMPLEX_KEYS = [
    ("operator_histogram", "operator_multiset"),
    ("path_ngrams", "path_ngrams"),
]
EXTRA_LABEL_METRICS = ["true_label", "est_label"]
ALL_METRICS = (
    [label for _, label in STRUCT_SCALAR_KEYS]
    + [label for _, label in STRUCT_COMPLEX_KEYS]
    + EXTRA_LABEL_METRICS
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Per-anchor Spearman case study from verbose CSVs.")
    parser.add_argument("--dataset", required=True, help="Dataset (e.g., job_full).")
    parser.add_argument("--task", required=True, choices=["card", "time"], help="Task type.")
    parser.add_argument("--seed", type=int, default=42, help="Seed to filter verbose CSVs.")
    parser.add_argument("--algo", default=None, help="Algorithm (e.g., llm, bao, aimai, qf, e2e_cost). Optional: if not set, processes all combinations.")
    parser.add_argument("--model", default=None, help="Model identifier when algo=llm (required for llm when algo is specified).")
    parser.add_argument("--verbose_root", type=Path, default=VERBOSE_ROOT_DEFAULT, help="Verbose root.")
    parser.add_argument("--ngram_n", type=int, default=3, help="n for path n-grams (default: 3).")
    parser.add_argument("--pc_drop_k", type=int, default=1, help="Top-k PCs to drop in LOO PC-drop (default: 1).")
    parser.add_argument(
        "--study_type",
        choices=["spearman", "counts"],
        default="spearman",
        help="Type of case study: 'spearman' (default) or 'counts' for simple structural metrics.",
    )
    parser.add_argument(
        "--plan_cache_limit",
        type=int,
        default=0,
        help="Optional cap on number of rows (0 = all). Applied after sorting by idx.",
    )
    return parser.parse_args()


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


def fit_pc_drop(Z: np.ndarray, k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    Z = np.asarray(Z, float)
    Zhat = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12)
    mu = Zhat.mean(axis=0, keepdims=True)
    X = Zhat - mu
    _, _, Vh = np.linalg.svd(X, full_matrices=False)
    U = Vh[:k].T
    return mu, U


def apply_pc_drop(Z: np.ndarray, mu: np.ndarray, U: np.ndarray) -> np.ndarray:
    Z = np.asarray(Z, float)
    Zhat = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12)
    X = Zhat - mu
    proj = (X @ U) @ U.T
    R = X - proj
    R = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-12)
    return R


def pc_drop_for_anchor(Z: np.ndarray, i: int, k: int = 1) -> np.ndarray:
    n = Z.shape[0]
    mask = np.arange(n) != i
    mu, U = fit_pc_drop(Z[mask], k=k)
    return apply_pc_drop(Z, mu, U)


def _rank(x: np.ndarray) -> np.ndarray:
    # Average ranks; smaller distance → better (rank 1)
    return pd.Series(x).rank(method="average", ascending=True).to_numpy()


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    da = a - a.mean()
    db = b - b.mean()
    denom = np.linalg.norm(da) * np.linalg.norm(db)
    if denom == 0.0:
        return float("nan")
    return float(np.dot(da, db) / denom)


def spearman_row(a: np.ndarray, b: np.ndarray) -> float:
    ra = _rank(a)
    rb = _rank(b)
    return _pearson(ra, rb)


def spearman_row_with_p(a: np.ndarray, b: np.ndarray) -> Tuple[float, float]:
    ra = _rank(a)
    rb = _rank(b)
    rho, p = stats.pearsonr(ra, rb)
    return float(rho), float(p)


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


def pairwise_abs_diff(values: np.ndarray) -> np.ndarray:
    return np.abs(values[:, None] - values[None, :])


def pairwise_hist_distance(summaries: List[PlanStructuralSummary]) -> np.ndarray:
    n = len(summaries)
    M = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = operator_multiset_distance(summaries[i].operator_histogram, summaries[j].operator_histogram, norm="l1")
            M[i, j] = M[j, i] = d
    return M


def pairwise_ngram_distance(summaries: List[PlanStructuralSummary]) -> np.ndarray:
    n = len(summaries)
    M = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = path_ngram_distance(summaries[i].path_ngrams, summaries[j].path_ngrams)
            M[i, j] = M[j, i] = d
    return M


def pick_quantile_indices(q_errors: np.ndarray, percentiles: List[int]) -> Dict[str, int]:
    # For p in percentiles, pick the first index with q_error >= percentile value (or nearest).
    idxs: Dict[str, int] = {}
    n = q_errors.size
    if n == 0:
        return {"q50": -1, "q90": -1, "q95": -1, "qmax": -1}
    values = np.percentile(q_errors, percentiles, interpolation="nearest") if hasattr(np, "percentile") else np.quantile(q_errors, np.array(percentiles) / 100.0)
    labels = [f"q{p}" for p in percentiles]
    for label, target in zip(labels, np.atleast_1d(values)):
        diffs = np.abs(q_errors - target)
        idxs[label] = int(np.argmin(diffs))
    idxs["qmax"] = int(np.argmax(q_errors))
    return idxs


def find_verbose_file(dataset_dir: Path, task: str, algo: str, seed: int, model: str | None) -> Path:
    pattern = f"{task}_{algo}*seed{seed}.csv"
    candidates = [p for p in dataset_dir.glob(pattern) if p.is_file()]
    if algo == "llm":
        if not model:
            raise ValueError("Argument --model is required for algo=llm.")
        candidates = [p for p in candidates if model in p.stem]
    if not candidates:
        raise FileNotFoundError(f"No verbose CSV found for pattern {pattern} (algo={algo}, model={model}) in {dataset_dir}")
    if len(candidates) > 1 and algo == "llm":
        # Prefer baseline file (without _rm-)
        baseline = [p for p in candidates if "_rm-" not in p.name]
        if len(baseline) == 1:
            return baseline[0]
        # else fallthrough
    if len(candidates) > 1:
        # Pick lexicographically first to be deterministic
        candidates.sort()
    return candidates[0]


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
        
        # Try to extract algo from filename
        # Pattern: {task}_{algo}_..._seed{seed}.csv
        stem = entry.stem
        parts = stem.replace(f"_{seed_token}", "").replace(f"{prefix}", "").split("_")
        
        algo = None
        model = None
        
        # Check for LLM first (files starting with {task}_llm_)
        # This must be checked first because LLM filenames may contain "postgres" as a config parameter
        if stem.startswith(f"{prefix}llm_"):
            algo = "llm"
            # For LLM, extract model name from filename
            # Pattern: {task}_llm_..._{model}_..._seed{seed}
            # Remove task prefix and seed token to get the middle part
            model_part = stem.replace(f"{prefix}llm_", "").replace(f"_{seed_token}", "")
            # Split by underscores and try to identify model parts
            # Common patterns: model names often contain hyphens or are multi-part
            # Try to find model identifier (usually appears after some config params)
            parts = model_part.split("_")
            # Look for known model prefixes
            model_candidates = [
                "meta-llama", "google-gemma", "Qwen", "microsoft", "mistral", 
                "BGE", "bge", "e5", "instructor", "sentence-transformers"
            ]
            model_found = False
            for i, part in enumerate(parts):
                for candidate in model_candidates:
                    if candidate.lower() in part.lower():
                        # Found a model candidate, collect subsequent parts until we hit config params
                        # Config params typically look like: emb, quant, downstream, etc.
                        config_keywords = ["emb", "quant", "downstream", "pretrained", "hid", "b", "h"]
                        model_parts = [part]
                        for j in range(i + 1, len(parts)):
                            if any(kw in parts[j].lower() for kw in config_keywords):
                                break
                            model_parts.append(parts[j])
                        model = "_".join(model_parts)
                        model_found = True
                        break
                if model_found:
                    break
            
            # If no model found, use first few parts as fallback
            if not model_found:
                # Take first 2-3 parts that don't look like config
                config_keywords = ["emb", "quant", "downstream", "pretrained", "hid", "b", "h", "cdf"]
                model_parts = []
                for part in parts[:4]:  # Check first 4 parts
                    if not any(kw in part.lower() for kw in config_keywords):
                        model_parts.append(part)
                    if len(model_parts) >= 2:
                        break
                model = "_".join(model_parts) if model_parts else "unknown"
        else:
            # If not LLM, check for non-LLM algorithms
            # For non-LLM, we need to check that the algo appears right after the task prefix
            # to avoid false matches (e.g., "postgres" appearing in LLM filenames)
            for non_llm_algo in non_llm_algos:
                if stem.startswith(f"{prefix}{non_llm_algo}_"):
                    algo = non_llm_algo
                    break
        
        if algo:
            results.append((entry, algo, model))
    
    return results


def process_single_case_study(
    verbose_csv: Path,
    args: argparse.Namespace,
    algo: str,
    model: str | None,
) -> None:
    """
    Process a single case study for a given verbose CSV file.
    """
    vdf = pd.read_csv(verbose_csv)
    if args.plan_cache_limit > 0:
        vdf = vdf.iloc[: args.plan_cache_limit]

    if "q_error" not in vdf.columns:
        raise KeyError(f"'q_error' not found in {verbose_csv}")

    plan_path = extract_first_nonempty(vdf["plan_file"])
    emb_path = extract_first_nonempty(vdf["embedding_file"])

    # Embeddings
    emb_df = load_embeddings(emb_path)
    # Align by idx if present; otherwise row-order
    if "idx" in vdf.columns and emb_df.index.name == "idx":
        valid_mask = vdf["idx"].isin(emb_df.index)
        vdf = vdf[valid_mask].reset_index(drop=True)
        vectors = emb_df.loc[vdf["idx"]].to_numpy(dtype=float)
    else:
        vectors = emb_df.to_numpy(dtype=float)
        vectors = vectors[: len(vdf)]

    D_emb = cosine_distance_matrix(vectors)

    # Structural summaries
    plan_df = pd.read_csv(plan_path)
    if "json" not in plan_df.columns:
        raise KeyError(f"'json' column not found in plan file: {plan_path}")
    plan_df = plan_df.reset_index(drop=True)
    q_errors = vdf["q_error"].to_numpy(dtype=float)
    indices = list(range(len(vdf)))

    # Parse and summarise all used plans
    summaries: List[PlanStructuralSummary] = []
    cache: Dict[str, PlanStructuralSummary] = {}
    for idx in indices:
        raw = plan_df.iloc[idx]["json"]
        if raw in cache:
            summaries.append(cache[raw])
        else:
            obj = json.loads(raw)
            summ = summarise_plan_structure(obj, ngram_n=args.ngram_n)
            summaries.append(summ)
            cache[raw] = summ

    # Structural distance matrices
    n = len(vectors)
    D_struct: Dict[str, np.ndarray] = {}
    # Scalar metrics
    for key, label in STRUCT_SCALAR_KEYS:
        vals = np.array([getattr(s, key) for s in summaries], dtype=float)
        D_struct[label] = pairwise_abs_diff(vals)
    # Complex metrics
    D_struct["operator_multiset"] = pairwise_hist_distance(summaries)
    D_struct["path_ngrams"] = pairwise_ngram_distance(summaries)
    # Label distances (true and estimated)
    if "true_label" in vdf.columns:
        true_vals = vdf["true_label"].to_numpy(dtype=float)
        D_struct["true_label"] = pairwise_abs_diff(true_vals)
    else:
        D_struct["true_label"] = np.full((n, n), np.nan, dtype=float)
    if "est_label" in vdf.columns:
        est_vals = vdf["est_label"].to_numpy(dtype=float)
        D_struct["est_label"] = pairwise_abs_diff(est_vals)
    else:
        D_struct["est_label"] = np.full((n, n), np.nan, dtype=float)

    # Pick anchors
    anchors = pick_quantile_indices(q_errors, [50, 90, 95])
    row_labels = ["q50", "q90", "q95", "qmax"]
    anchor_indices = [anchors["q50"], anchors["q90"], anchors["q95"], anchors["qmax"]]

    if args.study_type == "counts":
        # Simple type-2 case study: report structural counts at the four anchors
        table_counts = pd.DataFrame(
            index=row_labels,
            columns=["num_tables", "num_columns", "num_joins", "num_filters", "longest_path"],
            dtype=float,
        )
        for rlabel, anchor in zip(row_labels, anchor_indices):
            if anchor < 0 or anchor >= n:
                table_counts.loc[rlabel, :] = np.nan
                continue
            s = summaries[anchor]
            table_counts.loc[rlabel, "num_tables"] = s.num_tables
            table_counts.loc[rlabel, "num_columns"] = s.num_columns
            table_counts.loc[rlabel, "num_joins"] = s.num_joins
            table_counts.loc[rlabel, "num_filters"] = s.num_filters
            table_counts.loc[rlabel, "longest_path"] = s.longest_path_len

        dataset_dir = OUT_DIR / args.dataset
        dataset_dir.mkdir(parents=True, exist_ok=True)
        algo_tag = algo
        model_tag = model if (algo == "llm" and model) else "none"
        out_name = f"case_study_counts_{args.dataset}_{args.task}_seed{args.seed}_{algo_tag}_{model_tag}.csv"
        out_path = dataset_dir / out_name
        table_counts.to_csv(out_path)
        print(f"Saved case study counts table to {out_path}")
        return

    # Compute per-anchor Spearman (type-1 detailed)
    table = pd.DataFrame(index=row_labels, columns=ALL_METRICS, dtype=object)
    table_pc = pd.DataFrame(index=row_labels, columns=[f"{c}_pc_drop" for c in ALL_METRICS], dtype=object)
    for rlabel, anchor in zip(row_labels, anchor_indices):
        if anchor < 0 or anchor >= n:
            table.loc[rlabel, :] = "NaN"
            table_pc.loc[rlabel, :] = "NaN"
            continue
        emb_row = D_emb[anchor].copy()
        emb_row[anchor] = emb_row.max() + 1.0
        # PC-drop embedding distances (leave-one-out fit for this anchor)
        Z_star = pc_drop_for_anchor(vectors, anchor, k=args.pc_drop_k)
        norms_star = np.linalg.norm(Z_star, axis=1, keepdims=True)
        norms_star[norms_star == 0.0] = 1.0
        Zs = Z_star / norms_star
        emb_row_pc = 1.0 - (Zs[anchor:anchor+1] @ Zs.T).ravel()
        emb_row_pc[anchor] = emb_row_pc.max() + 1.0
        for label in ALL_METRICS:
            struct_row = D_struct[label][anchor].copy()
            struct_row[anchor] = struct_row.max() + 1.0
            rho, p = spearman_row_with_p(emb_row, struct_row)
            rho_pc, p_pc = spearman_row_with_p(emb_row_pc, struct_row)
            table.at[rlabel, label] = f"{rho:.4f}{significance_stars(p)}" if not np.isnan(rho) else "NaN"
            table_pc.at[rlabel, f"{label}_pc_drop"] = f"{rho_pc:.4f}{significance_stars(p_pc)}" if not np.isnan(rho_pc) else "NaN"

    dataset_dir = OUT_DIR / args.dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    algo_tag = algo
    model_tag = model if (algo == "llm" and model) else "none"
    out_name = f"case_study_{args.dataset}_{args.task}_seed{args.seed}_{algo_tag}_{model_tag}.csv"
    out_path = dataset_dir / out_name
    merged = pd.concat([table, table_pc], axis=1)
    merged.to_csv(out_path)
    print(f"Saved case study table to {out_path}")


def main() -> None:
    args = parse_args()
    dataset_dir = args.verbose_root / f"verbose_Train_{args.dataset}_Test_{args.dataset}_ours"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Verbose directory not found: {dataset_dir}")

    # Check if we should process all combinations
    if args.algo is None:
        # Process all combinations
        csv_combinations = _collect_verbose_csvs(dataset_dir, args.task, args.seed)
        if not csv_combinations:
            raise FileNotFoundError(
                f"No verbose CSV files found for task '{args.task}', seed {args.seed} in {dataset_dir}"
            )
        
        print(f"Processing {len(csv_combinations)} case studies...")
        for csv_path, algo, model in csv_combinations:
            print(f"\nProcessing: {csv_path.name} (algo={algo}, model={model})")
            try:
                process_single_case_study(csv_path, args, algo, model)
            except Exception as e:
                print(f"Error processing {csv_path.name}: {e}")
                continue
        print(f"\nCompleted processing {len(csv_combinations)} case studies.")
    else:
        # Process single combination
        if args.algo == "llm" and args.model is None:
            raise ValueError("Argument --model is required when --algo is 'llm'.")
        
        verbose_csv = find_verbose_file(dataset_dir, args.task, args.algo, args.seed, args.model)
        process_single_case_study(verbose_csv, args, args.algo, args.model)


if __name__ == "__main__":
    main()


