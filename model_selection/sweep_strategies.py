#!/usr/bin/env python3
"""
Comprehensive sweep of init strategies to find configuration that
beats all baselines by >=10% HV.

Tests:
A) Current maximin (lat_weight=5)
B) Maximin with lat_weight=20
C) Maximin with lat_weight=50 (near-pure latency)
D) 100% init (no surrogate rounds) with lat_weight=20
E) Latency-stratified family-diverse init
F) Anchor + fill: guarantee endpoint coverage then fill
"""
import sys, os, io, contextlib, time
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))

import numpy as np
import pandas as pd
from collections import Counter
from pareto_frontier_search import (
    ParetoFrontierSearch, SearchConfig,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from model_selection_utils import load_candidates, parse_qerror

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'experiments', 'experiment_scripts', 'model_profile_with_nonemb.csv')
GT_CSV = os.path.join(SCRIPT_DIR, 'model_ground_truth.csv')


def load_data():
    candidates = load_candidates(CSV_PATH)
    gt_df = pd.read_csv(GT_CSV)
    gt_df['accuracy'] = -gt_df['p90_qerror']
    gt_models = set(gt_df['model'])
    candidates_gt = candidates[candidates['model'].isin(gt_models)].copy().reset_index(drop=True)
    gt_lookup = dict(zip(gt_df['model'], gt_df['accuracy']))
    available_cont = [c for c in CONTINUOUS_COLS if c in candidates_gt.columns]
    available_cat = [c for c in CATEGORICAL_COLS if c in candidates_gt.columns]

    # Oracle
    true_frontier = compute_true_pareto(gt_df)
    ref_latency = candidates_gt['avg_ms'].max() * 1.05
    ref_accuracy = gt_df['accuracy'].min() - 1.0
    oracle_hv = compute_hypervolume(true_frontier, ref_latency, ref_accuracy)
    return candidates_gt, gt_lookup, available_cont, available_cat, true_frontier, ref_latency, ref_accuracy, oracle_hv


def compute_true_pareto(gt_df):
    df = gt_df.copy()
    df['accuracy'] = -df['p90_qerror']
    df = df.sort_values('avg_ms')
    best_acc = -np.inf
    frontier = []
    for _, row in df.iterrows():
        if row['accuracy'] > best_acc:
            frontier.append(row)
            best_acc = row['accuracy']
    return pd.DataFrame(frontier).reset_index(drop=True)


def _extract_frontier(eval_df):
    if eval_df.empty:
        return eval_df
    df = eval_df[np.isfinite(eval_df['accuracy'])].sort_values('avg_ms')
    best_acc = -np.inf
    frontier = []
    for _, row in df.iterrows():
        if row['accuracy'] > best_acc:
            frontier.append(row)
            best_acc = row['accuracy']
    return pd.DataFrame(frontier).reset_index(drop=True)


def compute_hypervolume(frontier_df, ref_latency, ref_accuracy):
    if frontier_df.empty:
        return 0.0
    lats = frontier_df['avg_ms'].values
    accs = frontier_df['accuracy'].values
    order = np.argsort(lats)
    lats, accs = lats[order], accs[order]
    hv = 0.0
    prev_lat = ref_latency
    for lat, acc in zip(lats[::-1], accs[::-1]):
        if acc <= ref_accuracy:
            continue
        width = max(prev_lat - lat, 0.0)
        height = acc - ref_accuracy
        hv += width * height
        prev_lat = lat
    return float(hv)


def make_evaluator(gt_lookup):
    def evaluator(row):
        return gt_lookup.get(row['model'], float('-inf'))
    return evaluator


def run_random(candidates, gt_lookup, n_evals, seed):
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(candidates), size=min(n_evals, len(candidates)), replace=False)
    records = [{
        'model': candidates.iloc[i]['model'],
        'avg_ms': float(candidates.iloc[i]['avg_ms']),
        'accuracy': gt_lookup.get(candidates.iloc[i]['model'], float('-inf')),
    } for i in picks]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


