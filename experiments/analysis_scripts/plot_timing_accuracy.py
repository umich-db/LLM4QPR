#!/usr/bin/env python3
"""
Script to plot timing vs accuracy graphs from combined_timing_accuracy_report.csv

Usage:
    python plot_timing_accuracy.py [--group_by task|task_dataset]
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import colorsys


def parse_args():
    parser = argparse.ArgumentParser(description="Plot timing vs accuracy graphs")
    parser.add_argument("--group_by", type=str, default="task_dataset", 
                        choices=["task", "task_dataset"],
                        help="Group by 'task' only (averages across datasets) or 'task_dataset' (default: task_dataset)")
    parser.add_argument("--input", type=str, default="combined_timing_accuracy_report.csv",
                        help="Input CSV file (default: combined_timing_accuracy_report.csv)")
    parser.add_argument("--output_dir", type=str, default="graphs",
                        help="Output directory for graphs (default: graphs)")
    parser.add_argument("--outlier_nth", type=int, default=3,
                        help="Use nth highest value for outlier filtering (default: 3). Outliers are filtered if > 10x this value.")
    parser.add_argument("--relative", type=str, choices=["pg", "min"], default=None,
                        help="Plot relative error. Use 'pg' for postgres baseline (current behavior) "
                             "or 'min' to use the smallest error as baseline.")
    return parser.parse_args()


def extract_model_size(model_name):
    """
    Extract model size in billions from model name.
    Looks for patterns like "3B", "0.6B", "12b", etc.
    Returns the size as a float, or None if not found.
    """
    if not model_name:
        return None
    
    # Split by "-" and look for {number}b or {number}B pattern
    parts = model_name.split('-')
    for part in parts:
        # Match patterns like "3B", "0.6B", "12b", "1.5b"
        match = re.search(r'(\d+\.?\d*)[bB]', part)
        if match:
            return float(match.group(1))
    
    return None


def get_color_for_model(algo, model, all_models_in_group):
    """
    Assign color based on algo and model name.
    
    Rules:
    - Non-LLM algos: Distinct colors (purple for aimai, pink for bao, cyan for e2e, black for qf, grey for postgres, orange for mscn, dark teal for alece, light red for price)
    - LLM with "sentence": Darkest red (high saturation, low brightness)
    - LLM with "bert" (lowercase): Medium red (medium saturation and brightness)
    - LLM with "BERT" or "ModernBERT": Lightest red (low saturation, high brightness)
    - LLM with "gemma": Different shades of blue (varying saturation/brightness by model size)
    - LLM with "llama": Different shades of green (varying saturation/brightness by model size)
    - LLM with "Qwen" and "Embedding": Different shades of orange (varying saturation/brightness by model size)
    - LLM with "Qwen" but no "Embedding": Different shades of red (varying saturation/brightness by model size)
    """
    if algo != 'llm':
        # Non-LLM: explicit color assignment for each algorithm
        algo_color_map = {
            'aimai': (0.6, 0.0, 0.8),   # Purple
            'bao': (1.0, 0.4, 0.7),     # Pink
            'e2e': (0.0, 0.8, 0.8),     # Cyan
            'qf': (0.0, 0.0, 0.0),      # Black
            'postgres': (0.4, 0.4, 0.4), # Grey
            'mscn': (1.0, 0.65, 0.0),   # Orange
            'alece': (0.0, 0.5, 0.5),   # Dark Teal
            'price': (1.0, 0.5, 0.5),   # Light Red
        }
        # Return the mapped color, or a default if algo not found
        return algo_color_map.get(algo, (0.5, 0.5, 0.5))
    
    # For LLM, extract size
    size = extract_model_size(model)
    if size is None:
        size = 1.0  # Default size if not found
    
    # Determine base hue based on model name
    model_lower = model.lower()
    
    # Special handling for sentence/bert/BERT models (assign fixed colors based on name)
    if 'sentence' in model_lower or 'bert' in model_lower:
        hue = 0.0  # Red hue for sentence/bert/BERT models
        # Assign specific saturation and value based on model type
        if 'sentence' in model_lower:
            # Darkest red for sentence models
            saturation = 1.0
            value = 0.5
        elif 'modernbert' in model_lower or model.count('BERT') > 0:
            # Lightest red for ModernBERT (contains uppercase BERT)
            saturation = 0.6
            value = 1.0
        else:
            # Medium red for bert models (lowercase bert)
            saturation = 0.8
            value = 0.75
        
        # Convert HSV to RGB and return early
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return (r, g, b)
    
    if 'gemma' in model_lower:
        hue = 0.6  # Blue hue
    elif 'llama' in model_lower:
        hue = 0.33  # Green hue
    elif 'qwen' in model_lower and 'embedding' in model_lower:
        hue = 0.08  # Orange hue
    elif 'qwen' in model_lower:
        hue = 0.0  # Red hue
    else:
        # Default to purple for unknown LLM models
        hue = 0.75
    
    # Find all models in this group with the same base color
    same_color_models = []
    for other_model in all_models_in_group:
        other_model_lower = other_model.lower()
        if 'gemma' in model_lower and 'gemma' in other_model_lower:
            same_color_models.append(other_model)
        elif 'llama' in model_lower and 'llama' in other_model_lower:
            same_color_models.append(other_model)
        elif 'qwen' in model_lower and 'embedding' in model_lower and \
             'qwen' in other_model_lower and 'embedding' in other_model_lower:
            same_color_models.append(other_model)
        elif 'qwen' in model_lower and 'embedding' not in model_lower and \
             'qwen' in other_model_lower and 'embedding' not in other_model_lower:
            same_color_models.append(other_model)
    
    # Get sizes for all same-color models
    sizes = []
    for m in same_color_models:
        s = extract_model_size(m)
        if s is not None:
            sizes.append(s)
    
    if not sizes or len(sizes) == 1:
        # Single model or no size info: use mid-range saturation and brightness
        saturation = 0.8
        value = 0.8
    else:
        min_size = min(sizes)
        max_size = max(sizes)
        
        # Normalize size to [0, 1] range
        normalized_size = (size - min_size) / (max_size - min_size)
        
        # Vary saturation: larger models have higher saturation (0.6 to 1.0)
        saturation = 0.6 + 0.4 * normalized_size
        
        # Vary value/brightness: larger models have higher brightness (0.6 to 1.0)
        value = 0.6 + 0.4 * normalized_size
    
    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (r, g, b)


def filter_extreme_outliers(df, error_col='error', nth_highest=3):
    """
    Filter out extreme outliers based on the rule:
    If any error value is > 10x the nth highest error, exclude it.
    If nth_highest is larger than the number of data points, use the smallest error as reference.
    
    Args:
        df: DataFrame with error column
        error_col: Name of the error column
        nth_highest: Which highest value to use as reference (default: 3 for third highest)
    
    Returns:
        Tuple of (filtered_df, outliers_df)
    """
    if len(df) == 0:
        return df, pd.DataFrame()
    
    # Get sorted error values (descending order, highest first)
    sorted_errors = df[error_col].sort_values(ascending=False).values
    
    # If nth_highest is larger than available data, use the smallest value (most lenient)
    if nth_highest > len(sorted_errors):
        reference_value = sorted_errors[-1]  # Last element = smallest error
        print(f"    Note: outlier_nth ({nth_highest}) > data points ({len(sorted_errors)}), using smallest error as reference")
    else:
    # Get the nth highest value (nth_highest - 1 because of 0-indexing)
        reference_value = sorted_errors[nth_highest - 1]
    
    # Calculate threshold (10x the reference value, or 10 if reference is negative)
    if reference_value < 0:
        threshold = 10  # Use fixed threshold when reference is negative (relative error mode)
        print(f"    Note: reference value is negative ({reference_value:.2f}), using fixed threshold of 10")
    else:
        threshold = min(10, 10 * reference_value)
    
    # Check if any values exceed the threshold
    if sorted_errors[0] > threshold or (len(sorted_errors) > 1 and sorted_errors[1] > threshold):
        # Split into filtered and outliers
        filtered_df = df[df[error_col] <= threshold].copy()
        outliers_df = df[df[error_col] > threshold].copy()
        num_filtered = len(outliers_df)
        if num_filtered > 0:
            print(f"    Filtered out {num_filtered} extreme outlier(s) (>{threshold:.2f})")
        return filtered_df, outliers_df
    
    return df, pd.DataFrame()


def assign_colors_to_dataframe(df, all_llm_models_in_group):
    """
    Assign colors to each row in the dataframe based on algo and model.
    Returns a list of colors in the same order as df.
    
    Args:
        df: DataFrame with data to assign colors to
        all_llm_models_in_group: List of ALL LLM models in the group (before filtering)
    """
    colors = []
    for _, row in df.iterrows():
        color = get_color_for_model(row['algo'], row['model'], all_llm_models_in_group)
        colors.append(color)
    
    return colors


def convert_to_relative_error(df, error_col='error', mode='pg'):
    """
    Convert errors to relative errors.
    
    Args:
        df: DataFrame with error column and algo column
        error_col: Name of the error column
        mode: 'pg' to use postgres as baseline (current behavior),
              'min' to use the smallest error as baseline.
    
    Returns:
        DataFrame with relative errors
    """
    df = df.copy()
    
    if mode == 'pg':
        # Find postgres error
        postgres_rows = df[df['algo'] == 'postgres']
        if postgres_rows.empty or pd.isna(postgres_rows[error_col].iloc[0]):
            raise ValueError("No postgres error found or postgres error is NaN, cannot compute relative error")
        
        postgres_error = postgres_rows[error_col].iloc[0]
        
        # Handle special cases
        if postgres_error == 0:
            raise ValueError("Postgres error is 0, cannot compute relative error")
        
        if postgres_error == np.inf:
            raise ValueError("Postgres error is inf, cannot compute relative error")
        
        # Convert all errors to relative errors (postgres baseline becomes 0)
        df[error_col] = df[error_col] / postgres_error - postgres_error / df[error_col]
    elif mode == 'min':
        # Use the smallest non-NaN, non-negative error as baseline
        errors = df[error_col].dropna()
        if errors.empty:
            raise ValueError("Cannot compute relative error - all errors are NaN")
        
        # Prefer strictly positive minimum to avoid divide-by-zero; fallback to zero if all zeros
        positive_errors = errors[errors > 0]
        if not positive_errors.empty:
            baseline = positive_errors.min()
        else:
            # If all errors are zero, relative comparison is undefined
            raise ValueError("Cannot compute relative error - all errors are zero")
        
        df[error_col] = df[error_col] / baseline
    else:
        raise ValueError(f"Unsupported relative mode: {mode}")
    
    return df


def create_scatter_plot(df, phase, metric, group_name, output_dir, all_llm_models_in_group,
                        nth_highest=3, relative_mode=None, convert_relative=False):
    """
    Create a scatter plot for a specific phase (train/test) and metric (q50/q90/q95/qmax).
    
    Args:
        df: DataFrame with columns [time_ms, error, algo, model, label]
        phase: 'train' or 'test'
        metric: 'q50', 'q90', 'q95', or 'qmax'
        group_name: Name of the group (for title and filename)
        output_dir: Directory to save the plot
        all_llm_models_in_group: List of ALL LLM models in the group (before filtering)
        nth_highest: Which highest value to use for outlier filtering (default: 3)
        relative_mode: None for absolute error, 'pg' for postgres baseline, 'min' for minimum baseline
        convert_relative: If True, convert to relative error (default: False, used when data is not already relative)
    """
    # Filter out rows with missing data and exclude postgres
    # First, identify rows with missing data
    missing_time = df['time_ms'].isna()
    missing_error = df['error'].isna()
    missing_rows = df[missing_time | missing_error]
    
    if not missing_rows.empty:
        print(f"  Rows with missing data in {group_name}/{phase}_{metric}:")
        for idx, row in missing_rows.iterrows():
            missing_fields = []
            if pd.isna(row['time_ms']):
                missing_fields.append('time_ms')
            if pd.isna(row['error']):
                missing_fields.append(metric)
            print(f"    {row['algo']}-{row['model'] if row['model'] else ''}: missing {', '.join(missing_fields)}")
    
    # Convert to relative error if requested and not already converted
    if convert_relative:
        df = convert_to_relative_error(df, error_col='error', mode=relative_mode if relative_mode else 'pg')
    
    # Separate postgres rows (may have NaN time)
    postgres_rows = df[df['algo'] == 'postgres'].copy()
    df_clean = df[df['algo'] != 'postgres'].copy()
    
    # Separate rows with inf error
    inf_rows = df_clean[df_clean['error'] == np.inf].copy()
    df_clean = df_clean[df_clean['error'] != np.inf].copy()
    
    # Drop rows with missing error (but keep rows with missing time for now)
    df_clean = df_clean.dropna(subset=['error']).copy()
    
    # Temporarily disable Qwen without Embedding models
    def is_qwen_without_embedding(row):
        if row['algo'] == 'llm' and pd.notna(row['model']) and row['model']:
            if 'qwen' in row['model'].lower():
                return 'embedding' not in row['model'].lower()
        return False
    
    df_clean = df_clean[~df_clean.apply(is_qwen_without_embedding, axis=1)]
    
    # Check if df_clean still has data and time_ms column before filtering
    if df_clean.empty or 'time_ms' not in df_clean.columns:
        print(f"  Skipping {group_name}/{phase}_{metric}.png - no data after filtering Qwen models")
        return
    
    # Now drop rows with missing time
    df_clean = df_clean.dropna(subset=['time_ms']).copy()
    
    if df_clean.empty:
        print(f"  Skipping {group_name}/{phase}_{metric}.png - no valid data")
        return
    
    # Filter extreme outliers (top 2 if they're > 10x the nth highest)
    df_clean, df_outliers = filter_extreme_outliers(df_clean, error_col='error', nth_highest=nth_highest)
    
    # Add postgres back with time set to the fastest non-filtered algorithm
    # But if postgres has inf error, add it to inf_rows instead
    if not postgres_rows.empty and not df_clean.empty:
        # Get the minimum time from non-filtered data
        min_time = df_clean['time_ms'].min()
        
        # Set postgres time to minimum time
        for idx, row in postgres_rows.iterrows():
            if pd.notna(row['error']):  # Only add if it has error data
                postgres_rows.at[idx, 'time_ms'] = min_time
        
        # Separate postgres into normal and inf
        postgres_clean = postgres_rows.dropna(subset=['time_ms', 'error'])
        postgres_inf = postgres_clean[postgres_clean['error'] == np.inf].copy()
        postgres_normal = postgres_clean[postgres_clean['error'] != np.inf].copy()
        
        # Add normal postgres to df_clean
        if not postgres_normal.empty:
            df_clean = pd.concat([df_clean, postgres_normal], ignore_index=True)
        
        # Add inf postgres to inf_rows
        if not postgres_inf.empty:
            inf_rows = pd.concat([inf_rows, postgres_inf], ignore_index=True)
    
    if df_clean.empty:
        print(f"  Skipping {group_name}/{phase}_{metric}.png - no data after filtering outliers")
        return
    
    # Print the number of data points and their coordinates
    print(f"  Plotting {len(df_clean)} data points in {group_name}/{phase}_{metric}:")
    
    # Prepare data for CSV export
    csv_data = []
    for idx, row in df_clean.iterrows():
        label = f"{row['algo']}-{row['model']}" if row['model'] else row['algo']
        print(f"    {label}: x={row['time_ms']:.2f}, y={row['error']:.2f}")
        csv_data.append({
            'label': label,
            'time': row['time_ms'],
            'error': row['error'],
            'filtered': False
        })
    
    # Add filtered outliers to CSV
    if not df_outliers.empty:
        print(f"  Filtered outliers (shown in legend with 'x' marker):")
        for idx, row in df_outliers.iterrows():
            label = f"{row['algo']}-{row['model']}" if row['model'] else row['algo']
            print(f"    {label}: x={row['time_ms']:.2f}, y={row['error']:.2f} (filtered)")
            csv_data.append({
                'label': label,
                'time': row['time_ms'],
                'error': row['error'],
                'filtered': True
            })
    
    # Add rows with inf error to CSV
    if not inf_rows.empty:
        print(f"  Algorithms with inf error (shown in legend with 'x' marker):")
        for idx, row in inf_rows.iterrows():
            label = f"{row['algo']}-{row['model']}" if row['model'] else row['algo']
            print(f"    {label}: x={row['time_ms']:.2f}, y=inf (filtered)")
            csv_data.append({
                'label': label,
                'time': row['time_ms'],
                'error': row['error'],
                'filtered': True
            })
    
    # Save data to CSV
    csv_df = pd.DataFrame(csv_data)
    if relative_mode:
        filename_suffix = f'_relative-{relative_mode}'
    else:
        filename_suffix = ''
    csv_output_path = Path(output_dir) / group_name / f'{phase}_{metric}{filename_suffix}_data.csv'
    csv_output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_df.to_csv(csv_output_path, index=False)
    
    # Assign colors to each row
    colors = assign_colors_to_dataframe(df_clean, all_llm_models_in_group)
    df_clean['color'] = colors
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each point with its assigned color
    for idx, row in df_clean.iterrows():
        ax.scatter(row['time_ms'], row['error'], 
                  color=row['color'], s=100, alpha=0.7)
    
    # Create legend by grouping similar models
    # Group by algo for non-LLM, and by model family for LLM
    non_llm_entries = {}
    llm_entries = {}
    outlier_entries = {}
    
    for idx, row in df_clean.iterrows():
        if row['algo'] != 'llm':
            key = row['algo']
            if key not in non_llm_entries:
                non_llm_entries[key] = row['color']
        else:
            # For LLM, use model name as legend key
            key = row['model']
            if key not in llm_entries:
                llm_entries[key] = row['color']
    
    # Add filtered outliers to legend
    if not df_outliers.empty:
        # Get colors for outliers
        outlier_colors = assign_colors_to_dataframe(df_outliers, all_llm_models_in_group)
        for i, (idx, row) in enumerate(df_outliers.iterrows()):
            if row['algo'] != 'llm':
                key = f"{row['algo']} (filtered)"
            else:
                key = f"{row['model']} (filtered)"
            if key not in outlier_entries:
                outlier_entries[key] = outlier_colors[i]
    
    # Add inf error rows to legend
    if not inf_rows.empty:
        # Get colors for inf error rows
        inf_colors = assign_colors_to_dataframe(inf_rows, all_llm_models_in_group)
        for i, (idx, row) in enumerate(inf_rows.iterrows()):
            if row['algo'] != 'llm':
                key = f"{row['algo']} (inf)"
            else:
                key = f"{row['model']} (inf)"
            if key not in outlier_entries:
                outlier_entries[key] = inf_colors[i]
    
    # Create legend handles: non-LLM first, then LLM
    handles = []
    labels = []
    
    # Add non-LLM entries (sorted)
    for label, color in sorted(non_llm_entries.items()):
        handles.append(plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color, markersize=8, alpha=0.7))
        labels.append(label)
    
    # Add LLM entries (sorted by family, then by size within family)
    def get_llm_sort_key(model_name):
        """
        Create a sort key for LLM models.
        Returns (family_order, size) tuple for sorting.
        """
        model_lower = model_name.lower()
        
        # Determine family order
        if 'sentence' in model_lower or 'bert' in model_lower:
            family_order = 0
        elif 'gemma' in model_lower:
            family_order = 1
        elif 'llama' in model_lower:
            family_order = 2
        elif 'qwen' in model_lower and 'embedding' in model_lower:
            family_order = 3
        elif 'qwen' in model_lower:
            family_order = 4
        else:
            family_order = 5
        
        # Extract size
        size = extract_model_size(model_name)
        if size is None:
            size = 0
        
        return (family_order, size)
    
    # Sort LLM entries by family and size
    sorted_llm = sorted(llm_entries.items(), key=lambda x: get_llm_sort_key(x[0]))
    
    for label, color in sorted_llm:
        handles.append(plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color, markersize=8, alpha=0.7))
        labels.append(label)
    
    # Add filtered outliers to legend (with different marker)
    for label, color in sorted(outlier_entries.items()):
        handles.append(plt.Line2D([0], [0], marker='x', color='w', 
                                  markeredgecolor=color, markersize=8, markeredgewidth=2))
        labels.append(label)
    
    # Set log scale for x-axis (time), but use linear scale for y-axis in relative mode
    # (because relative error can be negative or zero)
    ax.set_xscale('log')
    # For absolute errors and min-relative mode use log scale; for postgres-relative mode keep linear (values can be negative)
    if not relative_mode or relative_mode == 'min':
        ax.set_yscale('log')
    else:
        # In postgres-relative mode, values can be negative; keep linear scale and show baseline at 0
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    if relative_mode == 'min':
        ax.axhline(y=1, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Labels and title
    ax.set_xlabel('Time (ms)', fontsize=12)
    if relative_mode == 'pg':
        error_label = f'Relative Q-Error vs Postgres ({metric})'
    elif relative_mode == 'min':
        error_label = f'Relative Q-Error vs Min ({metric})'
    else:
        error_label = f'Q-Error ({metric})'
    ax.set_ylabel(error_label, fontsize=12)
    if relative_mode == 'pg':
        title_suffix = ' (Relative to Postgres)'
    elif relative_mode == 'min':
        title_suffix = ' (Relative to Min Error)'
    else:
        title_suffix = ''
    ax.set_title(f'{group_name} - {phase.capitalize()} - {metric.upper()}{title_suffix}', fontsize=14)
    
    # Legend
    ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure
    output_path = Path(output_dir) / group_name / f'{phase}_{metric}{filename_suffix}.png'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Created: {output_path}")


def process_group(group_df, group_name, output_dir, nth_highest=3, relative_mode=None, already_relative=False):
    """Process a group and create all 8 plots."""
    print(f"\nProcessing group: {group_name}")
    
    # Get all LLM models in this group (before any filtering) for consistent color assignment
    all_llm_models_in_group = group_df[group_df['algo'] == 'llm']['model'].dropna().unique().tolist()
    
    metrics = ['q50', 'q90', 'q95', 'qmax']
    phases = ['train', 'test']
    
    for phase in phases:
        # Determine time column
        if phase == 'train':
            time_col = 'train_time_ms'
            inference_col = 'llm_train_inference_ms'
        else:
            time_col = 'test_time_ms'
            inference_col = 'llm_test_inference_ms'
        
        # Calculate total time (sum of time_sum_ms and llm_inference_ms)
        # For training, multiply by 200 epochs
        if phase == 'train':
            group_df['time_ms'] = group_df[time_col].fillna(0) * 200 + group_df[inference_col].fillna(0)
        else:
            group_df['time_ms'] = group_df[time_col].fillna(0) + group_df[inference_col].fillna(0)
        
        for metric in metrics:
            # Prepare data for this plot
            plot_df = group_df[['time_ms', metric, 'algo', 'model']].copy()
            plot_df.rename(columns={metric: 'error'}, inplace=True)
            
            # Create label for each point (algo-model combination)
            plot_df['label'] = plot_df.apply(
                lambda row: f"{row['algo']}-{row['model']}" if pd.notna(row['model']) and row['model'] else row['algo'], 
                axis=1
            )
            
            # Create the plot
            # Pass convert_relative flag: only convert if relative is True and data is not already relative
            create_scatter_plot(
                plot_df,
                phase,
                metric,
                group_name,
                output_dir,
                all_llm_models_in_group,
                nth_highest=nth_highest,
                relative_mode=relative_mode,
                convert_relative=(relative_mode is not None and not already_relative)
            )


def main():
    args = parse_args()
    
    # Read the CSV
    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"Error: Input file {csv_path} not found")
        return
    
    print(f"Reading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows")
    print(f"Grouping by: {args.group_by}")
    
    # Rename columns for consistency
    df.rename(columns={
        'train_time_sum_ms': 'train_time_ms',
        'test_time_sum_ms': 'test_time_ms'
    }, inplace=True)
    
    # Remove job_full/card combination (applies to both grouping modes)
    print("\nFiltering out job_full/card combination...")
    original_len = len(df)
    df = df[~((df['dataset'] == 'job_full') & (df['task'] == 'card'))].copy()
    filtered_count = original_len - len(df)
    print(f"Removed {filtered_count} rows with job_full/card")
    
    # If grouping by task only, automatically average across datasets
    relative_mode = args.relative

    if args.group_by == "task":
        # If relative mode, calculate relative error for each dataset first, then average
        if relative_mode:
            print(f"\nCalculating relative error ({relative_mode}) for each dataset before averaging...")
            df_list = []
            for (dataset, task), group in df.groupby(['dataset', 'task']):
                # Make a copy to avoid modifying the view
                group = group.copy()
                # Convert each metric to relative error for this dataset
                for metric in ['q50', 'q90', 'q95', 'qmax']:
                    temp_df = group[['algo', metric]].rename(columns={metric: 'error'})
                    try:
                        converted = convert_to_relative_error(temp_df, error_col='error', mode=relative_mode)
                        group[metric] = converted['error']
                    except ValueError as exc:
                        print(f"    Warning: Skipping {dataset}/{task}/{metric} - {exc}")
                df_list.append(group)
            df = pd.concat(df_list, ignore_index=True)
            print("Relative error calculated for each dataset")
        
        print("\nAveraging Q-error and time across all datasets for each task...")
        # Group by task, algo, model and compute averages
        # Use dropna=False to keep groups where model is NaN (non-LLM algorithms)
        avg_df = df.groupby(['task', 'algo', 'model'], dropna=False).agg({
            'train_time_ms': 'mean',
            'test_time_ms': 'mean',
            'llm_train_inference_ms': 'mean',
            'llm_test_inference_ms': 'mean',
            'q50': 'mean',
            'q90': 'mean',
            'q95': 'mean',
            'qmax': 'mean'
        }).reset_index()
        df = avg_df
        print(f"After averaging: {len(df)} rows (averaged across datasets)")
    
    # Group the data
    if args.group_by == "task":
        groups = df.groupby('task')
    else:  # task_dataset
        groups = df.groupby(['dataset', 'task'])
    
    # Process each group
    output_dir = Path(args.output_dir)
    
    # Adjust output directory name if grouping by task (which averages)
    if args.group_by == "task":
        output_dir = output_dir / "averaged_by_task"
        print(f"Results will be saved to: {output_dir}")
    
    total_groups = len(groups)
    
    print(f"\nFound {total_groups} groups to process")
    
    for group_key, group_df in groups:
        # Create group name
        if args.group_by == "task":
            group_name = f"{str(group_key)}_averaged"
        else:  # task_dataset
            dataset, task = group_key
            group_name = f"{dataset}_{task}"
        
        # Process this group
        # If we're grouping by task and in relative mode, the data is already relative
        already_relative = (args.group_by == "task" and relative_mode is not None)
        process_group(
            group_df,
            group_name,
            output_dir,
            nth_highest=args.outlier_nth,
            relative_mode=relative_mode,
            already_relative=already_relative
        )
    
    print(f"\n✓ All graphs saved to: {output_dir.absolute()}")
    print(f"  Total groups processed: {total_groups}")
    print(f"  Expected total plots: {total_groups * 8}")


if __name__ == "__main__":
    main()

