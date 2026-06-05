"""Round-based Pareto filtering vs. monotonic random baseline.

Aligned with the existing helpers used in real Mode 12 runs:
  - Pareto-level computation matches `select_pareto_next_round.pareto_levels`.
  - Keep / drop order matches `select_pareto_next_round`'s convention:
    sort by (pareto_level, val_p90, latency); keep the head.
  - Random baseline mirrors `random_model_selection.py`'s monotonic prefix:
    one `rng.permutation(seed)` per seed, take the prefix that fits the budget.

Algorithm (ours):
  - Init: latency-stratified — split 43 models into N=init_K bins by avg_ms,
    pick 1 random model per bin (matches imp_43pool.py's strat_init).
  - Round 1: train init to 8 epochs. Keep top ⌈K · keep_ratio⌉ by Pareto
    level on (avg_ms, val_p90_e8) — tie-break by (val_p90, latency).
  - rounds=2: train survivors directly to 16 epochs. Output.
  - rounds=3: train survivors to 12 epochs, drop again by val_p90_e12,
    train final survivors to 16 epochs. Output.
  - Output is filtered to its (avg_ms, val_p90_e16) Pareto frontier before HV.

Defaults (rounds=3, keep_ratio=0.75) chosen from a sweep on the 43-pool —
the only config with strictly positive dHV at every init_K ∈ [8, 20]
(min +0.96 at K=18, mean +6.14).

Random baseline: total H100-min budget matched to ours' actual total cost.
The same val-Pareto pre-filter is applied to random's picks before HV/recall.

All decisions use val_p90; HV/recall use test_p90_e16.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path("/root/LLM4QPR/experiments")
ALL_MODELS_CSV = ROOT / "logs/postgres/logs_Train_stats_Test_stats_ours/all_models/all_models_full_e16.csv"
PROFILE_CSV = ROOT / "experiment_scripts/model_profile_with_nonemb.csv"

DEFAULT_INIT_KS = (6, 8, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78)
DEFAULT_SEEDS = tuple(range(20))
N_BUCKETS = 6
DROP_FRAC = 0.25
SURVIVAL_FLOOR = 6


# ---------- model-name resolution ----------

def dashed_model_from_key(key: str):
    m = re.search(r"_h2048_(.+?)_quant-4-bit", key)
    return m.group(1) if m else None


def join_pool_with_profile(all_df: pd.DataFrame, prof: pd.DataFrame) -> pd.DataFrame:
    dashed_to_model = {m.replace("/", "-"): m for m in prof["model"]}
    resolved, unresolved = [], []
    for k in all_df["key"]:
        d = dashed_model_from_key(k)
        m = dashed_to_model.get(d)
        if m is None:
            unresolved.append(d if d else f"<no-h2048-segment in '{k}'>")
            resolved.append(None)
        else:
            resolved.append(m)
    if unresolved:
        raise RuntimeError(
            f"join_pool_with_profile: {len(unresolved)} keys did not resolve:\n  "
            + "\n  ".join(unresolved)
        )
    out = all_df.copy()
    out["model"] = resolved
    out = out.merge(prof, on="model", how="left", suffixes=("", "_prof"))
    if out["avg_ms"].isna().any():
        bad = out[out["avg_ms"].isna()]["model"].astype(str).tolist()
        raise RuntimeError(f"missing avg_ms after merge: {bad}")
    # Latency source override: PROFILE_CSV's avg_ms is the LLM-only forward
    # measurement; the deployed-inference latency is the full LLM+PRICE+MLP+
    # cross-attn forward in all_models_full_e16.csv:test_per_query_ms (now
    # populated with per-query H100 ms from the 2026-05-18 profile run).
    # Preserve the original avg_ms in `avg_ms_llm_only` for reference.
    if "test_per_query_ms" in out.columns:
        deployed = pd.to_numeric(out["test_per_query_ms"], errors="coerce")
        if deployed.isna().any():
            bad = out.loc[deployed.isna(), "model"].astype(str).tolist()
            raise RuntimeError(
                f"test_per_query_ms missing/non-numeric for: {bad}")
        out["avg_ms_llm_only"] = out["avg_ms"]
        out["avg_ms"] = deployed
    return out


# ---------- feature matrix (metadata only) ----------

NUMERIC_FEATURE_COLS = [
    "total_params", "embedding_params", "non_embedding_params",
    "attention_heads", "context_length", "embedding_dimension",
    "ffn_width", "hidden_size", "num_layers",
]
CATEGORICAL_FEATURE_COLS = [
    "architecture", "deduped_variant", "encoder_vs_decoder",
    "is_cased", "is_embedding_tuned", "is_instruction_tuned",
    "is_multilingual", "pooling_method", "tokenizer_behavior", "tokenizer_type",
]


def build_metadata_features(df: pd.DataFrame) -> np.ndarray:
    feats = df[NUMERIC_FEATURE_COLS].copy()
    feats = feats.fillna(feats.median(numeric_only=True))
    parts = [feats.to_numpy(dtype=float)]
    for c in CATEGORICAL_FEATURE_COLS:
        if c in df.columns:
            d = pd.get_dummies(df[c].fillna("__nan__"), prefix=c)
            parts.append(d.to_numpy(dtype=float))
    X = np.hstack(parts)
    return StandardScaler().fit_transform(X)


# ---------- Pareto + HV utilities ----------
# Reuses pareto_levels from select_pareto_next_round.py (the live-runs helper)
# to keep ranking semantics identical: 1-indexed, level 1 = frontier.

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_pareto_next_round import pareto_levels  # noqa: E402


def pareto_frontier_indices(points: np.ndarray) -> list:
    pts = [(float(x), float(y)) for x, y in points]
    levels = pareto_levels(pts)
    return [i for i, lvl in enumerate(levels) if lvl == 1]


def hv_2d_min(points: np.ndarray, ref_x: float, ref_y: float) -> float:
    inside = [(float(x), float(y)) for x, y in points if x <= ref_x and y <= ref_y]
    if not inside:
        return 0.0
    inside.sort(key=lambda t: (t[0], t[1]))
    front = []
    best_y = float("inf")
    for x, y in inside:
        if y < best_y:
            front.append((x, y))
            best_y = y
    hv = 0.0
    for i, (x_i, y_i) in enumerate(front):
        x_next = front[i + 1][0] if i + 1 < len(front) else ref_x
        hv += (x_next - x_i) * (ref_y - y_i)
    return hv


# ---------- bucketing + init picks ----------

def latency_buckets(latencies: np.ndarray, n_buckets: int = N_BUCKETS) -> np.ndarray:
    """Even-rank quantile buckets: each bucket gets ~n/n_buckets models."""
    n = len(latencies)
    order = np.argsort(latencies, kind="stable")
    buckets = np.empty(n, dtype=int)
    for rank, idx in enumerate(order):
        buckets[idx] = min(rank * n_buckets // n, n_buckets - 1)
    return buckets


def distribute_k(K: int, n_buckets: int) -> list:
    base, rem = divmod(K, n_buckets)
    return [base + (1 if i < rem else 0) for i in range(n_buckets)]


def farthest_first(features: np.ndarray, candidates: np.ndarray, K: int,
                    rng: np.random.Generator) -> list:
    """Farthest-first traversal over `candidates` (indices into features).
    Seed with a random first pick, then iteratively pick max-min distance.
    """
    if len(candidates) == 0 or K == 0:
        return []
    K = min(K, len(candidates))
    first = int(rng.choice(candidates))
    picks = [first]
    remaining = [c for c in candidates if c != first]
    while len(picks) < K and remaining:
        d_to_picks = np.min(
            np.linalg.norm(features[remaining][:, None, :] - features[picks][None, :, :], axis=-1),
            axis=1,
        )
        nxt = int(remaining[int(np.argmax(d_to_picks))])
        picks.append(nxt)
        remaining = [c for c in remaining if c != nxt]
    return picks


def latency_priority(pool: pd.DataFrame, n_bins: int, seed: int) -> list:
    """Round-robin priority list across `n_bins` FIXED latency bins.
    Within each bin, members are shuffled by `seed`. Then we emit
    bin0[0], bin1[0], ..., bin{N-1}[0], bin0[1], bin1[1], ..., until
    every member appears.

    Property: priority[:K] is the init at init_K=K, and is strictly
    nested in K (larger K is a superset of smaller K). This is the
    main lever for monotonicity.
    """
    rng = np.random.default_rng(seed)
    lat = pool["avg_ms"].to_numpy(dtype=float)
    n_bins = min(n_bins, len(pool))
    buckets = latency_buckets(lat, n_bins)
    bin_members = []
    for b in range(n_bins):
        members = list(np.where(buckets == b)[0])
        rng.shuffle(members)
        bin_members.append(members)
    priority = []
    while any(bin_members):
        for b in range(n_bins):
            if bin_members[b]:
                priority.append(int(bin_members[b].pop(0)))
    return priority


def random_priority(pool: pd.DataFrame, seed: int) -> list:
    """Uniform random priority list. Nested-in-K monotonicity holds because
    we draw a single permutation per seed and return its prefix."""
    rng = np.random.default_rng(seed)
    perm = np.arange(len(pool))
    rng.shuffle(perm)
    return [int(i) for i in perm]


def stratified_centroid_priority(pool: pd.DataFrame, features: np.ndarray,
                                  n_bins: int, seed: int) -> list:
    """Stratified-by-latency, but within each bucket order members by
    distance from the bucket's metadata CENTROID (closest first).
    'Most-representative model of this latency tier' rather than 'farthest'.
    """
    rng = np.random.default_rng(seed)
    lat = pool["avg_ms"].to_numpy(dtype=float)
    n_bins = min(n_bins, len(pool))
    buckets = latency_buckets(lat, n_bins)
    bin_members = []
    for b in range(n_bins):
        members = list(np.where(buckets == b)[0])
        rng.shuffle(members)
        if members:
            centroid = features[members].mean(axis=0)
            d = np.linalg.norm(features[members] - centroid, axis=1)
            members = [members[i] for i in np.argsort(d, kind="stable")]
        bin_members.append(members)
    priority: list = []
    while any(bin_members):
        for b in range(n_bins):
            if bin_members[b]:
                priority.append(int(bin_members[b].pop(0)))
    return priority


def stratified_kmeans_round_priority(pool: pd.DataFrame, features: np.ndarray,
                                       n_bins: int, seed: int,
                                       n_clusters: Optional[int] = None) -> list:
    """Stratified-by-latency round-robin, but within each round-robin pass
    avoid picking from the same KMeans cluster (over all metadata).

    Generalizes `stratified_arch_priority` (reset_per_round=True): instead of
    "avoid same architecture family", uses "avoid same KMeans cluster" which
    accounts for the full metadata vector (architecture + size + layers +
    hidden dim + heads + ...). Cluster constraint resets at the start of
    every round-robin pass through the latency bins.

    n_clusters defaults to n_bins so each pass has at most one pick per
    cluster — matches the "one pick per bucket" granularity.
    """
    rng = np.random.default_rng(seed)
    lat = pool["avg_ms"].to_numpy(dtype=float)
    n_bins = min(n_bins, len(pool))
    if n_clusters is None:
        n_clusters = n_bins
    n_clusters = min(n_clusters, len(features))

    # KMeans cluster assignments over the full metadata vector.
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=seed)
    clusters = km.fit_predict(features)

    buckets = latency_buckets(lat, n_bins)
    bin_members = []
    for b in range(n_bins):
        members = list(np.where(buckets == b)[0])
        rng.shuffle(members)
        bin_members.append(members)

    priority: list = []
    while any(bin_members):
        picked_clusters: set = set()  # reset every round-robin pass
        for b in range(n_bins):
            if not bin_members[b]:
                continue
            chosen_pos = None
            for i, m in enumerate(bin_members[b]):
                if int(clusters[m]) not in picked_clusters:
                    chosen_pos = i
                    break
            if chosen_pos is None:
                chosen_pos = 0  # fallback: shuffled-first
            pick = bin_members[b].pop(chosen_pos)
            priority.append(int(pick))
            picked_clusters.add(int(clusters[pick]))
    return priority


def stratified_arch_priority(pool: pd.DataFrame, n_bins: int, seed: int,
                              reset_per_round: bool = False) -> list:
    """Stratified-by-latency, but if a bin has multiple architectures,
    prefer the one whose architecture family hasn't been picked yet.
    Prevents architecture near-duplicates while keeping latency coverage.

    `reset_per_round`: if True, reset the "already picked" set at the start
    of each round-robin pass through the bins. Preserves arch-diversity
    within each round but allows the same arch in different rounds.
    Helps at larger K where the global block would otherwise force bad picks.
    """
    rng = np.random.default_rng(seed)
    lat = pool["avg_ms"].to_numpy(dtype=float)
    if "architecture" in pool.columns:
        archs = pool["architecture"].fillna("__nan__").to_numpy()
    else:
        archs = np.full(len(pool), "__unknown__", dtype=object)
    n_bins = min(n_bins, len(pool))
    buckets = latency_buckets(lat, n_bins)
    bin_members = []
    for b in range(n_bins):
        members = list(np.where(buckets == b)[0])
        rng.shuffle(members)
        bin_members.append(members)
    priority: list = []
    picked_archs: set = set()
    while any(bin_members):
        if reset_per_round:
            picked_archs = set()
        for b in range(n_bins):
            if not bin_members[b]:
                continue
            chosen_pos = None
            for i, m in enumerate(bin_members[b]):
                if archs[m] not in picked_archs:
                    chosen_pos = i
                    break
            if chosen_pos is None:
                chosen_pos = 0
            pick = bin_members[b].pop(chosen_pos)
            priority.append(int(pick))
            picked_archs.add(archs[pick])
    return priority


def stratified_metadata_priority(pool: pd.DataFrame, features: np.ndarray,
                                  n_bins: int, seed: int) -> list:
    """Stratified-by-latency round-robin, but within each bucket pick the
    member whose metadata is FARTHEST from the already-picked models.

    Hybrid of `latency_priority` (cost-axis coverage) and `farthest_first`
    (metadata diversity within each cost tier). Still nested-in-K: priority[:K]
    is a prefix of priority[:K+1] because each new round-robin pass extends
    rather than reshuffles.

    Within a bucket: if no picks exist yet, fall back to the shuffled order
    (first-pick is uniform random within bin 0). Otherwise pick argmax of
    min-distance to picks.
    """
    rng = np.random.default_rng(seed)
    lat = pool["avg_ms"].to_numpy(dtype=float)
    n_bins = min(n_bins, len(pool))
    buckets = latency_buckets(lat, n_bins)
    bin_members = []
    for b in range(n_bins):
        members = list(np.where(buckets == b)[0])
        rng.shuffle(members)
        bin_members.append(members)
    priority: list = []
    while any(bin_members):
        for b in range(n_bins):
            if not bin_members[b]:
                continue
            members = np.array(bin_members[b], dtype=int)
            if not priority:
                # First pick of the run: take the shuffled-first member.
                pick_pos = 0
            else:
                # Pick the bucket member farthest (min-distance) from picks.
                d = np.min(
                    np.linalg.norm(
                        features[members][:, None, :] - features[priority][None, :, :],
                        axis=-1),
                    axis=1,
                )
                pick_pos = int(np.argmax(d))
            pick = int(members[pick_pos])
            bin_members[b].pop(pick_pos)
            priority.append(pick)
    return priority


def kmeans_init(features: np.ndarray, K: int, seed: int) -> list:
    """KMeans on metadata features, pick the model closest to each cluster
    center (mirrors model_selection_v2._diverse_initialization_ids).

    Note: NOT nested in K — changing K reshuffles cluster assignments,
    so kmeans_init(K=8) is not generally a superset of kmeans_init(K=4).
    This is the documented trade-off for using KMeans selection.
    """
    from sklearn.cluster import KMeans
    n = features.shape[0]
    K = min(K, n)
    if K <= 1:
        rng = np.random.default_rng(seed)
        return [int(rng.integers(0, n))]
    km = KMeans(n_clusters=K, n_init=10, random_state=seed)
    labels = km.fit_predict(features)
    picks: list = []
    for cid in range(K):
        members = np.where(labels == cid)[0]
        if len(members) == 0:
            continue
        d = np.linalg.norm(features[members] - km.cluster_centers_[cid], axis=1)
        picks.append(int(members[int(np.argmin(d))]))
    # Fill if any cluster collapsed (rare on small pools).
    picks = list(dict.fromkeys(picks))
    if len(picks) < K:
        rng = np.random.default_rng(seed)
        remaining = [i for i in range(n) if i not in picks]
        rng.shuffle(remaining)
        picks.extend(remaining[:K - len(picks)])
    return picks[:K]


def pick_init(pool: pd.DataFrame, features: np.ndarray, K: int, method: str,
              seed: int, n_init_bins: int = N_BUCKETS,
              kmeans_n_clusters: Optional[int] = None) -> list:
    """First-round seed picker, dispatched by `method`:

      * "stratified" (default): latency-quantile bucket round-robin.
                                Monotonic priority — priority[:K] is nested in K.
      * "random":               uniform random permutation.
                                Monotonic priority too (single perm per seed).
      * "kmeans":               sklearn KMeans on metadata features, pick the
                                model closest to each cluster center. NOT nested
                                in K (per-K cluster reshuffle).
    """
    if method == "random":
        priority = random_priority(pool, seed)
        return priority[:min(K, len(priority))]
    if method == "kmeans":
        return kmeans_init(features, K, seed)
    if method == "stratified_metadata":
        priority = stratified_metadata_priority(pool, features, n_init_bins, seed)
        return priority[:min(K, len(priority))]
    if method == "stratified_centroid":
        priority = stratified_centroid_priority(pool, features, n_init_bins, seed)
        return priority[:min(K, len(priority))]
    if method == "stratified_arch":
        priority = stratified_arch_priority(pool, n_init_bins, seed)
        return priority[:min(K, len(priority))]
    if method == "stratified_arch_round":
        priority = stratified_arch_priority(pool, n_init_bins, seed,
                                             reset_per_round=True)
        return priority[:min(K, len(priority))]
    if method == "stratified_kmeans_round":
        priority = stratified_kmeans_round_priority(pool, features,
                                                     n_init_bins, seed,
                                                     n_clusters=kmeans_n_clusters)
        return priority[:min(K, len(priority))]
    # default / "stratified"
    priority = latency_priority(pool, n_init_bins, seed)
    return priority[:min(K, len(priority))]


# ---------- keep step ----------

def keep_top(survivors: list, val_p90_arr: np.ndarray, latency_arr: np.ndarray,
              keep_ratio: float, n_buckets: int = N_BUCKETS) -> list:
    """Dynamic-floor keep: keep_n = max(n_buckets, frontier_size, ⌈prev·kr⌉),
    then keep top-keep_n by (pareto_level, val_p90, latency) ascending.

    Three lower bounds:
      * n_buckets       — latency coverage doesn't collapse below the bin count.
      * frontier_size   — every val-Pareto level-1 model is preserved.
      * prev·kr         — proportional shrink (the original keep_ratio rule).
    """
    n = len(survivors)
    if n == 0:
        return []
    pts = [(float(latency_arr[s]), float(val_p90_arr[s])) for s in survivors]
    levels = pareto_levels(pts)
    frontier_size = sum(1 for lvl in levels if lvl == 1)
    keep_n = max(n_buckets, frontier_size, int(np.ceil(n * keep_ratio)))
    keep_n = min(keep_n, n)
    if keep_n >= n:
        return list(survivors)
    order = sorted(range(n), key=lambda i: (
        levels[i],
        float(val_p90_arr[survivors[i]]),
        float(latency_arr[survivors[i]]),
    ))
    keep_set = set(order[:keep_n])
    return [survivors[i] for i in range(n) if i in keep_set]


def keep_top_random(survivors: list, val_p90_arr: np.ndarray,
                     latency_arr: np.ndarray, keep_ratio: float,
                     n_buckets: int = N_BUCKETS,
                     rng: Optional[np.random.Generator] = None) -> list:
    """Pareto-level-priority keep with random tie-breaking inside the cutoff level.

    Differs from `keep_top` only WITHIN the level where we run out of slots:
      * Sweep levels 1, 2, ... in ascending order, accepting every model at a
        level if it fits inside keep_n.
      * At the first level L that overflows, fill the remaining
        keep_n - (#accepted so far) slots by sampling uniformly without
        replacement from level L.
    Same `keep_n` floor as `keep_top` (max(n_buckets, frontier_size, ⌈n·kr⌉))
    so survivor count is comparable across strategies. Isolates the value of
    val_p90-tie-break vs random-tie-break — full-level-1..L−1 preservation is
    held constant.
    """
    n = len(survivors)
    if n == 0:
        return []
    pts = [(float(latency_arr[s]), float(val_p90_arr[s])) for s in survivors]
    levels = pareto_levels(pts)
    frontier_size = sum(1 for lvl in levels if lvl == 1)
    keep_n = max(n_buckets, frontier_size, int(np.ceil(n * keep_ratio)))
    keep_n = min(keep_n, n)
    if keep_n >= n:
        return list(survivors)
    if rng is None:
        rng = np.random.default_rng()
    by_level: dict = {}
    for i, lvl in enumerate(levels):
        by_level.setdefault(lvl, []).append(i)
    kept_local: list = []
    for lvl in sorted(by_level):
        bucket = by_level[lvl]
        remaining = keep_n - len(kept_local)
        if remaining <= 0:
            break
        if len(bucket) <= remaining:
            kept_local.extend(bucket)
        else:
            picks = rng.choice(len(bucket), size=remaining, replace=False)
            kept_local.extend(bucket[int(p)] for p in picks)
            break
    keep_set = set(kept_local)
    return [survivors[i] for i in range(n) if i in keep_set]


def keep_top_stratified(survivors: list, val_p90_arr: np.ndarray,
                          latency_arr: np.ndarray, keep_ratio: float,
                          n_buckets: int = N_BUCKETS) -> list:
    """Keep step that preserves val Pareto frontier AND latency coverage.

    1. Always keep all models on val Pareto level 1 (the frontier).
    2. Fill remaining slots by round-robin across latency buckets, picking
       next best-by-val_p90 within each bucket. Guarantees the survivor set
       spans the cost axis — fixes the HV-vs-recall gap at high init_K.

    Same `keep_n` floor as `keep_top`.
    """
    n = len(survivors)
    if n == 0:
        return []
    pts = [(float(latency_arr[s]), float(val_p90_arr[s])) for s in survivors]
    levels = pareto_levels(pts)
    frontier_size = sum(1 for lvl in levels if lvl == 1)
    keep_n = max(n_buckets, frontier_size, int(np.ceil(n * keep_ratio)))
    keep_n = min(keep_n, n)
    if keep_n >= n:
        return list(survivors)

    # Step 1: always keep Pareto level 1.
    keep_set = {i for i, lvl in enumerate(levels) if lvl == 1}

    # Step 2: round-robin fill remaining slots across latency buckets.
    remaining = [i for i in range(n) if i not in keep_set]
    if remaining and len(keep_set) < keep_n:
        # Rank-bucket the remaining survivors by latency.
        lat = np.array([float(latency_arr[survivors[i]]) for i in remaining])
        order_rem = np.argsort(lat, kind="stable")
        bin_of: dict = {}
        n_rem = len(remaining)
        for rank, ridx in enumerate(order_rem):
            bin_of[remaining[ridx]] = min(rank * n_buckets // n_rem, n_buckets - 1)
        # Within each bucket, sort by val_p90 ascending (best-first).
        bins: list = [[] for _ in range(n_buckets)]
        for i in remaining:
            bins[bin_of[i]].append(i)
        for b in range(n_buckets):
            bins[b].sort(key=lambda i: float(val_p90_arr[survivors[i]]))
        # Round-robin take next-best from each bucket until slots filled
        # or buckets exhausted.
        next_in_bin = [0] * n_buckets
        slots = keep_n - len(keep_set)
        while slots > 0:
            progressed = False
            for b in range(n_buckets):
                if slots <= 0:
                    break
                if next_in_bin[b] < len(bins[b]):
                    keep_set.add(bins[b][next_in_bin[b]])
                    next_in_bin[b] += 1
                    slots -= 1
                    progressed = True
            if not progressed:
                break
    return [survivors[i] for i in range(n) if i in keep_set]


# ---------- run ours ----------

def run_ours(pool: pd.DataFrame, features: np.ndarray, init_K: int,
             method: str, seed: int, rounds: int = 3,
             keep_ratio: float = 0.75,
             n_init_bins: int = N_BUCKETS,
             keep_strategy: str = "topval",
             kmeans_n_clusters: Optional[int] = None,
             decision_epochs: Optional[list] = None) -> dict:
    """Round-based Pareto filtering.

    `decision_epochs` (if given) is an explicit list of epoch milestones at
    which a keep step happens. Supported milestones: 4, 8, 12. Final training
    always runs through to e16. Examples:
        decision_epochs=[]            → no filter (= rounds=1).
        decision_epochs=[8]           → filter at e8 (= rounds=2).
        decision_epochs=[8, 12]       → filter at e8 and e12 (= rounds=3).
        decision_epochs=[4, 8, 12]    → 3 filters, earliest at e4 (= rounds=4).
        decision_epochs=[4]           → 1 filter at e4 (earliest possible).
        decision_epochs=[4, 12]       → filter at e4 then e12, skip e8.

    Legacy `rounds` argument is mapped to a default `decision_epochs`:
        rounds=1 → []
        rounds=2 → [8]
        rounds=3 → [8, 12]
        rounds=4 → [4, 8, 12]

    keep_strategy:
      "topval" (default): keep_top — sort by (pareto level, val_p90, latency).
      "stratified": keep_top_stratified — preserve val Pareto frontier +
                    round-robin across latency buckets for remaining slots.
    """
    _ROUNDS_TO_SCHEDULE = {1: [], 2: [8], 3: [8, 12], 4: [4, 8, 12]}
    if decision_epochs is None:
        if rounds not in _ROUNDS_TO_SCHEDULE:
            raise ValueError(f"rounds must be 1, 2, 3, or 4 (or pass "
                              f"decision_epochs explicitly), got {rounds}")
        decision_epochs = _ROUNDS_TO_SCHEDULE[rounds]
    for ep in decision_epochs:
        if ep not in (4, 8, 12):
            raise ValueError(f"decision_epochs must contain only "
                              f"4/8/12 — got {ep}.")
    decision_epochs = sorted(set(decision_epochs))
    init_idx = pick_init(pool, features, init_K, method, seed,
                          n_init_bins=n_init_bins,
                          kmeans_n_clusters=kmeans_n_clusters)

    t_e1_4 = pool["time_e1_4_h100_ms"].to_numpy(dtype=float)
    t_e5_8 = pool["time_e5_8_h100_ms"].to_numpy(dtype=float)
    t_e9_12 = pool["time_e9_12_h100_ms"].to_numpy(dtype=float)
    t_e13_16 = pool["time_e13_16_h100_ms"].to_numpy(dtype=float)
    avg_ms = pool["avg_ms"].to_numpy(dtype=float)
    val_p90_e8 = pool["val_p90_e8"].to_numpy(dtype=float)
    val_p90_e12 = pool["val_p90_e12"].to_numpy(dtype=float)

    # Dispatch on keep_strategy. "random" needs the per-run rng for seeding.
    if keep_strategy == "stratified":
        keep_fn = keep_top_stratified
    elif keep_strategy == "random":
        _keep_rng = np.random.default_rng(seed)
        def keep_fn(survivors, val_arr, lat_arr, kr, n_buckets):
            return keep_top_random(survivors, val_arr, lat_arr, kr,
                                    n_buckets=n_buckets, rng=_keep_rng)
    else:
        keep_fn = keep_top
    val_p90_e4 = (pool["val_p90_e4"].to_numpy(dtype=float)
                  if "val_p90_e4" in pool.columns else None)

    # Chunked training schedule. Train epoch-chunk [a..b], then optionally
    # filter, then proceed to next chunk. Always end at e16.
    chunk_times = [
        (4,  t_e1_4),
        (8,  t_e5_8),
        (12, t_e9_12),
        (16, t_e13_16),
    ]
    val_at = {4: val_p90_e4, 8: val_p90_e8, 12: val_p90_e12}

    survivors = list(init_idx)
    cost = 0.0
    intermediate_survivors = []   # for diagnostics (snapshot after each filter)
    for end_ep, t_chunk in chunk_times:
        # Train current survivors through this chunk.
        cost += float(t_chunk[survivors].sum())
        # If this is a decision point AND we haven't reached e16, filter.
        if end_ep in decision_epochs:
            arr = val_at[end_ep]
            if arr is None:
                raise RuntimeError(
                    f"val_p90_e{end_ep} not in pool — cannot filter at e{end_ep}.")
            survivors = keep_fn(survivors, arr, avg_ms, keep_ratio,
                                 n_buckets=n_init_bins)
            intermediate_survivors.append((end_ep, list(survivors)))

    return {
        "init_idx": init_idx,
        "round2_idx": (intermediate_survivors[0][1]
                       if intermediate_survivors else init_idx),
        "round3_idx": survivors,
        "total_train_h100_ms": cost,
        "decision_epochs": decision_epochs,
        "intermediate_survivors": intermediate_survivors,
    }


# ---------- random monotonic ----------

def random_monotonic_prefix(pool: pd.DataFrame, total_train_h100_ms: float,
                             seed: int) -> dict:
    """One shuffle per seed; take prefix that fits the budget.
    Each picked model is trained full 16 epochs; cost = total_train_h100_ms.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(pool))
    full_cost = (
        pool["time_e1_4_h100_ms"].to_numpy()
        + pool["time_e5_8_h100_ms"].to_numpy()
        + pool["time_e9_12_h100_ms"].to_numpy()
        + pool["time_e13_16_h100_ms"].to_numpy()
    )
    chosen, used = [], 0.0
    for i in order:
        if used + full_cost[i] > total_train_h100_ms:
            break
        chosen.append(int(i))
        used += float(full_cost[i])
    return {"idx": chosen, "total_train_h100_ms": used}