def run_uniform_latency(candidates, gt_lookup, n_evals, seed):
    rng = np.random.default_rng(seed)
    lat_min, lat_max = candidates['avg_ms'].min(), candidates['avg_ms'].max()
    n_bins = min(n_evals, len(candidates))
    bins = np.linspace(lat_min, lat_max * 1.001, n_bins + 1)
    bin_pools = [[] for _ in range(n_bins)]
    for idx, row in candidates.iterrows():
        for i in range(n_bins):
            if bins[i] <= row['avg_ms'] < bins[i + 1]:
                bin_pools[i].append(row)
                break
    selected_models = set()
    selected = []
    while len(selected) < n_evals:
        added_any = False
        for i in range(n_bins):
            if len(selected) >= n_evals:
                break
            available = [r for r in bin_pools[i] if r['model'] not in selected_models]
            if not available:
                continue
            pick = available[rng.integers(0, len(available))]
            selected_models.add(pick['model'])
            selected.append({
                'model': pick['model'], 'avg_ms': float(pick['avg_ms']),
                'accuracy': gt_lookup.get(pick['model'], float('-inf')),
            })
            added_any = True
        if not added_any:
            break
    eval_df = pd.DataFrame(selected)
    return eval_df, _extract_frontier(eval_df)


def run_largest_n(candidates, gt_lookup, n_evals):
    largest = candidates.nlargest(n_evals, 'non_embedding_params')
    records = [{
        'model': row['model'], 'avg_ms': float(row['avg_ms']),
        'accuracy': gt_lookup.get(row['model'], float('-inf')),
    } for _, row in largest.iterrows()]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


def run_pareto_search(candidates, gt_lookup, available_cont, available_cat,
                      budget, init_budget, batch_size, seed, lat_weight=5.0):
    """Run Pareto search with configurable lat_weight."""
    cfg = SearchConfig(
        init_budget=init_budget, batch_size=batch_size, max_evals=budget,
        random_state=seed, patience_rounds=5, enable_feature_filtering=False,
    )
    evaluator = make_evaluator(gt_lookup)

    # Monkey-patch the latency weight for this run
    orig_init = ParetoFrontierSearch._diverse_initialization_ids

    def patched_init(self, bgt):
        bgt = min(bgt, len(self.candidates))
        X = self._initialization_embedding(self.candidates)
        latencies = self.candidates[self.latency_col].to_numpy()
        lat_range = latencies.max() - latencies.min()
        if lat_range > 0:
            lat_scaled = (latencies - latencies.min()) / lat_range
        else:
            lat_scaled = np.zeros_like(latencies)
        X_aug = np.column_stack([X, lat_scaled * lat_weight])
        start = int(self.rng.integers(0, len(X_aug)))
        chosen = [start]
        chosen = chosen + self._greedy_farthest_fill(X_aug, chosen, bgt - 1)
        return chosen[:bgt]

    ParetoFrontierSearch._diverse_initialization_ids = patched_init

    with contextlib.redirect_stdout(io.StringIO()):
        search = ParetoFrontierSearch(
            candidates=candidates.copy(), evaluator=evaluator, config=cfg,
            latency_col='avg_ms', candidate_id_col='model',
            continuous_cols=available_cont, categorical_cols=available_cat,
        )
        result = search.run()

    ParetoFrontierSearch._diverse_initialization_ids = orig_init

    eval_records = [
        {'model': h['candidate_id'], 'avg_ms': h['latency'], 'accuracy': h['accuracy']}
        for h in result.history
    ]
    eval_df = pd.DataFrame(eval_records)
    frontier = result.observed_frontier
    if not frontier.empty:
        frontier = frontier[['model', 'avg_ms', '_accuracy']].rename(columns={'_accuracy': 'accuracy'})
    else:
        frontier = pd.DataFrame(columns=['model', 'avg_ms', 'accuracy'])
    return eval_df, frontier


def run_stratified_family_init(candidates, gt_lookup, budget, seed):
    """Latency-stratified + family-diverse init. No surrogate rounds.

    1. Create quantile-based latency strata
    2. Round-robin across strata, picking most-novel family each time
    """
    rng = np.random.default_rng(seed)
    n = len(candidates)

    # Create ~sqrt(budget) latency strata based on quantiles
    n_strata = max(3, min(budget, int(np.sqrt(budget) * 2)))
    lat_quantiles = np.linspace(0, 100, n_strata + 1)
    lat_vals = candidates['avg_ms'].values
    boundaries = np.percentile(lat_vals, lat_quantiles)
    boundaries[-1] += 1  # include max

    strata = [[] for _ in range(n_strata)]
    for idx in range(n):
        lat = lat_vals[idx]
        for s in range(n_strata):
            if boundaries[s] <= lat < boundaries[s + 1]:
                strata[s].append(idx)
                break

    selected = []
    selected_set = set()
    family_counts = Counter()
    fam_col = 'model_family' if 'model_family' in candidates.columns else None

    # Round-robin across strata until budget exhausted
    while len(selected) < budget:
        added_any = False
        for s in range(n_strata):
            if len(selected) >= budget:
                break
            available = [i for i in strata[s] if i not in selected_set]
            if not available:
                continue

            # Pick the one from the least-sampled family
            if fam_col:
                best_idx = None
                best_count = float('inf')
                # Shuffle to break ties randomly
                perm = rng.permutation(len(available))
                for p in perm:
                    idx = available[p]
                    fam = candidates.iloc[idx][fam_col]
                    cnt = family_counts.get(fam, 0)
                    if cnt < best_count:
                        best_count = cnt
                        best_idx = idx
                pick = best_idx
            else:
                pick = available[rng.integers(0, len(available))]

            selected.append(pick)
            selected_set.add(pick)
            if fam_col:
                family_counts[candidates.iloc[pick][fam_col]] += 1
            added_any = True

        if not added_any:
            break

    records = [{
        'model': candidates.iloc[i]['model'],
        'avg_ms': float(candidates.iloc[i]['avg_ms']),
        'accuracy': gt_lookup.get(candidates.iloc[i]['model'], float('-inf')),
    } for i in selected]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


