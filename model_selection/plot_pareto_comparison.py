#!/usr/bin/env python3
"""
Two-phase Pareto frontier comparison:

Phase 1 — Collect ground truth:
  For each model in the profile CSV, look for a CDF result file with _maxq-10000.
  If missing, run the experiment to generate it.  Save all results to a ground
  truth CSV (model_ground_truth.csv).

Phase 2 — Run algorithms & plot:
  Read the ground truth CSV.  Run Pareto Search + baselines.  Write detailed
  results to pareto_comparison_results.csv and draw pareto_comparison.png.
"""
import sys, os, io, contextlib, argparse, subprocess, glob
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from pareto_frontier_search import (
    ParetoFrontierSearch, SearchConfig,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from model_selection_utils import load_candidates, parse_qerror

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.join(SCRIPT_DIR, '..', 'experiments')
CSV_PATH = os.path.join(EXPERIMENTS_DIR, 'experiment_scripts', 'model_profile_with_nonemb.csv')


# ─── Phase 1: Collect ground truth ───────────────────────────────────────

def find_cdf_file_maxq(model: str, db='postgres', embed_size=1000) -> str | None:
    """Find a CDF result file with _maxq-10000 in its name."""
    model_safe = model.replace("/", "-")
    results_base = os.path.join(
        EXPERIMENTS_DIR,
        f"results/{db}/results_Train_stats_Test_stats_ours",
    )
    pattern = os.path.join(
        results_base,
        f"time_llm_pretrained-None_1.0_cdf_{db}_*"
        f"_{model_safe}_emb{embed_size}*_maxq-10000_seed42.csv",
    )
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return matches[0] if matches else None


def run_single_model_eval(model: str):
    """Run the experiment for a single model via run_different_llms.sh."""
    script = os.path.join(EXPERIMENTS_DIR, 'experiment_scripts', 'run_different_llms.sh')
    env = {
        **os.environ,
        'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
        'CUDA_VISIBLE_DEVICES': '1',
        'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
        'WINDOW_BATCH_SIZE': '1',
        'MAX_QUERIES': '10000',
    }
    cmd = [
        'bash', script,
        '--models', model,
        '--workloads', 'stats',
        '--task', 'time',
        '--finetune_mode', '1',
        '--seeds', '42',
        '--db', 'postgres',
        '--quantification', '4-bit',
        '--embed_size', '1000',
        '--downstream', 'mlp',
        '--bucketize', 'None',
        '--concat_true', 'false',
        '--removed_fields', '',
    ]
    result = subprocess.run(cmd, env=env, cwd=EXPERIMENTS_DIR)
    return result.returncode == 0


def collect_ground_truth(candidates: pd.DataFrame, gt_csv_path: str,
                         skip_eval: bool = False) -> pd.DataFrame:
    """
    Phase 1: for every model in candidates, ensure a _maxq-10000 CDF file
    exists.  Parse Q-errors and write model_ground_truth.csv.
    """
    records = []
    missing = []

    for _, row in candidates.iterrows():
        model = row['model']
        cdf = find_cdf_file_maxq(model)
        if cdf is None:
            missing.append(model)

    if missing and not skip_eval:
        print(f"\n{len(missing)} models missing _maxq-10000 CDF files:")
        for m in missing:
            print(f"  - {m}")
        print()

        for i, model in enumerate(missing, 1):
            print(f"[{i}/{len(missing)}] Evaluating: {model}")
            ok = run_single_model_eval(model)
            if not ok:
                print(f"  WARNING: Failed for {model}")
    elif missing and skip_eval:
        print(f"\n{len(missing)} models missing CDF files (skipping eval):")
        for m in missing:
            print(f"  - {m}")

    # Now parse all available CDF files
    n_total = len(candidates)
    for idx, (_, row) in enumerate(candidates.iterrows()):
        model = row['model']
        print(f"  Parsing CDF files... {idx+1}/{n_total}", end='\r', flush=True)
        cdf = find_cdf_file_maxq(model)
        if cdf is None:
            continue
        qe = parse_qerror(cdf)
        records.append({
            'model': model,
            'avg_ms': float(row['avg_ms']),
            'p50_qerror': qe['p50'],
            'p90_qerror': qe['p90'],
            'p95_qerror': qe['p95'],
            'max_qerror': qe['max'],
            'cdf_file': os.path.basename(cdf),
        })

    gt_df = pd.DataFrame(records)
    gt_df.to_csv(gt_csv_path, index=False)
    print(f"\nGround truth saved: {gt_csv_path}  ({len(gt_df)} models)")
    return gt_df


# ─── Phase 2: Run algorithms & plot ──────────────────────────────────────

def compute_true_pareto(gt_df):
    """Identify the true Pareto frontier (lower latency, lower p90 Q-error)."""
    # accuracy = -p90 (higher is better)
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


def make_evaluator(gt_lookup):
    def evaluator(row):
        return gt_lookup.get(row['model'], float('-inf'))
    return evaluator


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


# ─── Selection methods ────────────────────────────────────────────────────

def run_pareto_search(candidates, gt_lookup, available_cont, available_cat, config, seed):
    cfg = SearchConfig(
        init_budget=config.init_budget,
        batch_size=config.batch_size,
        max_evals=config.max_evals,
        random_state=seed,
        exploration_weight=config.exploration_weight,
        coverage_weight=config.coverage_weight,
        diversity_weight=config.diversity_weight,
        family_weight=config.family_weight,
        ensemble_size=config.ensemble_size,
        rf_num_trees=config.rf_num_trees,
        rf_min_samples_leaf=config.rf_min_samples_leaf,
        enable_feature_filtering=config.enable_feature_filtering,
        feature_filter_after=config.feature_filter_after,
        keep_top_k_features=config.keep_top_k_features,
        patience_rounds=config.patience_rounds,
        surrogate_quality_threshold=config.surrogate_quality_threshold,
        anchor_init=config.anchor_init,
        latency_weight=config.latency_weight,
        feature_weight=config.feature_weight,
    )
    evaluator = make_evaluator(gt_lookup)
    with contextlib.redirect_stdout(io.StringIO()):
        search = ParetoFrontierSearch(
            candidates=candidates.copy(),
            evaluator=evaluator,
            config=cfg,
            latency_col='avg_ms',
            candidate_id_col='model',
            continuous_cols=available_cont,
            categorical_cols=available_cat,
        )
        result = search.run()

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


def run_uniform_latency(candidates, gt_lookup, n_evals, seed):
    """Sample n_evals models spread across the latency range via round-robin bins."""
    rng = np.random.default_rng(seed)
    lat_min, lat_max = candidates['avg_ms'].min(), candidates['avg_ms'].max()
    n_bins = min(n_evals, len(candidates))
    bins = np.linspace(lat_min, lat_max * 1.001, n_bins + 1)

    # Assign each candidate to a bin
    bin_pools = [[] for _ in range(n_bins)]
    for idx, row in candidates.iterrows():
        for i in range(n_bins):
            if bins[i] <= row['avg_ms'] < bins[i + 1]:
                bin_pools[i].append(row)
                break

    # Round-robin across non-empty bins until we reach n_evals
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
            break  # all bins exhausted

    eval_df = pd.DataFrame(selected)
    return eval_df, _extract_frontier(eval_df)


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


def run_largest_n(candidates, gt_lookup, n_evals):
    largest = candidates.nlargest(n_evals, 'non_embedding_params')
    records = [{
        'model': row['model'], 'avg_ms': float(row['avg_ms']),
        'accuracy': gt_lookup.get(row['model'], float('-inf')),
    } for _, row in largest.iterrows()]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


def run_smallest_n(candidates, gt_lookup, n_evals):
    smallest = candidates.nsmallest(n_evals, 'non_embedding_params')
    records = [{
        'model': row['model'], 'avg_ms': float(row['avg_ms']),
        'accuracy': gt_lookup.get(row['model'], float('-inf')),
    } for _, row in smallest.iterrows()]
    eval_df = pd.DataFrame(records)
    return eval_df, _extract_frontier(eval_df)


# ─── Plotting ─────────────────────────────────────────────────────────────

def _plot_method_panel(ax, gt_df, true_frontier, mdata):
    name = mdata['name']
    eval_df = mdata['eval_df']
    frontier_df = mdata['frontier_df']
    hv_ratio = mdata['hv_ratio']
    n_eval = len(eval_df)

    gt_p90 = gt_df['p90_qerror']
    tf_sorted = true_frontier.sort_values('avg_ms')
    tf_p90 = tf_sorted['p90_qerror']

    ax.scatter(gt_df['avg_ms'], gt_p90, c='lightgray', s=20, alpha=0.5,
               zorder=1, edgecolors='none', label=f'All models ({len(gt_df)})')
    ax.plot(tf_sorted['avg_ms'], tf_p90, color='goldenrod', linewidth=2,
            alpha=0.6, linestyle='--', zorder=2)
    ax.scatter(tf_sorted['avg_ms'], tf_p90, c='gold', s=70, marker='D',
               edgecolors='darkgoldenrod', linewidths=0.8, zorder=5,
               label=f'True Pareto ({len(true_frontier)})')

    eval_finite = eval_df[np.isfinite(eval_df['accuracy'])]
    if not eval_finite.empty:
        eval_p90 = -eval_finite['accuracy']
        colors = np.arange(len(eval_finite))
        ax.scatter(eval_finite['avg_ms'], eval_p90, c=colors, cmap='Blues',
                   s=40, alpha=0.8, zorder=3, edgecolors='steelblue',
                   linewidths=0.5, label=f'Sampled ({n_eval})')

    if not frontier_df.empty:
        fr_sorted = frontier_df.sort_values('avg_ms')
        fr_p90 = -fr_sorted['accuracy']
        ax.plot(fr_sorted['avg_ms'], fr_p90, 'r-', linewidth=2, alpha=0.7, zorder=4)
        ax.scatter(fr_sorted['avg_ms'], fr_p90, c='red', s=120, marker='*',
                   edgecolors='darkred', linewidths=0.8, zorder=6,
                   label=f'Recovered Pareto ({len(frontier_df)})')

    true_set = set(true_frontier['model'])
    found_set = set(frontier_df['model']) if not frontier_df.empty else set()
    n_true_found = len(true_set & found_set)

    ax.set_yscale('log')
    ax.set_title(f'{name}\nHV={hv_ratio:.1%} | Evals={n_eval} | '
                 f'Frontier={len(frontier_df)} | TrueFound={n_true_found}/{len(true_frontier)}',
                 fontsize=12, fontweight='bold')
    ax.set_xlabel('Latency (ms)', fontsize=11)
    ax.set_ylabel('p90 Q-error (lower is better)', fontsize=11)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.2)


