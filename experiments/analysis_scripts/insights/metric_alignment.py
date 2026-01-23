"""
Compute alignment between embedding distances and structural plan metrics.

For each verbose CSV (one per algo/model), this script:
  * Loads embeddings referenced in the verbose file.
  * Loads the corresponding plan file and extracts structural summaries.
  * Builds pairwise cosine distances between embeddings.
  * Builds pairwise structural distances (tables, columns, joins, filters,
    operator histograms, path n-grams).
  * Computes the mean per-anchor Spearman correlation between the embedding
    distance ordering and each structural distance ordering.
  * Writes a CSV where each column corresponds to an algo/model combination and
    each row is one Spearman score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from plan_structural_metrics import (
    PlanStructuralSummary,
    operator_multiset_distance,
    path_ngram_distance,
    summarise_plan_structure,
)


EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
VERBOSE_ROOT_DEFAULT = EXPERIMENTS_DIR / "verbose"
OUTPUT_DIR = Path(__file__).resolve().parent / "metric_alignment_results"

METRIC_ROWS = [
    ("num_tables", "spearman_num_tables"),
    ("num_columns", "spearman_num_columns"),
    ("num_joins", "spearman_num_joins"),
    ("num_filters", "spearman_num_filters"),
    ("operator_hist", "spearman_operator_multiset"),
    ("path_ngrams", "spearman_path_ngrams"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Metric alignment vs embeddings.")
    parser.add_argument("--dataset", required=True, help="Dataset identifier (e.g., job_full).")
    parser.add_argument(
        "--task",
        required=True,
        choices=["card", "time"],
        help="Task to analyze (card or time).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed filter (default: 42).")
    parser.add_argument(
        "--verbose_root",
        type=Path,
        default=VERBOSE_ROOT_DEFAULT,
        help="Root directory containing verbose_* folders.",
    )
    parser.add_argument(
        "--ngram_n",
        type=int,
        default=3,
        help="Path n-gram length when summarising plans (default: 3).",
    )
    parser.add_argument(
        "--plan_cache_limit",
        type=int,
        default=0,
        help="Optional limit on number of plans to process (0 = no limit).",
    )
    return parser.parse_args()


def _rank_array(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy()


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return float("nan")
    da = a - a.mean()
    db = b - b.mean()
    denom = np.linalg.norm(da) * np.linalg.norm(db)
    if denom == 0.0:
        return float("nan")
    return float(np.dot(da, db) / denom)


def mean_spearman(D_emb: np.ndarray, D_struct: np.ndarray) -> float:
    n = D_emb.shape[0]
    if n <= 1:
        return float("nan")
    rhos: List[float] = []
    for i in range(n):
        emb_row = D_emb[i].copy()
        struct_row = D_struct[i].copy()
        emb_row[i] = emb_row.max() + 1.0
        struct_row[i] = struct_row.max() + 1.0
        emb_ranks = _rank_array(emb_row)
        struct_ranks = _rank_array(struct_row)
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        rho = _pearson(emb_ranks[mask], struct_ranks[mask])
        if not np.isnan(rho):
            rhos.append(rho)
    return float(np.mean(rhos)) if rhos else float("nan")


def load_embeddings(embedding_path: Path) -> pd.DataFrame:
    df = pd.read_csv(embedding_path)
    if "idx" in df.columns:
        feature_cols = [col for col in df.columns if col != "idx"]
        return df.set_index("idx")[feature_cols]
    df = df.reset_index().rename(columns={"index": "idx"})
    return df.set_index("idx")


def extract_plan_path(series: pd.Series) -> Path:
    filled = series.replace("", pd.NA).ffill().dropna()
    if filled.empty:
        raise ValueError("No plan_file paths found in verbose CSV.")
    rel_path = filled.iloc[0]
    path = (EXPERIMENTS_DIR / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {path}")
    return path


def extract_embedding_path(series: pd.Series) -> Path:
    filled = series.replace("", pd.NA).ffill().dropna()
    if filled.empty:
        raise ValueError("No embedding_file paths found in verbose CSV.")
    rel_path = filled.iloc[0]
    path = (EXPERIMENTS_DIR / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Embedding file not found: {path}")
    return path


def load_plan_dataframe(plan_path: Path) -> pd.DataFrame:
    df = pd.read_csv(plan_path)
    if "json" not in df.columns:
        raise KeyError(f"'json' column not found in plan file: {plan_path}")
    return df.reset_index(drop=True)


def summarise_plans_for_indices(
    plan_df: pd.DataFrame, indices: List[int], ngram_n: int
) -> Dict[int, PlanStructuralSummary]:
    summaries: Dict[int, PlanStructuralSummary] = {}
    cache = {}
    for idx in indices:
        if idx in summaries:
            continue
        if idx >= len(plan_df):
            raise IndexError(f"Plan idx {idx} out of range for plan file with {len(plan_df)} rows.")
        plan_json = plan_df.iloc[idx]["json"]
        if plan_json in cache:
            summaries[idx] = cache[plan_json]
            continue
        plan_obj = json.loads(plan_json)
        summary = summarise_plan_structure(plan_obj, ngram_n=ngram_n)
        summaries[idx] = summary
        cache[plan_json] = summary
    return summaries


def cosine_distance_matrix(vectors: np.ndarray) -> np.ndarray:
    if vectors.ndim != 2:
        raise ValueError("Embeddings array must be 2-D.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    Z = vectors / norms
    sim = np.clip(Z @ Z.T, -1.0, 1.0)
    dist = 1.0 - sim
    np.fill_diagonal(dist, 0.0)
    return dist


def pairwise_abs_diff(values: np.ndarray) -> np.ndarray:
    return np.abs(values[:, None] - values[None, :])


def pairwise_hist_distance(summaries: List[PlanStructuralSummary]) -> np.ndarray:
    n = len(summaries)
    mat = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = operator_multiset_distance(
                summaries[i].operator_histogram, summaries[j].operator_histogram, norm="l1"
            )
            mat[i, j] = mat[j, i] = d
    return mat


def pairwise_ngram_distance(summaries: List[PlanStructuralSummary]) -> np.ndarray:
    n = len(summaries)
    mat = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = path_ngram_distance(summaries[i].path_ngrams, summaries[j].path_ngrams)
            mat[i, j] = mat[j, i] = d
    return mat


def compute_alignment_for_file(
    csv_path: Path, ngram_n: int, plan_cache_limit: int
) -> Dict[str, float]:
    verbose_df = pd.read_csv(csv_path)
    if "idx" not in verbose_df.columns:
        raise KeyError(f"'idx' column missing in verbose file {csv_path}")

    plan_path = extract_plan_path(verbose_df["plan_file"])
    embedding_path = extract_embedding_path(verbose_df["embedding_file"])

    embedding_df = load_embeddings(embedding_path)
    idx_list = verbose_df["idx"].tolist()
    if plan_cache_limit > 0:
        idx_list = idx_list[:plan_cache_limit]
        verbose_df = verbose_df.iloc[:plan_cache_limit]

    available_indices = [idx for idx in idx_list if idx in embedding_df.index]
    if len(available_indices) < 2:
        return {row_name: float("nan") for _, row_name in METRIC_ROWS}

    vectors = embedding_df.loc[available_indices].to_numpy(dtype=float)
    D_emb = cosine_distance_matrix(vectors)

    plan_df = load_plan_dataframe(plan_path)
    summaries_map = summarise_plans_for_indices(plan_df, available_indices, ngram_n)
    summaries = [summaries_map[idx] for idx in available_indices]

    tables = np.array([summary.num_tables for summary in summaries], dtype=float)
    columns = np.array([summary.num_columns for summary in summaries], dtype=float)
    joins = np.array([summary.num_joins for summary in summaries], dtype=float)
    filters = np.array([summary.num_filters for summary in summaries], dtype=float)

    D_tables = pairwise_abs_diff(tables)
    D_columns = pairwise_abs_diff(columns)
    D_joins = pairwise_abs_diff(joins)
    D_filters = pairwise_abs_diff(filters)
    D_hist = pairwise_hist_distance(summaries)
    D_ngrams = pairwise_ngram_distance(summaries)

    results = {
        "spearman_num_tables": mean_spearman(D_emb, D_tables),
        "spearman_num_columns": mean_spearman(D_emb, D_columns),
        "spearman_num_joins": mean_spearman(D_emb, D_joins),
        "spearman_num_filters": mean_spearman(D_emb, D_filters),
        "spearman_operator_multiset": mean_spearman(D_emb, D_hist),
        "spearman_path_ngrams": mean_spearman(D_emb, D_ngrams),
    }
    return results


def build_output_dataframe(results: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    index = [row_name for _, row_name in METRIC_ROWS]
    df = pd.DataFrame(index=index)
    for column, metrics in results.items():
        column_values = [metrics.get(row_name, float("nan")) for row_name in index]
        df[column] = column_values
    return df


def main() -> None:
    args = parse_args()
    dataset_dir = args.verbose_root / f"verbose_Train_{args.dataset}_Test_{args.dataset}_ours"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Verbose directory not found: {dataset_dir}")

    pattern = f"{args.task}_*_seed{args.seed}.csv"
    csv_files = sorted(dataset_dir.glob(pattern))
    if not csv_files:
        raise FileNotFoundError(f"No verbose CSV files matched pattern {pattern} in {dataset_dir}")

    column_results: Dict[str, Dict[str, float]] = {}
    for csv_path in csv_files:
        print(f"Processing {csv_path.name} ...")
        metrics = compute_alignment_for_file(csv_path, args.ngram_n, args.plan_cache_limit)
        column_results[csv_path.stem] = metrics

    dataset_dir = OUTPUT_DIR / args.dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    out_path = dataset_dir / f"metric_alignment_{args.dataset}_{args.task}_seed{args.seed}.csv"
    df_out = build_output_dataframe(column_results)
    df_out.to_csv(out_path)
    print(f"Saved metric alignment table to {out_path}")


if __name__ == "__main__":
    main()

