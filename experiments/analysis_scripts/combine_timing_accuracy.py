#!/usr/bin/env python3
"""
Script to combine timing (from A_Train_Eva files) and accuracy (from quantile_table files).

Usage:
    python combine_timing_accuracy.py --base_dir logs_results_embeddings_10.11
"""

import os
import re
import argparse
import pandas as pd
from pathlib import Path
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Combine timing and accuracy metrics")
    parser.add_argument("--base_dir", type=str, required=True,
                        help="Base directory containing logs/ and results/ subdirectories")
    return parser.parse_args()


def extract_dataset_from_folder(folder_name):
    """Extract content between 'Train_' and '_Test' from folder name."""
    match = re.search(r'Train_(.+?)_Test', folder_name)
    if match:
        return match.group(1)
    return None


def parse_column_name_for_algo_model(col_name):
    """
    Parse column name to extract algo and model.
    For LLM: extract model between h{number}_ and _emb{number} (without embedding size since we filter to emb1000 only)
    For non-LLM: extract algo (content between first and second _)
    """
    # Check if LLM
    if 'llm' in col_name.lower():
        # Extract model between h{number}_ and _emb{number}
        h_pattern = r'_h(\d+)_'
        emb_pattern = r'_emb(\d+)'
        
        h_match = re.search(h_pattern, col_name)
        emb_match = re.search(emb_pattern, col_name)
        
        if h_match and emb_match:
            start_pos = h_match.end()
            end_pos = emb_match.start()
            model = col_name[start_pos:end_pos]
            return 'llm', model
        return 'llm', ''
    else:
        # Non-LLM: extract algo (second part), no model needed
        parts = col_name.split('_')
        if len(parts) >= 2:
            algo = parts[1]
            # For non-LLM algorithms, we don't distinguish by model/feature mask
            return algo, ''
        return None, None


def collect_timing_data(logs_dir):
    """Collect timing data from A_Train_Eva files."""
    timing_data = []
    
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return pd.DataFrame()
    
    # Find all A_Train_Eva files
    train_eva_files = list(logs_path.glob('*/A_Train_Eva_*.csv'))
    
    for file_path in train_eva_files:
        # Extract dataset from filename
        dataset = file_path.stem.replace('A_Train_Eva_', '')
        df = pd.read_csv(file_path)
        df['dataset'] = dataset
        timing_data.append(df)
    
    if timing_data:
        all_timing = pd.concat(timing_data, ignore_index=True)
        # Fill NaN model values with empty string for proper merging
        all_timing['model'] = all_timing['model'].fillna('')
        # Average across seeds only, keep dataset separate
        grouped = all_timing.groupby(['dataset', 'task', 'algo', 'model']).agg({
            'train_time_sum_ms': 'mean',
            'test_time_sum_ms': 'mean'
        }).reset_index()
        return grouped
    return pd.DataFrame()


def collect_llm_inference_data(logs_dir):
    """Collect LLM inference timing data from A_LLM_summary files."""
    llm_data = []
    
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return pd.DataFrame()
    
    # Find all A_LLM_summary files
    summary_files = list(logs_path.glob('*/A_LLM_summary_*.csv'))
    
    for file_path in summary_files:
        # Extract dataset from filename
        dataset = file_path.stem.replace('A_LLM_summary_', '')
        df = pd.read_csv(file_path)
        df['dataset'] = dataset
        llm_data.append(df)
    
    if llm_data:
        return pd.concat(llm_data, ignore_index=True)
    return pd.DataFrame()


def get_dat_path_mapping(dataset, task):
    """
    Get the training and testing dat_paths and their multipliers for a given dataset and task.
    Returns: (train_dat_path, test_dat_path, train_multiplier, test_multiplier)
    Note: train_dat_path or test_dat_path can be None if not available
    """
    mapping = {
        # job dataset
        ('job', 'card'): ('imdb', 'imdb_job_sub', 0.9, 1.0),
        ('job', 'time'): ('imdb', 'imdb_job', 0.9, 1.0),
        # job_full dataset (uses imdb_job_full_sub_selected instead of imdb_job_full_sub)
        ('job_full', 'card'): ('imdb', 'imdb_job_full_sub_selected', 0.9, 1.0),
        ('job_full', 'time'): ('imdb', 'imdb_job_full', 0.9, 1.0),
        # syn dataset
        ('syn', 'card'): ('imdb', 'imdb_syn_sub', 0.9, 1.0),
        ('syn', 'time'): ('imdb', 'imdb_syn', 0.9, 1.0),
        # stats dataset
        ('stats', 'card'): ('stats', 'stats_statsCEB_sub', 0.9, 1.0),
        ('stats', 'time'): ('stats', 'stats_statsCEB', 0.9, 1.0),
        # tpch and tpcds datasets
        ('tpch', 'time'): ('tpch', 'tpch', 0.67, 0.167),
        ('tpcds', 'time'): ('tpcds', 'tpcds', 0.67, 0.167),
    }
    return mapping.get((dataset, task), (None, None, 0, 0))


