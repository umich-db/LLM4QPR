#!/usr/bin/env python3
"""
Script to extract q_error quantiles from baseline verbose files (ALECE, MSCN, PRICE)
and add them to the corresponding quantile summary files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from collections import defaultdict

# Base directories
BASE_DIR = Path("/home/jovyan/workspace/LLM4QPR/experiments")
VERBOSE_DIR = BASE_DIR / "verbose"
RESULTS_DIR = BASE_DIR / "results"

# Baseline algorithms
BASELINES = ["ALECE", "MSCN", "PRICE"]

def strip_seed(filename):
    """Remove seed suffix from filename to get column name"""
    return re.sub(r'_seed\d+', '', filename)

def calculate_quantiles(q_errors, quantiles=[50, 90, 95]):
    """
    Calculate quantiles from q_error values.
    Returns a dict with quantile values and max.
    """
    if len(q_errors) == 0:
        return {q: np.nan for q in quantiles} | {'max': np.nan}
    
    q_errors = np.array(q_errors)
    q_errors = q_errors[~np.isnan(q_errors)]  # Remove NaN values
    
    if len(q_errors) == 0:
        return {q: np.nan for q in quantiles} | {'max': np.nan}
    
    result = {}
    for q in quantiles:
        result[q] = np.percentile(q_errors, q)
    result['max'] = np.max(q_errors)
    
    return result

def find_quantile_table_file(dataset, task):
    """
    Find the quantile table file for a given dataset and task.
    Returns Path or None if not found.
    """
    # Map dataset names to directory patterns
    dataset_map = {
        'job': 'Train_job_Test_job_ours',
        'stats': 'Train_stats_Test_stats_ours',
        'syn': 'Train_syn_Test_syn_ours',
        'tpch': 'Train_tpch_Test_tpch_ours',
        'tpcds': 'Train_tpcds_Test_tpcds_ours',
    }
    
    if dataset not in dataset_map:
        return None
    
    results_subdir = RESULTS_DIR / f"results_{dataset_map[dataset]}"
    # The filename format is: quantile_table_results_{dataset_map}_{task}.csv
    quantile_file = results_subdir / f"quantile_table_results_{dataset_map[dataset]}_{task}.csv"
    
    if quantile_file.exists():
        return quantile_file
    
    # Try alternative format (with double "results_")
    quantile_file_alt = results_subdir / f"quantile_table_results_results_{dataset_map[dataset]}_{task}.csv"
    if quantile_file_alt.exists():
        return quantile_file_alt
    
    return None

def process_verbose_file(verbose_path):
    """
    Process a single verbose file and extract quantiles.
    Returns (column_name, quantile_dict, dataset, task) or None if error.
    """
    try:
        # Read verbose file
        df = pd.read_csv(verbose_path)
        
        if 'q_error' not in df.columns:
            print(f"Warning: {verbose_path} does not have 'q_error' column")
            return None
        
        # Extract q_error values
        q_errors = df['q_error'].dropna().tolist()
        
        if len(q_errors) == 0:
            print(f"Warning: {verbose_path} has no valid q_error values")
            return None
        
        # Calculate quantiles
        quantiles = calculate_quantiles(q_errors, quantiles=[50, 90, 95])
        
        # Extract column name (filename without extension and seed)
        filename = verbose_path.stem  # filename without .csv
        column_name = strip_seed(filename)
        
        # Extract dataset and task from filename
        # Format: {task}_{ALGORITHM}_{...}
        match = re.match(r'^(card|time)_([A-Z]+)', filename)
        if not match:
            print(f"Warning: Could not parse filename {filename}")
            return None
        
        task = match.group(1)
        algorithm = match.group(2)
        
        # Extract dataset from path
        # Path format: verbose/verbose_Train_{dataset}_Test_{dataset}_ours/
        path_str = str(verbose_path.resolve())  # Use absolute path
        # Match pattern like "verbose_Train_job_Test_job_ours" or "verbose_Train_stats_Test_stats_ours"
        dataset_match = re.search(r'verbose_Train_(\w+)_Test_\1_ours', path_str)
        if not dataset_match:
            print(f"Warning: Could not extract dataset from path {path_str}")
            return None
        
        dataset = dataset_match.group(1)
        
        return (column_name, quantiles, dataset, task)
        
    except Exception as e:
        print(f"Error processing {verbose_path}: {e}")
        return None

def update_quantile_table(quantile_file, column_name, quantiles):
    """
    Update a quantile table file by adding or updating a column.
    """
    # Read existing quantile table
    df = pd.read_csv(quantile_file, index_col=0)
    
    # Add the new column if it doesn't exist
    if column_name not in df.columns:
        df[column_name] = np.nan
    
    # Update the values for each quantile row
    # The index should be strings like "50", "90", "95", "max"
    for quantile_key, value in quantiles.items():
        # Convert quantile_key to string to match index
        quantile_str = str(quantile_key)
        if quantile_str in df.index:
            df.at[quantile_str, column_name] = value
        elif quantile_key == 'max':
            # Handle 'max' as string
            if 'max' in df.index:
                df.at['max', column_name] = value
            else:
                # If quantile row doesn't exist, add it
                df.loc['max', column_name] = value
        else:
            # If quantile row doesn't exist, add it
            df.loc[quantile_str, column_name] = value
    
    # Remove any duplicate rows (keep first occurrence)
    df = df[~df.index.duplicated(keep='first')]
    
    # Save updated table
    df.to_csv(quantile_file)
    print(f"Updated {quantile_file} with column {column_name}")

def main():
    """Main function to process all baseline verbose files"""
    
    # Find all baseline verbose files
    baseline_files = []
    for baseline in BASELINES:
        pattern = f"**/*{baseline}*.csv"
        files = list(VERBOSE_DIR.glob(pattern))
        baseline_files.extend(files)
    
    print(f"Found {len(baseline_files)} baseline verbose files")
    
    # Group by (dataset, task) to process quantile tables efficiently
    grouped_data = defaultdict(list)
    
    for verbose_file in baseline_files:
        result = process_verbose_file(verbose_file)
        if result:
            column_name, quantiles, dataset, task = result
            grouped_data[(dataset, task)].append((column_name, quantiles))
    
    # Update quantile tables
    for (dataset, task), columns_data in grouped_data.items():
        quantile_file = find_quantile_table_file(dataset, task)
        
        if quantile_file is None:
            print(f"Warning: Could not find quantile table for dataset={dataset}, task={task}")
            continue
        
        print(f"\nUpdating quantile table: {quantile_file}")
        for column_name, quantiles in columns_data:
            update_quantile_table(quantile_file, column_name, quantiles)
            print(f"  Added {column_name}: 50th={quantiles[50]:.2f}, 90th={quantiles[90]:.2f}, "
                  f"95th={quantiles[95]:.2f}, max={quantiles['max']:.2f}")

if __name__ == "__main__":
    main()

