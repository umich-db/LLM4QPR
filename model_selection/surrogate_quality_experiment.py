#!/usr/bin/env python3
"""
Experiment: Can model metadata predict query-estimation accuracy?

This script rigorously evaluates whether a surrogate model trained on
model metadata (architecture, parameter counts, hidden sizes, etc.) can
predict the query-estimation accuracy (p90 Q-error) of LLMs used for
query-plan representation.

Experiments:
  1. Leave-One-Out (LOO) cross-validation with Random Forest
  2. 5-fold and 10-fold CV with multiple regressors (RF, GBT, Ridge, kNN, SVM)
  3. Spearman / Pearson / R² metrics
  4. Per-feature univariate predictive power
  5. Exhaustive pairwise & triple feature search for best Spearman
  6. Permutation-test null distribution (shuffle labels, measure how often
     a random surrogate matches or beats the real one)
  7. Learning curve: does more training data help?

If the surrogate is useless, we expect:
  - R² ≈ 0 or negative
  - Spearman ρ close to 0 with high p-value
  - Permutation-test p-value >> 0.05
  - No feature or feature combination achieves meaningful correlation
"""
import sys, os, warnings
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))
warnings.filterwarnings('ignore', category=UserWarning)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import (
    cross_val_predict,
    LeaveOneOut,
    KFold,
    learning_curve,
)
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVR

from pareto_frontier_search import CONTINUOUS_COLS, CATEGORICAL_COLS
from model_selection_v2 import load_candidates

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'experiments', 'experiment_scripts',
                        'model_profile_with_nonemb.csv')
GT_CSV = os.path.join(SCRIPT_DIR, 'model_ground_truth.csv')


# ── Helpers ──────────────────────────────────────────────────────────────

def load_data():
    candidates = load_candidates(CSV_PATH)
    gt = pd.read_csv(GT_CSV)
    merged = candidates.merge(gt[['model', 'p90_qerror']], on='model', how='inner')
    merged['accuracy'] = -merged['p90_qerror']  # higher = better
    cont = [c for c in CONTINUOUS_COLS if c in merged.columns]
    cat = [c for c in CATEGORICAL_COLS if c in merged.columns]
    return merged, cont, cat


def make_preprocessor(cont_cols, cat_cols):
    cont_pipe = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ('impute', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])
    return ColumnTransformer([
        ('cont', cont_pipe, list(cont_cols)),
        ('cat', cat_pipe, list(cat_cols)),
    ], remainder='drop')


def make_pipeline(regressor, cont_cols, cat_cols):
    return Pipeline([
        ('prep', make_preprocessor(cont_cols, cat_cols)),
        ('model', regressor),
    ])


def eval_predictions(y_true, y_pred):
    """Return a dict of regression metrics."""
    mask = np.isfinite(y_pred) & np.isfinite(y_true)
    y_t, y_p = y_true[mask], y_pred[mask]
    rho, rho_p = spearmanr(y_t, y_p)
    r, r_p = pearsonr(y_t, y_p)
    r2 = r2_score(y_t, y_p)
    rmse = np.sqrt(mean_squared_error(y_t, y_p))
    return {
        'spearman': rho, 'spearman_p': rho_p,
        'pearson': r, 'pearson_p': r_p,
        'r2': r2, 'rmse': rmse, 'n': len(y_t),
    }


# ── Experiment 1: LOO Cross-Validation ──────────────────────────────────

def experiment_loo(df, cont, cat, y):
    print('=' * 70)
    print('  Experiment 1: Leave-One-Out Cross-Validation (Random Forest)')
    print('=' * 70)

    rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                               random_state=42, n_jobs=-1)
    pipe = make_pipeline(rf, cont, cat)

    loo_pred = cross_val_predict(pipe, df[cont + cat], y, cv=LeaveOneOut(),
                                 n_jobs=-1)
    m = eval_predictions(y, loo_pred)

    print(f'  N = {m["n"]}')
    print(f'  R²          = {m["r2"]:.4f}')
    print(f'  Spearman ρ  = {m["spearman"]:.4f}  (p = {m["spearman_p"]:.4f})')
    print(f'  Pearson r   = {m["pearson"]:.4f}  (p = {m["pearson_p"]:.4f})')
    print(f'  RMSE        = {m["rmse"]:.2f}')
    print()
    return loo_pred, m


# ── Experiment 2: K-Fold CV with Multiple Regressors ───────────────────

