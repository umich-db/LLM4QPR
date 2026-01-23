#!/usr/bin/env python3
"""
Generate LaTeX/Overleaf table code from quantile table CSV files.

Usage:
    python generate_overleaf_table.py --datasets <dataset1,dataset2,...> --task <time|card> [--output <output_file>]
"""

import pandas as pd
import argparse
import os
import re
from collections import defaultdict
from typing import List, Tuple, Dict, Optional
from pathlib import Path


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


def format_algo_name_for_display(algo_name):
    """
    Format algorithm name for display.
    Renames non-LLM algorithms to their display names.
    """
    if not algo_name:
        return algo_name
    
    algo_lower = algo_name.lower()
    
    # Map non-LLM algorithm names
    algo_name_map = {
        'aimai': 'AiMeetsAi',
        'alece': 'ALECE',
        'bao': 'Bao',
        'e2e': 'E2E-Cost',
        'mscn': 'MSCN',
        'postgres': 'PostgreSQL',
        'price': 'PRICE',
        'qf': 'QueryFormer',
    }
    
    return algo_name_map.get(algo_lower, algo_name)


def format_model_name_for_display(model_name):
    """
    Format model name for display.
    Renames models to shorter, cleaner names.
    """
    if not model_name:
        return model_name
    
    model_lower = model_name.lower()
    
    # Handle BERT family models
    if 'sentence' in model_lower or 'sentence-transformers' in model_lower:
        return 'SentenceBert'
    elif 'bert-base-uncased' in model_lower:
        return 'Bert'
    elif 'modernbert' in model_lower or 'answerdotai-modernbert' in model_lower:
        return 'ModernBert'
    
    # Handle Qwen models
    if 'qwen' in model_lower and 'embedding' in model_lower:
        size = extract_model_size(model_name)
        if size:
            return f'Qwen-{size:.0f}B' if size >= 1 else f'Qwen-{size}B'
        return 'Qwen-8B'  # Default for Qwen-Qwen3-Embedding-8B
    
    # Handle Llama models
    if 'llama' in model_lower:
        size = extract_model_size(model_name)
        if size:
            return f'Llama-{size:.0f}B' if size >= 1 else f'Llama-{size}B'
        return 'Llama'
    
    # Handle Gemma models
    if 'gemma' in model_lower:
        size = extract_model_size(model_name)
        if size:
            return f'Gemma-{size:.0f}B' if size >= 1 else f'Gemma-{size}B'
        return 'Gemma'
    
    # Return original if no match
    return model_name


