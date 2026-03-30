#!/usr/bin/env python3
"""
Analyze correlation between model size (parameter count) and accuracy (p90_qerror).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'experiments', 'experiment_scripts',
                        'model_profile_with_nonemb.csv')
GT_CSV = os.path.join(SCRIPT_DIR, 'model_ground_truth.csv')

# Load and merge
profile = pd.read_csv(CSV_PATH)
gt = pd.read_csv(GT_CSV)
df = profile.merge(gt[['model', 'p90_qerror']], on='model', how='inner')
df['accuracy'] = -df['p90_qerror']  # higher = better

print(f"Merged dataset: {len(df)} models")
print(f"p90_qerror range: [{df['p90_qerror'].min():.1f}, {df['p90_qerror'].max():.1f}]")
print()

# Columns of interest for "model size"
size_cols = [
    'non_embedding_params',
    'embedding_params',
    'total_params',
    'num_layers',
    'hidden_size',
    'attention_heads',
    'ffn_width',
    'embedding_dimension',
    'context_length',
]

print(f"{'Feature':<30s} {'Spearman':>9s} {'sp_pval':>9s} {'Pearson':>9s} {'pe_pval':>9s}  {'N':>4s}")
print("-" * 80)

y = df['accuracy'].values

for col in size_cols:
    if col not in df.columns:
        print(f"{col:<30s}  NOT FOUND")
        continue
    vals = pd.to_numeric(df[col], errors='coerce').values
    mask = np.isfinite(vals) & np.isfinite(y)
    n = mask.sum()
    if n < 5:
        print(f"{col:<30s}  insufficient data (n={n})")
        continue
    rho, rho_p = spearmanr(vals[mask], y[mask])
    r, r_p = pearsonr(vals[mask], y[mask])
    print(f"{col:<30s} {rho:>9.4f} {rho_p:>9.4f} {r:>9.4f} {r_p:>9.4f}  {n:>4d}")

# Also compute with log-transformed params
print()
print("--- Log-transformed parameter counts ---")
print(f"{'Feature':<30s} {'Spearman':>9s} {'sp_pval':>9s} {'Pearson':>9s} {'pe_pval':>9s}  {'N':>4s}")
print("-" * 80)

for col in ['non_embedding_params', 'embedding_params', 'total_params']:
    if col not in df.columns:
        continue
    vals = pd.to_numeric(df[col], errors='coerce').values
    mask = np.isfinite(vals) & (vals > 0) & np.isfinite(y)
    n = mask.sum()
    if n < 5:
        continue
    log_vals = np.log10(vals[mask])
    rho, rho_p = spearmanr(log_vals, y[mask])
    r, r_p = pearsonr(log_vals, y[mask])
    print(f"log10({col})" f"{'':>{max(0, 30-7-len(col))}} {rho:>9.4f} {rho_p:>9.4f} {r:>9.4f} {r_p:>9.4f}  {n:>4d}")

# --- Scatter plot: log(non_embedding_params) vs accuracy ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: log(non_embedding_params) vs accuracy
ax = axes[0]
vals = pd.to_numeric(df['non_embedding_params'], errors='coerce').values
mask = np.isfinite(vals) & (vals > 0) & np.isfinite(y)
log_params = np.log10(vals[mask])
acc = y[mask]

ax.scatter(log_params, acc, alpha=0.6, s=40, edgecolors='steelblue', linewidths=0.5)

# Fit line
z = np.polyfit(log_params, acc, 1)
p_line = np.poly1d(z)
x_range = np.linspace(log_params.min(), log_params.max(), 100)
ax.plot(x_range, p_line(x_range), 'r--', linewidth=1.5, alpha=0.7, label='Linear fit')

rho, rho_p = spearmanr(log_params, acc)
r, r_p = pearsonr(log_params, acc)

ax.set_xlabel('log10(non_embedding_params)', fontsize=12)
ax.set_ylabel('Accuracy (-p90_qerror)', fontsize=12)
ax.set_title(f'Model Size vs Accuracy\nSpearman={rho:.3f} (p={rho_p:.3f}), Pearson={r:.3f} (p={r_p:.3f})',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.2)

# Right: log(total_params) vs accuracy
ax = axes[1]
vals_total = pd.to_numeric(df['total_params'], errors='coerce').values
mask2 = np.isfinite(vals_total) & (vals_total > 0) & np.isfinite(y)
log_total = np.log10(vals_total[mask2])
acc2 = y[mask2]

ax.scatter(log_total, acc2, alpha=0.6, s=40, edgecolors='darkorange', linewidths=0.5, color='orange')

z2 = np.polyfit(log_total, acc2, 1)
p_line2 = np.poly1d(z2)
x_range2 = np.linspace(log_total.min(), log_total.max(), 100)
ax.plot(x_range2, p_line2(x_range2), 'r--', linewidth=1.5, alpha=0.7, label='Linear fit')

rho2, rho_p2 = spearmanr(log_total, acc2)
r2, r_p2 = pearsonr(log_total, acc2)

ax.set_xlabel('log10(total_params)', fontsize=12)
ax.set_ylabel('Accuracy (-p90_qerror)', fontsize=12)
ax.set_title(f'Total Params vs Accuracy\nSpearman={rho2:.3f} (p={rho_p2:.3f}), Pearson={r2:.3f} (p={r_p2:.3f})',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.2)

fig.tight_layout()
output_path = os.path.join(SCRIPT_DIR, 'size_vs_accuracy.png')
fig.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nFigure saved: {output_path}")
