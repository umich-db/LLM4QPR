#!/usr/bin/env python3
"""
Generate LaTeX table comparing no finetuning vs finetuning (last and lora) for llama-8B.

Usage:
    python generate_finetune_comparison_table.py [--output <output_file>]
"""

import os
import re
import argparse
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Tuple


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


def find_llama8b_column(df: pd.DataFrame, task: str, pretrained_mode: str) -> Optional[str]:
    """
    Find column name matching llama-8B with specific pretrained mode.
    
    Args:
        df: DataFrame with quantile data
        task: 'time' or 'card'
        pretrained_mode: 'None', 'last', or 'lora'
    
    Returns:
        Column name or None if not found
    """
    # Pattern: {task}_llm_pretrained-{mode}_1.0_*meta-llama-Llama-3.1-8B*
    # Escape special characters in pretrained_mode
    if pretrained_mode == 'None':
        mode_pattern = 'None'
    else:
        mode_pattern = pretrained_mode
    
    pattern = f"{task}_llm_pretrained-{mode_pattern}_1\\.0_.*meta-llama-Llama-3\\.1-8B"
    
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
        return f"{value:.3f}"
    elif value < 10:
        return f"{value:.3f}"
    elif value < 100:
        return f"{value:.3f}"
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


def generate_finetune_table(results_dir: str = "results", output_path: Optional[str] = None) -> str:
    """
    Generate LaTeX table comparing finetuning methods.
    
    Structure:
    - Rows: None, Last Transformer Block, LoRA
    - Columns: TPC-H cost, TPC-DS cost, STATS cost, STATS card (each with 50th, 90th, 95th, Max)
    """
    
    # Define datasets and tasks
    datasets_config = [
        ('tpch', 'time', 'TPC-H cost'),
        ('tpcds', 'time', 'TPC-DS cost'),
        ('job_full', 'time', 'JOB-FULL cost'),
        ('stats', 'card', 'STATS card'),
    ]
    
    # Collect data
    data = {}  # {(dataset, task, pretrained_mode): {quantile: value}}
    
    for dataset, task, display_name in datasets_config:
        csv_path = find_quantile_csv(dataset, task, results_dir)
        if not csv_path or not os.path.exists(csv_path):
            print(f"Warning: Could not find CSV file for {dataset}/{task}")
            continue
        
        df = pd.read_csv(csv_path, index_col=0)
        
        # Find columns for each pretrained mode
        for pretrained_mode in ['None', 'last', 'lora']:
            col = find_llama8b_column(df, task, pretrained_mode)
            if col is None:
                print(f"Warning: Could not find column for {dataset}/{task}/pretrained-{pretrained_mode}")
                continue
            
            # Get quantile values
            for quantile in ['50', '90', '95', 'max']:
                value = get_quantile_value(df, col, quantile)
                if value is not None:
                    key = (dataset, task, pretrained_mode, quantile)
                    data[key] = value
    
    # Build LaTeX table
    lines = []
    lines.append("\\begin{tabular}{l|cccc|cccc|cccc|cccc}")
    lines.append("")
    lines.append("\\toprule")
    lines.append("")
    
    # Header row 1: Dataset names
    header1 = "\\multirow{2}{*}{Finetuning Method}"
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
    
    # Data rows
    row_labels = [
        ('None', 'None'),
        ('last', 'Last Transformer Block'),
        ('lora', 'LoRA'),
    ]
    
    for pretrained_mode, row_label in row_labels:
        row_parts = [row_label]
        
        for dataset, task, _ in datasets_config:
            for quantile in ['50', '90', '95', 'max']:
                key = (dataset, task, pretrained_mode, quantile)
                if key in data:
                    value = data[key]
                    formatted = format_number(value)
                    row_parts.append(formatted)
                else:
                    row_parts.append('-')
        
        lines.append(" & ".join(row_parts) + " \\\\")
    
    lines.append("")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    
    latex_code = "\n".join(lines)
    
    # Find minimum values for each column and add highlighting
    # Rebuild with highlighting
    lines = []
    lines.append("\\begin{tabular}{l|cccc|cccc|cccc|cccc}")
    lines.append("")
    lines.append("\\toprule")
    lines.append("")
    
    # Header row 1
    header1 = "\\multirow{2}{*}{Finetuning Method}"
    for _, _, display_name in datasets_config:
        header1 += f" & \\multicolumn{{4}}{{c|}}{{{display_name}}}"
    lines.append(header1 + " \\\\")
    lines.append("")
    
    # Header row 2
    header2_parts = []
    for _ in datasets_config:
        header2_parts.extend(['50th', '90th', '95th', 'Max'])
    lines.append(" & " + " & ".join(header2_parts) + " \\\\")
    lines.append("")
    lines.append("\\midrule")
    lines.append("")
    
    # Find minimums for each column
    column_mins = {}  # {(dataset, task, quantile): min_value}
    for dataset, task, _ in datasets_config:
        for quantile in ['50', '90', '95', 'max']:
            values = []
            for pretrained_mode in ['None', 'last', 'lora']:
                key = (dataset, task, pretrained_mode, quantile)
                if key in data:
                    values.append((pretrained_mode, data[key]))
            
            if values:
                min_value = min(v[1] for v in values)
                column_mins[(dataset, task, quantile)] = min_value
    
    # Data rows with highlighting
    for pretrained_mode, row_label in row_labels:
        row_parts = [row_label]
        
        for dataset, task, _ in datasets_config:
            for quantile in ['50', '90', '95', 'max']:
                key = (dataset, task, pretrained_mode, quantile)
                col_key = (dataset, task, quantile)
                
                if key in data:
                    value = data[key]
                    formatted = format_number(value)
                    
                    # Check if this is the minimum for this column
                    if col_key in column_mins and abs(value - column_mins[col_key]) < 1e-6:
                        cell = f"\\cellcolor{{myorange}}\\textbf{{{formatted}}}"
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
    parser = argparse.ArgumentParser(description='Generate finetune comparison LaTeX table')
    parser.add_argument('--results_dir', type=str, default='results', 
                        help='Results directory (default: results)')
    parser.add_argument('--output', type=str, default=None, 
                        help='Output file path (default: print to stdout)')
    
    args = parser.parse_args()
    
    # Generate table
    latex_code = generate_finetune_table(args.results_dir, args.output)
    
    if not args.output:
        print(latex_code)


if __name__ == '__main__':
    main()