def find_quantile_csv(dataset: str, task: str, results_dir: str = "results") -> Optional[str]:
    """Find quantile table CSV file for a given dataset and task."""
    # Map dataset names to directory patterns
    dataset_map = {
        'job': 'Train_job_Test_job_ours',
        'job_full': 'Train_job_full_Test_job_full_ours',
        'stats': 'Train_stats_Test_stats_ours',
        'syn': 'Train_syn_Test_syn_ours',
        'tpch': 'Train_tpch_Test_tpch_ours',
        'tpcds': 'Train_tpcds_Test_tpcds_ours',
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


def extract_model_name(col_name: str) -> Optional[str]:
    """Extract model name from column name."""
    if 'llm' not in col_name.lower():
        return None
    
    # Pattern: time_llm_..._model-name_...
    # Look for known model prefixes (they may be split across underscores)
    parts = col_name.split('_')
    model_parts = []
    
    # Find where model name starts (look for known prefixes)
    start_idx = None
    for i, part in enumerate(parts):
        part_lower = part.lower()
        if any(prefix in part_lower for prefix in ['qwen', 'meta', 'llama', 'gemma', 'bert', 'answerdotai', 'sentence', 'modernbert']):
            start_idx = i
            break
    
    if start_idx is None:
        return None
    
    # Collect model name parts until we hit 'emb' or 'quant'
    for i in range(start_idx, len(parts)):
        # Stop if this part starts with 'emb' or 'quant'
        if parts[i].startswith('emb') or parts[i].startswith('quant'):
            break
        model_parts.append(parts[i])
    
    if model_parts:
        return '_'.join(model_parts)
    return None


def get_llm_family(model_name: Optional[str]) -> str:
    """Determine LLM family from model name."""
    if not model_name:
        return 'other'
    
    model_lower = model_name.lower()
    if 'llama' in model_lower or 'meta-llama' in model_lower:
        return 'llama'
    elif 'qwen' in model_lower:
        return 'qwen'
    elif 'gemma' in model_lower:
        return 'gemma'
    elif 'bert' in model_lower or 'modernbert' in model_lower or 'sentence-transformers' in model_lower:
        return 'bert'
    return 'other'


def get_short_name(col_name: str) -> str:
    """Get short display name for column."""
    # For non-LLM: extract algorithm name
    if 'llm' not in col_name.lower():
        parts = col_name.split('_')
        if len(parts) > 1:
            algo = parts[1]
            # Use the same naming function as plot_timing_accuracy.py
            return format_algo_name_for_display(algo)
        return format_algo_name_for_display(col_name)
    
    # For LLM: extract and format model name
    model_name = extract_model_name(col_name)
    if model_name:
        return format_model_name_for_display(model_name)
    return col_name


def format_number(value: float) -> str:
    """Format number for LaTeX display."""
    if pd.isna(value):
        return '-'
    
    # Handle scientific notation for very large or very small numbers
    if abs(value) >= 1000 or (abs(value) < 0.01 and value != 0):
        return f"{value:.2e}"
    
    # Format with appropriate precision
    if value < 1:
        return f"{value:.3f}"
    elif value < 10:
        return f"{value:.3f}"
    elif value < 100:
        return f"{value:.3f}"
    else:
        return f"{value:.2f}"


def process_single_dataset(csv_path: str, task: str) -> Tuple[pd.DataFrame, List[str], List[str], Dict[str, List[str]]]:
    """Process a single dataset CSV and return separated columns."""
    # Read CSV
    df = pd.read_csv(csv_path, index_col=0)
    
    # Filter columns based on task
    filtered_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if col_lower.startswith(task.lower() + '_'):
            filtered_cols.append(col)
    
    if not filtered_cols:
        return None, [], [], {}
    
    df = df[filtered_cols]
    
    # Separate non-LLM and LLM columns
    non_llm_cols = []
    llm_cols = []
    
    for col in df.columns:
        if 'llm' in col.lower():
            # Exclude LLM models with "lora", "last", or "32b" in their name
            col_lower = col.lower()
            if 'lora' not in col_lower and 'last' not in col_lower and '32b' not in col_lower and '0.2_' not in col_lower and '0.4_' not in col_lower and '0.6_' not in col_lower and '0.8_' not in col_lower:
                llm_cols.append(col)
        else:
            non_llm_cols.append(col)
    
    # Group LLM columns by family
    llm_by_family = defaultdict(list)
    for col in llm_cols:
        model_name = extract_model_name(col)
        family = get_llm_family(model_name)
        llm_by_family[family].append(col)
    
    # Define family order
    family_order = ['llama', 'qwen', 'gemma', 'bert', 'other']
    ordered_llm_cols = []
    
    for family in family_order:
        if family in llm_by_family:
            ordered_llm_cols.extend(sorted(llm_by_family[family]))
    
    # Add any remaining families
    for family, cols in llm_by_family.items():
        if family not in family_order:
            ordered_llm_cols.extend(sorted(cols))
    
    return df, non_llm_cols, ordered_llm_cols, llm_by_family


def generate_latex_table(
    datasets: List[str],
    task: str,
    results_dir: str = "results",
    output_path: Optional[str] = None,
    coloring: str = "diff"
) -> str:
    """Generate LaTeX table from multiple dataset CSV files.
    
    Structure:
    - Rows: Algorithms/models (non-LLM first, then LLM grouped by family)
    - Columns: Quantiles (50th, 90th, 95th, max) for each dataset
    """
    
    # Load data for each dataset
    dataset_data = {}
    # Collect all unique algorithm/model names across ALL datasets
    # This ensures algorithms that appear in at least one dataset are included in the table
    # They will show "-" in cells where they don't have values, but will be ranked in cells where they do
    all_algos = set()  # All unique algorithm/model names across datasets
    
    for dataset in datasets:
        csv_path = find_quantile_csv(dataset, task, results_dir)
        if not csv_path or not os.path.exists(csv_path):
            print(f"Warning: Could not find CSV file for dataset '{dataset}' and task '{task}'")
            continue
        
        df, non_llm_cols, llm_cols, llm_by_family = process_single_dataset(csv_path, task)
        if df is None:
            continue
        
        dataset_data[dataset] = {
            'df': df,
            'non_llm_cols': non_llm_cols,
            'llm_cols': llm_cols,
            'llm_by_family': llm_by_family
        }
        # Add algorithms from this dataset to the union
        # Algorithms that appear in at least one dataset will be included in the table
        all_algos.update(non_llm_cols)
        all_algos.update(llm_cols)
    
    if not dataset_data:
        raise ValueError(f"No valid CSV files found for datasets {datasets} and task '{task}'")
    
    # Quantile columns
    quantile_cols = ['50', '90', '95', 'max']
    
    # Organize algorithms: non-LLM first, then LLM grouped by family
    non_llm_algos = []
    llm_algos_by_family = defaultdict(list)
    
    for algo in all_algos:
        if 'llm' in algo.lower():
            # Exclude LLM models with "lora", "last", "32b", or certain quantile patterns in their name
            algo_lower = algo.lower()
            if ('lora' not in algo_lower and 'last' not in algo_lower and '32b' not in algo_lower and 
                '0.2_' not in algo_lower and '0.4_' not in algo_lower and '0.6_' not in algo_lower and '0.8_' not in algo_lower):
                model_name = extract_model_name(algo)
                family = get_llm_family(model_name)
                llm_algos_by_family[family].append(algo)
        else:
            non_llm_algos.append(algo)
    
    # Sort non-LLM algorithms: PostgreSQL first, then alphabetically
    def sort_non_llm_key(algo):
        """Sort key for non-LLM algorithms: PostgreSQL first, then alphabetical."""
        algo_display = format_algo_name_for_display(algo.split('_')[1] if '_' in algo else algo)
        if algo_display == 'PostgreSQL':
            return (-1, 0)
        return (0, algo_display)
    
    non_llm_algos.sort(key=sort_non_llm_key)
    
    # Order LLM algorithms by family and size (matching plot_timing_accuracy.py)
    def get_llm_sort_key(model_name):
        """
        Create a sort key for LLM models.
        Returns (family_order, size) tuple for sorting.
        For BERT family: SentenceBert (smallest) -> Bert (medium) -> ModernBert (largest)
        """
        if not model_name:
            return (5, 0)
        
        model_lower = model_name.lower()
        
        # Determine family order
        if 'sentence' in model_lower or 'bert' in model_lower:
            family_order = 0
            # For BERT family, assign sizes: SentenceBert=1, Bert=2, ModernBert=3
            if 'sentence' in model_lower:
                size = 1  # Smallest
            elif 'modernbert' in model_lower or 'BERT' in model_name:
                size = 3  # Largest
            else:
                size = 2  # Medium
        elif 'gemma' in model_lower:
            family_order = 1
            size = extract_model_size(model_name) or 0
        elif 'llama' in model_lower:
            family_order = 2
            size = extract_model_size(model_name) or 0
        elif 'qwen' in model_lower and 'embedding' in model_lower:
            family_order = 3
            size = extract_model_size(model_name) or 0
        elif 'qwen' in model_lower:
            family_order = 4
            size = extract_model_size(model_name) or 0
        else:
            family_order = 5
            size = extract_model_size(model_name) or 0
        
        return (family_order, size)
    
    # Sort LLM algorithms by family and size
    ordered_llm_algos = []
    for family, algos in llm_algos_by_family.items():
        # Sort within each family by model size
        algos_with_keys = [(algo, get_llm_sort_key(extract_model_name(algo))) for algo in algos]
        algos_with_keys.sort(key=lambda x: x[1])
        ordered_llm_algos.extend([algo for algo, _ in algos_with_keys])
    
    # Re-sort all LLM algorithms by family and size
    ordered_llm_algos.sort(key=lambda algo: get_llm_sort_key(extract_model_name(algo)))
    
    all_ordered_algos = non_llm_algos + ordered_llm_algos
    
    # Compute rankings
    # Rankings: per quantile, per dataset, rank algorithms
    # IMPORTANT: Only rank algorithms that will be displayed in the table (all_ordered_algos)
    quantile_rankings = {}  # {quantile: {dataset: {algo: (type, rank)}}}
    
    for quantile in quantile_cols:
        rankings_by_dataset = {}
        
        for dataset, data in dataset_data.items():
            df = data['df']
            if quantile not in df.index:
                continue
            
            row_data = df.loc[quantile]
            dataset_rankings = {}
            
            if coloring == 'same':
                # Rank all algorithms together (top 5 overall get green colors)
                # Only rank algorithms that:
                # 1. Will be displayed in the table (in all_ordered_algos)
                # 2. Have a value in this specific dataset/quantile cell
                # Algorithms with missing values in this cell are excluded from ranking for this cell only
                # but will still appear in the table with "-" in that cell
                all_values = [(algo, row_data[algo]) for algo in all_ordered_algos
                             if algo in df.columns and algo in row_data and pd.notna(row_data[algo])]
                all_values.sort(key=lambda x: x[1])
                for rank, (algo, _) in enumerate(all_values[:5], 1):
                    # Determine if it's LLM or non-LLM for type tracking
                    algo_type = 'llm' if 'llm' in algo.lower() else 'non_llm'
                    # rank: 1=best, 2=2nd, 3=3rd, 4=4th, 5=5th
                    # Map to green: best->green5, 2nd->green4, 3rd->green3, 4th->green2, 5th->green1
                    green_rank = 6 - rank  # 1->5, 2->4, 3->3, 4->2, 5->1
                    dataset_rankings[algo] = (algo_type, green_rank)
            else:  # coloring == 'diff'
                # Rank non-LLM within this dataset and quantile (top 3)
                # Only rank algorithms that:
                # 1. Will be displayed in the table (in non_llm_algos)
                # 2. Have a value in this specific dataset/quantile cell
                non_llm_values = [(algo, row_data[algo]) for algo in non_llm_algos
                                 if algo in df.columns and algo in row_data and pd.notna(row_data[algo])]
                non_llm_values.sort(key=lambda x: x[1])
                for rank, (algo, _) in enumerate(non_llm_values[:3], 1):
                    dataset_rankings[algo] = ('non_llm', 4 - rank)  # 3rd=1, 2nd=2, best=3
                
                # Rank LLM within this dataset and quantile (top 5)
                # Only rank algorithms that:
                # 1. Will be displayed in the table (in ordered_llm_algos)
                # 2. Have a value in this specific dataset/quantile cell
                llm_values = [(algo, row_data[algo]) for algo in ordered_llm_algos
                             if algo in df.columns and algo in row_data and pd.notna(row_data[algo])]
                llm_values.sort(key=lambda x: x[1])
                for rank, (algo, _) in enumerate(llm_values[:5], 1):
                    dataset_rankings[algo] = ('llm', 6 - rank)  # 5th=1, ..., best=5
            
            rankings_by_dataset[dataset] = dataset_rankings
        
        quantile_rankings[quantile] = rankings_by_dataset
    
    # Compare LLM models against non-LLM algorithms
    # For each column, find best and second-best non-LLM
    # Then count how many columns each LLM beats them
    llm_name_formatting = {}  # {algo: 'bold', 'italic', or None}
    
    # Count total columns
    total_columns = 0
    for dataset in datasets:
        if dataset not in dataset_data:
            continue
        for quantile in quantile_cols:
            if quantile in dataset_data[dataset]['df'].index:
                total_columns += 1
    
    if total_columns > 0:
        threshold = total_columns / 2  # 1/2 of columns
        
        # For each LLM model, count wins
        llm_stats = []  # Store stats for printing
        
        for llm_algo in ordered_llm_algos:
            beats_best_count = 0
            beats_second_count = 0
            
            for dataset in datasets:
                if dataset not in dataset_data:
                    continue
                data = dataset_data[dataset]
                df = data['df']
                
                for quantile in quantile_cols:
                    if quantile not in df.index:
                        continue
                    
                    if llm_algo not in df.columns:
                        continue
                    
                    llm_value = df.loc[quantile, llm_algo]
                    if pd.isna(llm_value):
                        continue
                    
                    # Find best and second-best non-LLM for this column
                    non_llm_values = [(algo, df.loc[quantile, algo]) 
                                     for algo in data['non_llm_cols'] 
                                     if algo in df.columns and pd.notna(df.loc[quantile, algo])]
                    non_llm_values.sort(key=lambda x: x[1])
                    
                    if len(non_llm_values) >= 1:
                        best_non_llm_value = non_llm_values[0][1]
                        if llm_value < best_non_llm_value:
                            beats_best_count += 1
                    
                    if len(non_llm_values) >= 2:
                        second_best_non_llm_value = non_llm_values[1][1]
                        if llm_value < second_best_non_llm_value:
                            beats_second_count += 1
            
            # Store stats
            llm_stats.append({
                'algo': llm_algo,
                'beats_best': beats_best_count,
                'beats_second': beats_second_count,
                'total_columns': total_columns
            })
            
            # Apply formatting based on counts
            # Bold if it beats the second best in at least 1/2 of columns
            if beats_second_count >= threshold:
                llm_name_formatting[llm_algo] = 'bold'
        
        # Print statistics
        print("\n" + "="*80)
        print("LLM Model Performance Statistics")
        print("="*80)
        print(f"{'Model':<30} {'Beats Best':<15} {'Beats 2nd Best':<15} {'Total Columns':<15} {'Bold?'}")
        print("-"*80)
        for stat in llm_stats:
            algo_short = get_short_name(stat['algo'])
            is_bold = "Yes" if stat['algo'] in llm_name_formatting else "No"
            print(f"{algo_short:<30} {stat['beats_best']:<15} {stat['beats_second']:<15} {stat['total_columns']:<15} {is_bold}")
        print("="*80 + "\n")
    
    # Build column specification
    col_spec_parts = ['l']  # Algorithm name column
    
    for dataset in datasets:
        if dataset not in dataset_data:
            continue
        col_spec_parts.append('|')
        col_spec_parts.append('c' * len(quantile_cols))  # 4 columns per dataset (50, 90, 95, max)
    
    col_spec = ''.join(col_spec_parts)
    
    # Generate LaTeX
    lines = []
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("")
    lines.append("\\toprule")
    lines.append("")
    
    # Header row 1: Dataset names
    header1 = "\\multirow{2}{*}{Algorithm}"
    for dataset in datasets:
        if dataset not in dataset_data:
            continue
        # Map dataset names to display names
        dataset_display_map = {
            'tpch': 'TPC-H',
            'tpcds': 'TPC-DS',
            'syn': 'Synthetic',
            'job': 'JOB-light',
            'job_full': 'JOB',
            'stats': 'STATS'
        }
        dataset_display = dataset_display_map.get(dataset.lower(), dataset.upper().replace('_', '-'))
        header1 += f" & \\multicolumn{{{len(quantile_cols)}}}{{c|}}{{{dataset_display}}}"
    lines.append(header1 + " \\\\")
    lines.append("")
    
    # Header row 2: Quantile labels
    header2_parts = []
    for dataset in datasets:
        if dataset not in dataset_data:
            continue
        for quantile in quantile_cols:
            if quantile == 'max':
                header2_parts.append('Max')
            else:
                header2_parts.append(f"{quantile}th")
    
    lines.append(" & " + " & ".join(header2_parts) + " \\\\")
    lines.append("")
    lines.append("\\midrule")
    lines.append("")
    
    # Add separator between non-LLM and LLM
    non_llm_count = len(non_llm_algos)
    llm_count = len(ordered_llm_algos)
    
    # Data rows
    prev_is_llm = False
    for i, algo in enumerate(all_ordered_algos):
        is_llm = 'llm' in algo.lower()
        
        # Add double separator between non-LLM and LLM
        if i == non_llm_count and non_llm_count > 0 and llm_count > 0:
            lines.append("\\midrule")
            lines.append("")
        
        # Add single separator between LLM families
        if is_llm and prev_is_llm:
            model_name = extract_model_name(algo)
            prev_model_name = extract_model_name(all_ordered_algos[i-1])
            if get_llm_family(model_name) != get_llm_family(prev_model_name):
                lines.append("\\midrule")
                lines.append("")
        
        # Format algorithm name based on LLM comparison
        algo_name = get_short_name(algo)
        if is_llm and algo in llm_name_formatting:
            if llm_name_formatting[algo] == 'bold':
                algo_name = f"\\textbf{{{algo_name}}}"
        
        row_parts = [algo_name]
        
        for dataset in datasets:
            if dataset not in dataset_data:
                # Fill with '-' if dataset not found
                for _ in quantile_cols:
                    row_parts.append("-")
                continue
            
            data = dataset_data[dataset]
            df = data['df']
            
            for quantile in quantile_cols:
                if quantile not in df.index:
                    row_parts.append("-")
                    continue
                
                if algo not in df.columns:
                    row_parts.append("-")
                    continue
                
                value = df.loc[quantile, algo]
                if pd.isna(value):
                    row_parts.append("-")
                else:
                    formatted = format_number(value)
                    
                    # Get ranking for this quantile and dataset
                    rankings = quantile_rankings.get(quantile, {}).get(dataset, {})
                    cell = formatted
                    
                    if algo in rankings:
                        rank_type, rank_num = rankings[algo]
                        if coloring == 'same':
                            # Use green colors for both LLM and non-LLM (top 5 overall)
                            # rank_num is already set to green rank: 1=green1, 2=green2, 3=green3, 4=green4, 5=green5
                            cell = f"\\cellcolor{{green{rank_num}}}{{{cell}}}"
                        else:  # coloring == 'diff'
                            # Use different colors: orange for non-LLM, green for LLM
                            if rank_type == 'non_llm':
                                cell = f"\\cellcolor{{orange{rank_num}}}{{{cell}}}"
                            elif rank_type == 'llm':
                                cell = f"\\cellcolor{{green{rank_num}}}{{{cell}}}"
                    
                    row_parts.append(cell)
        
        lines.append(" & ".join(row_parts) + " \\\\")
        prev_is_llm = is_llm
    
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
    parser = argparse.ArgumentParser(description='Generate LaTeX table from quantile CSV files')
    parser.add_argument('--datasets', type=str, required=True, help='Comma-separated list of datasets (e.g., tpch,tpcds,stats)')
    parser.add_argument('--task', type=str, required=True, choices=['time', 'card'], help='Task type: time or card')
    parser.add_argument('--results_dir', type=str, default='results', help='Results directory (default: results)')
    parser.add_argument('--output', type=str, default=None, help='Output file path (default: print to stdout)')
    parser.add_argument('--coloring', type=str, default='same', choices=['diff', 'same'], 
                       help='Coloring scheme: diff (different colors for LLM/non-LLM) or same (green for both)')
    
    args = parser.parse_args()
    
    # Parse datasets
    datasets = [d.strip() for d in args.datasets.split(',')]
    
    # Generate table
    latex_code = generate_latex_table(datasets, args.task, args.results_dir, args.output, args.coloring)
    
    if not args.output:
        print(latex_code)


if __name__ == '__main__':
    main()