def experiment_kfold(df, cont, cat, y):
    print('=' * 70)
    print('  Experiment 2: K-Fold CV — Multiple Regressors')
    print('=' * 70)

    regressors = {
        'RandomForest-300': RandomForestRegressor(
            n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1),
        'GradientBoosting-200': GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42),
        'Ridge': Ridge(alpha=1.0),
        'kNN-5': KNeighborsRegressor(n_neighbors=5),
        'kNN-10': KNeighborsRegressor(n_neighbors=10),
        'SVR-rbf': SVR(kernel='rbf', C=1.0),
    }

    results = []
    for name, reg in regressors.items():
        for k in [5, 10]:
            pipe = make_pipeline(reg, cont, cat)
            cv = KFold(n_splits=k, shuffle=True, random_state=42)
            pred = cross_val_predict(pipe, df[cont + cat], y, cv=cv, n_jobs=-1)
            m = eval_predictions(y, pred)
            m['regressor'] = name
            m['cv'] = f'{k}-fold'
            results.append(m)

    header = f'  {"Regressor":<25s} {"CV":<8s} {"R²":>7s} {"Spearman":>9s} {"p-val":>8s} {"RMSE":>8s}'
    print(header)
    print('  ' + '-' * len(header.strip()))
    for m in results:
        print(f'  {m["regressor"]:<25s} {m["cv"]:<8s} {m["r2"]:>7.4f} '
              f'{m["spearman"]:>9.4f} {m["spearman_p"]:>8.4f} {m["rmse"]:>8.2f}')
    print()
    return results


# ── Experiment 3: Per-Feature Univariate Predictive Power ──────────────

def experiment_univariate(df, cont, cat, y):
    print('=' * 70)
    print('  Experiment 3: Per-Feature Univariate Correlation with p90 Q-error')
    print('=' * 70)

    results = []
    for col in cont:
        vals = pd.to_numeric(df[col], errors='coerce').values
        mask = np.isfinite(vals) & np.isfinite(y)
        if mask.sum() < 10:
            continue
        rho, rho_p = spearmanr(vals[mask], y[mask])
        r, r_p = pearsonr(vals[mask], y[mask])
        results.append({
            'feature': col, 'type': 'continuous',
            'spearman': rho, 'sp_pval': rho_p,
            'pearson': r, 'pe_pval': r_p,
        })

    for col in cat:
        if col not in df.columns:
            continue
        # Encode categories as integers for rank correlation
        codes = df[col].astype('category').cat.codes.values
        mask = np.isfinite(y) & (codes >= 0)
        if mask.sum() < 10:
            continue
        rho, rho_p = spearmanr(codes[mask], y[mask])
        results.append({
            'feature': col, 'type': 'categorical',
            'spearman': rho, 'sp_pval': rho_p,
            'pearson': float('nan'), 'pe_pval': float('nan'),
        })

    results.sort(key=lambda x: -abs(x['spearman']))
    print(f'  {"Feature":<30s} {"Type":<12s} {"Spearman":>9s} {"p-val":>8s} {"Pearson":>9s} {"p-val":>8s}')
    print('  ' + '-' * 80)
    for r in results:
        pe_str = f'{r["pearson"]:>9.4f}' if np.isfinite(r["pearson"]) else '      N/A'
        pe_p_str = f'{r["pe_pval"]:>8.4f}' if np.isfinite(r["pe_pval"]) else '     N/A'
        print(f'  {r["feature"]:<30s} {r["type"]:<12s} {r["spearman"]:>9.4f} '
              f'{r["sp_pval"]:>8.4f} {pe_str} {pe_p_str}')
    print()
    return results


# ── Experiment 4: Best Feature Pairs and Triples ───────────────────────