def plot_comparison(gt_df, true_frontier, methods_data, oracle_hv, output_path):
    n_methods = len(methods_data)
    ncols = 2
    nrows = (n_methods + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 7 * nrows))
    if nrows == 1:
        axes = axes.reshape(1, -1)
    plt.style.use('seaborn-v0_8-ticks')

    for idx, mdata in enumerate(methods_data):
        ax = axes[idx // ncols, idx % ncols]
        _plot_method_panel(ax, gt_df, true_frontier, mdata)

    for idx in range(n_methods, nrows * ncols):
        axes[idx // ncols, idx % ncols].set_visible(False)

    fig.suptitle('Pareto Frontier Recovery — Sampling Points Comparison',
                 fontsize=16, fontweight='bold', y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved figure: {output_path}")


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Pareto frontier comparison')
    parser.add_argument('--budget', type=int, default=30, help='Evaluation budget per method')
    parser.add_argument('--init_budget', type=int, default=10, help='Initial diverse seed budget')
    parser.add_argument('--batch_size', type=int, default=4, help='Batch size per surrogate round')
    parser.add_argument('--n_seeds', type=int, default=10, help='Number of random seeds (trials)')
    parser.add_argument('--skip_eval', action='store_true',
                        help='Skip running experiments for missing models')
    parser.add_argument('--gt_csv', type=str,
                        default=os.path.join(SCRIPT_DIR, 'model_ground_truth.csv'),
                        help='Path to ground truth CSV')
    parser.add_argument('--output_csv', type=str,
                        default=os.path.join(SCRIPT_DIR, 'pareto_comparison_results.csv'),
                        help='Path to output results CSV')
    parser.add_argument('--output_png', type=str,
                        default=os.path.join(SCRIPT_DIR, 'pareto_comparison.png'),
                        help='Path to output figure')
    args = parser.parse_args()

    # ── Phase 1: Collect ground truth ──
    print("=" * 70)
    print("  Phase 1: Collect ground truth")
    print("=" * 70)
    candidates = load_candidates(CSV_PATH)
    print(f"Total candidate models: {len(candidates)}")

    gt_df = collect_ground_truth(candidates, args.gt_csv, skip_eval=args.skip_eval)

    if gt_df.empty:
        print("ERROR: No ground truth data available.")
        sys.exit(1)

    # Add accuracy column (higher = better) for algorithm use
    gt_df['accuracy'] = -gt_df['p90_qerror']

    # Filter candidates to those with ground truth
    gt_models = set(gt_df['model'])
    candidates_gt = candidates[candidates['model'].isin(gt_models)].copy().reset_index(drop=True)
    print(f"Models with ground truth: {len(candidates_gt)}/{len(candidates)}")

    # ── Phase 2: Run algorithms & plot ──
    print()
    print("=" * 70)
    print("  Phase 2: Run algorithms & plot")
    print("=" * 70)

    gt_lookup = dict(zip(gt_df['model'], gt_df['accuracy']))

    true_frontier = compute_true_pareto(gt_df)
    print(f"True Pareto frontier: {len(true_frontier)} models")
    for _, r in true_frontier.iterrows():
        print(f"  {r['model']:55s}  lat={r['avg_ms']:6.1f}ms  p90={r['p90_qerror']:.2f}")

    ref_latency = candidates_gt['avg_ms'].max() * 1.05
    ref_accuracy = gt_df['accuracy'].min() - 1.0
    oracle_hv = compute_hypervolume(true_frontier, ref_latency, ref_accuracy)
    print(f"Oracle HV: {oracle_hv:.2f}")

    available_cont = [c for c in CONTINUOUS_COLS if c in candidates_gt.columns]
    available_cat = [c for c in CATEGORICAL_COLS if c in candidates_gt.columns]

    max_evals = args.budget
    config = SearchConfig(
        init_budget=args.init_budget, batch_size=args.batch_size, max_evals=max_evals,
        patience_rounds=5, enable_feature_filtering=False,
    )

    # Single-seed run for plotting
    seed = 42
    methods_data = []
    single_seed_results = []

    config_metadata_only = SearchConfig(
        init_budget=max_evals, batch_size=args.batch_size, max_evals=max_evals,
        patience_rounds=5, enable_feature_filtering=False,
        latency_weight=0.0, feature_weight=3.0,
    )
    config_latency_only = SearchConfig(
        init_budget=max_evals, batch_size=args.batch_size, max_evals=max_evals,
        patience_rounds=5, enable_feature_filtering=False,
        latency_weight=5.0, feature_weight=0.0,
    )

    for method_name, run_fn in [
        ('Pareto Search (Ours)', lambda: run_pareto_search(
            candidates_gt, gt_lookup, available_cont, available_cat, config, seed)),
        ('Metadata-Only Maximin', lambda: run_pareto_search(
            candidates_gt, gt_lookup, available_cont, available_cat, config_metadata_only, seed)),
        ('Latency-Only Spacing', lambda: run_pareto_search(
            candidates_gt, gt_lookup, available_cont, available_cat, config_latency_only, seed)),
        ('Uniform Latency Sampling', lambda: run_uniform_latency(
            candidates_gt, gt_lookup, max_evals, seed)),
        ('Random Selection', lambda: run_random(
            candidates_gt, gt_lookup, max_evals, seed)),
        (f'Largest-{max_evals} by Parameters', lambda: run_largest_n(
            candidates_gt, gt_lookup, max_evals)),
    ]:
        print(f"\nRunning {method_name}...")
        eval_df, frontier_df = run_fn()
        hv = compute_hypervolume(frontier_df, ref_latency, ref_accuracy)
        hv_ratio = hv / oracle_hv
        true_set = set(true_frontier['model'])
        found_set = set(frontier_df['model']) if not frontier_df.empty else set()
        n_true_found = len(true_set & found_set)

        methods_data.append({
            'name': method_name, 'eval_df': eval_df, 'frontier_df': frontier_df,
            'hv': hv, 'hv_ratio': hv_ratio,
        })
        single_seed_results.append({
            'method': method_name, 'seed': seed, 'budget': max_evals,
            'hv': hv, 'hv_pct': hv_ratio * 100,
            'n_evals': len(eval_df), 'n_frontier': len(frontier_df),
            'n_true_found': n_true_found, 'n_true_total': len(true_frontier),
        })
        print(f"  HV={hv_ratio:.1%}, evals={len(eval_df)}, "
              f"frontier={len(frontier_df)}, true_found={n_true_found}/{len(true_frontier)}")

    # Multi-seed summary
    seeds = list(range(42, 42 + args.n_seeds))
    print(f"\n{'='*70}")
    print(f"  Multi-seed summary ({len(seeds)} seeds, {max_evals} evals each)")
    print(f"{'='*70}")
    print(f"{'Method':<30s} {'HV%':>7s} {'std':>7s} {'#Front':>7s} {'#True':>7s}")
    print('-' * 65)

    multi_seed_results = []
    true_set = set(true_frontier['model'])

    for method_name, run_fn in [
        ('Pareto Search', lambda s: run_pareto_search(
            candidates_gt, gt_lookup, available_cont, available_cat, config, s)),
        ('Metadata-Only', lambda s: run_pareto_search(
            candidates_gt, gt_lookup, available_cont, available_cat, config_metadata_only, s)),
        ('Latency-Only', lambda s: run_pareto_search(
            candidates_gt, gt_lookup, available_cont, available_cat, config_latency_only, s)),
        ('Uniform Latency', lambda s: run_uniform_latency(
            candidates_gt, gt_lookup, max_evals, s)),
        ('Random', lambda s: run_random(
            candidates_gt, gt_lookup, max_evals, s)),
    ]:
        hvs, fronts, trues = [], [], []
        for si, s in enumerate(seeds):
            print(f"  {method_name} seed {si+1}/{len(seeds)}...", end='\r', flush=True)
            e_df, f_df = run_fn(s)
            h = compute_hypervolume(f_df, ref_latency, ref_accuracy)
            hvs.append(h / oracle_hv)
            fronts.append(len(f_df))
            trues.append(len(set(f_df['model']) & true_set) if not f_df.empty else 0)
        print(f"{method_name:<30s} {np.mean(hvs):>6.1%} {np.std(hvs):>6.1%} "
              f"{np.mean(fronts):>7.1f} {np.mean(trues):>7.1f}")
        for i, s in enumerate(seeds):
            multi_seed_results.append({
                'method': method_name, 'seed': s, 'budget': max_evals,
                'hv_pct': hvs[i] * 100, 'n_frontier': fronts[i], 'n_true_found': trues[i],
            })

    # Largest-N (deterministic)
    _, f_df_l = run_largest_n(candidates_gt, gt_lookup, max_evals)
    hv_l = compute_hypervolume(f_df_l, ref_latency, ref_accuracy) / oracle_hv
    n_true_l = len(set(f_df_l['model']) & true_set) if not f_df_l.empty else 0
    print(f"{'Largest-N':<30s} {hv_l:>6.1%} {'N/A':>7s} {len(f_df_l):>7.0f} {n_true_l:>7.0f}")
    print(f"{'Oracle':<30s} {'100.0%':>7s} {'':>7s} {len(true_frontier):>7.0f} {len(true_frontier):>7.0f}")
    multi_seed_results.append({
        'method': 'Largest-N', 'seed': 'all', 'budget': max_evals,
        'hv_pct': hv_l * 100, 'n_frontier': len(f_df_l), 'n_true_found': n_true_l,
    })

    # Save results CSV
    results_df = pd.DataFrame(multi_seed_results)
    results_df.to_csv(args.output_csv, index=False)
    print(f"\nResults saved: {args.output_csv}")

    # Plot
    plot_comparison(gt_df, true_frontier, methods_data, oracle_hv, args.output_png)


if __name__ == '__main__':
    main()
