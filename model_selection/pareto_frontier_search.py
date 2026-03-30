
"""
pareto_frontier_search.py

A heavily commented implementation of a surrogate-guided algorithm for
recovering the latency-accuracy Pareto frontier over a large discrete model pool.

Design philosophy
-----------------
This module is built for the setting where:

1) Latency for *all* candidate models is already known offline.
   Therefore, we do NOT fit a latency surrogate.
   Latency is treated as a fixed attribute of each candidate.

2) Accuracy is expensive to obtain.
   Therefore, we fit a surrogate only for accuracy.

3) We do not just want "the single best model under a latency limit".
   Instead, we want to *recover the Pareto frontier*:
   the set of non-dominated models in the (latency, accuracy) plane.

4) Each candidate is evaluated at most once.
   This is not a bandit-style repeated-pull setting. It is a sequential
   experimental-design / pool-based selection problem.

High-level algorithm
--------------------
At a high level, the algorithm does this:

    a) Start with a diverse seed set of models.
    b) Evaluate their true accuracy.
    c) Build the *observed* Pareto frontier from those evaluations.
    d) Fit a bootstrap-ensemble surrogate for accuracy from metadata.
    e) For each unevaluated candidate:
          - use the candidate's KNOWN latency
          - predict mean/std of accuracy
          - compare against the current observed frontier at that latency
          - score the candidate by expected frontier improvement
            (EI relative to the frontier envelope, not relative to one global best)
          - optionally add a "coverage bonus" for large frontier gaps
    f) Select a diverse batch of candidates with high acquisition score.
    g) Evaluate them, update the frontier, refit the surrogate, repeat.

This is "EHVI-inspired" but specialized to the much simpler case where
latency is known exactly for every candidate. In this setting, full general
2D EHVI machinery is often overkill. A candidate improves the frontier only
if it beats the current observed frontier envelope at *its own known latency*.

So we define the core acquisition as:

    frontier_best(latency) = best observed frontier accuracy achievable
                             at that latency or lower

    acquisition(x) = E[max(A(x) - frontier_best(L(x)), 0)]

where A(x) is the surrogate's predictive distribution for accuracy and
L(x) is the candidate's known offline latency.

This is just Expected Improvement, but the "best" value is not global.
It is *latency-specific* via the current Pareto frontier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import math
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


@dataclass
class SearchConfig:
    init_budget: int = 20
    batch_size: int = 4
    max_evals: int = 60
    random_state: int = 42

    exploration_weight: float = 0.15
    coverage_weight: float = 0.30
    diversity_weight: float = 1.5
    family_weight: float = 0.8

    ensemble_size: int = 10
    rf_num_trees: int = 300
    rf_min_samples_leaf: int = 2

    enable_feature_filtering: bool = True
    feature_filter_after: int = 24
    keep_top_k_features: Optional[int] = 12

    patience_rounds: int = 4
    min_relative_frontier_gain: float = 1e-4
    n_init_clusters: Optional[int] = None
    min_sigma: float = 1e-9
    surrogate_quality_threshold: float = 0.3

    # Initialization parameters
    anchor_init: bool = False
    latency_weight: float = 5.0
    feature_weight: float = 3.0


@dataclass
class SearchResult:
    evaluated: pd.DataFrame
    observed_frontier: pd.DataFrame
    history: List[Dict]
    selected_feature_names: List[str] = field(default_factory=list)
    round_snapshots: List[Dict] = field(default_factory=list)


class ParetoFrontierSearch:
    def __init__(
        self,
        candidates: pd.DataFrame,
        evaluator: Callable[[pd.Series], float],
        config: SearchConfig,
        latency_col: str = "avg_ms",
        candidate_id_col: str = "model_id",
        continuous_cols: Optional[Sequence[str]] = None,
        categorical_cols: Optional[Sequence[str]] = None,
    ) -> None:
        if candidate_id_col not in candidates.columns:
            raise ValueError(f"Missing candidate_id_col={candidate_id_col!r}")
        if latency_col not in candidates.columns:
            raise ValueError(f"Missing latency_col={latency_col!r}")

        self.config = config
        self.latency_col = latency_col
        self.candidate_id_col = candidate_id_col
        self.evaluator = evaluator
        self.rng = np.random.default_rng(config.random_state)

        self.candidates = candidates.copy().reset_index(drop=True)
        self.candidates["_evaluated"] = False
        self.candidates["_accuracy"] = np.nan

        if "non_embedding_params" in self.candidates.columns:
            eps = 1e-12
            self.candidates["log_non_embedding_params"] = np.log(
                self.candidates["non_embedding_params"].astype(float).clip(lower=eps)
            )

        self.feature_cols_all, self.continuous_cols, self.categorical_cols = self._infer_features(
            continuous_cols, categorical_cols
        )
        self.selected_feature_cols = list(self.feature_cols_all)

        self.accuracy_surrogate: Optional[BootstrapEnsembleRegressor] = None
        self.surrogate_quality: float = 0.0
        self.family_col: Optional[str] = (
            "model_family" if "model_family" in self.candidates.columns else None
        )
        self.history: List[Dict] = []
        self.round_snapshots: List[Dict] = []
        self.best_hypervolume: float = 0.0
        self.rounds_without_improvement = 0

    def run(self) -> SearchResult:
        self._initialize_seed_set()
        self.best_hypervolume = self._current_hypervolume()

        while True:
            if self._should_stop():
                break

            self._fit_surrogate()

            if (
                self.config.enable_feature_filtering
                and self.num_evaluated >= self.config.feature_filter_after
            ):
                changed = self._feature_filter()
                if changed:
                    self._fit_surrogate()

            batch_indices = self._select_batch()
            if len(batch_indices) == 0:
                break

            self._collect_snapshot(batch_indices)
            self._evaluate_ids(batch_indices)

            new_hv = self._current_hypervolume()
            rel_gain = (
                (new_hv - self.best_hypervolume) / max(abs(self.best_hypervolume), 1e-12)
                if self.best_hypervolume > 0
                else float(new_hv > 0)
            )

            if rel_gain > self.config.min_relative_frontier_gain:
                self.best_hypervolume = new_hv
                self.rounds_without_improvement = 0
            else:
                self.rounds_without_improvement += 1

        evaluated = self.candidates[self.candidates["_evaluated"]].copy()
        frontier = self._observed_frontier()

        return SearchResult(
            evaluated=evaluated,
            observed_frontier=frontier,
            history=self.history,
            selected_feature_names=self.selected_feature_cols,
            round_snapshots=self.round_snapshots,
        )

    def _initialize_seed_set(self) -> None:
        init_ids = self._diverse_initialization_ids(self.config.init_budget)
        self._evaluate_ids(init_ids)

    def _diverse_initialization_ids(self, budget: int) -> List[int]:
        """Select a diverse seed set via anchor-and-fill or maximin in
        latency-weighted feature space.

        When ``anchor_init`` is True (default), the algorithm:
        1. Anchors the two latency extremes (min & max) to guarantee
           full-range coverage.
        2. Fills the rest with greedy farthest-point in a feature space
           where model metadata is scaled by ``feature_weight`` and
           latency by ``latency_weight``.

        The anchor-and-fill approach is deterministic (seed-independent)
        and eliminates the variance caused by random starting points.
        It significantly improves Pareto frontier recovery because it
        guarantees coverage of sparse latency regions that random methods
        frequently miss.

        When ``anchor_init`` is False, falls back to randomized maximin
        (random starting point, same farthest-point fill).
        """
        budget = min(budget, len(self.candidates))

        X = self._initialization_embedding(self.candidates)
        X = X * self.config.feature_weight

        # Add latency as a weighted extra dimension
        latencies = self.candidates[self.latency_col].to_numpy()
        lat_range = latencies.max() - latencies.min()
        if lat_range > 0:
            lat_scaled = (latencies - latencies.min()) / lat_range
        else:
            lat_scaled = np.zeros_like(latencies)
        X_aug = np.column_stack([X, lat_scaled * self.config.latency_weight])

        if self.config.anchor_init:
            # Anchor at latency extremes
            anchors = [int(np.argmin(latencies)), int(np.argmax(latencies))]
            chosen = list(dict.fromkeys(anchors))  # deduplicate, preserve order
        else:
            # Random starting point (old behavior)
            start = int(self.rng.integers(0, len(X_aug)))
            chosen = [start]

        chosen = chosen + self._greedy_farthest_fill(X_aug, chosen, budget - len(chosen))
        return chosen[:budget]

    def _initialization_embedding(self, df: pd.DataFrame) -> np.ndarray:
        prep = make_preprocessor(self.continuous_cols, self.categorical_cols)
        X = prep.fit_transform(df[self.feature_cols_all])
        if hasattr(X, "toarray"):
            X = X.toarray()
        return np.asarray(X, dtype=float)

    def _greedy_farthest_fill(self, X: np.ndarray, chosen: List[int], n_extra: int) -> List[int]:
        remaining = [i for i in range(len(X)) if i not in chosen]
        extra: List[int] = []
        chosen_set = set(chosen)

        while n_extra > 0 and remaining:
            rem_idx = np.array(remaining, dtype=int)
            if not chosen_set:
                pick = int(self.rng.choice(rem_idx))
            else:
                d = pairwise_distances(X[rem_idx], X[list(chosen_set)])
                min_dist = d.min(axis=1)
                pick = int(rem_idx[np.argmax(min_dist)])
            extra.append(pick)
            chosen_set.add(pick)
            remaining.remove(pick)
            n_extra -= 1
        return extra

    def _evaluate_ids(self, row_indices: Sequence[int]) -> None:
        for idx in row_indices:
            row = self.candidates.loc[idx]
            accuracy = float(self.evaluator(row))
            latency = float(row[self.latency_col])

            self.candidates.at[idx, "_evaluated"] = True
            self.candidates.at[idx, "_accuracy"] = accuracy

            self.history.append(
                {
                    "candidate_id": row[self.candidate_id_col],
                    "row_index": int(idx),
                    "latency": latency,
                    "accuracy": accuracy,
                    "num_evaluated": int(self.num_evaluated),
                }
            )

    def _fit_surrogate(self) -> None:
        train_df = self.candidates[self.candidates["_evaluated"]].copy()
        train_df = train_df[np.isfinite(train_df["_accuracy"])]
        if len(train_df) == 0:
            raise RuntimeError("No successful evaluations available for surrogate fitting.")

        X = train_df[self.selected_feature_cols]
        y = train_df["_accuracy"].to_numpy()

        cont_cols = [c for c in self.selected_feature_cols if c in self.continuous_cols]
        cat_cols = [c for c in self.selected_feature_cols if c in self.categorical_cols]

        preprocessor = make_preprocessor(cont_cols, cat_cols)
        base_estimator = Pipeline(
            steps=[
                ("prep", preprocessor),
                ("model", RandomForestRegressor(
                    n_estimators=self.config.rf_num_trees,
                    min_samples_leaf=self.config.rf_min_samples_leaf,
                    random_state=self.config.random_state,
                    n_jobs=-1,
                )),
            ]
        )

        self.accuracy_surrogate = BootstrapEnsembleRegressor(
            base_estimator=base_estimator,
            n_estimators=self.config.ensemble_size,
            random_state=self.config.random_state + 100,
        ).fit(X, y)

    def _estimate_surrogate_quality(
        self, X: pd.DataFrame, y: np.ndarray,
        cont_cols: List[str], cat_cols: List[str],
    ) -> float:
        """Leave-one-out Spearman correlation to assess whether the surrogate
        provides useful ranking information."""
        from scipy.stats import spearmanr
        n = len(y)
        if n < 6:
            return 0.0
        loo_preds = np.full(n, np.nan)
        for i in range(n):
            mask = np.ones(n, dtype=bool)
            mask[i] = False
            prep = make_preprocessor(cont_cols, cat_cols)
            rf = RandomForestRegressor(
                n_estimators=50, min_samples_leaf=2,
                random_state=self.config.random_state, n_jobs=-1,
            )
            pipe = Pipeline([("prep", prep), ("model", rf)])
            pipe.fit(X.iloc[mask], y[mask])
            loo_preds[i] = pipe.predict(X.iloc[[i]])[0]
        valid = np.isfinite(loo_preds)
        if valid.sum() < 5:
            return 0.0
        rho, _ = spearmanr(loo_preds[valid], y[valid])
        return float(rho) if np.isfinite(rho) else 0.0

    def _feature_filter(self) -> bool:
        assert self.accuracy_surrogate is not None
        train_df = self.candidates[self.candidates["_evaluated"]].copy()
        train_df = train_df[np.isfinite(train_df["_accuracy"])]

        if len(train_df) < max(12, len(self.selected_feature_cols) + 2):
            return False

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
            return False

        importances = pd.Series(avg_importances, index=self.selected_feature_cols).sort_values(ascending=False)
        if self.config.keep_top_k_features is None:
            keep = importances[importances > 0].index.tolist()
        else:
            keep = importances.head(min(self.config.keep_top_k_features, len(importances))).index.tolist()

        if len(keep) >= 2 and keep != self.selected_feature_cols:
            self.selected_feature_cols = keep
            return True
        return False

    def _score_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score unevaluated candidates using EI + coverage + family novelty.

        EI provides frontier-depth-aware scoring (models in weak frontier
        regions score higher).  Coverage bonus fills frontier gaps.
        Family novelty penalizes over-sampled model families.
        """
        assert self.accuracy_surrogate is not None

        scored = df.copy()
        X = scored[self.selected_feature_cols]

        mu_A, std_A = self.accuracy_surrogate.predict(X, return_std=True)
        std_A = np.maximum(std_A, self.config.min_sigma)

        scored["_mu_accuracy"] = mu_A
        scored["_std_accuracy"] = std_A

        frontier = self._observed_frontier()

        if self.num_evaluated >= 2 and not frontier.empty:
            baselines = np.array([self._frontier_envelope_at_latency(lat) for lat in scored[self.latency_col].to_numpy()])
            worst_frontier_acc = frontier["_accuracy"].min()
            below_mask = baselines <= -1e30
            baselines[below_mask] = worst_frontier_acc
            scored["_frontier_baseline"] = baselines
            acq = expected_improvement_maximization(mu=mu_A, sigma=std_A, best=baselines)
        else:
            scored["_frontier_baseline"] = np.nan
            acq = mu_A + self.config.exploration_weight * std_A

        coverage_bonus = np.array([self._coverage_bonus_at_latency(lat) for lat in scored[self.latency_col].to_numpy()])
        family_novelty = self._family_novelty_scores(scored)
        scored["_coverage_bonus"] = coverage_bonus
        scored["_acq_score"] = (
            acq
            + self.config.coverage_weight * coverage_bonus
            + self.config.family_weight * family_novelty
        )
        return scored.sort_values("_acq_score", ascending=False)

    def _family_novelty_scores(self, df: pd.DataFrame) -> np.ndarray:
        """Score each candidate by how novel its model family is among
        evaluated models.  Returns values in (0, 1]: families with no
        evaluated models get 1.0; heavily-sampled families get low scores."""
        if self.family_col is None or self.family_col not in df.columns:
            return np.ones(len(df))

        evaluated = self.candidates[self.candidates["_evaluated"]]
        if self.family_col not in evaluated.columns:
            return np.ones(len(df))
        family_counts = evaluated[self.family_col].value_counts().to_dict()

        novelty = np.array([
            1.0 / (1.0 + family_counts.get(fam, 0))
            for fam in df[self.family_col]
        ])
        # Normalize to [0, 1]
        max_n = novelty.max()
        if max_n > 0:
            novelty = novelty / max_n
        return novelty

    def _select_batch(self) -> List[int]:
        """Select a batch using acquisition score + latency gap-filling +
        model-family novelty.

        Greedily picks candidates that maximize:
            final = acq_norm + diversity_weight * lat_diversity
                             + family_weight * batch_family_novelty

        lat_diversity fills gaps in the overall evaluated set.
        batch_family_novelty penalizes picking from the same model family
        as already-chosen batch members (prevents e.g. 4 pythias).
        """
        unevaluated = self.candidates[~self.candidates["_evaluated"]].copy()
        if unevaluated.empty:
            return []

        scored = self._score_candidates(unevaluated)
        if scored.empty:
            return []

        batch_size = min(self.config.batch_size, len(scored))

        # Normalize acq_score to [0, 1]
        acq_vals = scored["_acq_score"].to_numpy()
        acq_range = acq_vals.max() - acq_vals.min()
        acq_norm = (acq_vals - acq_vals.min()) / acq_range if acq_range > 0 else np.ones_like(acq_vals)
        scored["_acq_norm"] = acq_norm

        chosen: List[int] = []
        remaining = scored.copy()

        for _ in range(batch_size):
            # Latency distance from all evaluated + within-batch models
            eval_lats = self.candidates[self.candidates["_evaluated"]][self.latency_col].to_numpy()
            if chosen:
                chosen_lats = np.array([self.candidates.loc[c, self.latency_col] for c in chosen])
                ref_lats = np.concatenate([eval_lats, chosen_lats])
            else:
                ref_lats = eval_lats

            cand_lats = remaining[self.latency_col].to_numpy()
            if len(ref_lats) > 0:
                lat_dists = np.min(np.abs(cand_lats[:, None] - ref_lats[None, :]), axis=1)
                max_d = lat_dists.max()
                lat_div = lat_dists / max_d if max_d > 0 else np.ones_like(lat_dists)
            else:
                lat_div = np.ones(len(cand_lats))

            # Family novelty: penalize families already chosen in this batch
            if chosen and self.family_col and self.family_col in remaining.columns:
                batch_families = [
                    self.candidates.loc[c, self.family_col] for c in chosen
                    if self.family_col in self.candidates.columns
                ]
                from collections import Counter
                batch_fam_counts = Counter(batch_families)
                fam_nov = np.array([
                    1.0 / (1.0 + batch_fam_counts.get(fam, 0))
                    for fam in remaining[self.family_col]
                ])
                max_fn = fam_nov.max()
                fam_nov = fam_nov / max_fn if max_fn > 0 else np.ones_like(fam_nov)
            else:
                fam_nov = np.zeros(len(remaining))

            remaining["_lat_diversity"] = lat_div
            remaining["_batch_family_nov"] = fam_nov
            remaining["_final_score"] = (
                remaining["_acq_norm"]
                + self.config.diversity_weight * remaining["_lat_diversity"]
                + self.config.family_weight * remaining["_batch_family_nov"]
            )
            pick_idx = int(remaining["_final_score"].idxmax())
            chosen.append(pick_idx)
            remaining = remaining.drop(index=pick_idx)
            if remaining.empty:
                break

        return chosen

    def _observed_frontier(self) -> pd.DataFrame:
        df = self.candidates[self.candidates["_evaluated"]].copy()
        df = df[np.isfinite(df["_accuracy"])]
        if df.empty:
            return df

        df = df.sort_values([self.latency_col, "_accuracy"], ascending=[True, False])
        best_so_far = -np.inf
        frontier_rows = []
        for _, row in df.iterrows():
            acc = float(row["_accuracy"])
            if acc > best_so_far:
                frontier_rows.append(row)
                best_so_far = acc
        return pd.DataFrame(frontier_rows).reset_index(drop=True)

    def _frontier_envelope_at_latency(self, latency: float) -> float:
        frontier = self._observed_frontier()
        if frontier.empty:
            return -np.inf
        eligible = frontier[frontier[self.latency_col] <= latency]
        if eligible.empty:
            return -np.inf
        return float(eligible["_accuracy"].max())

    def _coverage_bonus_at_latency(self, latency: float) -> float:
        frontier = self._observed_frontier()
        if len(frontier) < 2:
            return 1.0 if len(frontier) > 0 else 0.5

        lats = np.sort(frontier[self.latency_col].to_numpy())
        if latency <= lats[0]:
            gap = lats[1] - lats[0]
        elif latency >= lats[-1]:
            gap = lats[-1] - lats[-2]
        else:
            idx = np.searchsorted(lats, latency)
            gap = lats[idx] - lats[idx - 1]

        total_span = max(lats[-1] - lats[0], 1e-12)
        return float(gap / total_span)

    def _current_hypervolume(self, reference_latency: Optional[float] = None, reference_accuracy: Optional[float] = None) -> float:
        frontier = self._observed_frontier()
        if frontier.empty:
            return 0.0

        lats = frontier[self.latency_col].to_numpy()
        accs = frontier["_accuracy"].to_numpy()

        if reference_latency is None:
            reference_latency = float(self.candidates[self.latency_col].max()) * 1.05
        if reference_accuracy is None:
            reference_accuracy = min(float(frontier["_accuracy"].min()), 0.0)

        order = np.argsort(lats)
        lats = lats[order]
        accs = accs[order]

        hv = 0.0
        prev_latency = reference_latency
        for lat, acc in zip(lats[::-1], accs[::-1]):
            width = max(prev_latency - lat, 0.0)
            height = max(acc - reference_accuracy, 0.0)
            hv += width * height
            prev_latency = lat
        return float(hv)

    def _collect_snapshot(self, batch_indices: Sequence[int]) -> None:
        if self.accuracy_surrogate is None:
            return
        scored_all = self._score_candidates(self.candidates[~self.candidates["_evaluated"]].copy())
        self.round_snapshots.append(
            {
                "num_evaluated": self.num_evaluated,
                "batch_indices": list(map(int, batch_indices)),
                "selected_feature_cols": list(self.selected_feature_cols),
                "observed_frontier_ids": self._observed_frontier()[self.candidate_id_col].tolist(),
                "scored_unevaluated": scored_all[
                    [self.candidate_id_col, self.latency_col, "_mu_accuracy", "_std_accuracy", "_acq_score"]
                ].to_dict(orient="records"),
            }
        )

    def _should_stop(self) -> bool:
        if self.num_evaluated >= self.config.max_evals:
            return True
        if self.rounds_without_improvement >= self.config.patience_rounds:
            return True
        if (~self.candidates["_evaluated"]).sum() == 0:
            return True
        return False

    @property
    def num_evaluated(self) -> int:
        return int(self.candidates["_evaluated"].sum())

    def _infer_features(
        self,
        continuous_cols: Optional[Sequence[str]],
        categorical_cols: Optional[Sequence[str]],
    ) -> Tuple[List[str], List[str], List[str]]:
        reserved = {self.candidate_id_col, self.latency_col, "_evaluated", "_accuracy"}
        if continuous_cols is None and categorical_cols is None:
            inferred_cont, inferred_cat = [], []
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
        max_d = np.max(min_d)
        if max_d <= 0:
            return np.ones_like(min_d)
        return min_d / max_d


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
            raise ValueError("Cannot fit ensemble on empty dataset.")

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
        return mu, std