def experiment_feature_combos(df, cont, cat, y):
    print('=' * 70)
    print('  Experiment 4: Exhaustive Search for Best Feature Subsets (RF LOO)')
    print('=' * 70)

    all_features = cont + cat
    n = len(all_features)

    # Single features (already done as univariate, but now with RF LOO)
    print('  Evaluating all single features...')
    single_results = []
    for f in all_features:
        f_cont = [f] if f in cont else []
        f_cat = [f] if f in cat else []
        rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=3,
                                   random_state=42, n_jobs=-1)
        pipe = make_pipeline(rf, f_cont, f_cat)
        try:
            pred = cross_val_predict(pipe, df[[f]], y, cv=5, n_jobs=-1)
            m = eval_predictions(y, pred)
            single_results.append((f, m['spearman'], m['r2']))
        except Exception:
            single_results.append((f, 0.0, 0.0))

    single_results.sort(key=lambda x: -abs(x[1]))
    print(f'\n  Top-5 single features (5-fold RF):')
    for f, rho, r2 in single_results[:5]:
        print(f'    {f:<30s}  Spearman={rho:+.4f}  R²={r2:.4f}')

    # All pairs
    print(f'\n  Evaluating all {n*(n-1)//2} feature pairs...')
    pair_results = []
    for i in range(n):
        for j in range(i + 1, n):
            feats = [all_features[i], all_features[j]]
            f_cont = [f for f in feats if f in cont]
            f_cat = [f for f in feats if f in cat]
            rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=3,
                                       random_state=42, n_jobs=-1)
            pipe = make_pipeline(rf, f_cont, f_cat)
            try:
                pred = cross_val_predict(pipe, df[feats], y, cv=5, n_jobs=-1)
                m = eval_predictions(y, pred)
                pair_results.append((feats, m['spearman'], m['r2']))
            except Exception:
                pair_results.append((feats, 0.0, 0.0))

    pair_results.sort(key=lambda x: -abs(x[1]))
    print(f'  Top-5 feature pairs:')
    for feats, rho, r2 in pair_results[:5]:
        print(f'    {str(feats):<55s}  Spearman={rho:+.4f}  R²={r2:.4f}')

    # Top-30 triples (from top-6 features)
    top_feats = [f for f, _, _ in single_results[:6]]
    print(f'\n  Evaluating triples from top-6 features: {top_feats}')
    triple_results = []
    for i in range(len(top_feats)):
        for j in range(i + 1, len(top_feats)):
            for k in range(j + 1, len(top_feats)):
                feats = [top_feats[i], top_feats[j], top_feats[k]]
                f_cont = [f for f in feats if f in cont]
                f_cat = [f for f in feats if f in cat]
                rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=3,
                                           random_state=42, n_jobs=-1)
                pipe = make_pipeline(rf, f_cont, f_cat)
                try:
                    pred = cross_val_predict(pipe, df[feats], y, cv=5, n_jobs=-1)
                    m = eval_predictions(y, pred)
                    triple_results.append((feats, m['spearman'], m['r2']))
                except Exception:
                    triple_results.append((feats, 0.0, 0.0))

    triple_results.sort(key=lambda x: -abs(x[1]))
    print(f'  Top-5 feature triples:')
    for feats, rho, r2 in triple_results[:5]:
        print(f'    {str(feats):<65s}  Spearman={rho:+.4f}  R²={r2:.4f}')

    # All features combined
    print(f'\n  All {n} features combined (5-fold RF):')
    rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                               random_state=42, n_jobs=-1)
    pipe = make_pipeline(rf, cont, cat)
    pred = cross_val_predict(pipe, df[cont + cat], y, cv=5, n_jobs=-1)
    m = eval_predictions(y, pred)
    print(f'    Spearman={m["spearman"]:+.4f}  R²={m["r2"]:.4f}  RMSE={m["rmse"]:.2f}')
    print()
    return single_results, pair_results, triple_results


# ── Experiment 5: Permutation Test ─────────────────────────────────────

