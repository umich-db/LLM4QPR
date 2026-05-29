#!/usr/bin/env python3
"""Diagnostic script: run Pareto search with verbose logging to understand failures."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))

import numpy as np
import pandas as pd
from pareto_frontier_search import (
    ParetoFrontierSearch, SearchConfig,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from model_selection_utils import load_candidates, parse_qerror
from plot_pareto_comparison import (
    find_cdf_file_maxq, compute_hypervolume,
    CSV_PATH, EXPERIMENTS_DIR,
)

def compute_true_pareto(gt_df):
    df = gt_df.sort_values('avg_ms').copy()
    best_acc = -np.inf
    frontier = []
    for _, row in df.iterrows():
        if row['accuracy'] > best_acc:
            frontier.append(row)
            best_acc = row['accuracy']
    return pd.DataFrame(frontier).reset_index(drop=True)

# ── Load data ──
candidates = load_candidates(CSV_PATH)
gt_records = []
for _, row in candidates.iterrows():
    cdf = find_cdf_file_maxq(row['model'])
    if cdf is None:
        continue
    qe = parse_qerror(cdf)
    gt_records.append({
        'model': row['model'], 'avg_ms': float(row['avg_ms']),
        'accuracy': -qe['p90'], 'p90': qe['p90'],
    })
gt_df = pd.DataFrame(gt_records)
gt_lookup = dict(zip(gt_df['model'], gt_df['accuracy']))

candidates_gt = candidates[candidates['model'].isin(gt_lookup)].copy().reset_index(drop=True)
print(f"Models: {len(candidates_gt)}, Ground truth: {len(gt_df)}")

true_frontier = compute_true_pareto(gt_df)
ref_latency = candidates_gt['avg_ms'].max() * 1.05
ref_accuracy = gt_df['accuracy'].min() - 1.0
oracle_hv = compute_hypervolume(true_frontier, ref_latency, ref_accuracy)

print(f"\nTrue Pareto frontier ({len(true_frontier)} models):")
for _, r in true_frontier.iterrows():
    print(f"  {r['model']:55s}  lat={r['avg_ms']:6.1f}ms  p90={r['p90']:.1f}")

# ── Run Pareto search with full logging ──
available_cont = [c for c in CONTINUOUS_COLS if c in candidates_gt.columns]
available_cat = [c for c in CATEGORICAL_COLS if c in candidates_gt.columns]

def evaluator(row):
    return gt_lookup.get(row['model'], float('-inf'))

seed = 42
budget = 30
config = SearchConfig(
    init_budget=10, batch_size=4, max_evals=budget,
    patience_rounds=5, enable_feature_filtering=False,
    random_state=seed,
)

search = ParetoFrontierSearch(
    candidates=candidates_gt.copy(),
    evaluator=evaluator,
    config=config,
    latency_col='avg_ms',
    candidate_id_col='model',
    continuous_cols=available_cont,
    categorical_cols=available_cat,
)

# Step through initialization
print(f"\n{'='*80}")
print("INITIALIZATION (diverse seed set)")
print(f"{'='*80}")
init_ids = search._diverse_initialization_ids(config.init_budget)
print(f"Selected {len(init_ids)} seed models:")
for idx in init_ids:
    row = search.candidates.loc[idx]
    model = row['model']
    true_acc = gt_lookup.get(model, float('nan'))
    print(f"  [{idx:3d}] {model:55s}  lat={row['avg_ms']:6.1f}ms  p90={-true_acc:.1f}")

search._evaluate_ids(init_ids)
search.best_hypervolume = search._current_hypervolume()

frontier = search._observed_frontier()
init_hv = compute_hypervolume(
    frontier.rename(columns={'_accuracy': 'accuracy'}),
    ref_latency, ref_accuracy
)
print(f"\nAfter init: frontier={len(frontier)}, HV={init_hv/oracle_hv:.1%}")
print("Frontier models:")
for _, r in frontier.iterrows():
    print(f"  {r['model']:55s}  lat={r['avg_ms']:6.1f}ms  p90={-r['_accuracy']:.1f}")

# Step through surrogate rounds
round_num = 0
while not search._should_stop():
    round_num += 1
    print(f"\n{'='*80}")
    print(f"ROUND {round_num}  (evaluated so far: {search.num_evaluated})")
    print(f"{'='*80}")

    search._fit_surrogate()

    # Score ALL candidates to see surrogate quality
    all_scored = search._score_candidates(
        search.candidates[~search.candidates['_evaluated']].copy()
    )

    # Show surrogate predictions vs reality for top candidates
    print(f"\nTop 10 candidates by acquisition score:")
    print(f"  {'Model':55s} {'lat':>6s} {'mu_acc':>8s} {'std':>6s} {'baseline':>8s} {'EI':>8s} {'true_p90':>9s}")
    for _, r in all_scored.head(10).iterrows():
        true_p90 = -gt_lookup.get(r['model'], float('nan'))
        baseline = r.get('_frontier_baseline', float('nan'))
        print(f"  {r['model']:55s} {r['avg_ms']:6.1f} {r['_mu_accuracy']:8.1f} "
              f"{r['_std_accuracy']:6.1f} {baseline:8.1f} {r['_acq_score']:8.2f} {true_p90:9.1f}")

    # Surrogate quality: correlation between predicted and true accuracy
    unevaluated_models = all_scored['model'].tolist()
    pred_acc = all_scored['_mu_accuracy'].values
    true_acc = np.array([gt_lookup[m] for m in unevaluated_models])
    corr = np.corrcoef(pred_acc, true_acc)[0, 1] if len(pred_acc) > 2 else float('nan')
    print(f"\nSurrogate quality: rank correlation = {corr:.3f}")

    # Rank correlation (Spearman)
    from scipy.stats import spearmanr
    sp_corr, _ = spearmanr(pred_acc, true_acc) if len(pred_acc) > 2 else (float('nan'), 0)
    print(f"  Spearman rank correlation = {sp_corr:.3f}")

    # Select batch
    batch_indices = search._select_batch()
    if len(batch_indices) == 0:
        print("No candidates to select. Stopping.")
        break

    print(f"\nSelected batch ({len(batch_indices)} models):")
    for idx in batch_indices:
        row = search.candidates.loc[idx]
        true_p90 = -gt_lookup.get(row['model'], float('nan'))
        pred_acc = all_scored.loc[idx, '_mu_accuracy'] if idx in all_scored.index else float('nan')
        print(f"  [{idx:3d}] {row['model']:55s}  lat={row['avg_ms']:6.1f}ms  "
              f"pred_p90={-pred_acc:.1f}  true_p90={true_p90:.1f}")

    search._evaluate_ids(batch_indices)

    new_hv = search._current_hypervolume()
    frontier = search._observed_frontier()
    hv_pct = compute_hypervolume(
        frontier.rename(columns={'_accuracy': 'accuracy'}),
        ref_latency, ref_accuracy
    ) / oracle_hv

    rel_gain = (
        (new_hv - search.best_hypervolume) / max(abs(search.best_hypervolume), 1e-12)
        if search.best_hypervolume > 0 else float(new_hv > 0)
    )

    if rel_gain > config.min_relative_frontier_gain:
        search.best_hypervolume = new_hv
        search.rounds_without_improvement = 0
        improved = "YES"
    else:
        search.rounds_without_improvement += 1
        improved = "NO"

    print(f"\n  HV={hv_pct:.1%}, frontier={len(frontier)}, "
          f"improved={improved}, stale_rounds={search.rounds_without_improvement}/{config.patience_rounds}")

print(f"\n{'='*80}")
print(f"FINAL: evaluated={search.num_evaluated}, HV={hv_pct:.1%}")
print(f"Stopped because: {'budget reached' if search.num_evaluated >= budget else f'patience exhausted ({search.rounds_without_improvement} rounds)'}")
print(f"{'='*80}")

# Show what the TRUE best unevaluated models were
evaluated_set = set(search.candidates[search.candidates['_evaluated']]['model'])
unevaluated = gt_df[~gt_df['model'].isin(evaluated_set)].copy()
unevaluated_frontier = compute_true_pareto(unevaluated)
print(f"\nBest unevaluated models (missed opportunities):")
missed_true = true_frontier[~true_frontier['model'].isin(evaluated_set)]
for _, r in missed_true.iterrows():
    print(f"  {r['model']:55s}  lat={r['avg_ms']:6.1f}ms  p90={r['p90']:.1f}  ** TRUE PARETO **")