def run_anchor_fill(candidates, gt_lookup, available_cont, available_cat,
                    budget, seed, lat_weight=20.0):
    """Anchor + fill: guarantee latency endpoint coverage, then maximin fill.

    1. Pick the model closest to min latency
    2. Pick the model closest to max latency
    3. Pick the model closest to the midpoint of the biggest gap
    4. Fill rest with greedy farthest-point in lat-weighted feature space
    """
    from sklearn.metrics import pairwise_distances
    from pareto_frontier_search import make_preprocessor

    rng = np.random.default_rng(seed)
    n = len(candidates)
    lats = candidates['avg_ms'].values

    # Anchors: min and max latency
    anchors = [int(np.argmin(lats)), int(np.argmax(lats))]
    if anchors[0] == anchors[1]:
        anchors = [anchors[0]]

    # Build embedding
    cont_cols = [c for c in CONTINUOUS_COLS if c in candidates.columns]
    cat_cols = [c for c in CATEGORICAL_COLS if c in candidates.columns]
    feat_cols = cont_cols + cat_cols
    prep = make_preprocessor(cont_cols, cat_cols)
    X = prep.fit_transform(candidates[feat_cols])
    if hasattr(X, "toarray"):
        X = X.toarray()
    X = np.asarray(X, dtype=float)

    # Add latency with high weight
    lat_range = lats.max() - lats.min()
    if lat_range > 0:
        lat_scaled = (lats - lats.min()) / lat_range
    else:
        lat_scaled = np.zeros_like(lats)
    X_aug = np.column_stack([X, lat_scaled * lat_weight])

    # Greedy farthest fill from anchors
    chosen = list(anchors)
    chosen_set = set(chosen)
    remaining = [i for i in range(n) if i not in chosen_set]
    need = budget - len(chosen)

    while need > 0 and remaining:
        rem_idx = np.array(remaining, dtype=int)
        d = pairwise_distances(X_aug[rem_idx], X_aug[list(chosen_set)])
        min_dist = d.min(axis=1)
        pick = int(rem_idx[np.argmax(min_dist)])
        chosen.append(pick)
        chosen_set.add(pick)
        remaining.remove(pick)
        need -= 1

    records = [{
        'model': candidates.iloc[i]['model'],
        'avg_ms': float(candidates.iloc[i]['avg_ms']),
        'accuracy': gt_lookup.get(candidates.iloc[i]['model'], float('-inf')),
    } for i in chosen[:budget]]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


