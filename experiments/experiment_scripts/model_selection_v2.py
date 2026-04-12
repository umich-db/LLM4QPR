#!/usr/bin/env python3
"""
Surrogate-based model selection (v2) using Bayesian optimization.

Uses rich metadata features and bootstrap ensemble surrogates to search
for the best LLM within a latency budget — no monotonicity assumption.

Usage (dry run):
    cd experiments
    python experiment_scripts/model_selection_v2.py \
        --latency_limit 20 --workload stats --dry_run

Usage (real evaluation):
    cd experiments
    python experiment_scripts/model_selection_v2.py \
        --latency_limit 50 --workload stats --task time --db postgres \
        --quantification 4-bit --init_budget 24 --batch_size 4 --max_evals 80
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import pairwise_distances
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / "model_profile_with_nonemb.csv"

# Column definitions for the model profile CSV
CONTINUOUS_COLS = [
    "non_embedding_params",
    "embedding_params",
    "num_layers",
    "hidden_size",
    "attention_heads",
    "ffn_width",
    "context_length",
    "embedding_dimension",
    "is_embedding_tuned",
    "is_instruction_tuned",
    "is_multilingual",
    "is_cased",
    "deduped_variant",
]

CATEGORICAL_COLS = [
    "model_family",
    "architecture",
    "encoder_vs_decoder",
    "pooling_method",
    "tokenizer_behavior",
]

# Workload -> training workload mapping (matches run_model_selection.sh)
TRAIN_WORKLOAD_MAP = {
    "syn": "job",
    "job_full": "job",
}


# ============================================================
# Config and result
# ============================================================

@dataclass
class SearchConfig:
    latency_limit: float
    init_budget: int = 24
    batch_size: int = 4
    max_evals: int = 80
    random_state: int = 42

    # Acquisition / pruning
    feasibility_quantile_floor: float = 0.02
    min_ei: float = 1e-8
    exploration_weight: float = 0.15
    diversity_weight: float = 0.20

    # Feature filtering
    enable_feature_filtering: bool = True
    feature_filter_after: int = 24
    keep_top_k_features: Optional[int] = 12

    # Initialization
    n_init_clusters: Optional[int] = None
    size_col: Optional[str] = "non_embedding_params"

    # Ensemble surrogate
    ensemble_size: int = 12
    rf_num_trees: int = 300
    rf_min_samples_leaf: int = 2

    # Stopping
    patience_rounds: int = 4
    min_relative_improvement: float = 1e-4


@dataclass
class SearchResult:
    evaluated: pd.DataFrame
    best_feasible_row: Optional[pd.Series]
    history: List[Dict]
    selected_feature_names: List[str] = field(default_factory=list)
    round_snapshots: List[Dict] = field(default_factory=list)


# ============================================================
# Main search class
# ============================================================

class ConstrainedModelSearch:
    """
    Metadata-aware surrogate search over a discrete pool of feasible models.
    Pre-filters candidates by known latency, then uses Bayesian optimization
    (Expected Improvement) on an accuracy surrogate to find the best model.
    """

    def __init__(
        self,
        candidates: pd.DataFrame,
        evaluator: Callable[[pd.Series], Tuple[float, float]],
        config: SearchConfig,
        candidate_id_col: str = "model",
        continuous_cols: Optional[Sequence[str]] = None,
        categorical_cols: Optional[Sequence[str]] = None,
    ) -> None:
        if candidate_id_col not in candidates.columns:
            raise ValueError(f"Missing candidate_id_col={candidate_id_col!r}")

        self.config = config
        self.candidate_id_col = candidate_id_col
        self.evaluator = evaluator
        self.rng = np.random.default_rng(config.random_state)

        # Pre-filter to feasible candidates only (latency is known from profiling)
        all_candidates = candidates.copy().reset_index(drop=True)
        feasible_mask = all_candidates["avg_ms"] <= config.latency_limit
        self.candidates = all_candidates[feasible_mask].copy().reset_index(drop=True)
        self.n_total_candidates = len(all_candidates)
        self.n_feasible = len(self.candidates)
        print(f"Pre-filtered to {self.n_feasible}/{self.n_total_candidates} "
              f"feasible candidates (latency <= {config.latency_limit}ms)", flush=True)

        self.candidates["_evaluated"] = False
        self.candidates["_latency"] = np.nan
        self.candidates["_accuracy"] = np.nan

        if config.size_col and config.size_col in self.candidates.columns:
            eps = 1e-12
            self.candidates["log_non_embedding_params"] = np.log(
                self.candidates[config.size_col].astype(float).clip(lower=eps)
            )

        self.feature_cols_all, self.continuous_cols, self.categorical_cols = (
            self._infer_features(continuous_cols, categorical_cols)
        )
        self.selected_feature_cols = list(self.feature_cols_all)

        self.accuracy_surrogate: Optional[BootstrapEnsembleRegressor] = None

        self.history: List[Dict] = []
        self.round_snapshots: List[Dict] = []
        self.best_feasible_accuracy: Optional[float] = None
        self.rounds_without_improvement = 0

    def run(self) -> SearchResult:
        self._initialize_seed_set()

        while True:
            if self._should_stop():
                break

            self._fit_surrogates()

            if (
                self.config.enable_feature_filtering
                and self.num_evaluated >= self.config.feature_filter_after
            ):
                old_features = list(self.selected_feature_cols)
                self._feature_filter()
                if self.selected_feature_cols != old_features:
                    self._fit_surrogates()  # re-fit with filtered features

            batch = self._select_batch()
            if len(batch) == 0:
                break

            self._collect_snapshot(batch)

            round_num = len(self.round_snapshots)
            batch_models = [self.candidates.loc[i, self.candidate_id_col] for i in batch]
            print(f"\n--- Round {round_num}: evaluating batch of {len(batch)} "
                  f"(total evaluated: {self.num_evaluated}/{self.config.max_evals}) ---",
                  flush=True)
            for m in batch_models:
                print(f"  -> {m}", flush=True)

            old_best = self.best_feasible_accuracy
            self._evaluate_ids(batch)
            new_best = self.best_feasible_accuracy

            improved = (
                old_best is None
                or (new_best is not None and new_best > old_best + abs(old_best or 1.0) * self.config.min_relative_improvement)
            )
            if improved:
                self.rounds_without_improvement = 0
            else:
                self.rounds_without_improvement += 1

            best_str = f"{new_best:.4f}" if new_best is not None else "N/A"
            print(f"--- Round {round_num} done. Best feasible accuracy: {best_str} "
                  f"(patience: {self.rounds_without_improvement}/{self.config.patience_rounds}) ---",
                  flush=True)

        evaluated = self.candidates[self.candidates["_evaluated"]].copy()
        feasible = evaluated[evaluated["_latency"] <= self.config.latency_limit]
        best_feasible_row = None if feasible.empty else feasible.sort_values("_accuracy", ascending=False).iloc[0]

        return SearchResult(
            evaluated=evaluated,
            best_feasible_row=best_feasible_row,
            history=self.history,
            selected_feature_names=self.selected_feature_cols,
            round_snapshots=self.round_snapshots,
        )

    # --------------------------------------------------------
    # Core search steps
    # --------------------------------------------------------

    def _initialize_seed_set(self) -> None:
        init_ids = self._diverse_initialization_ids(self.config.init_budget)
        self._evaluate_ids(init_ids)

    def _fit_surrogates(self) -> None:
        train_df = self.candidates[self.candidates["_evaluated"]].copy()
        # Exclude failed evaluations (accuracy = -inf)
        train_df = train_df[np.isfinite(train_df["_accuracy"])].copy()
        if train_df.empty or len(train_df) < 2:
            raise RuntimeError("Not enough successful evaluations to fit surrogates.")

        X = train_df[self.selected_feature_cols]
        y_accuracy = train_df["_accuracy"].to_numpy()

        cont_cols = [c for c in self.selected_feature_cols if c in self.continuous_cols]
        cat_cols = [c for c in self.selected_feature_cols if c in self.categorical_cols]

        preprocessor = make_preprocessor(cont_cols, cat_cols)

        base_accuracy = Pipeline(
            steps=[
                ("prep", preprocessor),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=self.config.rf_num_trees,
                        min_samples_leaf=self.config.rf_min_samples_leaf,
                        random_state=self.config.random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

        self.accuracy_surrogate = BootstrapEnsembleRegressor(
            base_estimator=base_accuracy,
            n_estimators=self.config.ensemble_size,
            random_state=self.config.random_state + 200,
        ).fit(X, y_accuracy)

    def _feature_filter(self) -> None:
        assert self.accuracy_surrogate is not None

        train_df = self.candidates[self.candidates["_evaluated"]].copy()
        train_df = train_df[np.isfinite(train_df["_accuracy"])].copy()
        if len(train_df) < max(12, len(self.selected_feature_cols) + 2):
            return

        X = train_df[self.selected_feature_cols]
        y = train_df["_accuracy"].to_numpy()

        try:
            all_importances = []
            for est in self.accuracy_surrogate.estimators_:
                pi = permutation_importance(
                    est, X, y,
                    n_repeats=5,
                    random_state=self.config.random_state,
                    n_jobs=-1,
                )
                all_importances.append(pi.importances_mean)
            avg_importances = np.mean(all_importances, axis=0)
        except Exception:
            return

        importances = pd.Series(
            avg_importances, index=self.selected_feature_cols
        ).sort_values(ascending=False)

        if self.config.keep_top_k_features is None:
            keep = importances[importances > 0].index.tolist()
        else:
            keep = importances.head(
                min(self.config.keep_top_k_features, len(importances))
            ).index.tolist()

        if len(keep) >= 2:
            self.selected_feature_cols = keep

    def _select_batch(self) -> List[int]:
        unevaluated = self.candidates[~self.candidates["_evaluated"]].copy()
        if unevaluated.empty:
            return []

        scored = self._score_candidates(unevaluated)
        if scored.empty:
            return []

        chosen_indices: List[int] = []
        remaining = scored.copy()

        for _ in range(min(self.config.batch_size, len(remaining))):
            if chosen_indices:
                remaining["_batch_diversity_bonus"] = self._diversity_bonus(
                    remaining[self.selected_feature_cols],
                    self.candidates.loc[chosen_indices, self.selected_feature_cols],
                )
            else:
                remaining["_batch_diversity_bonus"] = 1.0

            remaining["_final_score"] = (
                remaining["_acq_score"]
                + self.config.diversity_weight * remaining["_batch_diversity_bonus"]
            )

            pick_idx = remaining["_final_score"].idxmax()
            chosen_indices.append(int(pick_idx))
            remaining = remaining.drop(index=pick_idx)

            if remaining.empty:
                break

        return chosen_indices

    def _score_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        assert self.accuracy_surrogate is not None

        X = df[self.selected_feature_cols]
        mu_A, std_A = self.accuracy_surrogate.predict(X, return_std=True)

        if self.best_feasible_accuracy is None:
            # Before any feasible evaluation, use optimistic exploration
            ei_A = mu_A + self.config.exploration_weight * std_A
        else:
            ei_A = expected_improvement_maximization(
                mu=mu_A, sigma=std_A, best=self.best_feasible_accuracy,
            )

        scored = df.copy()
        scored["_mu_accuracy"] = mu_A
        scored["_std_accuracy"] = std_A
        scored["_ei_accuracy"] = ei_A
        scored["_acq_score"] = ei_A  # Pure EI — all candidates are feasible

        return scored.sort_values("_acq_score", ascending=False)

    def _evaluate_ids(self, row_indices: Sequence[int]) -> None:
        for idx in row_indices:
            row = self.candidates.loc[idx]
            latency, accuracy = self.evaluator(row)

            self.candidates.at[idx, "_evaluated"] = True
            self.candidates.at[idx, "_latency"] = float(latency)
            self.candidates.at[idx, "_accuracy"] = float(accuracy)

            # All candidates are pre-filtered feasible; update best if finite
            feasible = latency <= self.config.latency_limit
            if np.isfinite(accuracy):
                if self.best_feasible_accuracy is None or accuracy > self.best_feasible_accuracy:
                    self.best_feasible_accuracy = float(accuracy)

            self.history.append({
                "candidate_id": row[self.candidate_id_col],
                "row_index": int(idx),
                "latency": float(latency),
                "accuracy": float(accuracy),
                "feasible": bool(feasible),
                "num_evaluated": int(self.num_evaluated),
            })

    def _should_stop(self) -> bool:
        if self.num_evaluated >= self.config.max_evals:
            return True
        if self.rounds_without_improvement >= self.config.patience_rounds:
            return True
        if (~self.candidates["_evaluated"]).sum() == 0:
            return True
        return False

    # --------------------------------------------------------
    # Initialization helpers
    # --------------------------------------------------------

    def _diverse_initialization_ids(self, budget: int) -> List[int]:
        budget = min(budget, len(self.candidates))
        X = self._initialization_embedding(self.candidates)

        n_clusters = self.config.n_init_clusters or budget
        n_clusters = min(n_clusters, len(self.candidates))

        if n_clusters <= 1:
            return self.rng.choice(len(self.candidates), size=budget, replace=False).tolist()

        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=self.config.random_state)
        labels = km.fit_predict(X)
        centers = km.cluster_centers_

        chosen: List[int] = []
        for cluster_id in range(n_clusters):
            members = np.where(labels == cluster_id)[0]
            if len(members) == 0:
                continue
            d = np.linalg.norm(X[members] - centers[cluster_id], axis=1)
            chosen.append(int(members[np.argmin(d)]))

        chosen = list(dict.fromkeys(chosen))
        if len(chosen) < budget:
            extra = self._greedy_farthest_fill(X, chosen, budget - len(chosen))
            chosen.extend(extra)

        return chosen[:budget]

    def _initialization_embedding(self, df: pd.DataFrame) -> np.ndarray:
        cont_cols = self.continuous_cols
        cat_cols = self.categorical_cols

        prep = make_preprocessor(cont_cols, cat_cols)
        X = prep.fit_transform(df[self.feature_cols_all])

        if hasattr(X, "toarray"):
            X = X.toarray()
        return np.asarray(X, dtype=float)

    def _greedy_farthest_fill(
        self, X: np.ndarray, chosen: List[int], n_extra: int,
    ) -> List[int]:
        remaining = [i for i in range(len(X)) if i not in chosen]
        extra: List[int] = []

        if not remaining or n_extra <= 0:
            return extra

        if not chosen:
            first = int(self.rng.integers(0, len(X)))
            chosen = [first]
            remaining.remove(first)
            extra.append(first)
            n_extra -= 1

        chosen_set = set(chosen)
        while n_extra > 0 and remaining:
            rem_idx = np.array(remaining, dtype=int)
            d = pairwise_distances(X[rem_idx], X[list(chosen_set)])
            min_dist = d.min(axis=1)
            pick = int(rem_idx[np.argmax(min_dist)])
            extra.append(pick)
            chosen_set.add(pick)
            remaining.remove(pick)
            n_extra -= 1

        return extra

    # --------------------------------------------------------
    # Snapshot collection for visualization
    # --------------------------------------------------------

    def _collect_snapshot(self, batch_indices: List[int]) -> None:
        """Record surrogate predictions for ALL candidates at this round."""
        assert self.accuracy_surrogate is not None

        X_all = self.candidates[self.selected_feature_cols]
        mu_A, std_A = self.accuracy_surrogate.predict(X_all, return_std=True)

        unevaluated_mask = ~self.candidates["_evaluated"].to_numpy()
        unevaluated_X = self.candidates.loc[unevaluated_mask, self.selected_feature_cols]
        if len(unevaluated_X) > 0:
            mu_A_uneval, std_A_uneval = self.accuracy_surrogate.predict(
                unevaluated_X, return_std=True
            )
            if self.best_feasible_accuracy is None:
                acq = mu_A_uneval + self.config.exploration_weight * std_A_uneval
            else:
                acq = expected_improvement_maximization(
                    mu=mu_A_uneval, sigma=std_A_uneval,
                    best=self.best_feasible_accuracy,
                )
        else:
            acq = np.array([])

        self.round_snapshots.append({
            "round": len(self.round_snapshots) + 1,
            "num_evaluated": int(self.num_evaluated),
            "batch_indices": list(batch_indices),
            "all_mu_accuracy": mu_A.copy(),
            "all_std_accuracy": std_A.copy(),
            "all_prob_feasible": np.ones(len(self.candidates)),  # all feasible
            "all_acq_score": acq.copy(),
            "best_feasible_accuracy": self.best_feasible_accuracy,
            "selected_feature_cols": list(self.selected_feature_cols),
        })

    # --------------------------------------------------------
    # Utilities
    # --------------------------------------------------------

    def _infer_features(
        self,
        continuous_cols: Optional[Sequence[str]],
        categorical_cols: Optional[Sequence[str]],
    ) -> Tuple[List[str], List[str], List[str]]:
        reserved = {self.candidate_id_col, "_evaluated", "_latency", "_accuracy"}

        if continuous_cols is None and categorical_cols is None:
            inferred_cont = []
            inferred_cat = []
            for c in self.candidates.columns:
                if c in reserved:
                    continue
                if pd.api.types.is_numeric_dtype(self.candidates[c]):
                    inferred_cont.append(c)
                else:
                    inferred_cat.append(c)
            return inferred_cont + inferred_cat, inferred_cont, inferred_cat

        cont = list(continuous_cols or [])
        cat = list(categorical_cols or [])
        return cont + cat, cont, cat

    @property
    def num_evaluated(self) -> int:
        return int(self.candidates["_evaluated"].sum())

    def _diversity_bonus(self, X_pool: pd.DataFrame, X_chosen: pd.DataFrame) -> np.ndarray:
        prep = make_preprocessor(
            [c for c in self.selected_feature_cols if c in self.continuous_cols],
            [c for c in self.selected_feature_cols if c in self.categorical_cols],
        )
        pool_mat = prep.fit_transform(X_pool)
        chosen_mat = prep.transform(X_chosen)

        if hasattr(pool_mat, "toarray"):
            pool_mat = pool_mat.toarray()
        if hasattr(chosen_mat, "toarray"):
            chosen_mat = chosen_mat.toarray()

        d = pairwise_distances(pool_mat, chosen_mat)
        min_d = d.min(axis=1)
        if np.max(min_d) <= 0:
            return np.ones_like(min_d)
        return min_d / np.max(min_d)


# ============================================================
# Surrogate wrapper
# ============================================================

class BootstrapEnsembleRegressor:
    def __init__(self, base_estimator, n_estimators: int = 10, random_state: int = 42):
        self.base_estimator = base_estimator
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.estimators_: List = []

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        self.estimators_ = []
        rng = np.random.default_rng(self.random_state)
        n = len(X)
        if n == 0:
            raise ValueError("Empty training set.")
        for _ in range(self.n_estimators):
            sample_idx = rng.integers(0, n, size=n)
            est = clone(self.base_estimator)
            est.fit(X.iloc[sample_idx], y[sample_idx])
            self.estimators_.append(est)
        return self

    def predict(self, X: pd.DataFrame, return_std: bool = False):
        preds = np.column_stack([est.predict(X) for est in self.estimators_])
        mu = preds.mean(axis=1)
        if not return_std:
            return mu
        std = preds.std(axis=1, ddof=1) if preds.shape[1] > 1 else np.zeros(len(mu))
        std = np.maximum(std, 1e-9)
        return mu, std


# ============================================================
# Math helpers
# ============================================================

def normal_pdf(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z**2) / math.sqrt(2.0 * math.pi)


def normal_cdf(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


def expected_improvement_maximization(
    mu: np.ndarray, sigma: np.ndarray, best: float,
) -> np.ndarray:
    sigma = np.maximum(sigma, 1e-9)
    z = (mu - best) / sigma
    return (mu - best) * normal_cdf(z) + sigma * normal_pdf(z)


def make_preprocessor(
    continuous_cols: Sequence[str], categorical_cols: Sequence[str],
) -> ColumnTransformer:
    cont_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    cat_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(
        transformers=[
            ("cont", cont_pipe, list(continuous_cols)),
            ("cat", cat_pipe, list(categorical_cols)),
        ],
        remainder="drop",
    )


# ============================================================
# Evaluator
# ============================================================

def synthetic_accuracy_noiseless(row: pd.Series) -> float:
    """Deterministic component of synthetic accuracy (ground truth for oracle)."""
    log_params = np.log10(max(row["non_embedding_params"], 1e5))
    is_emb = int(row.get("is_embedding_tuned", 0))
    return 0.55 + 0.03 * log_params + 0.01 * is_emb


def synthetic_accuracy(row: pd.Series) -> float:
    """Synthetic accuracy for --dry_run mode (with observation noise)."""
    return synthetic_accuracy_noiseless(row) + np.random.normal(0, 0.01)


def find_cdf_file(model: str, args) -> Optional[str]:
    """Locate the CDF CSV produced by run_different_llms.sh mode 1."""
    model_safe = model.replace("/", "-")
    train_wl = TRAIN_WORKLOAD_MAP.get(args.workload, args.workload)
    results_base = (
        f"results/{args.db}/results_Train_{train_wl}_Test_{args.workload}_ours"
    )
    pattern = (
        f"{results_base}/time_llm_pretrained-None_1.0_cdf_{args.db}_*"
        f"_{model_safe}_emb{args.embed_size}*_seed42.csv"
    )
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return matches[0] if matches else None


def parse_qerror(csv_path: str) -> Dict[str, float]:
    """Parse Q-error percentiles from a CDF CSV (same as parse_qerror.py)."""
    df = pd.read_csv(csv_path).sort_values("percentage")
    result = {}
    for q in [50, 90, 95]:
        sub = df[df["percentage"] >= q]
        if not sub.empty:
            result[f"p{q}"] = float(sub.iloc[0]["Qerror"])
        else:
            result[f"p{q}"] = float(df["Qerror"].max())
    result["max"] = float(df["Qerror"].max())
    return result


def make_evaluator(args):
    """Return an evaluator function closed over args."""

    def evaluator(row: pd.Series) -> Tuple[float, float]:
        latency = float(row["avg_ms"])

        if args.dry_run:
            return latency, synthetic_accuracy(row)

        # Real evaluation: check for cached CDF first
        model = row["model"]
        cached_cdf = find_cdf_file(model, args)
        if cached_cdf is not None:
            qerror = parse_qerror(cached_cdf)
            accuracy = -qerror["p90"]
            print(f"  {model}: CACHED latency={latency:.1f}ms, p90={qerror['p90']:.2f}", flush=True)
            return latency, accuracy

        # No cache — run inference via run_different_llms.sh
        price_s_flag = ["--price_s"] if args.price_s else []
        cmd = [
            "bash", str(SCRIPT_DIR / "run_different_llms.sh"),
            "--models", model,
            "--workloads", args.workload,
            "--task", args.task,
            "--finetune_mode", "1",
            "--seeds", "42",
            "--db", args.db,
            "--quantification", args.quantification,
            "--embed_size", str(args.embed_size),
            "--downstream", "mlp",
            "--bucketize", "None",
            "--concat_true", "false",
            "--removed_fields", "",
        ] + price_s_flag

        env = {**os.environ, "MAX_QUERIES": str(args.max_eval_queries)}
        print(f"  Evaluating {model} ...", flush=True)
        # Stream subprocess output to terminal for visibility
        result = subprocess.run(
            cmd, env=env, stdout=sys.stdout, stderr=sys.stderr, text=True,
        )
        if result.returncode != 0:
            print(f"  WARNING: Inference failed for {model} (exit code {result.returncode})", flush=True)
            return latency, float("-inf")

        cdf_file = find_cdf_file(model, args)
        if cdf_file is None:
            print(f"  WARNING: CDF file not found for {model}", flush=True)
            return latency, float("-inf")

        qerror = parse_qerror(cdf_file)
        accuracy = -qerror["p90"]  # Negate: higher = better
        print(f"  {model}: latency={latency:.1f}ms, p90={qerror['p90']:.2f}", flush=True)
        return latency, accuracy

    return evaluator


# ============================================================
# Data loading
# ============================================================

def load_candidates(csv_path: str) -> pd.DataFrame:
    """Load model profile CSV and prepare features."""
    df = pd.read_csv(csv_path)

    # Filter to status=ok only
    if "status" in df.columns:
        df = df[df["status"] == "ok"].copy()

    # Convert boolean strings to 0/1
    bool_cols = [
        "is_embedding_tuned", "is_instruction_tuned", "is_multilingual",
        "is_cased", "deduped_variant",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({"True": 1, "False": 0, True: 1, False: 0}).fillna(0).astype(int)

    # Ensure numeric columns are numeric
    numeric_cols = [
        "non_embedding_params", "embedding_params", "total_params",
        "num_layers", "hidden_size", "attention_heads", "ffn_width",
        "context_length", "embedding_dimension", "avg_ms",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with missing essential fields
    df = df.dropna(subset=["model", "avg_ms", "non_embedding_params"])

    return df.reset_index(drop=True)


# ============================================================
# Oracle comparison (dry run)
# ============================================================

def oracle_comparison(result: SearchResult, all_candidates: pd.DataFrame, config: SearchConfig):
    """Compare search result against noise-free oracle over ALL models."""
    print("\n===== ORACLE COMPARISON =====")

    # Compute noise-free ground truth for every model
    oracle_data = []
    for _, row in all_candidates.iterrows():
        lat = float(row["avg_ms"])
        acc = synthetic_accuracy_noiseless(row)
        oracle_data.append({
            "model": row["model"],
            "latency": lat,
            "accuracy": acc,
            "feasible": lat <= config.latency_limit,
        })

    oracle_df = pd.DataFrame(oracle_data)
    feasible_oracle = oracle_df[oracle_df["feasible"]].sort_values("accuracy", ascending=False)

    if feasible_oracle.empty:
        print("No feasible models exist under the latency limit.")
        return {}

    oracle_best = feasible_oracle.iloc[0]
    print(f"Oracle best (noiseless): {oracle_best['model']} "
          f"(acc={oracle_best['accuracy']:.4f}, lat={oracle_best['latency']:.1f}ms)")
    print(f"Feasible pool size: {len(feasible_oracle)}")

    comparison = {
        "oracle_best_model": oracle_best["model"],
        "oracle_best_accuracy": float(oracle_best["accuracy"]),
        "oracle_best_latency": float(oracle_best["latency"]),
        "feasible_pool_size": int(len(feasible_oracle)),
    }

    if result.best_feasible_row is not None:
        selected = result.best_feasible_row
        # Look up the selected model's noiseless accuracy for fair comparison
        selected_noiseless = oracle_df[oracle_df["model"] == selected["model"]]["accuracy"].values
        if len(selected_noiseless) > 0:
            sel_acc = float(selected_noiseless[0])
        else:
            sel_acc = float(selected["_accuracy"])

        gap = oracle_best["accuracy"] - sel_acc
        rank = int((feasible_oracle["accuracy"] > sel_acc).sum()) + 1

        print(f"\nSelected:    {selected['model']}")
        print(f"  Noisy acc (observed):    {selected['_accuracy']:.4f}")
        print(f"  Noiseless acc (true):    {sel_acc:.4f}")
        print(f"  Latency:                 {selected['_latency']:.1f} ms")
        print(f"Accuracy gap from oracle:  {gap:.4f}")
        print(f"Rank among feasible:       {rank}/{len(feasible_oracle)}")
        print(f"Evaluations used:          {len(result.evaluated)}/{len(all_candidates)}")

        comparison.update({
            "selected_model": selected["model"],
            "selected_accuracy_observed": float(selected["_accuracy"]),
            "selected_accuracy_noiseless": sel_acc,
            "selected_latency": float(selected["_latency"]),
            "accuracy_gap": float(gap),
            "rank_among_feasible": rank,
            "evaluations_used": int(len(result.evaluated)),
            "total_candidates": int(len(all_candidates)),
        })
    else:
        print("\nSearch found no feasible model.")
        comparison["selected_model"] = None

    return comparison


# ============================================================
# CLI
# ============================================================

def parse_args():
    p = argparse.ArgumentParser(description="Surrogate-based model selection v2")

    # Search config
    p.add_argument("--latency_limit", type=float, required=True, help="Max inference latency (ms)")
    p.add_argument("--init_budget", type=int, default=24, help="Initial diverse evaluation budget")
    p.add_argument("--batch_size", type=int, default=4, help="Batch size per surrogate round")
    p.add_argument("--max_evals", type=int, default=80, help="Maximum total evaluations")
    p.add_argument("--random_state", type=int, default=42)

    # Evaluation
    p.add_argument("--workload", type=str, default="stats", help="Workload name")
    p.add_argument("--task", type=str, default="time", help="Prediction task")
    p.add_argument("--db", type=str, default="postgres", help="Database engine")
    p.add_argument("--quantification", type=str, default="4-bit")
    p.add_argument("--embed_size", type=int, default=1000)
    p.add_argument("--max_eval_queries", type=int, default=500, help="Max queries per eval")
    p.add_argument("--price_s", action="store_true", help="Enable PRICE stats injection")

    # Data
    p.add_argument("--csv", type=str, default=str(DEFAULT_CSV), help="Model profile CSV path")

    # Mode
    p.add_argument("--dry_run", action="store_true", help="Use synthetic accuracy (no GPU needed)")

    # Output
    p.add_argument("--output", type=str, default=None, help="Output JSON path")

    # Visualization
    p.add_argument("--visualize", action="store_true", default=None,
                   help="Generate search visualization (default: auto on --dry_run)")
    p.add_argument("--no_visualize", action="store_true",
                   help="Disable search visualization")

    return p.parse_args()


def main():
    args = parse_args()

    # Load candidates
    candidates = load_candidates(args.csv)
    print(f"Loaded {len(candidates)} candidate models from {args.csv}")

    # Verify feature columns exist
    available_cont = [c for c in CONTINUOUS_COLS if c in candidates.columns]
    available_cat = [c for c in CATEGORICAL_COLS if c in candidates.columns]
    missing = [c for c in CONTINUOUS_COLS + CATEGORICAL_COLS if c not in candidates.columns]
    if missing:
        print(f"Warning: missing columns (ignored): {missing}")
    print(f"Features: {len(available_cont)} continuous, {len(available_cat)} categorical")

    # Build config
    config = SearchConfig(
        latency_limit=args.latency_limit,
        init_budget=args.init_budget,
        batch_size=args.batch_size,
        max_evals=args.max_evals,
        random_state=args.random_state,
    )

    # Build evaluator
    evaluator = make_evaluator(args)

    # Run search
    search = ConstrainedModelSearch(
        candidates=candidates,
        evaluator=evaluator,
        config=config,
        candidate_id_col="model",
        continuous_cols=available_cont + ["log_non_embedding_params"],
        categorical_cols=available_cat,
    )

    print(f"\nStarting surrogate search (limit={config.latency_limit}ms, "
          f"init={config.init_budget}, batch={config.batch_size}, max={config.max_evals})")
    result = search.run()

    # Report
    print(f"\n===== SEARCH COMPLETE =====")
    print(f"Evaluated: {len(result.evaluated)} models")

    output = {
        "config": {
            "latency_limit": config.latency_limit,
            "init_budget": config.init_budget,
            "batch_size": config.batch_size,
            "max_evals": config.max_evals,
            "dry_run": args.dry_run,
            "workload": args.workload,
        },
        "selected_feature_names": result.selected_feature_names,
        "num_evaluated": int(len(result.evaluated)),
        "history": result.history,
    }

    if result.best_feasible_row is not None:
        best = result.best_feasible_row
        print(f"Best feasible: {best['model']}")
        print(f"  Latency: {best['_latency']:.1f} ms")
        print(f"  Accuracy: {best['_accuracy']:.4f}")
        output["selected_model"] = best["model"]
        output["selected_latency_ms"] = float(best["_latency"])
        output["selected_accuracy"] = float(best["_accuracy"])
    else:
        print("No feasible model found under the latency budget.")
        output["selected_model"] = None
        output["selected_latency_ms"] = None
        output["selected_accuracy"] = None

    print(f"\nSelected features: {result.selected_feature_names}")

    # Oracle comparison for dry run
    oracle = None
    if args.dry_run:
        oracle = oracle_comparison(result, candidates, config)
        output["oracle_comparison"] = oracle

    # Visualization
    do_visualize = args.visualize if args.visualize is not None else (args.dry_run and not args.no_visualize)
    if do_visualize:
        try:
            from visualize_search import visualize_search
        except ImportError:
            sys.path.insert(0, str(SCRIPT_DIR))
            from visualize_search import visualize_search
        viz_path = Path("model_selection_v2_search.png").resolve()
        visualize_search(result, candidates, config, oracle_data=oracle, output_path=str(viz_path))
        print(f"Visualization saved to {viz_path}")

    # Write output
    out_path = args.output
    if out_path is None:
        out_path = f"model_selection_v2_result_{args.workload}_{int(config.latency_limit)}ms.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