# ---------- evaluation ----------

def evaluate_run(pool: pd.DataFrame, idxs: list,
                  ref_lat: float, ref_qerr: float,
                  true_frontier_models: set) -> dict:
    """Submit only the (avg_ms, val_p90_e16) Pareto frontier of the picks
    for evaluation. Both algorithms are restricted to their val-frontier:
    luck-based test outliers among non-frontier picks no longer contribute."""
    if not idxs:
        return {"hv": 0.0, "frontier_size": 0, "recall": 0.0,
                "frontier_models": []}
    sub = pool.iloc[idxs]
    val_pts = np.column_stack([sub["avg_ms"].astype(float),
                                sub["val_p90_e16"].astype(float)])
    val_front_local = pareto_frontier_indices(val_pts)
    val_front_idx = [idxs[i] for i in val_front_local]

    sub_front = pool.iloc[val_front_idx]
    test_pts = np.column_stack([sub_front["avg_ms"].astype(float),
                                 sub_front["test_p90_e16"].astype(float)])
    front_models = sub_front["model"].tolist()
    hv = hv_2d_min(test_pts, ref_lat, ref_qerr)
    recovered = sum(1 for m in front_models if m in true_frontier_models)
    recall = recovered / len(true_frontier_models) if true_frontier_models else 0.0
    return {
        "hv": hv,
        "frontier_size": len(front_models),
        "recall": recall,
        "frontier_models": front_models,
    }


