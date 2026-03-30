#!/usr/bin/env python3
"""
Rank stability analysis: does low-fidelity (few epochs) performance
predict high-fidelity (more epochs) performance?

Tests:
1. Positive cross-fidelity rank correlation
2. Correlation improves with fidelity
"""

import os, re, glob
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LOG_DIR = '/root/LLM4QPR/experiments/logs/rank_stability'
GT_CSV = '/root/LLM4QPR/model_selection/model_ground_truth.csv'
OUT_DIR = '/root/LLM4QPR/model_selection'


def extract_model_name(logpath):
    """Extract model name from log filename, restoring org/model format."""
    base = os.path.basename(logpath)
    m = re.match(r'finetune_(.+?)_seed\d+\.log', base)
    if not m:
        return None
    raw = m.group(1)
    # Known org prefixes — restore the first '-' after these as '/'
    orgs = ['google', 'distilbert', 'EleutherAI', 'albert', 'nreimers',
            'sentence-transformers', 'FacebookAI', 'facebook', 'google-bert',
            'HuggingFaceTB', 'Qwen', 'microsoft', 'prajjwal1', 'Alibaba-NLP']
    for org in sorted(orgs, key=len, reverse=True):
        prefix = org.replace('/', '-')
        if raw.startswith(prefix + '-'):
            return org + '/' + raw[len(prefix) + 1:]
    # Fallback: first '-' becomes '/'
    return raw.replace('-', '/', 1)


def parse_finetune_log(logpath):
    """Extract per-epoch p90 Q-error from finetune training log.
    Returns dict: {epoch: {'train_p90': ..., 'val_p90': ...}}"""
    epochs = {}
    current_epoch = 0
    current_section = None

    with open(logpath, 'r') as f:
        for line in f:
            # Track epoch from batch log
            em = re.search(r'Epoch (\d+) Batch', line)
            if em:
                current_epoch = int(em.group(1))

            # Detect data section
            if 'Data section: train' in line:
                current_section = 'train'
            elif 'Data section: val' in line:
                current_section = 'val'
            elif 'Data section: test' in line:
                current_section = 'test'

            # Extract p90
            pm = re.search(r'90th percentile:\s*([\d.]+)', line)
            if pm:
                p90 = float(pm.group(1))
                if current_epoch not in epochs:
                    epochs[current_epoch] = {}

                if current_section == 'val':
                    epochs[current_epoch]['val_p90'] = p90
                elif current_section == 'train':
                    epochs[current_epoch]['train_p90'] = p90
                elif current_section == 'test':
                    epochs[current_epoch]['test_p90'] = p90
                else:
                    # No section marker yet — likely train
                    epochs[current_epoch].setdefault('train_p90', p90)

    return epochs


