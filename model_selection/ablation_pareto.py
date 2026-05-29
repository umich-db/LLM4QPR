#!/usr/bin/env python3
"""
Ablation: sweep eval budget and exploration/coverage weights for Pareto search.
Compare against baselines at each budget level.
Produces a table + a figure with panels per budget.
"""
import sys, os, io, contextlib
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from argparse import Namespace
from itertools import product

from pareto_frontier_search import (
    ParetoFrontierSearch, SearchConfig,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from model_selection_utils import load_candidates, find_cdf_file, parse_qerror

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'experiments', 'experiment_scripts', 'model_profile_with_nonemb.csv')


def build_ground_truth(candidates, args):
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
            'p90': qe['p90'],
        })
    return pd.DataFrame(records)


def compute_true_pareto(gt_df):
    df = gt_df.sort_values('avg_ms').copy()
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
        hv += max(prev_lat - lat, 0.0) * (acc - ref_accuracy)
        prev_lat = lat
    return float(hv)


def make_evaluator(gt_lookup):
    def evaluator(row):
        return gt_lookup.get(row['model'], float('-inf'))
    return evaluator


# ─── Methods ───────────────────────────────────────────────────────────
def run_pareto(candidates, gt_lookup, cont, cat, seed,
               max_evals, init_budget, exploration_w, coverage_w):
    cfg = SearchConfig(
        init_budget=init_budget,
        batch_size=4,
        max_evals=max_evals,
        random_state=seed,
        exploration_weight=exploration_w,
        coverage_weight=coverage_w,
        diversity_weight=0.20,
        ensemble_size=10,
        rf_num_trees=300,
        rf_min_samples_leaf=2,
        enable_feature_filtering=False,
        patience_rounds=6,  # more patience to avoid early stop
    )
    evaluator = make_evaluator(gt_lookup)
    with contextlib.redirect_stdout(io.StringIO()):
        search = ParetoFrontierSearch(
            candidates=candidates.copy(),
            evaluator=evaluator,
            config=cfg,
            latency_col='avg_ms',
            candidate_id_col='model',
            continuous_cols=cont,
            categorical_cols=cat,
        )
        result = search.run()
    eval_records = [{'model': h['candidate_id'], 'avg_ms': h['latency'], 'accuracy': h['accuracy']}
                    for h in result.history]
    eval_df = pd.DataFrame(eval_records)
    frontier = result.observed_frontier
    if not frontier.empty:
        frontier = frontier[['model', 'avg_ms', '_accuracy']].rename(columns={'_accuracy': 'accuracy'})
    else:
        frontier = pd.DataFrame(columns=['model', 'avg_ms', 'accuracy'])
    return eval_df, frontier


def run_random(candidates, gt_lookup, n_evals, seed):
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(candidates), size=min(n_evals, len(candidates)), replace=False)
    records = [{'model': candidates.iloc[i]['model'],
                'avg_ms': float(candidates.iloc[i]['avg_ms']),
                'accuracy': gt_lookup.get(candidates.iloc[i]['model'], float('-inf'))}
               for i in picks]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


def run_uniform(candidates, gt_lookup, n_evals, seed):
    rng = np.random.default_rng(seed)
    lat_min, lat_max = candidates['avg_ms'].min(), candidates['avg_ms'].max()
    bins = np.linspace(lat_min, lat_max, n_evals + 1)
    selected = []
    for i in range(n_evals):
        bm = candidates[(candidates['avg_ms'] >= bins[i]) & (candidates['avg_ms'] < bins[i+1])]
        if bm.empty:
            continue
        pick = bm.iloc[rng.integers(0, len(bm))]
        selected.append({'model': pick['model'], 'avg_ms': float(pick['avg_ms']),
                         'accuracy': gt_lookup.get(pick['model'], float('-inf'))})
    eval_df = pd.DataFrame(selected)
    return eval_df, _extract_frontier(eval_df)


