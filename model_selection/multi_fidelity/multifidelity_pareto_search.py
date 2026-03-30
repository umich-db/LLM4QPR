
from __future__ import annotations

"""
multifidelity_pareto_search.py

Formal implementation of a multi-fidelity Pareto-frontier search algorithm.

Main idea
---------
We want the Pareto frontier after full fine-tuning for R epochs, but full
fine-tuning every candidate is too expensive.

So we use a staged schedule:

Round 0:
    - select n models by maximin space-filling
    - fine-tune them to 1 epoch

Round r > 0:
    - among currently active models, compute the Pareto frontier using:
          latency  (known offline, minimize)
          accuracy (measured after current epoch count, maximize)
    - let target_keep = ceil(n / shrink_factor^r)
    - keep all frontier models
    - fill remaining slots with models nearest to the frontier
    - train the kept models one more epoch

If target_keep becomes no larger than the frontier size, or we reach the
last intermediate round, stop pruning and directly train the current
frontier models to the final target epoch.

This is a successive-halving-style algorithm specialized to Pareto recovery.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import math
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import pairwise_distances
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class MFSearchConfig:
    init_count: int
    total_epochs: int
    shrink_factor: float = 2.0
    frontier_distance: str = "pareto_gap"   # or "euclidean"
    always_keep_frontier: bool = True
    exploration_reserve: float = 0.0        # fraction of extra slots reserved for diversity
    feature_weight: float = 3.0
    latency_weight: float = 5.0
    random_state: int = 42


@dataclass
class MFSearchResult:
    evaluated_table: pd.DataFrame
    final_frontier: pd.DataFrame
    round_history: List[Dict] = field(default_factory=list)
    total_epoch_budget_used: int = 0


class MultiFidelityParetoSearch:
    def __init__(
        self,
        candidates: pd.DataFrame,
        trainer: Callable[[pd.Series, int, int], float],
        config: MFSearchConfig,
        latency_col: str = "avg_ms",
        candidate_id_col: str = "model_id",
        continuous_cols: Optional[Sequence[str]] = None,
        categorical_cols: Optional[Sequence[str]] = None,
    ) -> None:
        if latency_col not in candidates.columns:
            raise ValueError(f"Missing latency column: {latency_col}")
        if candidate_id_col not in candidates.columns:
            raise ValueError(f"Missing candidate id column: {candidate_id_col}")
        if config.total_epochs < 1:
            raise ValueError("total_epochs must be >= 1")

        self.candidates = candidates.copy().reset_index(drop=True)
        self.trainer = trainer
        self.config = config
        self.latency_col = latency_col
        self.candidate_id_col = candidate_id_col
        self.rng = np.random.default_rng(config.random_state)

        self.feature_cols_all, self.continuous_cols, self.categorical_cols = self._infer_features(
            continuous_cols, categorical_cols
        )

        # Search state
        self.candidates["_current_epoch"] = 0
        self.candidates["_accuracy"] = np.nan
        self.candidates["_active"] = False
        self.candidates["_ever_selected"] = False

        self.round_history: List[Dict] = []
        self.total_epoch_budget_used = 0

    # ----------------------------
    # Public API
    # ----------------------------
    def run(self) -> MFSearchResult:
        # Round 0: space-filling init, train to epoch 1
        init_indices = self._space_filling_init(self.config.init_count)
        self._advance_models(init_indices, target_epoch=1)
        self._set_active(init_indices)
        self._record_round(round_id=0, selected_indices=init_indices, stop_pruning=False)

        # Intermediate pruning / promotion rounds
        for round_id in range(1, self.config.total_epochs):
            active = self.candidates[self.candidates["_active"]].copy()
            if active.empty:
                break

            frontier = self._observed_frontier(active)
            frontier_indices = frontier.index.tolist()

            target_keep = math.ceil(self.config.init_count / (self.config.shrink_factor ** round_id))
            if self.config.always_keep_frontier:
                target_keep = max(target_keep, len(frontier_indices))

            stop_pruning = (target_keep <= len(frontier_indices)) or (round_id == self.config.total_epochs - 1)

            if stop_pruning:
                final_indices = frontier_indices
                self._advance_models(final_indices, target_epoch=self.config.total_epochs)
                self._set_active(final_indices)
                self._record_round(round_id=round_id, selected_indices=final_indices, stop_pruning=True)
                break

            chosen = list(frontier_indices)
            remaining_budget = target_keep - len(chosen)

            if remaining_budget > 0:
                others = active.drop(index=chosen)
                ranked = self._rank_by_frontier_nearness(others, frontier)

                reserve = int(math.floor(self.config.exploration_reserve * remaining_budget))
                reserve = min(reserve, remaining_budget)
                exploit_count = remaining_budget - reserve

                exploit_indices = ranked.head(exploit_count).index.tolist()
                chosen.extend(exploit_indices)

                if reserve > 0:
                    leftovers = others.drop(index=exploit_indices)
                    explore_indices = self._choose_diverse_subset(leftovers, reserve)
                    chosen.extend(explore_indices)

            self._advance_models(chosen, target_epoch=round_id + 1)
            self._set_active(chosen)
            self._record_round(round_id=round_id, selected_indices=chosen, stop_pruning=False)

        final_frontier = self._observed_frontier(
            self.candidates[np.isfinite(self.candidates["_accuracy"])].copy()
        )
        return MFSearchResult(
            evaluated_table=self.candidates.copy(),
            final_frontier=final_frontier,
            round_history=self.round_history,
            total_epoch_budget_used=self.total_epoch_budget_used,
        )

    # ----------------------------
    # Initialization
    # ----------------------------
    def _space_filling_init(self, n: int) -> List[int]:
        """
        Weighted stochastic maximin in metadata + latency space.

        Steps:
        1. preprocess continuous/categorical metadata
        2. scale metadata by feature_weight
        3. append normalized latency scaled by latency_weight
        4. pick a random start
        5. repeatedly add the point farthest from the selected set
        """
        n = min(n, len(self.candidates))
        emb = self._build_augmented_embedding(self.candidates)

        first = int(self.rng.integers(0, len(self.candidates)))
        chosen = [first]

        while len(chosen) < n:
            remaining = [i for i in range(len(self.candidates)) if i not in chosen]
            rem_idx = np.array(remaining, dtype=int)
            dmat = pairwise_distances(emb[rem_idx], emb[chosen])
            min_dist = dmat.min(axis=1)
            pick = int(rem_idx[np.argmax(min_dist)])
            chosen.append(pick)

        return chosen

    # ----------------------------
    # Training / bookkeeping
    # ----------------------------
    def _advance_models(self, indices: Sequence[int], target_epoch: int) -> None:
        for idx in indices:
            row = self.candidates.loc[idx]
            current_epoch = int(row["_current_epoch"])
            if current_epoch >= target_epoch:
                continue

            # trainer should warm-start from current_epoch if possible
            acc = float(self.trainer(row, target_epoch, current_epoch))
            self.candidates.at[idx, "_current_epoch"] = target_epoch
            self.candidates.at[idx, "_accuracy"] = acc
            self.candidates.at[idx, "_ever_selected"] = True
            self.total_epoch_budget_used += (target_epoch - current_epoch)

    def _set_active(self, active_indices: Sequence[int]) -> None:
        self.candidates["_active"] = False
        self.candidates.loc[list(active_indices), "_active"] = True

    def _record_round(self, round_id: int, selected_indices: Sequence[int], stop_pruning: bool) -> None:
        active_df = self.candidates[self.candidates["_active"]].copy()
        frontier = self._observed_frontier(active_df)
        self.round_history.append(
            {
                "round_id": round_id,
                "selected_ids": self.candidates.loc[list(selected_indices), self.candidate_id_col].tolist(),
                "selected_count": len(selected_indices),
                "active_count_after_round": int(active_df.shape[0]),
                "frontier_count_after_round": int(frontier.shape[0]),
                "stop_pruning": bool(stop_pruning),
                "epochs_after_round": sorted(active_df["_current_epoch"].dropna().unique().tolist()),
            }
        )

    # ----------------------------
    # Pareto frontier utilities
    # ----------------------------
    def _observed_frontier(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute non-dominated points in (latency, accuracy), where:
            latency  -> minimize
            accuracy -> maximize

        In 2D, after sorting by latency ascending, frontier points are exactly
        those whose accuracy is a new running maximum.
        """
        if df.empty:
            return df.copy()

        work = df.copy()
        work = work[np.isfinite(work["_accuracy"])]
        if work.empty:
            return work

        work = work.sort_values([self.latency_col, "_accuracy"], ascending=[True, False])

        frontier_rows = []
        best_acc = -np.inf
        for _, row in work.iterrows():
            acc = float(row["_accuracy"])
            if acc > best_acc:
                frontier_rows.append(row)
                best_acc = acc

        # Preserve original indices so callers can use them for drop/lookup
        return pd.DataFrame(frontier_rows)

    def _rank_by_frontier_nearness(self, candidates: pd.DataFrame, frontier: pd.DataFrame) -> pd.DataFrame:
        """
        Rank dominated candidates by closeness to the current frontier.

        Recommended metric:
            pareto_gap = frontier_best(latency) - candidate_accuracy

        Smaller gap means the candidate is close to becoming non-dominated,
        so it is a good promotion candidate.
        """
        work = candidates.copy()

        if self.config.frontier_distance == "pareto_gap":
            lats = frontier[self.latency_col].to_numpy()
            accs = frontier["_accuracy"].to_numpy()

            order = np.argsort(lats)
            lats = lats[order]
            accs = accs[order]

            gaps = []
            for _, row in work.iterrows():
                lat = float(row[self.latency_col])
                acc = float(row["_accuracy"])

                eligible = np.where(lats <= lat)[0]
                if len(eligible) == 0:
                    frontier_best = -np.inf
                else:
                    frontier_best = float(accs[eligible].max())

                gap = frontier_best - acc if np.isfinite(frontier_best) else 0.0
                gaps.append(gap)

            work["_frontier_gap"] = np.array(gaps)
            return work.sort_values("_frontier_gap", ascending=True)

        elif self.config.frontier_distance == "euclidean":
            lat_min, lat_max = work[self.latency_col].min(), work[self.latency_col].max()
            acc_min, acc_max = work["_accuracy"].min(), work["_accuracy"].max()

            def norm(v, lo, hi):
                if hi <= lo:
                    return np.zeros_like(v, dtype=float)
                return (v - lo) / (hi - lo)

            cand_xy = np.column_stack([
                norm(work[self.latency_col].to_numpy(), lat_min, lat_max),
                norm(work["_accuracy"].to_numpy(), acc_min, acc_max),
            ])
            fr_xy = np.column_stack([
                norm(frontier[self.latency_col].to_numpy(), lat_min, lat_max),
                norm(frontier["_accuracy"].to_numpy(), acc_min, acc_max),
            ])

            d = pairwise_distances(cand_xy, fr_xy).min(axis=1)
            work["_frontier_gap"] = d
            return work.sort_values("_frontier_gap", ascending=True)

        else:
            raise ValueError(f"Unknown frontier_distance: {self.config.frontier_distance}")

    # ----------------------------
    # Exploration reserve helper
    # ----------------------------
    def _choose_diverse_subset(self, df: pd.DataFrame, k: int) -> List[int]:
        if df.empty or k <= 0:
            return []

        emb = self._build_augmented_embedding(df)
        chosen_local = [0]
        while len(chosen_local) < min(k, len(df)):
            remaining = [i for i in range(len(df)) if i not in chosen_local]
            rem_idx = np.array(remaining, dtype=int)
            dmat = pairwise_distances(emb[rem_idx], emb[chosen_local])
            min_dist = dmat.min(axis=1)
            pick_local = int(rem_idx[np.argmax(min_dist)])
            chosen_local.append(pick_local)

        return df.iloc[chosen_local].index.tolist()

    # ----------------------------
    # Embedding utilities
    # ----------------------------
    def _build_augmented_embedding(self, df: pd.DataFrame) -> np.ndarray:
        prep = make_preprocessor(self.continuous_cols, self.categorical_cols)
        X = prep.fit_transform(df[self.feature_cols_all])
        if hasattr(X, "toarray"):
            X = X.toarray()
        X = np.asarray(X, dtype=float)

        lat = df[self.latency_col].to_numpy(dtype=float)
        if len(lat) == 0:
            lat_norm = np.zeros((0, 1), dtype=float)
        else:
            lo, hi = float(np.min(lat)), float(np.max(lat))
            if hi <= lo:
                lat_norm = np.zeros((len(lat), 1), dtype=float)
            else:
                lat_norm = ((lat - lo) / (hi - lo)).reshape(-1, 1)

        Xw = self.config.feature_weight * X
        Lw = self.config.latency_weight * lat_norm
        return np.concatenate([Xw, Lw], axis=1)

    def _infer_features(
        self,
        continuous_cols: Optional[Sequence[str]],
        categorical_cols: Optional[Sequence[str]],
    ) -> Tuple[List[str], List[str], List[str]]:
        reserved = {
            self.candidate_id_col,
            self.latency_col,
            "_current_epoch",
            "_accuracy",
            "_active",
            "_ever_selected",
        }

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


