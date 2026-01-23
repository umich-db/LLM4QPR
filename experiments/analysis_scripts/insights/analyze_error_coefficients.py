"""
Analyze error coefficients for specific LLM models across datasets.

This script:
1. Finds grand_analysis files for three specific models:
   - google-gemma-3-1b-pt
   - meta-llama-Llama-3.1-8B
   - Qwen-Qwen3-Embedding-8B
2. For each metric, checks if error has statistically significant Huber regression coefficient
   with |coef| > 0.1
3. Records:
   - 1 if coefficient is positive and significant (p < 0.001, |coef| > 0.1)
   - -1 if coefficient is negative and significant (p < 0.001, |coef| > 0.1)
   - 0 otherwise
4. Outputs a CSV per task with:
   - Rows: metrics
   - Columns: datasets
   - Last row: sum of -1, 0, 1 values
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent / "grand_analysis_results"

# Models to analyze
TARGET_MODELS = [
    "google-gemma-3-1b-pt",
    "meta-llama-Llama-3.1-8B",
    "Qwen-Qwen3-Embedding-8B",
]

# All structural metrics (same as in grand_analysis.py)
STRUCT_METRICS = [
    "num_tables",
    "num_columns",
    "num_joins",
    "num_filters",
    "longest_path_len",
    "num_nodes",
    "join_tree_diameter",
    "num_blocking_ops",
    "num_nested_loop",
    "max_est_join_input_rows",
    "sum_est_join_input_rows",
    "num_highly_selective_filters",
    "log_filter_selectivity_product",
    "optimizer_est_cost_root",
    "log_max_est_rows",
    "log_sum_est_rows",
    "max_log_card_error",
]


def parse_error_coefficient(error_str: str) -> tuple[float, bool]:
    """
    Parse error coefficient string to extract numeric value and significance.
    
    Args:
        error_str: Formatted string like "0.2322***", "-1.2391***", "0.0472*", "-9.05e+10", "NaN"
    
    Returns:
        (coefficient_value, is_significant)
        - coefficient_value: numeric value (0.0 if NaN/invalid)
        - is_significant: True if has "***" (p < 0.001), False otherwise
    """
    if pd.isna(error_str) or error_str == "NaN" or str(error_str).strip() == "":
        return (0.0, False)
    
    error_str = str(error_str).strip()
    
    # Check for significance (*** means p < 0.001)
    is_significant = "***" in error_str
    
    # Extract numeric value (handles both regular and scientific notation)
    # Pattern: optional sign, digits, optional decimal point, digits, optional exponent
    # Examples: "0.2322", "-1.2391", "-9.05e+10", "1.17e+11"
    match = re.search(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", error_str)
    if match:
        try:
            numeric_value = float(match.group(1))
            return (numeric_value, is_significant)
        except ValueError:
            return (0.0, False)
    
    return (0.0, False)


def classify_error_coefficient(error_str: str) -> int:
    """
    Classify error coefficient into -1, 0, or 1.
    
    Returns:
        - 1 if coefficient is positive, significant (p < 0.001), and |coef| > 0.1
        - -1 if coefficient is negative, significant (p < 0.001), and |coef| > 0.1
        - 0 otherwise
    """
    coef_value, is_significant = parse_error_coefficient(error_str)
    
    if not is_significant:
        return 0
    
    if abs(coef_value) <= 0.1:
        return 0
    
    if coef_value > 0:
        return 1
    else:
        return -1


def collect_grand_analysis_files() -> dict[tuple[str, str, str], Path]:
    """
    Collect all grand_analysis files for target models.
    
    Returns:
        Dict mapping (dataset, task, model) -> file path
    """
    files_map: dict[tuple[str, str, str], Path] = {}
    
    if not OUT_DIR.exists():
        print(f"Warning: Output directory {OUT_DIR} does not exist.")
        return files_map
    
    # Pattern: grand_analysis_{dataset}_{task}_seed{seed}_llm_{model}.csv
    pattern = re.compile(r"grand_analysis_(.+?)_(card|time)_seed\d+_llm_(.+?)\.csv")
    
    # Iterate through all dataset folders
    for dataset_dir in OUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue
        
        # Look for grand_analysis files for target models
        for file_path in dataset_dir.glob("grand_analysis_*_llm_*.csv"):
            # Skip summary files
            if "summary" in file_path.name:
                continue
            
            # Extract dataset, task, and model from filename
            match = pattern.match(file_path.name)
            if match:
                dataset = match.group(1)
                task = match.group(2)
                model = match.group(3)
                
                # Only include target models
                if model in TARGET_MODELS:
                    files_map[(dataset, task, model)] = file_path
    
    return files_map


def process_task(task: str, files_map: dict[tuple[str, str, str], Path]) -> pd.DataFrame:
    """
    Process all files for a given task and create a table (aggregated across all models).
    
    Returns:
        DataFrame with metrics as rows, datasets as columns, last column is sum
    """
    # Collect data: metric -> dataset -> classification value
    metric_data: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    
    # Get all datasets for this task
    datasets = set()
    for (dataset, file_task, model), file_path in files_map.items():
        if file_task == task:
            datasets.add(dataset)
    
    datasets = sorted(datasets)
    
    # Process each file
    for (dataset, file_task, model), file_path in files_map.items():
        if file_task != task:
            continue
        
        try:
            df = pd.read_csv(file_path, index_col=0)
            if "error" not in df.columns:
                print(f"Warning: {file_path.name} does not have 'error' column. Skipping.")
                continue
            
            # Process each metric
            for metric in STRUCT_METRICS:
                if metric not in df.index:
                    continue
                
                error_str = df.loc[metric, "error"]
                classification = classify_error_coefficient(error_str)
                metric_data[metric][dataset].append(classification)
                
        except Exception as e:
            print(f"Warning: Failed to process {file_path.name}: {e}")
            continue
    
    # Build result table
    # For each metric-dataset combination, we have multiple values (one per model)
    # Sum across the three models
    result_rows = []
    
    for metric in STRUCT_METRICS:
        row = {"metric": metric}
        for dataset in datasets:
            values = metric_data[metric][dataset]
            if values:
                # Sum across the three models for this dataset
                row[dataset] = sum(values)
            else:
                # No data for this metric-dataset combination
                row[dataset] = 0
        result_rows.append(row)
    
    # Create DataFrame
    df_result = pd.DataFrame(result_rows)
    df_result = df_result.set_index("metric")
    
    # Add sum column (sum across datasets for each metric)
    df_result["sum"] = df_result.sum(axis=1)
    
    return df_result


def process_task_for_model(task: str, model: str, files_map: dict[tuple[str, str, str], Path]) -> pd.DataFrame:
    """
    Process files for a given task and model, create a table for that specific model.
    
    Returns:
        DataFrame with metrics as rows, datasets as columns, last column is sum
    """
    # Collect data: metric -> dataset -> classification value
    metric_data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    # Get all datasets for this task and model
    datasets = set()
    for (dataset, file_task, file_model), file_path in files_map.items():
        if file_task == task and file_model == model:
            datasets.add(dataset)
    
    datasets = sorted(datasets)
    
    # Process each file for this model
    for (dataset, file_task, file_model), file_path in files_map.items():
        if file_task != task or file_model != model:
            continue
        
        try:
            df = pd.read_csv(file_path, index_col=0)
            if "error" not in df.columns:
                print(f"Warning: {file_path.name} does not have 'error' column. Skipping.")
                continue
            
            # Process each metric
            for metric in STRUCT_METRICS:
                if metric not in df.index:
                    continue
                
                error_str = df.loc[metric, "error"]
                classification = classify_error_coefficient(error_str)
                metric_data[metric][dataset] = classification
                
        except Exception as e:
            print(f"Warning: Failed to process {file_path.name}: {e}")
            continue
    
    # Build result table
    result_rows = []
    
    for metric in STRUCT_METRICS:
        row = {"metric": metric}
        for dataset in datasets:
            classification = metric_data[metric][dataset]
            row[dataset] = classification
        result_rows.append(row)
    
    # Create DataFrame
    df_result = pd.DataFrame(result_rows)
    df_result = df_result.set_index("metric")
    
    # Add sum column (sum across datasets for each metric)
    df_result["sum"] = df_result.sum(axis=1)
    
    return df_result


def main() -> None:
    """Main function to process all files and generate analysis."""
    print("Collecting grand_analysis files for target models...")
    files_map = collect_grand_analysis_files()
    
    if not files_map:
        print("Warning: No grand_analysis files found for target models.")
        return
    
    print(f"Found {len(files_map)} files:")
    for (dataset, task, model), file_path in sorted(files_map.items()):
        print(f"  {dataset}/{task}/{model}: {file_path.name}")
    
    # Get all tasks
    tasks = sorted(set(task for (_, task, _) in files_map.keys()))
    
    # Process each task (aggregated across all models)
    for task in tasks:
        print(f"\nProcessing task: {task} (aggregated)")
        df_result = process_task(task, files_map)
        
        # Save to CSV
        output_path = OUT_DIR / f"error_coefficient_analysis_{task}.csv"
        df_result.to_csv(output_path)
        print(f"Saved aggregated analysis to {output_path}")
        print(f"Shape: {df_result.shape}")
        print(f"Datasets: {list(df_result.columns)}")
        print(f"Metrics: {len(df_result)} (with sum column)")
    
    # Process each task for each model separately
    for task in tasks:
        for model in TARGET_MODELS:
            print(f"\nProcessing task: {task}, model: {model}")
            df_result = process_task_for_model(task, model, files_map)
            
            if df_result.empty:
                print(f"  No data found for {model} in task {task}")
                continue
            
            # Create a safe filename from model name
            model_safe = model.replace("/", "_").replace("\\", "_")
            output_path = OUT_DIR / f"error_coefficient_analysis_{task}_{model_safe}.csv"
            df_result.to_csv(output_path)
            print(f"Saved model-specific analysis to {output_path}")
            print(f"Shape: {df_result.shape}")
            print(f"Datasets: {list(df_result.columns)}")


if __name__ == "__main__":
    main()

