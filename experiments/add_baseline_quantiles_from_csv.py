#!/usr/bin/env python3
"""
Script to extract q_error quantiles from combined_timing_accuracy_report_chiyu_full.csv
and add them to the corresponding quantile summary files for mscn, alece, and price.

This script reads from the CSV file instead of verbose files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

# Base directories
BASE_DIR = Path("/home/jovyan/workspace/LLM4QPR/experiments")
CSV_FILE = BASE_DIR / "combined_timing_accuracy_report_chiyu_full.csv"
RESULTS_DIR = BASE_DIR / "results"

# Baseline algorithms to process
BASELINES = ["mscn", "alece", "price"]

# Datasets to process
DATASETS = ["job", "stats", "syn"]

# Tasks to process
TASKS = ["card", "time"]

# Quantiles to extract
QUANTILES = [50, 90, 95, "max"]

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

def generate_column_name(task, algo):
    """
    Generate the column name for the quantile table.
    Based on the pattern seen in existing quantile tables.
    Format: {task}_{ALGORITHM}_1.0_postgres_0.001_b16_h256
    """
    algo_upper = algo.upper()
    return f"{task}_{algo_upper}_1.0_postgres_0.001_b16_h256"

def update_quantile_table(quantile_file, column_name, quantiles):
    """
    Update a quantile table file by adding or updating a column.
    
    Args:
        quantile_file: Path to the quantile table CSV file
        column_name: Name of the column to add/update
        quantiles: Dictionary with keys 50, 90, 95, 'max' and quantile values
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
    """Main function to process CSV file and update quantile tables"""
    
    # Read the CSV file
    if not CSV_FILE.exists():
        print(f"Error: CSV file not found: {CSV_FILE}")
        return
    
    print(f"Reading data from: {CSV_FILE}")
    # Skip the first row which contains "combined_timing_accuracy_report"
    df = pd.read_csv(CSV_FILE, skiprows=1)
    
    # Filter for the algorithms, datasets, and tasks we want
    filtered_df = df[
        (df['algo'].isin(BASELINES)) &
        (df['dataset'].isin(DATASETS)) &
        (df['task'].isin(TASKS))
    ].copy()
    
    if filtered_df.empty:
        print("No matching data found in CSV file")
        return
    
    print(f"Found {len(filtered_df)} rows matching criteria")
    
    # Process each row
    for idx, row in filtered_df.iterrows():
        dataset = row['dataset']
        task = row['task']
        algo = row['algo']
        
        # Extract quantile values
        quantiles = {
            50: row['q50'],
            90: row['q90'],
            95: row['q95'],
            'max': row['qmax']
        }
        
        # Check for NaN or inf values
        has_invalid = False
        for key, value in quantiles.items():
            if pd.isna(value) or (isinstance(value, (int, float)) and np.isinf(value)):
                print(f"Warning: {dataset}/{task}/{algo} has invalid value for {key}: {value}")
                has_invalid = True
        
        if has_invalid:
            continue
        
        # Find the quantile table file
        quantile_file = find_quantile_table_file(dataset, task)
        
        if quantile_file is None:
            print(f"Warning: Could not find quantile table for dataset={dataset}, task={task}")
            continue
        
        # Generate column name
        column_name = generate_column_name(task, algo)
        
        # Update the quantile table
        print(f"\nProcessing {dataset}/{task}/{algo}:")
        print(f"  Quantile file: {quantile_file}")
        print(f"  Column name: {column_name}")
        print(f"  Values: 50th={quantiles[50]:.2f}, 90th={quantiles[90]:.2f}, "
              f"95th={quantiles[95]:.2f}, max={quantiles['max']:.2f}")
        
        update_quantile_table(quantile_file, column_name, quantiles)
    
    print("\n✓ Processing complete!")

if __name__ == "__main__":
    main()