def make_preprocessor(
    continuous_cols: Sequence[str],
    categorical_cols: Sequence[str],
) -> ColumnTransformer:
    cont_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    cat_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("cont", cont_pipe, list(continuous_cols)),
            ("cat", cat_pipe, list(categorical_cols)),
        ],
        remainder="drop",
    )


# ----------------------------
# Demo trainer
# ----------------------------
def synthetic_trainer(row: pd.Series, target_epoch: int, current_epoch: int) -> float:
    """
    A toy trainer for demonstration only.

    Replace this with your real warm-start fine-tuning + evaluation code.
    """
    params = float(row.get("num_params", 1e8))
    hidden = float(row.get("hidden_size", 768))
    family = str(row.get("family", "unknown"))
    embedding_tuned = int(row.get("is_embedding_tuned", 0))
    latency = float(row.get("avg_ms", 10.0))

    base = (
        0.45
        + 0.03 * np.log10(max(params, 1e5))
        + 0.004 * embedding_tuned
        + (0.01 if family == "modernbert" else 0.0)
        - 0.0002 * max(latency - 40.0, 0.0)
    )

    speed = 0.10 + 0.02 * (hidden / 1024.0)
    family_bonus = {
        "modernbert": 0.04,
        "qwen": 0.03,
        "e5": 0.02,
        "minilm": 0.015,
    }.get(family, 0.01)

    gain = family_bonus * (1.0 - math.exp(-speed * target_epoch))
    noise = np.random.normal(0, 0.005)
    return float(base + gain + noise)