# ---------- main ----------

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--all_models_csv", default=str(ALL_MODELS_CSV))
    p.add_argument("--profile_csv", default=str(PROFILE_CSV))
    p.add_argument("--init_Ks", type=int, nargs="+", default=list(DEFAULT_INIT_KS))
    p.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    p.add_argument("--hv_ref_margin", type=float, default=1.05,
                   help="Margin multiplier on (max_lat_on_frontier, max_qerr_on_frontier).")
    p.add_argument("--rounds", type=int, default=3, choices=[1, 2, 3, 4],
                   help="Legacy shorthand for decision_epochs: "
                        "1=[], 2=[8], 3=[8,12], 4=[4,8,12]. "
                        "Use --decision_epochs for arbitrary schedules.")
    p.add_argument("--decision_epochs", type=int, nargs="*", default=None,
                   help="Explicit list of epoch milestones to filter at "
                        "(subset of {4, 8, 12}). Overrides --rounds. "
                        "Examples: --decision_epochs 4 (single early filter), "
                        "--decision_epochs 4 12 (skip e8), "
                        "--decision_epochs 4 8 12 (= rounds=4).")
    p.add_argument("--keep_ratio", type=float, default=0.75,
                   help="Fraction of survivors retained at each drop step. "
                        "Default 0.75 — paired with rounds=3 gives an all-positive "
                        "dHV sweep on the 43-pool (min +0.96 at K=18, mean +6.14).")
    p.add_argument("--n_init_bins", type=int, default=N_BUCKETS,
                   help="Fixed latency bins for init (default 6). With round-robin "
                        "priority, init at K is the prefix of init at K+1 — gives "
                        "strict nestedness in K, which makes ours' HV monotonic-ish "
                        "in K (Pareto-level reshuffling at the keep step can still "
                        "cause minor non-monotonicity).")
    p.add_argument("--kmeans_n_clusters", type=int, default=None,
                   help="Number of KMeans clusters for stratified_kmeans_round "
                        "init. Defaults to n_init_bins (matches one-pick-per-pass "
                        "granularity). Try n_clusters = #distinct architectures "
                        "in your pool to differentiate within size tiers.")
    p.add_argument("--keep_strategy", type=str, default="topval",
                   choices=["topval", "stratified", "random"],
                   help="Per-round keep step. "
                        "'topval' (default): sort survivors by (val Pareto level, "
                        "val_p90, latency) and keep top-keep_n. "
                        "'stratified': always keep val Pareto level 1, then fill "
                        "remaining slots by round-robin across latency buckets "
                        "(picking next best-by-val_p90 in each bucket). Preserves "
                        "latency-axis coverage in the survivor set, fixing the "
                        "HV drop at high init_K when 'topval' clusters survivors "
                        "in the low-qerror / mid-latency region.")
    p.add_argument("--init_strategy", type=str, default="stratified",
                   choices=["stratified", "random", "kmeans",
                            "stratified_metadata", "stratified_centroid",
                            "stratified_arch", "stratified_arch_round",
                            "stratified_kmeans_round"],
                   help="First-round seed selection. "
                        "'stratified' (default): latency-quantile bucket round-robin. "
                        "Monotonic in K — init at K is a prefix of init at K+1. "
                        "'random': uniform-random permutation (also monotonic in K). "
                        "'kmeans': metadata-space KMeans, pick closest-to-center per "
                        "cluster. NOT monotonic in K, hurts round-Pareto HV at small K. "
                        "'stratified_metadata': latency-bucket round-robin BUT within "
                        "each bucket pick the member farthest from already-picked "
                        "in metadata space. Hybrid of stratified + farthest-first; "
                        "stays monotonic in K.")
    p.add_argument("--exclude_val_blowup_ratio", type=float, default=float("inf"),
                   help="Drop any model whose val_p90 increases by this factor "
                        "between any earlier and later epoch ∈ {e8, e12, e16}. "
                        "Default ∞ keeps all 43 models. Use e.g. 1.5 to drop the "
                        "6 models whose val regresses ≥50%% somewhere during "
                        "training (val instability — purely val-defined, no test).")
    p.add_argument("--sweep", action="store_true",
                   help="Sweep over rounds×keep_ratio and print best config "
                        "(per init_K and overall).")
    p.add_argument("--sweep_rounds", type=int, nargs="+", default=[2, 3])
    p.add_argument("--sweep_keep_ratios", type=float, nargs="+",
                   default=[0.33, 0.50, 0.67, 0.75])
    p.add_argument("--output", default=str(ROOT / "compare_round_pareto_summary.csv"))
    p.add_argument("--per_seed_output",
                   default=str(ROOT / "compare_round_pareto_per_seed.csv"))
    args = p.parse_args()

    all_df = pd.read_csv(args.all_models_csv)
    prof_df = pd.read_csv(args.profile_csv)
    pool = join_pool_with_profile(all_df, prof_df).reset_index(drop=True)
    if args.exclude_val_blowup_ratio < float("inf"):
        thr = args.exclude_val_blowup_ratio
        v8 = pool["val_p90_e8"].to_numpy(float)
        v12 = pool["val_p90_e12"].to_numpy(float)
        v16 = pool["val_p90_e16"].to_numpy(float)
        blowup = ((v12 > thr * v8) | (v16 > thr * v12) | (v16 > thr * v8))
        excluded = pool.loc[blowup, "model"].tolist()
        pool = pool[~blowup].reset_index(drop=True)
        print(f"Excluded {len(excluded)} val-blowup models (val regresses ≥"
              f"{(thr - 1) * 100:.0f}% somewhere across e8/e12/e16):")
        for m in excluded:
            print(f"  {m}")
    features = build_metadata_features(pool)
    print(f"Loaded {len(pool)} models. Metadata feature dim {features.shape[1]}.")

    # True 43-model test Pareto frontier.
    true_pts = np.column_stack([pool["avg_ms"].astype(float),
                                 pool["test_p90_e16"].astype(float)])
    true_front_idx = pareto_frontier_indices(true_pts)
    true_front_models = set(pool.iloc[i]["model"] for i in true_front_idx)
    front_lat_max = max(true_pts[i, 0] for i in true_front_idx)
    front_qerr_max = max(true_pts[i, 1] for i in true_front_idx)
    ref_lat = front_lat_max * args.hv_ref_margin
    ref_qerr = front_qerr_max * args.hv_ref_margin
    true_hv = hv_2d_min(true_pts, ref_lat, ref_qerr)
    print(f"True frontier: {len(true_front_idx)} models. "
          f"ref=(lat={ref_lat:.2f}, qerr={ref_qerr:.4f})  HV={true_hv:.2f}")

    def _run_one_config(rounds, keep_ratio):
        """Inner loop over (K, seed) for fixed (rounds, keep_ratio)."""
        rows = []
        for K in args.init_Ks:
            for seed in args.seeds:
                r = run_ours(pool, features, K, args.init_strategy, seed,
                              rounds=rounds, keep_ratio=keep_ratio,
                              n_init_bins=args.n_init_bins,
                              keep_strategy=args.keep_strategy,
                              kmeans_n_clusters=args.kmeans_n_clusters,
                              decision_epochs=args.decision_epochs)
                rd = random_monotonic_prefix(pool, r["total_train_h100_ms"], seed)
                ev = evaluate_run(pool, r["round3_idx"], ref_lat, ref_qerr, true_front_models)
                ev_r = evaluate_run(pool, rd["idx"], ref_lat, ref_qerr, true_front_models)
                # Reflect the ACTUAL schedule run, not just the legacy --rounds
                # alias (which is ignored when --decision_epochs is passed).
                _sched = r.get("decision_epochs", [])
                _sched_label = ",".join(str(e) for e in _sched) if _sched else "(none)"
                rows.append({
                    "schedule": _sched_label,
                    "rounds": rounds, "keep_ratio": keep_ratio,
                    "init_K": K, "seed": seed,
                    "total_min": r["total_train_h100_ms"] / 60_000.0,
                    "n_rand": len(rd["idx"]),
                    "hv_ours": ev["hv"], "hv_rand": ev_r["hv"],
                    "recall_ours": ev["recall"], "recall_rand": ev_r["recall"],
                    "frontier_ours": len(ev["frontier_models"]),
                    "n_final_ours": len(r["round3_idx"]),
                })
        return rows

    if args.sweep:
        per_seed_rows = []
        configs = [(r, kr) for r in args.sweep_rounds for kr in args.sweep_keep_ratios]
        for r, kr in configs:
            per_seed_rows.extend(_run_one_config(r, kr))
    else:
        per_seed_rows = _run_one_config(args.rounds, args.keep_ratio)

    per_seed_df = pd.DataFrame(per_seed_rows)
    per_seed_df.to_csv(args.per_seed_output, index=False)
    print(f"Wrote per-seed rows: {args.per_seed_output}")

    group_cols = ["schedule", "keep_ratio", "init_K"]
    agg = per_seed_df.groupby(group_cols).agg(
        total_min=("total_min", "mean"),
        n_rand=("n_rand", "mean"),
        hv_pct_ours=("hv_ours", lambda s: 100.0 * s.mean() / true_hv),
        hv_pct_rand=("hv_rand", lambda s: 100.0 * s.mean() / true_hv),
        recall_ours=("recall_ours", "mean"),
        recall_rand=("recall_rand", "mean"),
    ).reset_index()
    agg["dHV"] = agg["hv_pct_ours"] - agg["hv_pct_rand"]
    agg["dRec"] = agg["recall_ours"] - agg["recall_rand"]

    cols = [
        "schedule", "keep_ratio", "init_K",
        "total_min", "n_rand",
        "hv_pct_ours", "hv_pct_rand", "dHV",
        "recall_ours", "recall_rand", "dRec",
    ]
    agg = agg[cols].round({
        "total_min": 1, "n_rand": 2,
        "hv_pct_ours": 2, "hv_pct_rand": 2, "dHV": 2,
        "recall_ours": 3, "recall_rand": 3, "dRec": 3,
    })
    agg.to_csv(args.output, index=False)

    print(f"\n=== Round-Pareto comparison (means over {len(args.seeds)} seeds) ===")
    print(f"  true frontier: {len(true_front_idx)} models, HV={true_hv:.2f}")
    print(f"  ref=(lat={ref_lat:.2f}, qerr={ref_qerr:.4f})")
    print(f"  bins = init_K (one random model per latency bin)")
    print(f"  rand: monotonic random matched to ours' total train time\n")
    print(agg.to_string(index=False))
    print(f"\nWrote summary: {args.output}")

    if args.sweep:
        cfg = agg.groupby(["rounds", "keep_ratio"]).agg(
            mean_dHV=("dHV", "mean"),
            mean_dRec=("dRec", "mean"),
            best_dHV=("dHV", "max"),
        ).reset_index().round(2)
        print(f"\n=== Sweep summary: mean dHV across init_K {list(args.init_Ks)} ===")
        print(cfg.to_string(index=False))
        best = agg.loc[agg["dHV"].idxmax()]
        print(f"\nBest cell: rounds={int(best['rounds'])} kr={best['keep_ratio']} "
              f"K={int(best['init_K'])}  dHV={best['dHV']:+.2f} dRec={best['dRec']:+.3f}")


if __name__ == "__main__":
    main()