def add_llm_inference_times(combined_df, llm_inference_df):
    """Add LLM inference times as separate columns to the combined dataframe."""
    if llm_inference_df.empty:
        return combined_df
    
    # Initialize new columns for LLM inference times
    combined_df['llm_train_inference_ms'] = np.nan
    combined_df['llm_test_inference_ms'] = np.nan
    
    # Process only LLM rows
    for idx, row in combined_df.iterrows():
        if row['algo'] != 'llm':
            continue
        
        dataset = row['dataset']
        task = row['task']
        model = row['model']
        
        # Get dat_path mapping for this dataset and task
        train_dat_path, test_dat_path, train_mult, test_mult = get_dat_path_mapping(dataset, task)
        
        if train_dat_path is None and test_dat_path is None:
            continue
        
        # Get training inference time (if train_dat_path is available)
        # Look across ALL datasets and tasks for the matching dat_path and model
        # Training data is shared across tasks (e.g., 'imdb' is used for both card and time)
        if train_dat_path is not None:
            train_data = llm_inference_df[
                (llm_inference_df['dat_path'] == train_dat_path) &
                (llm_inference_df['model'] == model)
            ]
            if not train_data.empty:
                # Pick rows with max max_prompt_num, then pick the one with smallest total_time_ms
                max_prompt_num = train_data['max_prompt_num'].max()
                train_data = train_data[train_data['max_prompt_num'] == max_prompt_num]
                train_inference_time = train_data['total_time_ms'].min() * train_mult
                combined_df.at[idx, 'llm_train_inference_ms'] = train_inference_time
        
        # Get testing inference time (if test_dat_path is available)
        # For testing, we still filter by dataset since test_dat_path is dataset-specific
        if test_dat_path is not None:
            test_data = llm_inference_df[
                (llm_inference_df['dataset'] == dataset) &
                (llm_inference_df['dat_path'] == test_dat_path) &
                (llm_inference_df['task'] == task) &
                (llm_inference_df['model'] == model)
            ]
            if not test_data.empty:
                # Pick rows with max max_prompt_num, then pick the one with smallest total_time_ms
                max_prompt_num = test_data['max_prompt_num'].max()
                test_data = test_data[test_data['max_prompt_num'] == max_prompt_num]
                test_inference_time = test_data['total_time_ms'].min() * test_mult
                combined_df.at[idx, 'llm_test_inference_ms'] = test_inference_time
    
    return combined_df


def collect_accuracy_data(results_dir):
    """Collect accuracy data from quantile_table files."""
    accuracy_data = []
    
    results_path = Path(results_dir)
    if not results_path.exists():
        return pd.DataFrame()
    
    # Find all quantile_table files
    quantile_files = list(results_path.glob('*/quantile_table_*.csv'))
    
    for file_path in quantile_files:
        # Extract dataset from folder name
        folder_name = file_path.parent.name
        dataset_match = re.search(r'Train_(.+?)_Test', folder_name)
        if dataset_match:
            dataset = dataset_match.group(1)
        else:
            continue
        
        # Extract task from filename
        filename = file_path.name
        if '_card.csv' in filename:
            task = 'card'
        elif '_time.csv' in filename:
            task = 'time'
        else:
            continue
        
        df = pd.read_csv(file_path, index_col=0)
        
        # Process each column (each represents an algo-model combination)
        for col in df.columns:
            # Filter: only process columns with emb1000 (or non-LLM columns)
            if 'llm' in col.lower() and 'emb1000' not in col.lower():
                continue
            
            # Filter: skip LLM models with removed fields (indicated by _rm-)
            if 'llm' in col.lower() and '_rm-' in col.lower():
                continue
            
            algo, model = parse_column_name_for_algo_model(col)
            if algo is None:
                continue
            
            # Get quantile values (indices are strings in the CSV)
            q50 = df.loc['50', col] if '50' in df.index else np.nan
            q90 = df.loc['90', col] if '90' in df.index else np.nan
            q95 = df.loc['95', col] if '95' in df.index else np.nan
            qmax = df.loc['max', col] if 'max' in df.index else np.nan
            
            accuracy_data.append({
                'dataset': dataset,
                'task': task,
                'algo': algo,
                'model': model,
                'q50': q50,
                'q90': q90,
                'q95': q95,
                'qmax': qmax
            })
    
    if accuracy_data:
        acc_df = pd.DataFrame(accuracy_data)
        
        # Check for duplicates (same dataset, task, algo, model combination)
        duplicates = acc_df.duplicated(subset=['dataset', 'task', 'algo', 'model'], keep=False)
        if duplicates.any():
            duplicate_rows = acc_df[duplicates].sort_values(['dataset', 'task', 'algo', 'model'])
            error_msg = "\n❌ ERROR: Found duplicate entries with same (dataset, task, algo, model):\n"
            
            # Group duplicates by key
            grouped = duplicate_rows.groupby(['dataset', 'task', 'algo', 'model'])
            for key, group in grouped:
                dataset, task, algo, model = key
                error_msg += f"\n  Dataset: {dataset}, Task: {task}, Algo: {algo}, Model: {model}\n"
                error_msg += f"    Found {len(group)} entries:\n"
                for idx, row in group.iterrows():
                    error_msg += f"      q50={row['q50']:.2f}, q90={row['q90']:.2f}, q95={row['q95']:.2f}, qmax={row['qmax']:.2e}\n"
            
            error_msg += "\nThis likely means quantile_table files contain data already averaged across seeds.\n"
            error_msg += "Please check for duplicate quantile_table files or multiple columns with the same model."
            raise ValueError(error_msg)
        
        return acc_df
    return pd.DataFrame()


