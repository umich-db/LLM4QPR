#!/usr/bin/env python3
"""
Test Pareto frontier search vs baselines on real model candidates.

Metrics:
  1. Hypervolume (standard MOO metric)
  2. Number of true Pareto-optimal points found
  3. Spacing (evenness of frontier coverage)
  4. Generational Distance (GD) to oracle frontier
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))

import numpy as np
import pandas as pd
import glob
from argparse import Namespace
from pareto_frontier_search import (
    ParetoFrontierSearch, SearchConfig,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from model_selection_v2 import (
    load_candidates, find_cdf_file, parse_qerror,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'experiments', 'experiment_scripts', 'model_profile_with_nonemb.csv')


# ─── Ground truth ──────────────────────────────────────────────────────────
def build_ground_truth(candidates, args):
    """Get real accuracy for all models from cached CDF results."""
    records = []
    for _, row in candidates.iterrows():
        cached = find_cdf_file(row['model'], args)
        if cached is None:
            continue
        qe = parse_qerror(cached)
        records.append({
            'model': row['model'],
            'avg_ms': float(row['avg_ms']),
            'accuracy': -qe['p90'],
            'non_embedding_params': float(row['non_embedding_params']),
        })
    return pd.DataFrame(records)


def compute_true_pareto(gt_df):
    """Compute the true Pareto frontier from ground truth."""
    df = gt_df.sort_values('avg_ms').copy()
    best_acc = -np.inf
    frontier = []
    for _, row in df.iterrows():
        if row['accuracy'] > best_acc:
            frontier.append(row)
            best_acc = row['accuracy']
    return pd.DataFrame(frontier).reset_index(drop=True)


# ─── Metrics ────────────────────────────────────────────────────────────────
def compute_hypervolume(frontier_df, ref_latency, ref_accuracy):
    """2D hypervolume with reference point (ref_latency, ref_accuracy).
    Convention: lower latency is better, higher accuracy is better.
    We compute HV as area dominated by frontier above ref_accuracy and left of ref_latency."""
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


def count_true_pareto_found(recovered_frontier, true_frontier):
    """How many true Pareto-optimal models appear in the recovered frontier."""
    true_set = set(true_frontier['model'])
    recovered_set = set(recovered_frontier['model'])
    return len(true_set & recovered_set)


def spacing_metric(frontier_df):
    """Spacing: std of consecutive distances along the frontier.
    Lower = more evenly distributed."""
    if len(frontier_df) < 2:
        return 0.0
    lats = np.sort(frontier_df['avg_ms'].values)
    gaps = np.diff(lats)
    return float(np.std(gaps))


def generational_distance(recovered_df, true_frontier_df):
    """Average min-distance from each recovered frontier point to the true frontier.
    Uses normalized (latency, accuracy) space."""
    if recovered_df.empty or true_frontier_df.empty:
        return float('inf')

    # Normalize
    all_lats = np.concatenate([recovered_df['avg_ms'].values, true_frontier_df['avg_ms'].values])
    all_accs = np.concatenate([recovered_df['accuracy'].values, true_frontier_df['accuracy'].values])
    lat_range = max(all_lats.max() - all_lats.min(), 1e-12)
    acc_range = max(all_accs.max() - all_accs.min(), 1e-12)

    rec_pts = np.column_stack([
        (recovered_df['avg_ms'].values - all_lats.min()) / lat_range,
        (recovered_df['accuracy'].values - all_accs.min()) / acc_range,
    ])
    true_pts = np.column_stack([
        (true_frontier_df['avg_ms'].values - all_lats.min()) / lat_range,
        (true_frontier_df['accuracy'].values - all_accs.min()) / acc_range,
    ])

    from sklearn.metrics import pairwise_distances
    dists = pairwise_distances(rec_pts, true_pts)
    min_dists = dists.min(axis=1)
    return float(np.mean(min_dists))


def inverted_generational_distance(recovered_df, true_frontier_df):
    """Average min-distance from each TRUE frontier point to the recovered frontier.
    Measures how well the recovered front covers the true front."""
    if recovered_df.empty or true_frontier_df.empty:
        return float('inf')

    all_lats = np.concatenate([recovered_df['avg_ms'].values, true_frontier_df['avg_ms'].values])
    all_accs = np.concatenate([recovered_df['accuracy'].values, true_frontier_df['accuracy'].values])
    lat_range = max(all_lats.max() - all_lats.min(), 1e-12)
    acc_range = max(all_accs.max() - all_accs.min(), 1e-12)

    rec_pts = np.column_stack([
        (recovered_df['avg_ms'].values - all_lats.min()) / lat_range,
        (recovered_df['accuracy'].values - all_accs.min()) / acc_range,
    ])
    true_pts = np.column_stack([
        (true_frontier_df['avg_ms'].values - all_lats.min()) / lat_range,
        (true_frontier_df['accuracy'].values - all_accs.min()) / acc_range,
    ])

    from sklearn.metrics import pairwise_distances
    dists = pairwise_distances(true_pts, rec_pts)
    min_dists = dists.min(axis=1)
    return float(np.mean(min_dists))


# ─── Evaluator using cached CDF results ────────────────────────────────────
def make_evaluator(gt_lookup):
    """Return evaluator that looks up accuracy from ground truth dict."""
    def evaluator(row):
        model = row['model']
        if model in gt_lookup:
            return gt_lookup[model]
        return float('-inf')
    return evaluator


# ─── Baselines ──────────────────────────────────────────────────────────────
def baseline_uniform_latency(candidates, gt_lookup, n_evals):
    """Baseline: uniformly sample models across the latency range."""
    lat_min = candidates['avg_ms'].min()
    lat_max = candidates['avg_ms'].max()
    bins = np.linspace(lat_min, lat_max, n_evals + 1)

    selected = []
    for i in range(n_evals):
        bin_models = candidates[(candidates['avg_ms'] >= bins[i]) & (candidates['avg_ms'] < bins[i+1])]
        if bin_models.empty:
            continue
        # Pick one random model per bin
        pick = bin_models.sample(1, random_state=42 + i).iloc[0]
        selected.append({
            'model': pick['model'],
            'avg_ms': float(pick['avg_ms']),
            'accuracy': gt_lookup.get(pick['model'], float('-inf')),
        })

    eval_df = pd.DataFrame(selected)
    # Compute frontier from evaluated
    return _extract_frontier(eval_df)


def baseline_uniform_latency_seeded(candidates, gt_lookup, n_evals, seed):
    """Baseline: uniformly sample models across the latency range with seed."""
    rng = np.random.default_rng(seed)
    lat_min = candidates['avg_ms'].min()
    lat_max = candidates['avg_ms'].max()
    bins = np.linspace(lat_min, lat_max, n_evals + 1)

    selected = []
    for i in range(n_evals):
        bin_models = candidates[(candidates['avg_ms'] >= bins[i]) & (candidates['avg_ms'] < bins[i+1])]
        if bin_models.empty:
            continue
        pick_idx = rng.integers(0, len(bin_models))
        pick = bin_models.iloc[pick_idx]
        selected.append({
            'model': pick['model'],
            'avg_ms': float(pick['avg_ms']),
            'accuracy': gt_lookup.get(pick['model'], float('-inf')),
        })

    eval_df = pd.DataFrame(selected)
    return _extract_frontier(eval_df), len(eval_df)


def baseline_largest_n(candidates, gt_lookup, n_evals):
    """Baseline: pick the n largest models by non_embedding_params."""
    largest = candidates.nlargest(n_evals, 'non_embedding_params')
    records = []
    for _, row in largest.iterrows():
        records.append({
            'model': row['model'],
            'avg_ms': float(row['avg_ms']),
            'accuracy': gt_lookup.get(row['model'], float('-inf')),
        })
    eval_df = pd.DataFrame(records)
    return _extract_frontier(eval_df)


def baseline_random(candidates, gt_lookup, n_evals, seed):
    """Baseline: randomly pick n models."""
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(candidates), size=min(n_evals, len(candidates)), replace=False)
    records = []
    for idx in picks:
        row = candidates.iloc[idx]
        records.append({
            'model': row['model'],
            'avg_ms': float(row['avg_ms']),
            'accuracy': gt_lookup.get(row['model'], float('-inf')),
        })
    eval_df = pd.DataFrame(records)
    return _extract_frontier(eval_df), len(eval_df)


def _extract_frontier(eval_df):
    """Extract Pareto frontier from evaluated models."""
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


# ─── Main ───────────────────────────────────────────────────────────────────
def run_pareto_search(candidates, gt_lookup, available_cont, available_cat, seed, config):
    """Run ParetoFrontierSearch with given config and seed."""
    config_copy = SearchConfig(
        init_budget=config.init_budget,
        batch_size=config.batch_size,
        max_evals=config.max_evals,
        random_state=seed,
        exploration_weight=config.exploration_weight,
        coverage_weight=config.coverage_weight,
        diversity_weight=config.diversity_weight,
        ensemble_size=config.ensemble_size,
        rf_num_trees=config.rf_num_trees,
        rf_min_samples_leaf=config.rf_min_samples_leaf,
        enable_feature_filtering=config.enable_feature_filtering,
        feature_filter_after=config.feature_filter_after,
        keep_top_k_features=config.keep_top_k_features,
        patience_rounds=config.patience_rounds,
    )

    import io, contextlib
    evaluator = make_evaluator(gt_lookup)
    with contextlib.redirect_stdout(io.StringIO()):
        search = ParetoFrontierSearch(
            candidates=candidates.copy(),
            evaluator=evaluator,
            config=config_copy,
            latency_col='avg_ms',
            candidate_id_col='model',
            continuous_cols=available_cont,
            categorical_cols=available_cat,
        )
        result = search.run()

    # Build frontier df with model, avg_ms, accuracy columns
    frontier = result.observed_frontier
    if not frontier.empty:
        frontier = frontier[['model', 'avg_ms', '_accuracy']].rename(columns={'_accuracy': 'accuracy'})
    return frontier, len(result.evaluated)


def main():
    candidates = load_candidates(CSV_PATH)
    print(f"Loaded {len(candidates)} candidate models")

    args = Namespace(
        dry_run=False, workload='stats', task='time', db='postgres',
        quantification='4-bit', embed_size=1000, price_s=True,
        max_eval_queries=200, csv=CSV_PATH,
    )

    # Build ground truth
    gt_df = build_ground_truth(candidates, args)
    gt_lookup = dict(zip(gt_df['model'], gt_df['accuracy']))
    print(f"Ground truth: {len(gt_df)} models with cached results")

    # Filter candidates to those with ground truth
    candidates_with_gt = candidates[candidates['model'].isin(gt_lookup)].copy().reset_index(drop=True)
    print(f"Candidates with ground truth: {len(candidates_with_gt)}")

    # True Pareto frontier
    true_frontier = compute_true_pareto(gt_df)
    print(f"\nTrue Pareto frontier: {len(true_frontier)} models")
    for _, r in true_frontier.iterrows():
        print(f"  {r['model']:55s}  lat={r['avg_ms']:6.1f}ms  p90={-r['accuracy']:.2f}")

    # Reference point for hypervolume
    ref_latency = candidates_with_gt['avg_ms'].max() * 1.05
    ref_accuracy = gt_df['accuracy'].min() - 1.0
    oracle_hv = compute_hypervolume(true_frontier, ref_latency, ref_accuracy)
    print(f"\nOracle hypervolume: {oracle_hv:.2f}")
    print(f"Reference point: latency={ref_latency:.1f}ms, accuracy={ref_accuracy:.2f}")

    # Feature columns
    available_cont = [c for c in CONTINUOUS_COLS if c in candidates_with_gt.columns]
    available_cat = [c for c in CATEGORICAL_COLS if c in candidates_with_gt.columns]

    # Config
    max_evals = 30
    config = SearchConfig(
        init_budget=10,
        batch_size=4,
        max_evals=max_evals,
        patience_rounds=5,
        enable_feature_filtering=False,
    )

    seeds = [42, 123, 7, 99, 256, 314, 500, 777, 1000, 2024]

    # ─── Run methods ──────────────────────────────────────────────────
    methods = {}

    # 1. Our Pareto search
    print(f"\n{'='*70}")
    print(f"  Pareto Frontier Search (init={config.init_budget}, batch={config.batch_size}, max={max_evals})")
    print(f"{'='*70}")
    pareto_results = []
    for seed in seeds:
        frontier, n_eval = run_pareto_search(
            candidates_with_gt, gt_lookup, available_cont, available_cat, seed, config)
        hv = compute_hypervolume(frontier, ref_latency, ref_accuracy)
        n_true = count_true_pareto_found(frontier, true_frontier)
        sp = spacing_metric(frontier)
        gd = generational_distance(frontier, true_frontier)
        igd = inverted_generational_distance(frontier, true_frontier)
        pareto_results.append({
            'seed': seed, 'hv': hv, 'hv_ratio': hv/oracle_hv,
            'n_frontier': len(frontier), 'n_true_found': n_true,
            'spacing': sp, 'gd': gd, 'igd': igd, 'n_eval': n_eval,
        })
        print(f"  seed={seed:>4d}  HV={hv:.1f} ({hv/oracle_hv:.1%})  "
              f"frontier={len(frontier)}  true_found={n_true}/{len(true_frontier)}  "
              f"GD={gd:.4f}  IGD={igd:.4f}  evals={n_eval}")
    methods['Pareto Search'] = pareto_results

    # 2. Uniform latency baseline
    print(f"\n{'='*70}")
    print(f"  Baseline: Uniform Latency Sampling ({max_evals} evals)")
    print(f"{'='*70}")
    uniform_results = []
    for seed in seeds:
        frontier, n_eval = baseline_uniform_latency_seeded(candidates_with_gt, gt_lookup, max_evals, seed)
        hv = compute_hypervolume(frontier, ref_latency, ref_accuracy)
        n_true = count_true_pareto_found(frontier, true_frontier)
        sp = spacing_metric(frontier)
        gd = generational_distance(frontier, true_frontier)
        igd = inverted_generational_distance(frontier, true_frontier)
        uniform_results.append({
            'seed': seed, 'hv': hv, 'hv_ratio': hv/oracle_hv,
            'n_frontier': len(frontier), 'n_true_found': n_true,
            'spacing': sp, 'gd': gd, 'igd': igd, 'n_eval': n_eval,
        })
        print(f"  seed={seed:>4d}  HV={hv:.1f} ({hv/oracle_hv:.1%})  "
              f"frontier={len(frontier)}  true_found={n_true}/{len(true_frontier)}  "
              f"GD={gd:.4f}  IGD={igd:.4f}  evals={n_eval}")
    methods['Uniform Latency'] = uniform_results

    # 3. Random baseline
    print(f"\n{'='*70}")
    print(f"  Baseline: Random Selection ({max_evals} evals)")
    print(f"{'='*70}")
    random_results = []
    for seed in seeds:
        frontier, n_eval = baseline_random(candidates_with_gt, gt_lookup, max_evals, seed)
        hv = compute_hypervolume(frontier, ref_latency, ref_accuracy)
        n_true = count_true_pareto_found(frontier, true_frontier)
        sp = spacing_metric(frontier)
        gd = generational_distance(frontier, true_frontier)
        igd = inverted_generational_distance(frontier, true_frontier)
        random_results.append({
            'seed': seed, 'hv': hv, 'hv_ratio': hv/oracle_hv,
            'n_frontier': len(frontier), 'n_true_found': n_true,
            'spacing': sp, 'gd': gd, 'igd': igd, 'n_eval': n_eval,
        })
        print(f"  seed={seed:>4d}  HV={hv:.1f} ({hv/oracle_hv:.1%})  "
              f"frontier={len(frontier)}  true_found={n_true}/{len(true_frontier)}  "
              f"GD={gd:.4f}  IGD={igd:.4f}  evals={n_eval}")
    methods['Random'] = random_results

    # 4. Largest-N baseline (deterministic)
    print(f"\n{'='*70}")
    print(f"  Baseline: Largest {max_evals} Models")
    print(f"{'='*70}")
    frontier_largest = baseline_largest_n(candidates_with_gt, gt_lookup, max_evals)
    hv_largest = compute_hypervolume(frontier_largest, ref_latency, ref_accuracy)
    n_true_largest = count_true_pareto_found(frontier_largest, true_frontier)
    sp_largest = spacing_metric(frontier_largest)
    gd_largest = generational_distance(frontier_largest, true_frontier)
    igd_largest = inverted_generational_distance(frontier_largest, true_frontier)
    print(f"  HV={hv_largest:.1f} ({hv_largest/oracle_hv:.1%})  "
          f"frontier={len(frontier_largest)}  true_found={n_true_largest}/{len(true_frontier)}  "
          f"GD={gd_largest:.4f}  IGD={igd_largest:.4f}")

    # ─── Summary ──────────────────────────────────────────────────────
    print(f"\n\n{'='*90}")
    print(f"  SUMMARY (max_evals={max_evals}, {len(seeds)} seeds, oracle frontier={len(true_frontier)} models)")
    print(f"{'='*90}")
    print(f"{'Method':<22s} {'HV%':>6s} {'HV%std':>6s} {'#Front':>6s} {'#True':>6s} "
          f"{'GD':>7s} {'IGD':>7s} {'Spacing':>7s}")
    print('-' * 80)

    for name, results in methods.items():
        df = pd.DataFrame(results)
        print(f"{name:<22s} {df['hv_ratio'].mean():>5.1%} {df['hv_ratio'].std():>6.1%} "
              f"{df['n_frontier'].mean():>6.1f} {df['n_true_found'].mean():>6.1f} "
              f"{df['gd'].mean():>7.4f} {df['igd'].mean():>7.4f} {df['spacing'].mean():>7.2f}")

    print(f"{'Largest-N':<22s} {hv_largest/oracle_hv:>5.1%} {'N/A':>6s} "
          f"{len(frontier_largest):>6.1f} {n_true_largest:>6.1f} "
          f"{gd_largest:>7.4f} {igd_largest:>7.4f} {sp_largest:>7.2f}")

    print(f"\nOracle:                100.0%        {len(true_frontier):>6.1f} {len(true_frontier):>6.1f}")


if __name__ == '__main__':
    main()
