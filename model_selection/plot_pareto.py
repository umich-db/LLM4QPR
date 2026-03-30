#!/usr/bin/env python3
"""Plot latency vs accuracy for all models, marking the true Pareto frontier."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'experiment_scripts'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from argparse import Namespace
from model_selection_v2 import load_candidates, find_cdf_file, parse_qerror

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'experiments', 'experiment_scripts', 'model_profile_with_nonemb.csv')

def main():
    candidates = load_candidates(CSV_PATH)
    args = Namespace(
        dry_run=False, workload='stats', task='time', db='postgres',
        quantification='4-bit', embed_size=1000, price_s=True,
        max_eval_queries=200, csv=CSV_PATH,
    )

    # Get accuracy for all models with cached results
    records = []
    for _, row in candidates.iterrows():
        cached = find_cdf_file(row['model'], args)
        if cached is None:
            continue
        qe = parse_qerror(cached)
        records.append({
            'model': row['model'],
            'avg_ms': float(row['avg_ms']),
            'p90': qe['p90'],
            'total_params': float(row['total_params']),
            'non_embedding_params': float(row['non_embedding_params']),
        })

    df = pd.DataFrame(records)
    print(f"{len(df)} models with cached results")

    # Compute true Pareto frontier (lower latency, lower p90 = better)
    # Sort by latency ascending, track running min of p90
    df_sorted = df.sort_values('avg_ms')
    best_p90 = float('inf')
    frontier_models = set()
    for _, row in df_sorted.iterrows():
        if row['p90'] < best_p90:
            frontier_models.add(row['model'])
            best_p90 = row['p90']

    df['is_frontier'] = df['model'].isin(frontier_models)
    frontier_df = df[df['is_frontier']].sort_values('avg_ms')

    print(f"Pareto frontier: {len(frontier_df)} models")
    for _, r in frontier_df.iterrows():
        print(f"  {r['model']:55s}  lat={r['avg_ms']:6.1f}ms  p90={r['p90']:.2f}")

    # Assign family for coloring
    def get_family(model):
        m = model.lower()
        if 'qwen' in m: return 'Qwen'
        if 'pythia' in m or 'gpt-neo' in m: return 'Pythia/GPT-Neo'
        if 'opt-' in m: return 'OPT'
        if 'smollm' in m: return 'SmolLM'
        if 'sentence-transformers' in m: return 'SentenceTransformers'
        if 'minilm' in m: return 'MiniLM'
        if 'albert' in m: return 'ALBERT'
        if 'electra' in m: return 'ELECTRA'
        if 'deberta' in m: return 'DeBERTa'
        if 'modernbert' in m or 'nomic' in m: return 'ModernBERT'
        if 'distilbert' in m or 'distilroberta' in m or 'distilgpt' in m: return 'DistilBERT'
        if 'roberta' in m or 'xlm-roberta' in m: return 'RoBERTa'
        if 'gemma' in m: return 'Gemma'
        if 'neuml' in m: return 'NeuML'
        if 'bert' in m: return 'BERT'
        return 'Other'

    df['family'] = df['model'].apply(get_family)

    # Color palette
    family_colors = {
        'BERT': '#1f77b4',
        'SentenceTransformers': '#2ca02c',
        'ALBERT': '#9467bd',
        'ELECTRA': '#8c564b',
        'DeBERTa': '#e377c2',
        'ModernBERT': '#17becf',
        'DistilBERT': '#ff7f0e',
        'RoBERTa': '#d62728',
        'Pythia/GPT-Neo': '#7f7f7f',
        'OPT': '#bcbd22',
        'SmolLM': '#aec7e8',
        'Qwen': '#ff9896',
        'MiniLM': '#98df8a',
        'Gemma': '#ffbb78',
        'NeuML': '#c5b0d5',
        'Other': '#c7c7c7',
    }

    # Plot
    plt.style.use('seaborn-v0_8-ticks')
    fig, ax = plt.subplots(figsize=(16, 10))

    # Plot non-frontier points by family
    non_frontier = df[~df['is_frontier']]
    for family in sorted(df['family'].unique()):
        subset = non_frontier[non_frontier['family'] == family]
        if subset.empty:
            continue
        ax.scatter(subset['avg_ms'], subset['p90'],
                   c=family_colors.get(family, '#c7c7c7'),
                   s=40, alpha=0.6, label=family, edgecolors='white', linewidths=0.5, zorder=2)

    # Plot Pareto frontier line + points
    ax.plot(frontier_df['avg_ms'], frontier_df['p90'],
            'r-', linewidth=2.5, alpha=0.7, zorder=3, label='Pareto frontier')
    ax.scatter(frontier_df['avg_ms'], frontier_df['p90'],
               c='red', s=120, marker='*', edgecolors='darkred', linewidths=0.8,
               zorder=4)

    # Label frontier points
    for _, r in frontier_df.iterrows():
        short_name = r['model'].split('/')[-1]
        # Shorten long names
        if len(short_name) > 30:
            short_name = short_name[:27] + '...'
        ax.annotate(
            short_name,
            (r['avg_ms'], r['p90']),
            textcoords='offset points',
            xytext=(8, -5),
            fontsize=8,
            fontweight='bold',
            color='darkred',
            path_effects=[pe.withStroke(linewidth=2.5, foreground='white')],
            zorder=5,
        )

    ax.set_xlabel('Latency (ms)', fontsize=14)
    ax.set_ylabel('p90 Q-error (lower is better)', fontsize=14)
    ax.set_title('Latency vs Accuracy (p90 Q-error) — All Evaluated Models\nRed stars = True Pareto Frontier',
                 fontsize=15)

    # Log scale for y-axis since p90 varies widely
    ax.set_yscale('log')

    ax.legend(loc='upper left', fontsize=9, ncol=2, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=12)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pareto_frontier.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved to {out_path}")
    plt.close()


if __name__ == '__main__':
    main()
