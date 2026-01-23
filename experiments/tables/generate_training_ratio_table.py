#!/usr/bin/env python3
"""
Generate LaTeX table comparing different training ratios for llama-8B pretrained-None.

Usage:
    python generate_training_ratio_table.py [--output <output_file>]
"""

import os
import re
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple, List


def find_quantile_csv(dataset: str, task: str, results_dir: str = "results") -> Optional[str]:
    """Find quantile table CSV file for a given dataset and task."""
    # Map dataset names to directory patterns
    dataset_map = {
        'tpch': 'Train_tpch_Test_tpch_ours',
        'tpcds': 'Train_tpcds_Test_tpcds_ours',
        'stats': 'Train_stats_Test_stats_ours',
        'job_full': 'Train_job_full_Test_job_full_ours',
    }
    
    if dataset not in dataset_map:
        return None
    
    dataset_dir = dataset_map[dataset]
    # Handle both absolute and relative paths
    if os.path.isabs(results_dir):
        results_subdir = Path(results_dir) / f"results_{dataset_dir}"
    else:
        # Relative to script location
        script_dir = Path(__file__).parent
        results_subdir = script_dir.parent / results_dir / f"results_{dataset_dir}"
    
    # Try the standard filename format
    quantile_file = results_subdir / f"quantile_table_results_results_{dataset_dir}_{task}.csv"
    if quantile_file.exists():
        return str(quantile_file)
    
    # Try alternative format
    quantile_file_alt = results_subdir / f"quantile_table_results_{dataset_dir}_{task}.csv"
    if quantile_file_alt.exists():
        return str(quantile_file_alt)
    
    return None


def find_llama8b_column_for_ratio(df: pd.DataFrame, task: str, ratio: float) -> Optional[str]:
    """
    Find column name matching llama-8B pretrained-None with specific training ratio.
    
    Args:
        df: DataFrame with quantile data
        task: 'time' or 'card'
        ratio: Training ratio (0.2, 0.4, 0.6, 0.8, or 1.0)
    
    Returns:
        Column name or None if not found
    """
    # Pattern: {task}_llm_pretrained-None_{ratio}_cdf_*meta-llama-Llama-3.1-8B*
    ratio_str = f"{ratio:.1f}"
    pattern = f"{task}_llm_pretrained-None_{ratio_str}_cdf_.*meta-llama-Llama-3\\.1-8B"
    
    for col in df.columns:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    
    return None


def format_number(value: float) -> str:
    """Format number for LaTeX display."""
    if pd.isna(value):
        return '-'
    
    # Handle scientific notation for very large numbers
    if abs(value) >= 1e10:
        # Format as "5.8e12" not "5.8e+12"
        formatted = f"{value:.1e}"
        return formatted.replace('e+', 'e').replace('e-', 'e-')
    elif abs(value) >= 1000:
        formatted = f"{value:.2e}"
        return formatted.replace('e+', 'e').replace('e-', 'e-')
    
    # Format with appropriate precision
    if value < 1:
        return f"{value:.4f}"
    elif value < 10:
        return f"{value:.4f}"
    elif value < 100:
        return f"{value:.2f}"
    else:
        return f"{value:.2f}"


def get_quantile_value(df: pd.DataFrame, column: str, quantile: str) -> Optional[float]:
    """Get quantile value from dataframe."""
    if column not in df.columns:
        return None
    
    # The index might be '50', '90', '95', 'max' or 50, 90, 95, 'max'
    # Try both string and integer versions
    if quantile == '50':
        row_indices = ['50', 50]
    elif quantile == '90':
        row_indices = ['90', 90]
    elif quantile == '95':
        row_indices = ['95', 95]
    elif quantile == 'max':
        row_indices = ['max']
    else:
        return None
    
    for row_idx in row_indices:
        if row_idx in df.index:
            value = df.loc[row_idx, column]
            if pd.notna(value):
                return float(value)
    
    return None


def assign_green_color(value: float, sorted_values: List[float]) -> str:
    """
    Assign green color based on value's rank (smaller = better = larger green number).
    
    Args:
        value: The value to color
        sorted_values: List of all values sorted in ascending order (best to worst)
    
    Returns:
        Green color name (green1 to green5, where green5 is best)
    """
    if len(sorted_values) == 0:
        return ''
    
    # Remove duplicates and sort
    unique_values = sorted(set(sorted_values))
    n_unique = len(unique_values)
    
    if n_unique == 1:
        # All values are the same
        return 'green3'
    
    # Find rank of value (0 = best, n-1 = worst)
    try:
        rank = unique_values.index(value)
    except ValueError:
        # Value not in list, find closest
        rank = min(range(len(unique_values)), key=lambda i: abs(unique_values[i] - value))
    
    # Map rank to green color (green5 = best, green1 = worst)
    # For 5 values: rank 0->green5, 1->green4, 2->green3, 3->green2, 4->green1
    if n_unique == 5:
        color_map = {0: 'green5', 1: 'green4', 2: 'green3', 3: 'green2', 4: 'green1'}
    elif n_unique == 4:
        color_map = {0: 'green5', 1: 'green4', 2: 'green3', 3: 'green2'}
    elif n_unique == 3:
        color_map = {0: 'green5', 1: 'green4', 2: 'green3'}
    elif n_unique == 2:
        color_map = {0: 'green5', 1: 'green4'}
    else:
        # For 1 or more than 5, use linear mapping
        if rank == 0:
            return 'green5'
        elif rank == n_unique - 1:
            return 'green1'
        else:
            # Interpolate between green5 and green1
            ratio = rank / (n_unique - 1)
            if ratio < 0.25:
                return 'green5'
            elif ratio < 0.5:
                return 'green4'
            elif ratio < 0.75:
                return 'green3'
            else:
                return 'green2'
    
    return color_map.get(rank, 'green3')