def run_largest(candidates, gt_lookup, n_evals):
    largest = candidates.nlargest(n_evals, 'non_embedding_params')
    records = [{'model': r['model'], 'avg_ms': float(r['avg_ms']),
                'accuracy': gt_lookup.get(r['model'], float('-inf'))}
               for _, r in largest.iterrows()]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


# ─── Main ──────────────────────────────────────────────────────────────
def main():
    candidates = load_candidates(CSV_PATH)
    args = Namespace(dry_run=False, workload='stats', task='time', db='postgres',
                     quantification='4-bit', embed_size=1000, price_s=True,
                     max_eval_queries=200, csv=CSV_PATH)

    gt_df = build_ground_truth(candidates, args)
    gt_lookup = dict(zip(gt_df['model'], gt_df['accuracy']))
    candidates_gt = candidates[candidates['model'].isin(gt_lookup)].copy().reset_index(drop=True)
    true_frontier = compute_true_pareto(gt_df)

    ref_latency = candidates_gt['avg_ms'].max() * 1.05
    ref_accuracy = gt_df['accuracy'].min() - 1.0
    oracle_hv = compute_hypervolume(true_frontier, ref_latency, ref_accuracy)

    n_pool = len(candidates_gt)
    n_true = len(true_frontier)
    true_set = set(true_frontier['model'])
    print(f"Pool: {n_pool} models | True Pareto: {n_true} models | Oracle HV: {oracle_hv:.1f}")

    cont = [c for c in CONTINUOUS_COLS if c in candidates_gt.columns]
    cat = [c for c in CATEGORICAL_COLS if c in candidates_gt.columns]

    seeds = [42, 123, 7, 99, 256, 314, 500, 777, 1000, 2024]

    # ─── Sweep configs ─────────────────────────────────────────────
    budgets = [10, 15, 20, 30]
    exploration_weights = [0.15, 0.50, 1.0, 2.0]
    coverage_weights = [0.20, 0.50, 1.0, 2.0]

    all_results = []

    # 1. Sweep exploration weight (fix coverage=0.20, budget=15)
    print(f"\n{'='*90}")
    print(f"  SWEEP 1: Exploration weight (budget=15, coverage=0.20)")
    print(f"{'='*90}")
    print(f"{'explor_w':>10s} {'HV%':>7s} {'std':>7s} {'#Front':>7s} {'#True':>7s}")
    print('-' * 45)
    for ew in exploration_weights:
        hvs, fronts, trues_found = [], [], []
        for s in seeds:
            _, f = run_pareto(candidates_gt, gt_lookup, cont, cat, s,
                              max_evals=15, init_budget=6, exploration_w=ew, coverage_w=0.20)
            hvs.append(compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv)
            fronts.append(len(f))
            trues_found.append(len(set(f['model']) & true_set) if not f.empty else 0)
        all_results.append({'sweep': 'exploration', 'param': ew, 'budget': 15,
                            'hv_mean': np.mean(hvs), 'hv_std': np.std(hvs),
                            'front_mean': np.mean(fronts), 'true_mean': np.mean(trues_found)})
        print(f"{ew:>10.2f} {np.mean(hvs):>6.1%} {np.std(hvs):>6.1%} "
              f"{np.mean(fronts):>7.1f} {np.mean(trues_found):>7.1f}")

    # 2. Sweep coverage weight (fix exploration=0.50, budget=15)
    print(f"\n{'='*90}")
    print(f"  SWEEP 2: Coverage weight (budget=15, exploration=0.50)")
    print(f"{'='*90}")
    print(f"{'cover_w':>10s} {'HV%':>7s} {'std':>7s} {'#Front':>7s} {'#True':>7s}")
    print('-' * 45)
    for cw in coverage_weights:
        hvs, fronts, trues_found = [], [], []
        for s in seeds:
            _, f = run_pareto(candidates_gt, gt_lookup, cont, cat, s,
                              max_evals=15, init_budget=6, exploration_w=0.50, coverage_w=cw)
            hvs.append(compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv)
            fronts.append(len(f))
            trues_found.append(len(set(f['model']) & true_set) if not f.empty else 0)
        all_results.append({'sweep': 'coverage', 'param': cw, 'budget': 15,
                            'hv_mean': np.mean(hvs), 'hv_std': np.std(hvs),
                            'front_mean': np.mean(fronts), 'true_mean': np.mean(trues_found)})
        print(f"{cw:>10.2f} {np.mean(hvs):>6.1%} {np.std(hvs):>6.1%} "
              f"{np.mean(fronts):>7.1f} {np.mean(trues_found):>7.1f}")

    # 3. Sweep budget with best exploration+coverage vs baselines
    # Use the best weights found above (we'll pick them after, but let's try a few combos)
    print(f"\n{'='*90}")
    print(f"  SWEEP 3: Budget comparison (all methods)")
    print(f"{'='*90}")

    # Try two Pareto configs: default and high-explore
    pareto_configs = [
        ('Pareto(default)',     0.15, 0.20),
        ('Pareto(hi-explore)',  1.0,  1.0),
    ]

    for budget in budgets:
        init_b = max(4, budget // 3)
        print(f"\n  --- Budget={budget} (init={init_b}, pool={n_pool}, sampling={budget/n_pool:.0%}) ---")
        print(f"  {'Method':<25s} {'HV%':>7s} {'std':>7s} {'#Front':>7s} {'#True':>7s}")
        print(f"  {'-'*60}")

        for pname, ew, cw in pareto_configs:
            hvs, fronts, trues_found = [], [], []
            for s in seeds:
                _, f = run_pareto(candidates_gt, gt_lookup, cont, cat, s,
                                  max_evals=budget, init_budget=init_b,
                                  exploration_w=ew, coverage_w=cw)
                hvs.append(compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv)
                fronts.append(len(f))
                trues_found.append(len(set(f['model']) & true_set) if not f.empty else 0)
            all_results.append({'sweep': 'budget', 'param': f'{pname}', 'budget': budget,
                                'hv_mean': np.mean(hvs), 'hv_std': np.std(hvs),
                                'front_mean': np.mean(fronts), 'true_mean': np.mean(trues_found)})
            print(f"  {pname:<25s} {np.mean(hvs):>6.1%} {np.std(hvs):>6.1%} "
                  f"{np.mean(fronts):>7.1f} {np.mean(trues_found):>7.1f}")

        # Baselines
        for bname, run_fn in [
            ('Random', lambda s, b=budget: run_random(candidates_gt, gt_lookup, b, s)),
            ('Uniform Latency', lambda s, b=budget: run_uniform(candidates_gt, gt_lookup, b, s)),
        ]:
            hvs, fronts, trues_found = [], [], []
            for s in seeds:
                _, f = run_fn(s)
                hvs.append(compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv)
                fronts.append(len(f))
                trues_found.append(len(set(f['model']) & true_set) if not f.empty else 0)
            all_results.append({'sweep': 'budget', 'param': bname, 'budget': budget,
                                'hv_mean': np.mean(hvs), 'hv_std': np.std(hvs),
                                'front_mean': np.mean(fronts), 'true_mean': np.mean(trues_found)})
            print(f"  {bname:<25s} {np.mean(hvs):>6.1%} {np.std(hvs):>6.1%} "
                  f"{np.mean(fronts):>7.1f} {np.mean(trues_found):>7.1f}")

        # Largest-N (deterministic)
        _, f = run_largest(candidates_gt, gt_lookup, budget)
        hv_l = compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv
        nt = len(set(f['model']) & true_set) if not f.empty else 0
        all_results.append({'sweep': 'budget', 'param': 'Largest-N', 'budget': budget,
                            'hv_mean': hv_l, 'hv_std': 0, 'front_mean': len(f), 'true_mean': nt})
        print(f"  {'Largest-N':<25s} {hv_l:>6.1%} {'N/A':>7s} {len(f):>7.0f} {nt:>7.0f}")

    # ─── Plot: Budget comparison figure ────────────────────────────
    budget_df = pd.DataFrame([r for r in all_results if r['sweep'] == 'budget'])
    if not budget_df.empty:
        _plot_budget_comparison(budget_df, budgets, output_path=os.path.join(SCRIPT_DIR, 'pareto_ablation_budget.png'))

    # ─── Plot: Sampling points at best config (budget=15, hi-explore) ───
    print(f"\n{'='*90}")
    print(f"  Generating sampling-point figure (budget=15, seed=42)")
    print(f"{'='*90}")
    _plot_sampling_comparison(
        candidates_gt, gt_df, gt_lookup, true_frontier, cont, cat,
        ref_latency, ref_accuracy, oracle_hv,
        budget=15, init_budget=5, seed=42,
        output_path=os.path.join(SCRIPT_DIR, 'pareto_comparison_b15.png'),
    )

    # Also at budget=10
    _plot_sampling_comparison(
        candidates_gt, gt_df, gt_lookup, true_frontier, cont, cat,
        ref_latency, ref_accuracy, oracle_hv,
        budget=10, init_budget=4, seed=42,
        output_path=os.path.join(SCRIPT_DIR, 'pareto_comparison_b10.png'),
    )


def _plot_budget_comparison(df, budgets, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    methods_order = ['Pareto(default)', 'Pareto(hi-explore)', 'Random', 'Uniform Latency', 'Largest-N']
    colors = {'Pareto(default)': '#1f77b4', 'Pareto(hi-explore)': '#ff7f0e',
              'Random': '#2ca02c', 'Uniform Latency': '#d62728', 'Largest-N': '#9467bd'}
    markers = {'Pareto(default)': 'o', 'Pareto(hi-explore)': 's',
               'Random': '^', 'Uniform Latency': 'D', 'Largest-N': 'v'}

    # Panel 1: HV% vs budget
    ax = axes[0]
    for method in methods_order:
        sub = df[df['param'] == method].sort_values('budget')
        if sub.empty:
            continue
        ax.errorbar(sub['budget'], sub['hv_mean'] * 100, yerr=sub['hv_std'] * 100,
                    label=method, marker=markers.get(method, 'o'), color=colors.get(method),
                    capsize=3, linewidth=2, markersize=7)
    ax.set_xlabel('Evaluation Budget', fontsize=12)
    ax.set_ylabel('Hypervolume (%)', fontsize=12)
    ax.set_title('HV% vs Evaluation Budget', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(budgets)

    # Panel 2: #True Pareto found vs budget
    ax = axes[1]
    for method in methods_order:
        sub = df[df['param'] == method].sort_values('budget')
        if sub.empty:
            continue
        ax.plot(sub['budget'], sub['true_mean'],
                label=method, marker=markers.get(method, 'o'), color=colors.get(method),
                linewidth=2, markersize=7)
    ax.set_xlabel('Evaluation Budget', fontsize=12)
    ax.set_ylabel('# True Pareto Found', fontsize=12)
    ax.set_title('True Pareto Points Found vs Budget', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(budgets)

    fig.suptitle('Pareto Search Ablation — Budget & Exploration Weights', fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved to {output_path}")


def _plot_sampling_comparison(candidates_gt, gt_df, gt_lookup, true_frontier, cont, cat,
                               ref_latency, ref_accuracy, oracle_hv,
                               budget, init_budget, seed, output_path):
    true_set = set(true_frontier['model'])

    methods = []

    # 1. Pareto default
    e, f = run_pareto(candidates_gt, gt_lookup, cont, cat, seed,
                      max_evals=budget, init_budget=init_budget,
                      exploration_w=0.15, coverage_w=0.20)
    hv = compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv
    methods.append({'name': 'Pareto (default)', 'eval_df': e, 'frontier_df': f, 'hv_ratio': hv})

    # 2. Pareto high-explore
    e, f = run_pareto(candidates_gt, gt_lookup, cont, cat, seed,
                      max_evals=budget, init_budget=init_budget,
                      exploration_w=1.0, coverage_w=1.0)
    hv = compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv
    methods.append({'name': 'Pareto (hi-explore)', 'eval_df': e, 'frontier_df': f, 'hv_ratio': hv})

    # 3. Random
    e, f = run_random(candidates_gt, gt_lookup, budget, seed)
    hv = compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv
    methods.append({'name': 'Random', 'eval_df': e, 'frontier_df': f, 'hv_ratio': hv})

    # 4. Uniform Latency
    e, f = run_uniform(candidates_gt, gt_lookup, budget, seed)
    hv = compute_hypervolume(f, ref_latency, ref_accuracy) / oracle_hv
    methods.append({'name': 'Uniform Latency', 'eval_df': e, 'frontier_df': f, 'hv_ratio': hv})

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 13))
    for idx, mdata in enumerate(methods):
        ax = axes[idx // 2, idx % 2]
        _draw_panel(ax, gt_df, true_frontier, mdata)

    fig.suptitle(f'Pareto Frontier Recovery — Budget={budget}, Seed={seed}, Pool={len(candidates_gt)}',
                 fontsize=15, fontweight='bold', y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved to {output_path}")


def _draw_panel(ax, gt_df, true_frontier, mdata):
    name = mdata['name']
    eval_df = mdata['eval_df']
    frontier_df = mdata['frontier_df']
    hv_ratio = mdata['hv_ratio']
    n_eval = len(eval_df)
    true_set = set(true_frontier['model'])
    found_set = set(frontier_df['model']) if not frontier_df.empty else set()

    # All models gray
    ax.scatter(gt_df['avg_ms'], gt_df['accuracy'],
               c='lightgray', s=20, alpha=0.5, zorder=1, edgecolors='none')

    # True Pareto
    tf = true_frontier.sort_values('avg_ms')
    ax.plot(tf['avg_ms'], tf['accuracy'], color='goldenrod', linewidth=2, alpha=0.6, linestyle='--', zorder=2)
    ax.scatter(tf['avg_ms'], tf['accuracy'], c='gold', s=70, marker='D',
               edgecolors='darkgoldenrod', linewidths=0.8, zorder=5, label=f'True Pareto ({len(tf)})')

    # Sampled
    ef = eval_df[np.isfinite(eval_df['accuracy'])]
    if not ef.empty:
        ax.scatter(ef['avg_ms'], ef['accuracy'], c=np.arange(len(ef)), cmap='Blues',
                   s=40, alpha=0.8, zorder=3, edgecolors='steelblue', linewidths=0.5,
                   label=f'Sampled ({n_eval})')

    # Recovered frontier
    if not frontier_df.empty:
        fr = frontier_df.sort_values('avg_ms')
        ax.plot(fr['avg_ms'], fr['accuracy'], 'r-', linewidth=2, alpha=0.7, zorder=4)
        ax.scatter(fr['avg_ms'], fr['accuracy'], c='red', s=120, marker='*',
                   edgecolors='darkred', linewidths=0.8, zorder=6,
                   label=f'Recovered ({len(fr)})')

    n_true_found = len(true_set & found_set)
    ax.set_title(f'{name}\nHV={hv_ratio:.1%} | Evals={n_eval} | '
                 f'Frontier={len(frontier_df)} | TrueFound={n_true_found}/{len(true_frontier)}',
                 fontsize=12, fontweight='bold')
    ax.set_xlabel('Latency (ms)', fontsize=11)
    ax.set_ylabel('Accuracy (neg. p90 Q-error)', fontsize=11)
    ax.legend(fontsize=8, loc='lower right')
    ax.grid(True, alpha=0.2)


if __name__ == '__main__':
    main()