def experiment_permutation_test(df, cont, cat, y, n_permutations=1000):
    print('=' * 70)
    print(f'  Experiment 5: Permutation Test ({n_permutations} shuffles)')
    print('=' * 70)
    print('  H₀: metadata features have no predictive power for accuracy')
    print('  Test: shuffle accuracy labels, refit RF, measure Spearman ρ')
    print()

    # Real score
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=3,
                               random_state=42, n_jobs=-1)
    pipe = make_pipeline(rf, cont, cat)
    real_pred = cross_val_predict(pipe, df[cont + cat], y, cv=5, n_jobs=-1)
    real_rho, _ = spearmanr(y, real_pred)
    real_r2 = r2_score(y, real_pred)
    print(f'  Real surrogate:   Spearman = {real_rho:.4f},  R² = {real_r2:.4f}')

    rng = np.random.default_rng(42)
    null_rhos = []
    null_r2s = []
    for i in range(n_permutations):
        y_shuf = rng.permutation(y)
        rf_s = RandomForestRegressor(n_estimators=100, min_samples_leaf=3,
                                     random_state=42, n_jobs=-1)
        pipe_s = make_pipeline(rf_s, cont, cat)
        pred_s = cross_val_predict(pipe_s, df[cont + cat], y_shuf, cv=5, n_jobs=-1)
        rho_s, _ = spearmanr(y_shuf, pred_s)
        r2_s = r2_score(y_shuf, pred_s)
        null_rhos.append(rho_s)
        null_r2s.append(r2_s)
        if (i + 1) % 100 == 0:
            print(f'    {i+1}/{n_permutations} permutations done...', flush=True)

    null_rhos = np.array(null_rhos)
    null_r2s = np.array(null_r2s)

    p_rho = np.mean(np.abs(null_rhos) >= np.abs(real_rho))
    p_r2 = np.mean(null_r2s >= real_r2)

    print(f'\n  Null distribution (shuffled labels):')
    print(f'    Spearman ρ:  mean={np.mean(null_rhos):.4f}  '
          f'std={np.std(null_rhos):.4f}  '
          f'[{np.percentile(null_rhos, 2.5):.4f}, {np.percentile(null_rhos, 97.5):.4f}]')
    print(f'    R²:          mean={np.mean(null_r2s):.4f}  '
          f'std={np.std(null_r2s):.4f}  '
          f'[{np.percentile(null_r2s, 2.5):.4f}, {np.percentile(null_r2s, 97.5):.4f}]')
    print(f'\n  Permutation p-values:')
    print(f'    P(|ρ_null| ≥ |ρ_real|) = {p_rho:.4f}')
    print(f'    P(R²_null ≥ R²_real)   = {p_r2:.4f}')

    if p_rho > 0.05:
        print(f'\n  CONCLUSION: Cannot reject H₀ (p={p_rho:.3f} > 0.05).')
        print(f'  The surrogate has NO statistically significant predictive power.')
    else:
        print(f'\n  CONCLUSION: Reject H₀ (p={p_rho:.3f} ≤ 0.05).')
        print(f'  The surrogate has statistically significant (though possibly weak) predictive power.')
    print()
    return real_rho, real_r2, null_rhos, null_r2s, p_rho, p_r2


# ── Experiment 6: Learning Curve ───────────────────────────────────────

def experiment_learning_curve(df, cont, cat, y):
    print('=' * 70)
    print('  Experiment 6: Learning Curve — Does More Data Help?')
    print('=' * 70)

    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=2,
                               random_state=42, n_jobs=-1)
    pipe = make_pipeline(rf, cont, cat)

    train_sizes_abs, train_scores, test_scores = learning_curve(
        pipe, df[cont + cat], y,
        train_sizes=np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]),
        cv=5, scoring='r2', n_jobs=-1, random_state=42,
    )

    print(f'  {"Train size":>12s} {"Train R²":>10s} {"Test R²":>10s} {"Test std":>10s}')
    print('  ' + '-' * 45)
    for ts, tr, te in zip(train_sizes_abs, train_scores, test_scores):
        print(f'  {ts:>12.0f} {np.mean(tr):>10.4f} {np.mean(te):>10.4f} {np.std(te):>10.4f}')

    print()
    if np.mean(test_scores[-1]) < 0:
        print('  CONCLUSION: Test R² is NEGATIVE even with 90% of data.')
        print('  The model is worse than predicting the mean. More data will not help.')
    print()
    return train_sizes_abs, train_scores, test_scores


# ── Visualization ──────────────────────────────────────────────────────

def plot_results(y, loo_pred, loo_metrics,
                 null_rhos, null_r2s, real_rho, real_r2,
                 train_sizes, train_scores, test_scores,
                 output_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel A: LOO predicted vs actual
    ax = axes[0, 0]
    ax.scatter(y, loo_pred, alpha=0.6, s=30, edgecolors='steelblue', linewidths=0.5)
    lims = [min(y.min(), loo_pred.min()), max(y.max(), loo_pred.max())]
    ax.plot(lims, lims, 'r--', linewidth=1, label='Perfect prediction')
    ax.set_xlabel('True accuracy (−p90 Q-error)', fontsize=12)
    ax.set_ylabel('LOO Predicted accuracy', fontsize=12)
    ax.set_title(f'A) LOO Prediction: Spearman={loo_metrics["spearman"]:.3f}, '
                 f'R²={loo_metrics["r2"]:.3f}', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2)

    # Panel B: Residuals
    ax = axes[0, 1]
    residuals = loo_pred - y
    ax.scatter(y, residuals, alpha=0.6, s=30, edgecolors='steelblue', linewidths=0.5)
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_xlabel('True accuracy (−p90 Q-error)', fontsize=12)
    ax.set_ylabel('Residual (predicted − true)', fontsize=12)
    ax.set_title('B) LOO Residuals', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.2)

    # Panel C: Permutation test
    ax = axes[1, 0]
    ax.hist(null_rhos, bins=40, alpha=0.7, color='gray', edgecolor='darkgray',
            label=f'Null distribution (n={len(null_rhos)})')
    ax.axvline(real_rho, color='red', linewidth=2, linestyle='-',
               label=f'Real ρ = {real_rho:.3f}')
    ax.axvline(-real_rho, color='red', linewidth=2, linestyle='--', alpha=0.5)
    p_val = np.mean(np.abs(null_rhos) >= np.abs(real_rho))
    ax.set_xlabel('Spearman ρ (shuffled labels)', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title(f'C) Permutation Test: p = {p_val:.3f}', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2)

    # Panel D: Learning curve
    ax = axes[1, 1]
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)
    test_std = np.std(test_scores, axis=1)
    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std,
                     alpha=0.1, color='blue')
    ax.fill_between(train_sizes, test_mean - test_std, test_mean + test_std,
                     alpha=0.1, color='orange')
    ax.plot(train_sizes, train_mean, 'o-', color='blue', label='Train R²')
    ax.plot(train_sizes, test_mean, 'o-', color='orange', label='Test R²')
    ax.axhline(0, color='gray', linestyle='--', linewidth=1, label='R² = 0 (mean baseline)')
    ax.set_xlabel('Training set size', fontsize=12)
    ax.set_ylabel('R²', fontsize=12)
    ax.set_title('D) Learning Curve', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, loc='lower right')
    ax.grid(True, alpha=0.2)

    fig.suptitle('Surrogate Quality Experiment: Can Metadata Predict Accuracy?',
                 fontsize=15, fontweight='bold', y=1.01)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Figure saved: {output_path}')


