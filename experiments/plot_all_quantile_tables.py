#!/usr/bin/env python3
"""
Script to plot heatmaps for all quantile table CSV files across all datasets and tasks.
Extracts the plotting functionality from to_table_seeds.py.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import re

# Base directory
BASE_DIR = Path("/home/jovyan/workspace/LLM4QPR/experiments")
RESULTS_DIR = BASE_DIR / "results"

def extract_display_name(col_name):
    """Extract display name from column name"""
    # For LLM: extract model name
    if 'llm' in col_name.lower():
        # Extract model name between h{number}_ and _emb or _quant
        match = re.search(r'h\d+_(.+?)(?:_emb|_quant)', col_name)
        if match:
            model = match.group(1)
            # Also extract quantization
            quant_match = re.search(r'quant-([^_]+)', col_name)
            if quant_match:
                display_name = f"{model}_quant-{quant_match.group(1)}"
            else:
                display_name = model
            
            # Extract removed fields suffix if present
            rm_match = re.search(r'(_rm-[a-z\-]+)', col_name)
            if rm_match:
                display_name += rm_match.group(1)
            
            return display_name
        return 'LLM'
    # For non-LLM: extract algorithm name
    else:
        # Extract algo name (e.g., aimai, qf, e2e_cost, bao, ALECE, MSCN, PRICE)
        match = re.search(r'_(aimai|qf|e2e_cost|bao|postgres|ALECE|MSCN|PRICE)_', col_name)
        if match:
            algo = match.group(1)
            # For aimai, also extract feature config if present
            feat_match = re.search(r'_f(\d+)', col_name)
            if feat_match and algo == 'aimai':
                return f"{algo}_f{feat_match.group(1)}"
            return algo
        return col_name

def is_llm_method(col_name):
    """Check if a method is LLM-based"""
    return 'llm' in col_name.lower()

def create_heatmap_with_comparison(table, output_path, dataset=None, task=None):
    """
    Create a heatmap comparing LLM and non-LLM algorithms with special color coding:
    - Non-LLM: Dark orange for lowest, light orange for second lowest (per column)
    - LLM: Different shades of green based on ranking (per column)
    - Bold LLM names that beat lowest non-LLM in ≥2 columns
    - Add *** prefix for LLM names that beat second lowest non-LLM in ≥2 columns
    """
    # Separate LLM and non-LLM columns
    llm_cols = [col for col in table.columns if is_llm_method(col)]
    non_llm_cols = [col for col in table.columns if not is_llm_method(col)]
    
    # Reorder: non-LLM first, then LLM
    ordered_cols = non_llm_cols + llm_cols
    table = table[ordered_cols]
    
    # Create display names for y-axis
    display_names = {col: extract_display_name(col) for col in table.columns}
    
    # Transpose for visualization (methods as rows, percentiles as columns)
    table_T = table.T
    
    # Calculate statistics for each percentile (column)
    lowest_non_llm = {}
    second_lowest_non_llm = {}
    
    for col in table_T.columns:
        non_llm_values = table_T.loc[non_llm_cols, col].sort_values()
        if len(non_llm_values) >= 1:
            lowest_non_llm[col] = non_llm_values.iloc[0]
        if len(non_llm_values) >= 2:
            second_lowest_non_llm[col] = non_llm_values.iloc[1]
    
    # Check LLM performance against non-LLM baselines
    llm_beats_lowest = {llm: 0 for llm in llm_cols}
    llm_beats_second = {llm: 0 for llm in llm_cols}
    
    for col in table_T.columns:
        for llm in llm_cols:
            llm_value = table_T.loc[llm, col]
            if col in lowest_non_llm and llm_value < lowest_non_llm[col]:
                llm_beats_lowest[llm] += 1
            if col in second_lowest_non_llm and llm_value < second_lowest_non_llm[col]:
                llm_beats_second[llm] += 1
    
    # Create custom y-axis labels with formatting
    y_labels = []
    for method in table_T.index:
        label = display_names[method]
        if method in llm_cols:
            # Bold if beats lowest in ≥2 columns
            if llm_beats_lowest[method] >= 2:
                # Escape underscores for LaTeX math mode
                label_escaped = label.replace('_', '\\_')
                label = f"$\\mathbf{{{label_escaped}}}$"
            # Add *** prefix if beats second lowest in ≥2 columns
            if llm_beats_second[method] >= 2:
                label = f"***{label}"
        y_labels.append(label)
    
    # Create figure with adjusted width for longer LLM names
    # Calculate max label length to adjust left margin
    max_label_length = max(len(str(label)) for label in y_labels)
    # Base width + extra for longer labels
    fig_width = max(12, len(table_T.columns) * 1.5 + max_label_length * 0.1)
    fig_height = max(8, len(table_T.index) * 0.5)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Create a custom colormap array
    n_rows, n_cols = table_T.shape
    colors = np.zeros((n_rows, n_cols, 4))  # RGBA
    
    # Color each cell based on rules
    for i, method in enumerate(table_T.index):
        for j, percentile in enumerate(table_T.columns):
            value = table_T.iloc[i, j]
            
            if method in non_llm_cols:
                # Non-LLM: mark lowest and second lowest
                non_llm_values = table_T.loc[non_llm_cols, percentile].sort_values()
                if len(non_llm_values) >= 1 and value == non_llm_values.iloc[0]:
                    # Dark orange for lowest
                    colors[i, j] = [1.0, 0.5, 0.0, 1.0]  # Dark orange
                elif len(non_llm_values) >= 2 and value == non_llm_values.iloc[1]:
                    # Light orange for second lowest
                    colors[i, j] = [1.0, 0.8, 0.4, 1.0]  # Light orange
                else:
                    # White for others
                    colors[i, j] = [1.0, 1.0, 1.0, 1.0]
            else:
                # LLM: shade of green based on ranking among LLM methods only
                # Smaller values (better performance) → darker green
                llm_values = table_T.loc[llm_cols, percentile].sort_values()
                # Find rank: 0 for smallest (best), n-1 for largest (worst)
                rank = list(llm_values.values).index(value)
                
                if len(llm_values) > 1:
                    # Map rank to intensity
                    # Rank 0 (best/smallest) → intensity = 0.3 (darkest)
                    # Rank n-1 (worst/largest) → intensity = 1.0 (brightest)
                    intensity = 0.3 + (rank / (len(llm_values) - 1)) * 0.7
                else:
                    # Single LLM method
                    intensity = 0.65
                
                colors[i, j] = [0.0, intensity, 0.0, 1.0]
    
    # Create the heatmap without color mapping (we'll use custom colors)
    im = ax.imshow(colors, aspect='auto')
    
    # Set ticks and labels
    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(table_T.columns, fontsize=12)
    ax.set_yticklabels(y_labels, fontsize=10)
    
    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add text annotations with values
    for i in range(n_rows):
        for j in range(n_cols):
            value = table_T.iloc[i, j]
            # Skip NaN values
            if pd.isna(value):
                continue
            # Use scientific notation for values >= 1000
            if value >= 1000:
                text_str = f'{value:.2e}'
            else:
                text_str = f'{value:.2f}'
            text = ax.text(j, i, text_str,
                          ha="center", va="center", color="black", fontsize=8)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=[1.0, 0.5, 0.0, 1.0], label='Non-LLM: Lowest'),
        mpatches.Patch(facecolor=[1.0, 0.8, 0.4, 1.0], label='Non-LLM: 2nd Lowest'),
        mpatches.Patch(facecolor=[0.0, 0.3, 0.0, 1.0], label='LLM: Best (Smallest)'),
        mpatches.Patch(facecolor=[0.0, 0.65, 0.0, 1.0], label='LLM: Middle'),
        mpatches.Patch(facecolor=[0.0, 1.0, 0.0, 1.0], label='LLM: Worst (Largest)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
    
    # Add separator line between non-LLM and LLM
    if len(non_llm_cols) > 0 and len(llm_cols) > 0:
        separator_y = len(non_llm_cols) - 0.5
        ax.axhline(y=separator_y, color='black', linewidth=2, linestyle='--')
    
    # Labels
    ax.set_xlabel('Percentile', fontsize=14, fontweight='bold')
    ax.set_ylabel('Method', fontsize=14, fontweight='bold')
    
    # Create title with dataset and task info if provided
    title = 'Q-Error Comparison: LLM vs Non-LLM Algorithms'
    if dataset and task:
        title = f'{title}\nDataset: {dataset.upper()}, Task: {task.upper()}'
    title += '\n(Bold: beats best non-LLM in ≥2 cols, ***: beats 2nd-best in ≥2 cols)'
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Heatmap saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("LLM PERFORMANCE SUMMARY")
    if dataset and task:
        print(f"Dataset: {dataset.upper()}, Task: {task.upper()}")
    print("="*80)
    for llm in llm_cols:
        print(f"{display_names[llm]}:")
        print(f"  Beats best non-LLM: {llm_beats_lowest[llm]}/{len(table_T.columns)} columns")
        print(f"  Beats 2nd-best non-LLM: {llm_beats_second[llm]}/{len(table_T.columns)} columns")
    print("="*80)

def find_all_quantile_tables():
    """
    Find all quantile table CSV files in the results directory.
    Returns a list of (csv_path, dataset, task) tuples.
    """
    quantile_tables = []
    
    # Pattern: quantile_table_results_results_Train_{dataset}_Test_{dataset}_ours_{task}.csv
    pattern = r'quantile_table_results_results_Train_(\w+)_Test_\1_ours_(card|time)\.csv'
    
    for results_subdir in RESULTS_DIR.iterdir():
        if not results_subdir.is_dir():
            continue
        
        for csv_file in results_subdir.glob('quantile_table_results*.csv'):
            match = re.search(pattern, csv_file.name)
            if match:
                dataset = match.group(1)
                task = match.group(2)
                quantile_tables.append((csv_file, dataset, task))
    
    return quantile_tables

def main():
    """Main function to plot all quantile tables"""
    
    # Find all quantile table files
    quantile_tables = find_all_quantile_tables()
    
    if not quantile_tables:
        print("No quantile table files found!")
        return
    
    print(f"Found {len(quantile_tables)} quantile table files")
    print("="*80)
    
    # Process each quantile table
    for csv_path, dataset, task in quantile_tables:
        print(f"\nProcessing: {csv_path.name}")
        print(f"  Dataset: {dataset}, Task: {task}")
        
        try:
            # Read the quantile table
            df = pd.read_csv(csv_path, index_col=0)
            
            # Remove duplicate index rows (keep first occurrence)
            df = df[~df.index.duplicated(keep='first')]
            
            # Remove any rows that are not quantile values (50, 90, 95, max)
            valid_indices = ['50', '90', '95', 'max']
            df = df.loc[df.index.isin(valid_indices)]
            
            if df.empty:
                print(f"  Warning: No valid quantile data in {csv_path.name}")
                continue
            
            # Create output path for heatmap
            heatmap_path = csv_path.parent / f"{csv_path.stem}_heatmap.png"
            
            # Create heatmap
            create_heatmap_with_comparison(df, heatmap_path, dataset=dataset, task=task)
            
        except Exception as e:
            print(f"  Error processing {csv_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("All plots generated successfully!")
    print("="*80)

if __name__ == "__main__":
    main()

