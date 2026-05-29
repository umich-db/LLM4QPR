#!/usr/bin/env python3
"""
Robustness experiment: randomly drop 13 of 103 models and re-run
the Pareto comparison.  Repeats 10 times with different subsamples.

Compares:
  A) Anchor+Fill (deterministic): anchor_init=True, fw=3, lw=5
  B) Stochastic maximin (random start): anchor_init=False, fw=3, lw=5
     — averaged over 20 seeds per trial
  C) Random baseline (20 seeds per trial)
  D) Uniform latency (20 seeds per trial)
  E) Largest-N (deterministic)
"""
import sys, os, io, contextlib, warnings
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))
warnings.filterwarnings('ignore', category=UserWarning)

import numpy as np
import pandas as pd

from pareto_frontier_search import (
    ParetoFrontierSearch, SearchConfig,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from model_selection_utils import load_candidates

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'experiments', 'experiment_scripts',
                        'model_profile_with_nonemb.csv')
GT_CSV = os.path.join(SCRIPT_DIR, 'model_ground_truth.csv')

KEY_MODELS = [
    'google-bert/bert-base-multilingual-uncased',
    'Qwen/Qwen2-0.5B-Instruct',
]


def load_full_data():
    candidates = load_candidates(CSV_PATH)
    gt = pd.read_csv(GT_CSV)
    gt['accuracy'] = -gt['p90_qerror']
    gt_models = set(gt['model'])
    candidates = candidates[candidates['model'].isin(gt_models)].copy().reset_index(drop=True)
    gt_lookup = dict(zip(gt['model'], gt['accuracy']))
    cont = [c for c in CONTINUOUS_COLS if c in candidates.columns]
    cat = [c for c in CATEGORICAL_COLS if c in candidates.columns]
    return candidates, gt_lookup, cont, cat


def compute_pareto(models_df, gt_lookup):
    df = models_df.copy()
    df['accuracy'] = df['model'].map(gt_lookup)
    df = df.sort_values('avg_ms')
    best = -np.inf
    frontier = []
    for _, r in df.iterrows():
        if r['accuracy'] > best:
            frontier.append(r)
            best = r['accuracy']
    return pd.DataFrame(frontier).reset_index(drop=True)


def compute_hv(frontier_df, ref_lat, ref_acc):
    if frontier_df.empty:
        return 0.0
    lats = frontier_df['avg_ms'].values
    accs = frontier_df['accuracy'].values
    order = np.argsort(lats)
    lats, accs = lats[order], accs[order]
    hv = 0.0
    prev = ref_lat
    for la, ac in zip(lats[::-1], accs[::-1]):
        if ac <= ref_acc:
            continue
        hv += max(prev - la, 0) * (ac - ref_acc)
        prev = la
    return float(hv)


def extract_frontier(eval_df):
    if eval_df.empty:
        return eval_df
    df = eval_df[np.isfinite(eval_df['accuracy'])].sort_values('avg_ms')
    best = -np.inf
    frontier = []
    for _, r in df.iterrows():
        if r['accuracy'] > best:
            frontier.append(r)
            best = r['accuracy']
    return pd.DataFrame(frontier).reset_index(drop=True)


def run_pareto(pool, gt_lookup, cont, cat, budget, seed, anchor):
    cfg = SearchConfig(
        init_budget=budget, batch_size=1, max_evals=budget,
        random_state=seed, patience_rounds=5,
        enable_feature_filtering=False,
        anchor_init=anchor, latency_weight=5.0, feature_weight=3.0,
    )
    evaluator = lambda row: gt_lookup.get(row['model'], float('-inf'))
    with contextlib.redirect_stdout(io.StringIO()):
        search = ParetoFrontierSearch(
            candidates=pool.copy(), evaluator=evaluator, config=cfg,
            latency_col='avg_ms', candidate_id_col='model',
            continuous_cols=cont, categorical_cols=cat,
        )
        result = search.run()
    picked = [h['candidate_id'] for h in result.history]
    frontier = result.observed_frontier
    if not frontier.empty:
        frontier = frontier[['model', 'avg_ms', '_accuracy']].rename(
            columns={'_accuracy': 'accuracy'})
    else:
        frontier = pd.DataFrame(columns=['model', 'avg_ms', 'accuracy'])
    return frontier, picked


