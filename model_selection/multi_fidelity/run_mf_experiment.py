#!/usr/bin/env python3
"""
Multi-fidelity Pareto search experiment using real finetune results.

Uses rank_stability_test_results.csv as a lookup table:
  - ep0_test_p90: pretrained performance (epoch 0)
  - ep1_test_p90: after 1 epoch LoRA finetuning
  - ep2_test_p90: after 2 epochs
  - ep3_test_p90: after 3 epochs

Experiment: x=2 (target = 3 epochs), n=16
  Multi-fidelity budget: (2 - 1/2^2) * 16 = 28 epoch-units
  Baseline budget: 28 / 3 ≈ 9 models finetuned for 3 epochs

Compares:
  1. Multi-fidelity Pareto search (ours)
  2. Random selection baseline
  3. Maximin space-filling baseline (single fidelity)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from multifidelity_pareto_search import (
    MultiFidelityParetoSearch, MFSearchConfig, make_preprocessor
)

# ── Load data ──────────────────────────────────────────────────────────

TEST_RESULTS = '/root/LLM4QPR/model_selection/rank_stability_test_results.csv'
PROFILE_CSV = '/root/LLM4QPR/experiments/experiment_scripts/model_profile_with_nonemb.csv'
OUT_DIR = '/root/LLM4QPR/model_selection/multi_fidelity'

test_df = pd.read_csv(TEST_RESULTS)
profile = pd.read_csv(PROFILE_CSV)

# Merge metadata
candidates = test_df.merge(profile, on='model', how='left', suffixes=('', '_prof'))

# accuracy = -p90 (higher is better)
for ep in range(4):
    col = f'ep{ep}_test_p90'
    candidates[f'acc_ep{ep}'] = -candidates[col]

# Build lookup: model -> {epoch -> accuracy}
acc_lookup = {}
for _, row in candidates.iterrows():
    acc_lookup[row['model']] = {
        0: row['acc_ep0'],
        1: row['acc_ep1'],
        2: row['acc_ep2'],
        3: row['acc_ep3'],
    }

LATENCY_COL = 'avg_ms'
ID_COL = 'model'

CONTINUOUS_COLS = [
    'non_embedding_params', 'embedding_params', 'num_layers',
    'hidden_size', 'attention_heads', 'ffn_width', 'context_length',
    'embedding_dimension', 'is_embedding_tuned', 'is_instruction_tuned',
    'is_multilingual', 'is_cased', 'deduped_variant',
]
CATEGORICAL_COLS = [
    'model_family', 'architecture', 'encoder_vs_decoder',
    'pooling_method', 'tokenizer_behavior',
]

# Filter to columns that exist
available_cont = [c for c in CONTINUOUS_COLS if c in candidates.columns]
available_cat = [c for c in CATEGORICAL_COLS if c in candidates.columns]


# ── Trainer (lookup-based) ─────────────────────────────────────────────

def make_trainer(lookup):
    """Returns a trainer that looks up pre-computed results."""
    def trainer(row, target_epoch, current_epoch):
        model = row[ID_COL]
        return lookup[model][target_epoch]
    return trainer


# ── Oracle frontier ────────────────────────────────────────────────────

def compute_frontier(df, lat_col, acc_col):
    """Compute Pareto frontier (minimize latency, maximize accuracy)."""
    work = df.sort_values(lat_col)
    best_acc = -np.inf
    frontier = []
    for _, row in work.iterrows():
        if row[acc_col] > best_acc:
            frontier.append(row)
            best_acc = row[acc_col]
    return pd.DataFrame(frontier).reset_index(drop=True)


def compute_hypervolume(frontier_df, lat_col, acc_col, ref_lat, ref_acc):
    if frontier_df.empty:
        return 0.0
    lats = frontier_df[lat_col].values
    accs = frontier_df[acc_col].values
    order = np.argsort(lats)
    lats, accs = lats[order], accs[order]
    hv = 0.0
    prev_lat = ref_lat
    for lat, acc in zip(lats[::-1], accs[::-1]):
        if acc <= ref_acc:
            continue
        hv += max(prev_lat - lat, 0) * (acc - ref_acc)
        prev_lat = lat
    return hv


# ── Baselines ──────────────────────────────────────────────────────────

def run_random_baseline(candidates_df, acc_lookup, n_models, target_epoch, seed):
    """Random selection: pick n_models, finetune all to target_epoch."""
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(candidates_df), size=min(n_models, len(candidates_df)), replace=False)
    result = candidates_df.iloc[picks].copy()
    result['_accuracy'] = [acc_lookup[m][target_epoch] for m in result[ID_COL]]
    frontier = compute_frontier(result, LATENCY_COL, '_accuracy')
    budget = n_models * target_epoch
    return frontier, budget


def run_maximin_baseline(candidates_df, acc_lookup, n_models, target_epoch, seed,
                         cont_cols, cat_cols):
    """Maximin space-filling: pick n_models by maximin, finetune all to target_epoch."""
    rng = np.random.default_rng(seed)

    # Build embedding
    prep = make_preprocessor(cont_cols, cat_cols)
    X = prep.fit_transform(candidates_df[cont_cols + cat_cols])
    if hasattr(X, 'toarray'):
        X = X.toarray()
    X = np.asarray(X, dtype=float) * 3.0  # feature_weight

    lat = candidates_df[LATENCY_COL].values
    lat_norm = (lat - lat.min()) / (lat.max() - lat.min() + 1e-12)
    X_aug = np.column_stack([X, lat_norm * 5.0])  # latency_weight

    n = min(n_models, len(candidates_df))
    chosen = [int(rng.integers(0, len(X_aug)))]
    while len(chosen) < n:
        rem = [i for i in range(len(X_aug)) if i not in chosen]
        rem_idx = np.array(rem)
        from sklearn.metrics import pairwise_distances
        d = pairwise_distances(X_aug[rem_idx], X_aug[chosen]).min(axis=1)
        chosen.append(int(rem_idx[np.argmax(d)]))

    result = candidates_df.iloc[chosen].copy()
    result['_accuracy'] = [acc_lookup[m][target_epoch] for m in result[ID_COL]]
    frontier = compute_frontier(result, LATENCY_COL, '_accuracy')
    budget = n_models * target_epoch
    return frontier, budget


# ── Experiment ─────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    N = 16          # init_count
    X = 2           # total_epochs - 1 (so target = 3 epochs)
    TARGET_EPOCH = 3
    N_SEEDS = 20

    # Budget: (2 - 1/2^x) * n = (2 - 0.25) * 16 = 28 epoch-units
    mf_budget = (2 - 2**(-X)) * N
    baseline_models = int(mf_budget / TARGET_EPOCH)  # 28 / 3 = 9 models

    print(f"Experiment: n={N}, target={TARGET_EPOCH} epochs, x={X}")
    print(f"MF budget: {mf_budget:.0f} epoch-units")
    print(f"Baseline: {baseline_models} models × {TARGET_EPOCH} epochs = {baseline_models * TARGET_EPOCH} epoch-units")
    print(f"Pool: {len(candidates)} models")
    print()

    # Oracle frontier at target epoch
    oracle_df = candidates.copy()
    oracle_df['_accuracy'] = oracle_df[f'acc_ep{TARGET_EPOCH}']
    oracle_frontier = compute_frontier(oracle_df, LATENCY_COL, '_accuracy')

    ref_lat = candidates[LATENCY_COL].max() * 1.05
    ref_acc = oracle_df['_accuracy'].min() - 1.0
    oracle_hv = compute_hypervolume(oracle_frontier, LATENCY_COL, '_accuracy', ref_lat, ref_acc)

    print(f"Oracle frontier: {len(oracle_frontier)} models, HV={oracle_hv:.2f}")
    for _, r in oracle_frontier.iterrows():
        print(f"  {r[ID_COL]:50s}  lat={r[LATENCY_COL]:6.1f}  p90={-r['_accuracy']:.1f}")
    print()

    # Run experiment across seeds
    results = []
    for seed in range(42, 42 + N_SEEDS):
        # 1. Multi-fidelity Pareto search
        cfg = MFSearchConfig(
            init_count=N,
            total_epochs=TARGET_EPOCH,
            shrink_factor=2.0,
            frontier_distance="pareto_gap",
            always_keep_frontier=True,
            exploration_reserve=0.10,
            feature_weight=3.0,
            latency_weight=0.0,  # metadata-only (best from earlier experiments)
            random_state=seed,
        )

        mf_search = MultiFidelityParetoSearch(
            candidates=candidates.copy(),
            trainer=make_trainer(acc_lookup),
            config=cfg,
            latency_col=LATENCY_COL,
            candidate_id_col=ID_COL,
            continuous_cols=available_cont,
            categorical_cols=available_cat,
        )
        mf_result = mf_search.run()
        mf_frontier = mf_result.final_frontier
        mf_hv = compute_hypervolume(mf_frontier, LATENCY_COL, '_accuracy', ref_lat, ref_acc)
        mf_true_found = len(set(mf_frontier[ID_COL]) & set(oracle_frontier[ID_COL]))

        results.append({
            'method': 'Multi-Fidelity', 'seed': seed,
            'hv': mf_hv, 'hv_pct': mf_hv / oracle_hv * 100,
            'n_frontier': len(mf_frontier), 'true_found': mf_true_found,
            'budget': mf_result.total_epoch_budget_used,
        })

        # 2. Random baseline
        rand_frontier, rand_budget = run_random_baseline(
            candidates, acc_lookup, baseline_models, TARGET_EPOCH, seed)
        rand_hv = compute_hypervolume(rand_frontier, LATENCY_COL, '_accuracy', ref_lat, ref_acc)
        rand_true_found = len(set(rand_frontier[ID_COL]) & set(oracle_frontier[ID_COL]))

        results.append({
            'method': 'Random', 'seed': seed,
            'hv': rand_hv, 'hv_pct': rand_hv / oracle_hv * 100,
            'n_frontier': len(rand_frontier), 'true_found': rand_true_found,
            'budget': rand_budget,
        })

        # 3. Maximin baseline (single fidelity)
        maximin_frontier, maximin_budget = run_maximin_baseline(
            candidates, acc_lookup, baseline_models, TARGET_EPOCH, seed,
            available_cont, available_cat)
        maximin_hv = compute_hypervolume(maximin_frontier, LATENCY_COL, '_accuracy', ref_lat, ref_acc)
        maximin_true_found = len(set(maximin_frontier[ID_COL]) & set(oracle_frontier[ID_COL]))

        results.append({
            'method': 'Maximin (single-fidelity)', 'seed': seed,
            'hv': maximin_hv, 'hv_pct': maximin_hv / oracle_hv * 100,
            'n_frontier': len(maximin_frontier), 'true_found': maximin_true_found,
            'budget': maximin_budget,
        })

    # ── Results ────────────────────────────────────────────────────────
    res_df = pd.DataFrame(results)

    print("=" * 70)
    print(f"Results over {N_SEEDS} seeds")
    print("=" * 70)

    summary_rows = []
    for method in ['Multi-Fidelity', 'Random', 'Maximin (single-fidelity)']:
        sub = res_df[res_df['method'] == method]
        row = {
            'method': method,
            'hv_pct_mean': sub['hv_pct'].mean(),
            'hv_pct_std': sub['hv_pct'].std(),
            'true_found_mean': sub['true_found'].mean(),
            'budget_mean': sub['budget'].mean(),
        }
        summary_rows.append(row)
        print(f"  {method:30s}  HV={row['hv_pct_mean']:.1f}%±{row['hv_pct_std']:.1f}%  "
              f"TrueFound={row['true_found_mean']:.1f}  Budget={row['budget_mean']:.0f}")

    summary = pd.DataFrame(summary_rows)

    # Win rates
    mf_hvs = res_df[res_df['method'] == 'Multi-Fidelity']['hv_pct'].values
    rand_hvs = res_df[res_df['method'] == 'Random']['hv_pct'].values
    maximin_hvs = res_df[res_df['method'] == 'Maximin (single-fidelity)']['hv_pct'].values

    print(f"\n  MF wins vs Random:  {(mf_hvs > rand_hvs).sum()}/{N_SEEDS}")
    print(f"  MF wins vs Maximin: {(mf_hvs > maximin_hvs).sum()}/{N_SEEDS}")

    # Save
    res_df.to_csv(os.path.join(OUT_DIR, 'mf_experiment_raw.csv'), index=False)
    summary.to_csv(os.path.join(OUT_DIR, 'mf_experiment_summary.csv'), index=False)

    # ── Plot ───────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel 1: HV% boxplot
    ax = axes[0]
    data = [res_df[res_df['method'] == m]['hv_pct'].values
            for m in ['Multi-Fidelity', 'Random', 'Maximin (single-fidelity)']]
    bp = ax.boxplot(data, labels=['MF (Ours)', 'Random', 'Maximin'], patch_artist=True)
    colors = ['steelblue', 'lightcoral', 'lightgreen']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax.set_ylabel('HV% of Oracle', fontsize=12)
    ax.set_title(f'Hypervolume Recovery\n(n={N}, target={TARGET_EPOCH}ep, {N_SEEDS} seeds)',
                 fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.2)

    # Panel 2: Per-round detail for one seed
    ax = axes[1]
    cfg_detail = MFSearchConfig(
        init_count=N, total_epochs=TARGET_EPOCH, shrink_factor=2.0,
        frontier_distance="pareto_gap", always_keep_frontier=True,
        exploration_reserve=0.10, feature_weight=3.0, latency_weight=0.0,
        random_state=42,
    )
    mf_detail = MultiFidelityParetoSearch(
        candidates=candidates.copy(), trainer=make_trainer(acc_lookup),
        config=cfg_detail, latency_col=LATENCY_COL, candidate_id_col=ID_COL,
        continuous_cols=available_cont, categorical_cols=available_cat,
    )
    detail_result = mf_detail.run()

    rounds = detail_result.round_history
    for i, rnd in enumerate(rounds):
        ax.bar(i, rnd['selected_count'], color='steelblue', alpha=0.7, label='Selected' if i == 0 else '')
        ax.bar(i, rnd['frontier_count_after_round'], color='gold', alpha=0.9,
               label='Frontier' if i == 0 else '')
    ax.set_xlabel('Round', fontsize=12)
    ax.set_ylabel('# Models', fontsize=12)
    ax.set_title('MF Search Rounds (seed=42)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2)

    # Panel 3: Frontier comparison for seed=42
    ax = axes[2]
    # All models
    ax.scatter(candidates[LATENCY_COL], -candidates[f'acc_ep{TARGET_EPOCH}'],
               c='lightgray', s=20, alpha=0.4, label=f'All ({len(candidates)})')
    # Oracle frontier
    ax.scatter(oracle_frontier[LATENCY_COL], -oracle_frontier['_accuracy'],
               c='gold', s=80, marker='D', edgecolors='darkgoldenrod',
               linewidths=0.8, zorder=5, label=f'Oracle ({len(oracle_frontier)})')
    # MF frontier
    mf_fr = detail_result.final_frontier
    ax.scatter(mf_fr[LATENCY_COL], -mf_fr['_accuracy'],
               c='red', s=120, marker='*', edgecolors='darkred',
               linewidths=0.8, zorder=6, label=f'MF ({len(mf_fr)})')

    ax.set_xlabel('Latency (ms)', fontsize=12)
    ax.set_ylabel('p90 Q-error (lower=better)', fontsize=12)
    ax.set_title(f'Frontier Recovery (seed=42)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

    fig.suptitle('Multi-Fidelity Successive Halving Pareto Search',
                 fontsize=15, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'mf_experiment.png'), dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\nSaved to {OUT_DIR}/")


if __name__ == '__main__':
    main()