def normal_pdf(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z ** 2) / math.sqrt(2.0 * math.pi)

def normal_cdf(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))

def expected_improvement_maximization(mu: np.ndarray, sigma: np.ndarray, best) -> np.ndarray:
    sigma = np.maximum(sigma, 1e-9)
    best = np.asarray(best)
    z = (mu - best) / sigma
    return (mu - best) * normal_cdf(z) + sigma * normal_pdf(z)

def make_preprocessor(
    continuous_cols: Sequence[str],
    categorical_cols: Sequence[str],
) -> ColumnTransformer:
    cont_pipe = Pipeline(
        steps=[("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    cat_pipe = Pipeline(
        steps=[("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]
    )
    return ColumnTransformer(
        transformers=[("cont", cont_pipe, list(continuous_cols)), ("cat", cat_pipe, list(categorical_cols))],
        remainder="drop",
    )


def synthetic_accuracy_evaluator(row: pd.Series) -> float:
    params = float(row.get("num_params", 1e8))
    latency = float(row.get("avg_ms", 10.0))
    family = str(row.get("family", "unknown"))
    embedding_tuned = int(row.get("is_embedding_tuned", 0))

    acc = (
        0.55
        + 0.03 * np.log10(max(params, 1e5))
        + 0.01 * embedding_tuned
        + (0.015 if family == "modernbert" else 0.0)
        - 0.0004 * max(latency - 30.0, 0.0)
        + np.random.normal(0, 0.012)
    )
    return float(acc)


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    demo = pd.DataFrame(
        {
            "model_id": [f"m{i}" for i in range(200)],
            "avg_ms": np.sort(rng.uniform(2, 80, size=200)),
            "num_params": np.exp(rng.uniform(np.log(5e5), np.log(1e9), size=200)),
            "num_layers": rng.choice([2, 4, 6, 8, 12, 16, 24], size=200),
            "hidden_size": rng.choice([128, 256, 384, 512, 768, 1024, 1536], size=200),
            "num_heads": rng.choice([2, 4, 6, 8, 12, 16], size=200),
            "ffn_width": rng.choice([512, 1024, 1536, 2048, 3072, 4096], size=200),
            "context_length": rng.choice([512, 1024, 2048, 4096, 8192], size=200),
            "embedding_dim": rng.choice([128, 256, 384, 512, 768, 1024], size=200),
            "arch_type": rng.choice(["encoder", "decoder"], size=200),
            "family": rng.choice(["minilm", "e5", "modernbert", "gte", "qwen", "bert", "tinybert"], size=200),
            "pooling_method": rng.choice(["mean", "cls", "last_token"], size=200),
            "tokenizer_behavior": rng.choice(["wordpiece", "bpe", "sentencepiece"], size=200),
            "is_embedding_tuned": rng.choice([0, 1], size=200),
            "multilingual": rng.choice([0, 1], size=200),
        }
    )

    cfg = SearchConfig(init_budget=20, batch_size=5, max_evals=60, random_state=7, keep_top_k_features=12)

    search = ParetoFrontierSearch(
        candidates=demo,
        evaluator=synthetic_accuracy_evaluator,
        config=cfg,
        latency_col="avg_ms",
        candidate_id_col="model_id",
        continuous_cols=[
            "avg_ms",
            "num_params",
            "num_layers",
            "hidden_size",
            "num_heads",
            "ffn_width",
            "context_length",
            "embedding_dim",
            "is_embedding_tuned",
            "multilingual",
        ],
        categorical_cols=["arch_type", "family", "pooling_method", "tokenizer_behavior"],
    )

    result = search.run()
    print("Evaluated:", len(result.evaluated))
    print("Frontier size:", len(result.observed_frontier))
    print(result.observed_frontier[["model_id", "avg_ms", "_accuracy"]].head())