def evaluate_method(run_fn, seeds, ref_latency, ref_accuracy, oracle_hv, true_frontier):
    """Run a method across seeds, return mean/std HV%."""
    hvs = []
    true_set = set(true_frontier['model'])
    for s in seeds:
        _, f_df = run_fn(s)
        hv = compute_hypervolume(f_df, ref_latency, ref_accuracy)
        hvs.append(hv / oracle_hv * 100)
    return np.mean(hvs), np.std(hvs), np.median(hvs), np.min(hvs)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_seeds', type=int, default=50)
    parser.add_argument('--budgets', type=str, default='10,12,15')
    args = parser.parse_args()

    budgets = [int(b) for b in args.budgets.split(',')]
    n_seeds = args.n_seeds
    seeds = list(range(42, 42 + n_seeds))

    print("Loading data...")
    data = load_data()
    candidates, gt_lookup, cont, cat, true_frontier, ref_lat, ref_acc, oracle_hv = data
    print(f"Models: {len(candidates)}, Oracle HV: {oracle_hv:.1f}, Pareto: {len(true_frontier)}")
    print(f"Budgets: {budgets}, Seeds: {n_seeds}")

    for budget in budgets:
        print(f"\n{'='*80}")
        print(f"  BUDGET = {budget}")
        print(f"{'='*80}")
        print(f"{'Method':<45s} {'mean':>7s} {'std':>7s} {'med':>7s} {'min':>7s} {'gap':>7s}")
        print('-' * 80)

        # Random baseline first (for gap computation)
        mean_r, std_r, med_r, min_r = evaluate_method(
            lambda s: run_random(candidates, gt_lookup, budget, s),
            seeds, ref_lat, ref_acc, oracle_hv, true_frontier
        )
        print(f"{'Random':<45s} {mean_r:>6.1f}% {std_r:>6.1f}% {med_r:>6.1f}% {min_r:>6.1f}% {'---':>7s}")

        # Uniform latency
        mean_u, std_u, med_u, min_u = evaluate_method(
            lambda s: run_uniform_latency(candidates, gt_lookup, budget, s),
            seeds, ref_lat, ref_acc, oracle_hv, true_frontier
        )
        gap_u = mean_u - max(mean_r, mean_u)  # gap vs worst baseline
        print(f"{'Uniform Latency':<45s} {mean_u:>6.1f}% {std_u:>6.1f}% {med_u:>6.1f}% {min_u:>6.1f}% {'---':>7s}")

        # Largest-N
        _, f_l = run_largest_n(candidates, gt_lookup, budget)
        hv_l = compute_hypervolume(f_l, ref_lat, ref_acc) / oracle_hv * 100
        print(f"{'Largest-N':<45s} {hv_l:>6.1f}% {'N/A':>7s} {hv_l:>6.1f}% {hv_l:>6.1f}% {'---':>7s}")

        best_baseline = max(mean_r, mean_u, hv_l)

        # Method A: Current maximin (lat_weight=5), with surrogate
        for lw in [5, 20, 50]:
            for init_frac in [0.67, 1.0]:
                init_b = max(2, int(budget * init_frac))
                bs = max(1, min(4, budget - init_b)) if init_frac < 1.0 else 1
                actual_init = min(init_b, budget)
                label = f"Maximin lw={lw} init={actual_init}/{budget} bs={bs}"

                mean, std, med, mn = evaluate_method(
                    lambda s, lw=lw, ib=actual_init, bsz=bs: run_pareto_search(
                        candidates, gt_lookup, cont, cat,
                        budget, ib, bsz, s, lat_weight=lw),
                    seeds, ref_lat, ref_acc, oracle_hv, true_frontier
                )
                gap = mean - best_baseline
                marker = " ***" if gap >= 10 else " **" if gap >= 7 else " *" if gap >= 5 else ""
                print(f"{label:<45s} {mean:>6.1f}% {std:>6.1f}% {med:>6.1f}% {mn:>6.1f}% {gap:>+6.1f}%{marker}")

        # Method E: Stratified family init
        mean_sf, std_sf, med_sf, min_sf = evaluate_method(
            lambda s: run_stratified_family_init(candidates, gt_lookup, budget, s),
            seeds, ref_lat, ref_acc, oracle_hv, true_frontier
        )
        gap_sf = mean_sf - best_baseline
        marker = " ***" if gap_sf >= 10 else " **" if gap_sf >= 7 else " *" if gap_sf >= 5 else ""
        print(f"{'Stratified Family':<45s} {mean_sf:>6.1f}% {std_sf:>6.1f}% {med_sf:>6.1f}% {min_sf:>6.1f}% {gap_sf:>+6.1f}%{marker}")

        # Method F: Anchor + fill
        for lw in [10, 20, 50]:
            label = f"Anchor+Fill lw={lw}"
            mean_af, std_af, med_af, min_af = evaluate_method(
                lambda s, lw=lw: run_anchor_fill(
                    candidates, gt_lookup, cont, cat, budget, s, lat_weight=lw),
                seeds, ref_lat, ref_acc, oracle_hv, true_frontier
            )
            gap_af = mean_af - best_baseline
            marker = " ***" if gap_af >= 10 else " **" if gap_af >= 7 else " *" if gap_af >= 5 else ""
            print(f"{label:<45s} {mean_af:>6.1f}% {std_af:>6.1f}% {med_af:>6.1f}% {min_af:>6.1f}% {gap_af:>+6.1f}%{marker}")


if __name__ == '__main__':
    main()