# ── Main ───────────────────────────────────────────────────────────────

def main():
    print()
    print('#' * 70)
    print('#  Surrogate Quality Experiment')
    print('#  Can model metadata predict query-estimation accuracy (p90 Q-error)?')
    print('#' * 70)
    print()

    df, cont, cat = load_data()
    y = df['accuracy'].values  # = -p90_qerror (higher is better)
    print(f'Dataset: {len(df)} models, {len(cont)} continuous features, '
          f'{len(cat)} categorical features')
    print(f'Target: accuracy (= -p90_qerror), range [{y.min():.1f}, {y.max():.1f}]')
    print()

    # Run all experiments
    loo_pred, loo_m = experiment_loo(df, cont, cat, y)
    kfold_results = experiment_kfold(df, cont, cat, y)
    univariate = experiment_univariate(df, cont, cat, y)
    singles, pairs, triples = experiment_feature_combos(df, cont, cat, y)
    real_rho, real_r2, null_rhos, null_r2s, p_rho, p_r2 = \
        experiment_permutation_test(df, cont, cat, y, n_permutations=1000)
    train_sizes, train_scores, test_scores = experiment_learning_curve(df, cont, cat, y)

    # Summary
    print('=' * 70)
    print('  OVERALL SUMMARY')
    print('=' * 70)
    print(f'  LOO R²              = {loo_m["r2"]:.4f}')
    print(f'  LOO Spearman ρ      = {loo_m["spearman"]:.4f} (p = {loo_m["spearman_p"]:.4f})')
    print(f'  Best single feature = {singles[0][0]} (ρ = {singles[0][1]:.4f})')
    print(f'  Best feature pair   = {pairs[0][0]} (ρ = {pairs[0][1]:.4f})')
    print(f'  Best feature triple = {triples[0][0]} (ρ = {triples[0][1]:.4f})')
    print(f'  Permutation p-value = {p_rho:.4f}')
    print(f'  Learning curve R²   = {np.mean(test_scores[-1]):.4f} (at 90% train)')
    print()

    if loo_m['r2'] < 0 and p_rho > 0.05:
        print('  VERDICT: The accuracy surrogate is USELESS.')
        print('  - R² < 0 means the surrogate is worse than predicting the mean.')
        print('  - Permutation test p > 0.05 means the observed correlation is')
        print('    indistinguishable from random chance.')
        print('  - No feature or feature combination achieves meaningful prediction.')
        print('  - More training data does not help (negative test R² at all sizes).')
    elif loo_m['spearman'] < 0.3:
        print('  VERDICT: The accuracy surrogate has VERY WEAK predictive power.')
        print(f'  - Spearman ρ = {loo_m["spearman"]:.3f} is too low for useful ranking.')
    else:
        print('  VERDICT: The accuracy surrogate has some predictive power.')
    print()

    # Plot
    output_path = os.path.join(SCRIPT_DIR, 'surrogate_quality_experiment.png')
    plot_results(y, loo_pred, loo_m, null_rhos, null_r2s, real_rho, real_r2,
                 train_sizes, train_scores, test_scores, output_path)


if __name__ == '__main__':
    main()