def run_random(pool, gt_lookup, budget, seed):
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(pool), size=min(budget, len(pool)), replace=False)
    recs = [{'model': pool.iloc[i]['model'],
             'avg_ms': float(pool.iloc[i]['avg_ms']),
             'accuracy': gt_lookup.get(pool.iloc[i]['model'], float('-inf'))}
            for i in picks]
    return extract_frontier(pd.DataFrame(recs))


def run_uniform(pool, gt_lookup, budget, seed):
    rng = np.random.default_rng(seed)
    lat_min, lat_max = pool['avg_ms'].min(), pool['avg_ms'].max()
    n_bins = min(budget, len(pool))
    bins = np.linspace(lat_min, lat_max * 1.001, n_bins + 1)
    bp = [[] for _ in range(n_bins)]
    for idx, row in pool.iterrows():
        for i in range(n_bins):
            if bins[i] <= row['avg_ms'] < bins[i + 1]:
                bp[i].append(row)
                break
    sel_m, sel = set(), []
    while len(sel) < budget:
        added = False
        for i in range(n_bins):
            if len(sel) >= budget:
                break
            avail = [r for r in bp[i] if r['model'] not in sel_m]
            if not avail:
                continue
            p = avail[rng.integers(0, len(avail))]
            sel_m.add(p['model'])
            sel.append({'model': p['model'], 'avg_ms': float(p['avg_ms']),
                        'accuracy': gt_lookup.get(p['model'], float('-inf'))})
            added = True
        if not added:
            break
    return extract_frontier(pd.DataFrame(sel))