def main():
    # Load ground truth (pretrained = 0-epoch fidelity)
    gt = pd.read_csv(GT_CSV)
    gt_lookup = dict(zip(gt['model'], gt['p90_qerror']))

    # Parse all finetune logs
    logs = sorted(glob.glob(os.path.join(LOG_DIR, 'finetune_*_seed42.log')))
    if not logs:
        print(f"No logs found in {LOG_DIR}")
        return

    print(f"Found {len(logs)} finetune logs")

    all_data = {}
    for lp in logs:
        model = extract_model_name(lp)
        if model is None:
            continue
        epochs = parse_finetune_log(lp)
        if epochs:
            all_data[model] = epochs
            pretrained_p90 = gt_lookup.get(model, None)
            print(f"\n  {model}:")
            print(f"    Pretrained (0-epoch) p90: {pretrained_p90}")
            for ep in sorted(epochs.keys()):
                parts = ', '.join(f"{k}={v:.1f}" for k, v in epochs[ep].items())
                print(f"    Epoch {ep}: {parts}")

    if len(all_data) < 3:
        print(f"\nOnly {len(all_data)} models with data — need at least 3 for correlation")
        return

    # Build comparison table: pretrained p90 vs each epoch's val/train p90
    models = sorted(all_data.keys())
    max_epoch = max(max(ep_data.keys()) for ep_data in all_data.values())

    print(f"\n{'='*60}")
    print(f"Cross-Fidelity Rank Correlation ({len(models)} models)")
    print(f"{'='*60}")

    # Epoch 0 = pretrained p90
    pretrained = np.array([gt_lookup.get(m, np.nan) for m in models])

    # For each fidelity level (epoch), compute Spearman with pretrained
    correlations = {}
    for ep in range(max_epoch + 1):
        vals = []
        valid_models = []
        for i, m in enumerate(models):
            ep_data = all_data[m].get(ep, {})
            # Prefer val_p90, fall back to train_p90
            p90 = ep_data.get('val_p90', ep_data.get('train_p90', None))
            if p90 is not None and not np.isnan(pretrained[i]):
                vals.append(p90)
                valid_models.append(i)

        if len(vals) >= 3:
            p90_arr = np.array(vals)
            pre_arr = pretrained[np.array(valid_models)]
            rho, pval = spearmanr(pre_arr, p90_arr)
            tau, _ = kendalltau(pre_arr, p90_arr)
            correlations[ep] = {'spearman': rho, 'p_value': pval, 'kendall': tau, 'n': len(vals)}
            print(f"  Epoch {ep:>2d} vs Pretrained: Spearman={rho:+.3f} (p={pval:.3f}), "
                  f"Kendall={tau:+.3f}, n={len(vals)}")

    # Also compute adjacent epoch correlations
    print(f"\n{'='*60}")
    print("Adjacent Epoch Correlation")
    print(f"{'='*60}")
    epoch_list = sorted(correlations.keys())
    for i in range(len(epoch_list) - 1):
        ep1, ep2 = epoch_list[i], epoch_list[i+1]
        vals1, vals2 = [], []
        for m in models:
            d1 = all_data[m].get(ep1, {})
            d2 = all_data[m].get(ep2, {})
            v1 = d1.get('val_p90', d1.get('train_p90', None))
            v2 = d2.get('val_p90', d2.get('train_p90', None))
            if v1 is not None and v2 is not None:
                vals1.append(v1)
                vals2.append(v2)
        if len(vals1) >= 3:
            rho, pval = spearmanr(vals1, vals2)
            print(f"  Epoch {ep1} vs Epoch {ep2}: Spearman={rho:+.3f} (p={pval:.3f}), n={len(vals1)}")

    # === PLOT ===
    if not correlations:
        print("No correlations to plot")
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel 1: Spearman vs fidelity (epoch)
    ax = axes[0]
    eps = sorted(correlations.keys())
    rhos = [correlations[e]['spearman'] for e in eps]
    ax.plot(eps, rhos, 'o-', color='steelblue', linewidth=2, markersize=8)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Fidelity (epoch)', fontsize=12)
    ax.set_ylabel('Spearman ρ vs pretrained', fontsize=12)
    ax.set_title('Cross-Fidelity Rank Correlation\n(higher = more predictive)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.2)
    ax.set_ylim(-0.3, 1.1)
    for e, r in zip(eps, rhos):
        ax.annotate(f'{r:.2f}', (e, r), textcoords='offset points', xytext=(5, 8), fontsize=9)

    # Panel 2: Scatter — pretrained vs last epoch
    ax = axes[1]
    last_ep = max(correlations.keys())
    pre_vals, ft_vals, model_labels = [], [], []
    for m in models:
        ep_data = all_data[m].get(last_ep, {})
        p90 = ep_data.get('val_p90', ep_data.get('train_p90', None))
        pre = gt_lookup.get(m, None)
        if p90 is not None and pre is not None:
            pre_vals.append(pre)
            ft_vals.append(p90)
            model_labels.append(m.split('/')[-1])

    ax.scatter(pre_vals, ft_vals, s=60, edgecolors='steelblue', linewidths=0.8, alpha=0.7)
    for x, y, label in zip(pre_vals, ft_vals, model_labels):
        short = label[:18] + '..' if len(label) > 20 else label
        ax.annotate(short, (x, y), fontsize=7, xytext=(4, 4), textcoords='offset points', alpha=0.8)

    rho = correlations[last_ep]['spearman']
    ax.set_xlabel('Pretrained p90 Q-error (0-epoch)', fontsize=11)
    ax.set_ylabel(f'Finetuned p90 Q-error (epoch {last_ep})', fontsize=11)
    ax.set_title(f'Pretrained vs Epoch {last_ep}\nSpearman={rho:+.3f}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.2)

    # Panel 3: Rank trajectory
    ax = axes[2]
    for m in models:
        short = m.split('/')[-1]
        if len(short) > 18:
            short = short[:16] + '..'
        # Rank at each epoch (by val_p90 or train_p90)
        ep_vals = {}
        for ep in eps:
            d = all_data[m].get(ep, {})
            v = d.get('val_p90', d.get('train_p90', None))
            if v is not None:
                ep_vals[ep] = v

        # Add pretrained as epoch -1
        pre = gt_lookup.get(m, None)
        if pre is not None:
            ep_vals[-1] = pre

        if len(ep_vals) >= 2:
            sorted_eps = sorted(ep_vals.keys())
            ax.plot(sorted_eps, [ep_vals[e] for e in sorted_eps], 'o-', markersize=4, alpha=0.7, label=short)

    ax.set_xlabel('Fidelity (epoch, -1=pretrained)', fontsize=11)
    ax.set_ylabel('p90 Q-error', fontsize=11)
    ax.set_title('Performance Trajectory per Model', fontsize=13, fontweight='bold')
    ax.legend(fontsize=6.5, loc='upper right', ncol=2)
    ax.grid(True, alpha=0.2)

    fig.suptitle('Multi-Fidelity Rank Stability Experiment', fontsize=15, fontweight='bold')
    fig.tight_layout()
    outpath = os.path.join(OUT_DIR, 'rank_stability_experiment.png')
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: {outpath}")


if __name__ == '__main__':
    main()
