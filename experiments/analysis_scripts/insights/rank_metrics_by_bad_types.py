"""
Rank metrics by sum of bad types for LLM models across all datasets and tasks.

This script:
1. Reads all individual grand_analysis files (not summary files) for LLM models
2. For each metric, counts how many times it has type_number in {1, 4, 5, 7} (bad types)
3. Sums the bad type counts across all LLM models for each dataset/task
4. Ranks metrics by the sum (higher sum = worse rank)
5. Outputs a CSV with dataset, task, metric, rank, sum_bad_types
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).resolve().parent / "grand_analysis_results"

# Bad types: 1, 4, 5, 7
BAD_TYPES = {1, 4, 5, 7}


def collect_llm_grand_analysis_files() -> dict[tuple[str, str], list[Path]]:
    """
    Collect all LLM grand_analysis files, grouped by (dataset, task).
    
    Returns:
        Dict mapping (dataset, task) -> list of file paths
    """
    files_by_dataset_task: dict[tuple[str, str], list[Path]] = defaultdict(list)
    
    if not OUT_DIR.exists():
        print(f"Warning: Output directory {OUT_DIR} does not exist.")
        return files_by_dataset_task
    
    # Pattern for individual grand_analysis files (not summary files)
    # grand_analysis_{dataset}_{task}_seed{seed}_{algo}_{model}.csv
    pattern = re.compile(r"grand_analysis_(.+?)_(card|time)_seed\d+_llm_(.+?)\.csv")
    
    # Iterate through all dataset folders
    for dataset_dir in OUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue
        
        # Look for LLM grand_analysis files in this dataset directory
        for file_path in dataset_dir.glob("grand_analysis_*_llm_*.csv"):
            # Skip summary files
            if "summary" in file_path.name:
                continue
            
            # Extract dataset and task from filename
            match = pattern.match(file_path.name)
            if match:
                dataset = match.group(1)
                task = match.group(2)
                files_by_dataset_task[(dataset, task)].append(file_path)
    
    return files_by_dataset_task


def count_bad_types_for_metric(df: pd.DataFrame, metric: str) -> int:
    """
    Count how many times a metric has a bad type_number in a single file.
    
    Returns:
        Number of bad types (0 or 1, since each metric appears once per file)
    """
    if metric not in df.index:
        return 0
    
    type_number = df.loc[metric, "type_number"]
    if pd.isna(type_number):
        return 0
    
    try:
        type_num = int(type_number)
        return 1 if type_num in BAD_TYPES else 0
    except (ValueError, TypeError):
        return 0


def process_dataset_task(dataset: str, task: str, file_paths: list[Path]) -> list[dict]:
    """
    Process all LLM files for a dataset/task combination.
    
    Returns:
        List of dictionaries with metric, sum_bad_types
    """
    # Count bad types for each metric across all LLM files
    metric_bad_counts: dict[str, int] = defaultdict(int)
    
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path, index_col=0)
            if "type_number" not in df.columns:
                print(f"Warning: {file_path.name} does not have 'type_number' column. Skipping.")
                continue
            
            # Count bad types for each metric in this file
            for metric in df.index:
                bad_count = count_bad_types_for_metric(df, metric)
                metric_bad_counts[metric] += bad_count
                
        except Exception as e:
            print(f"Warning: Failed to process {file_path.name}: {e}")
            continue
    
    # Create results with ranking
    results = []
    for metric, sum_bad in metric_bad_counts.items():
        results.append({
            "dataset": dataset,
            "task": task,
            "metric": metric,
            "sum_bad_types": sum_bad,
        })
    
    # Sort by sum_bad_types (descending) to determine rank
    # Higher sum_bad_types = worse = lower rank number (rank 1 is worst)
    results.sort(key=lambda x: x["sum_bad_types"], reverse=True)
    
    # Add rank (tie handling: same rank for same sum)
    # Rank 1 = worst (highest sum_bad_types), higher ranks = better
    current_rank = 1
    prev_sum = None
    for i, result in enumerate(results):
        if prev_sum is not None and result["sum_bad_types"] < prev_sum:
            # New sum value, so new rank
            current_rank = i + 1
        result["rank"] = current_rank
        prev_sum = result["sum_bad_types"]
    
    return results


def main() -> None:
    """Main function to process all files and generate ranking."""
    print("Collecting LLM grand_analysis files...")
    files_by_dataset_task = collect_llm_grand_analysis_files()
    
    if not files_by_dataset_task:
        print("Warning: No LLM grand_analysis files found.")
        return
    
    print(f"Found files for {len(files_by_dataset_task)} dataset/task combinations:")
    for (dataset, task), files in sorted(files_by_dataset_task.items()):
        print(f"  {dataset}/{task}: {len(files)} files")
    
    # Process each dataset/task combination
    all_results = []
    for (dataset, task), file_paths in sorted(files_by_dataset_task.items()):
        print(f"\nProcessing {dataset}/{task} ({len(file_paths)} LLM files)...")
        results = process_dataset_task(dataset, task, file_paths)
        all_results.extend(results)
        print(f"  Processed {len(results)} metrics")
    
    if not all_results:
        print("Warning: No data collected.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    # Sort by dataset, task, rank
    df = df.sort_values(by=["dataset", "task", "rank", "metric"])
    
    # Reorder columns
    df = df[["dataset", "task", "metric", "rank", "sum_bad_types"]]
    
    # Save to CSV
    output_path = OUT_DIR / "metric_ranking_by_bad_types.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved metric ranking to {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Datasets: {df['dataset'].nunique()}")
    print(f"Tasks: {df['task'].unique().tolist()}")
    
    # Print summary statistics
    print("\nSummary statistics:")
    print(f"Metrics per dataset/task: {df.groupby(['dataset', 'task']).size().tolist()}")
    print(f"Max bad types: {df['sum_bad_types'].max()}")
    print(f"Min bad types: {df['sum_bad_types'].min()}")
    print(f"Mean bad types: {df['sum_bad_types'].mean():.2f}")


if __name__ == "__main__":
    main()