def run_largest(pool, gt_lookup, budget):
    largest = pool.nlargest(budget, 'non_embedding_params')
    recs = [{'model': row['model'], 'avg_ms': float(row['avg_ms']),
             'accuracy': gt_lookup.get(row['model'], float('-inf'))}
            for _, row in largest.iterrows()]
    return extract_frontier(pd.DataFrame(recs))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--budget', type=int, default=10)
    parser.add_argument('--pool_size', type=int, default=90)
    parser.add_argument('--n_trials', type=int, default=10)
    parser.add_argument('--n_seeds', type=int, default=20,
                        help='Seeds per trial for stochastic methods')
    args = parser.parse_args()

    budget = args.budget
    pool_size = args.pool_size
    n_trials = args.n_trials
    n_seeds = args.n_seeds

    full_cands, gt_lookup, cont, cat = load_full_data()
    n_full = len(full_cands)
    print(f'Full pool: {n_full} models')
    print(f'Subsample: {pool_size} models per trial')
    print(f'Budget: {budget} evaluations')
    print(f'Trials: {n_trials}, Seeds per stochastic method: {n_seeds}')
    print()

    rng = np.random.default_rng(0)
    trial_seeds = rng.integers(0, 100000, size=n_trials)
    eval_seeds = list(range(42, 42 + n_seeds))

    all_rows = []

    print(f'{"Trial":>5s}  {"#PF":>3s}  '
          f'{"Anchor":>8s} {"Stoch":>8s} {"Random":>8s} {"Unif":>8s} {"LargN":>8s}  '
          f'{"A-R":>6s} {"S-R":>6s}  '
          f'{"bert":>4s} {"qwen":>4s}')
    print('-' * 90)

    for trial in range(n_trials):
        tseed = int(trial_seeds[trial])
        trial_rng = np.random.default_rng(tseed)

        idx = trial_rng.choice(n_full, size=pool_size, replace=False)
        pool = full_cands.iloc[idx].copy().reset_index(drop=True)
        pool_models = set(pool['model'])

        true_pf = compute_pareto(pool, gt_lookup)
        ref_lat = pool['avg_ms'].max() * 1.05
        ref_acc = min(gt_lookup[m] for m in pool_models) - 1.0
        oracle_hv = compute_hv(true_pf, ref_lat, ref_acc)
        if oracle_hv == 0:
            continue

        bert_in = KEY_MODELS[0] in pool_models
        qwen_in = KEY_MODELS[1] in pool_models

        # A) Anchor+Fill deterministic (single run)
        af, _ = run_pareto(pool, gt_lookup, cont, cat, budget, 42, anchor=True)
        a_hv = compute_hv(af, ref_lat, ref_acc) / oracle_hv * 100

        # B) Stochastic maximin (average over seeds)
        s_hvs = []
        for es in eval_seeds:
            sf, _ = run_pareto(pool, gt_lookup, cont, cat, budget, es, anchor=False)
            s_hvs.append(compute_hv(sf, ref_lat, ref_acc) / oracle_hv * 100)
        s_mean = np.mean(s_hvs)

        # C) Random
        r_hvs = []
        for es in eval_seeds:
            rf = run_random(pool, gt_lookup, budget, es)
            r_hvs.append(compute_hv(rf, ref_lat, ref_acc) / oracle_hv * 100)
        r_mean = np.mean(r_hvs)

        # D) Uniform
        u_hvs = []
        for es in eval_seeds:
            uf = run_uniform(pool, gt_lookup, budget, es)
            u_hvs.append(compute_hv(uf, ref_lat, ref_acc) / oracle_hv * 100)
        u_mean = np.mean(u_hvs)

        # E) Largest-N
        lf = run_largest(pool, gt_lookup, budget)
        l_hv = compute_hv(lf, ref_lat, ref_acc) / oracle_hv * 100

        gap_a_r = a_hv - r_mean
        gap_s_r = s_mean - r_mean

        all_rows.append({
            'trial': trial, 'n_pf': len(true_pf),
            'anchor': a_hv, 'stochastic': s_mean,
            'random': r_mean, 'uniform': u_mean, 'largest': l_hv,
            'gap_a_r': gap_a_r, 'gap_s_r': gap_s_r,
            'bert_in': bert_in, 'qwen_in': qwen_in,
        })

        a_mark = '**' if gap_a_r >= 10 else '*' if gap_a_r >= 5 else ''
        s_mark = '**' if gap_s_r >= 10 else '*' if gap_s_r >= 5 else ''
        print(f'{trial:>5d}  {len(true_pf):>3d}  '
              f'{a_hv:>7.1f}% {s_mean:>7.1f}% {r_mean:>7.1f}% {u_mean:>7.1f}% {l_hv:>7.1f}%  '
              f'{gap_a_r:>+5.1f}%{a_mark:<2s} {gap_s_r:>+5.1f}%{s_mark:<2s}  '
              f'{"Y" if bert_in else "N":>4s} {"Y" if qwen_in else "N":>4s}',
              flush=True)

    df = pd.DataFrame(all_rows)
    print()
    print('=' * 70)
    print('  SUMMARY across 10 pool subsamples')
    print('=' * 70)
    print(f'  {"Method":<20s} {"mean HV%":>9s} {"std":>7s} {"min":>7s} {"max":>7s}')
    print('  ' + '-' * 50)
    for col, label in [
        ('anchor', 'Anchor+Fill'),
        ('stochastic', 'Stochastic maximin'),
        ('random', 'Random'),
        ('uniform', 'Uniform Latency'),
        ('largest', 'Largest-N'),
    ]:
        v = df[col].values
        print(f'  {label:<20s} {np.mean(v):>8.1f}% {np.std(v):>6.1f}% '
              f'{np.min(v):>6.1f}% {np.max(v):>6.1f}%')

    print()
    print(f'  {"Gap metric":<30s} {"mean":>7s} {"std":>7s} {"min":>7s} {"max":>7s}')
    print('  ' + '-' * 55)
    for col, label in [
        ('gap_a_r', 'Anchor vs Random'),
        ('gap_s_r', 'Stochastic vs Random'),
    ]:
        v = df[col].values
        print(f'  {label:<30s} {np.mean(v):>+6.1f}% {np.std(v):>6.1f}% '
              f'{np.min(v):>+6.1f}% {np.max(v):>+6.1f}%')

    print()
    print(f'  Anchor wins (gap_a_r > 0):     {(df["gap_a_r"] > 0).sum()}/{len(df)}')
    print(f'  Stochastic wins (gap_s_r > 0): {(df["gap_s_r"] > 0).sum()}/{len(df)}')
    print(f'  Anchor ≥ 10% gap:              {(df["gap_a_r"] >= 10).sum()}/{len(df)}')
    print(f'  Stochastic ≥ 5% gap:           {(df["gap_s_r"] >= 5).sum()}/{len(df)}')


if __name__ == '__main__':
    main()