def generate_training_ratio_table(results_dir: str = "results", output_path: Optional[str] = None) -> str:
    """
    Generate LaTeX table comparing different training ratios.
    
    Structure:
    - Rows: 20%, 40%, 60%, 80%, 100% (training ratios 0.2, 0.4, 0.6, 0.8, 1.0)
    - Columns: TPC-H cost, TPC-DS cost, JOB-FULL cost, STATS card (each with 50th, 90th, 95th, Max)
    - Cell coloring: green5 (best) to green1 (worst) based on value ranking
    """
    
    # Define datasets and tasks
    datasets_config = [
        ('tpch', 'time', 'TPC-H cost'),
        ('tpcds', 'time', 'TPC-DS cost'),
        ('job_full', 'time', 'JOB-FULL cost'),
        ('stats', 'card', 'STATS card'),
    ]
    
    # Training ratios to check
    training_ratios = [0.2, 0.4, 0.6, 0.8, 1.0]
    
    # Collect data
    data = {}  # {(dataset, task, ratio, quantile): value}
    
    for dataset, task, display_name in datasets_config:
        csv_path = find_quantile_csv(dataset, task, results_dir)
        if not csv_path or not os.path.exists(csv_path):
            print(f"Warning: Could not find CSV file for {dataset}/{task}")
            continue
        
        df = pd.read_csv(csv_path, index_col=0)
        
        # Find columns for each training ratio
        for ratio in training_ratios:
            col = find_llama8b_column_for_ratio(df, task, ratio)
            if col is None:
                print(f"Warning: Could not find column for {dataset}/{task}/ratio-{ratio}")
                continue
            
            # Get quantile values
            for quantile in ['50', '90', '95', 'max']:
                value = get_quantile_value(df, col, quantile)
                if value is not None:
                    key = (dataset, task, ratio, quantile)
                    data[key] = value
    
    # Build LaTeX table
    lines = []
    lines.append("\\begin{tabular}{l|cccc|cccc|cccc|cccc}")
    lines.append("")
    lines.append("\\toprule")
    lines.append("")
    
    # Header row 1: Dataset names
    header1 = "\\multirow{2}{*}{Training Set Ratio}"
    for _, _, display_name in datasets_config:
        header1 += f" & \\multicolumn{{4}}{{c|}}{{{display_name}}}"
    lines.append(header1 + " \\\\")
    lines.append("")
    
    # Header row 2: Quantile labels
    header2_parts = []
    for _ in datasets_config:
        header2_parts.extend(['50th', '90th', '95th', 'Max'])
    lines.append(" & " + " & ".join(header2_parts) + " \\\\")
    lines.append("")
    lines.append("\\midrule")
    lines.append("")
    
    # Calculate green colors for each column
    # For each (dataset, task, quantile) combination, rank all ratio values
    column_colors = {}  # {(dataset, task, ratio, quantile): color}
    
    for dataset, task, _ in datasets_config:
        for quantile in ['50', '90', '95', 'max']:
            # Collect all values for this column
            values = []
            for ratio in training_ratios:
                key = (dataset, task, ratio, quantile)
                if key in data:
                    values.append((ratio, data[key]))
            
            if len(values) > 0:
                # Sort by value (ascending - smaller is better)
                values_sorted = sorted(values, key=lambda x: x[1])
                sorted_value_list = [v[1] for v in values_sorted]
                
                # Assign colors
                for ratio, value in values:
                    color = assign_green_color(value, sorted_value_list)
                    column_colors[(dataset, task, ratio, quantile)] = color
    
    # Data rows
    ratio_labels = {
        0.2: '20\\%',
        0.4: '40\\%',
        0.6: '60\\%',
        0.8: '80\\%',
        1.0: '100\\%',
    }
    
    for ratio in training_ratios:
        row_parts = [ratio_labels[ratio]]
        
        for dataset, task, _ in datasets_config:
            for quantile in ['50', '90', '95', 'max']:
                key = (dataset, task, ratio, quantile)
                color_key = (dataset, task, ratio, quantile)
                
                if key in data:
                    value = data[key]
                    formatted = format_number(value)
                    
                    # Add green color if available
                    if color_key in column_colors:
                        color = column_colors[color_key]
                        cell = f"\\cellcolor{{{color}}}{formatted}"
                    else:
                        cell = formatted
                    
                    row_parts.append(cell)
                else:
                    row_parts.append('-')
        
        lines.append(" & ".join(row_parts) + " \\\\")
    
    lines.append("")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    
    latex_code = "\n".join(lines)
    
    # Save to file if specified
    if output_path:
        with open(output_path, 'w') as f:
            f.write(latex_code)
        print(f"LaTeX table saved to: {output_path}")
    
    return latex_code


def main():
    parser = argparse.ArgumentParser(description='Generate training ratio comparison LaTeX table')
    parser.add_argument('--results_dir', type=str, default='results', 
                        help='Results directory (default: results)')
    parser.add_argument('--output', type=str, default=None, 
                        help='Output file path (default: print to stdout)')
    
    args = parser.parse_args()
    
    # Generate table
    latex_code = generate_training_ratio_table(args.results_dir, args.output)
    
    if not args.output:
        print(latex_code)


if __name__ == '__main__':
    main()