def main():
    args = parse_args()
    base_dir = Path(args.base_dir)
    
    logs_dir = base_dir / 'logs'
    results_dir = base_dir / 'results'
    
    print(f"Processing base directory: {base_dir}")
    print(f"  Logs directory: {logs_dir}")
    print(f"  Results directory: {results_dir}")
    
    # Collect timing data
    print("\nCollecting timing data from A_Train_Eva files...")
    timing_df = collect_timing_data(logs_dir)
    if timing_df.empty:
        print("  No timing data found")
    else:
        print(f"  Found {len(timing_df)} task-algo-model combinations with timing data")
    
    # Collect LLM inference data
    print("\nCollecting LLM inference data from A_LLM_summary files...")
    llm_inference_df = collect_llm_inference_data(logs_dir)
    if llm_inference_df.empty:
        print("  No LLM inference data found")
    else:
        print(f"  Found {len(llm_inference_df)} LLM inference entries")
    
    # Collect accuracy data
    print("\nCollecting accuracy data from quantile_table files...")
    accuracy_df = collect_accuracy_data(results_dir)
    if accuracy_df.empty:
        print("  No accuracy data found")
    else:
        print(f"  Found {len(accuracy_df)} task-algo-model combinations with accuracy data")
    
    # Merge timing and accuracy data
    if timing_df.empty and accuracy_df.empty:
        print("\nNo data to combine")
        return
    
    print("\nMerging timing and accuracy data...")
    
    # Merge on dataset, task, algo, model
    if not timing_df.empty and not accuracy_df.empty:
        combined_df = pd.merge(
            timing_df, 
            accuracy_df, 
            on=['dataset', 'task', 'algo', 'model'], 
            how='outer'
        )
    elif not timing_df.empty:
        combined_df = timing_df
    else:
        combined_df = accuracy_df
    
    # Sort by dataset, task, algo, model
    combined_df = combined_df.sort_values(by=['dataset', 'task', 'algo', 'model'])
    
    # Add LLM inference times
    if not llm_inference_df.empty:
        print("\nAdding LLM inference times to combined data...")
        combined_df = add_llm_inference_times(combined_df, llm_inference_df)
        print("  LLM inference times added")
    
    # Reorder columns (after adding LLM inference columns)
    column_order = ['dataset', 'task', 'algo', 'model', 'train_time_sum_ms', 'test_time_sum_ms', 
                    'llm_train_inference_ms', 'llm_test_inference_ms', 'q50', 'q90', 'q95', 'qmax']
    # Only include columns that exist
    column_order = [col for col in column_order if col in combined_df.columns]
    combined_df = combined_df[column_order]
    
    # Round numeric columns
    for col in ['train_time_sum_ms', 'test_time_sum_ms', 'llm_train_inference_ms', 'llm_test_inference_ms', 
                'q50', 'q90', 'q95', 'qmax']:
        if col in combined_df.columns:
            combined_df[col] = combined_df[col].round(2)
    
    # Save combined report
    output_path = base_dir / 'combined_timing_accuracy_report.csv'
    combined_df.to_csv(output_path, index=False)
    print(f"\n✓ Combined report saved to: {output_path}")
    print(f"  Total rows: {len(combined_df)}")
    
    # Print sample
    print("\nSample of combined data (first 10 rows):")
    print(combined_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