if __name__ == "__main__":
    rng = np.random.default_rng(7)

    demo = pd.DataFrame(
        {
            "model_id": [f"m{i}" for i in range(128)],
            "avg_ms": np.sort(rng.uniform(2, 80, size=128)),
            "num_params": np.exp(rng.uniform(np.log(5e5), np.log(1e9), size=128)),
            "num_layers": rng.choice([2, 4, 6, 8, 12, 16, 24], size=128),
            "hidden_size": rng.choice([128, 256, 384, 512, 768, 1024, 1536], size=128),
            "num_heads": rng.choice([2, 4, 6, 8, 12, 16], size=128),
            "ffn_width": rng.choice([512, 1024, 1536, 2048, 3072, 4096], size=128),
            "context_length": rng.choice([512, 1024, 2048, 4096, 8192], size=128),
            "embedding_dim": rng.choice([128, 256, 384, 512, 768, 1024], size=128),
            "arch_type": rng.choice(["encoder", "decoder"], size=128),
            "family": rng.choice(["minilm", "e5", "modernbert", "gte", "qwen", "bert"], size=128),
            "encoder_decoder_flag": rng.choice(["encoder", "decoder"], size=128),
            "pooling_method": rng.choice(["mean", "cls", "last_token"], size=128),
            "tokenizer_behavior": rng.choice(["wordpiece", "bpe", "sentencepiece"], size=128),
            "is_embedding_tuned": rng.choice([0, 1], size=128),
            "multilingual": rng.choice([0, 1], size=128),
        }
    )

    cfg = MFSearchConfig(
        init_count=24,
        total_epochs=5,
        shrink_factor=2.0,
        frontier_distance="pareto_gap",
        always_keep_frontier=True,
        exploration_reserve=0.10,
        feature_weight=3.0,
        latency_weight=5.0,
        random_state=7,
    )

    search = MultiFidelityParetoSearch(
        candidates=demo,
        trainer=synthetic_trainer,
        config=cfg,
        latency_col="avg_ms",
        candidate_id_col="model_id",
        continuous_cols=[
            "num_params", "num_layers", "hidden_size", "num_heads",
            "ffn_width", "context_length", "embedding_dim",
            "is_embedding_tuned", "multilingual",
        ],
        categorical_cols=[
            "family", "arch_type", "encoder_decoder_flag",
            "pooling_method", "tokenizer_behavior",
        ],
    )

    result = search.run()
    print("Total epoch budget used:", result.total_epoch_budget_used)
    print("Final frontier size:", len(result.final_frontier))
    print(result.final_frontier[["model_id", "avg_ms", "_accuracy", "_current_epoch"]].head())
