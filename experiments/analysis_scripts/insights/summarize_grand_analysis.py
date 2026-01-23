"""
Summarize grand analysis results across all datasets and tasks.

This script:
1. Reads all grand_analysis_summary files from different dataset folders
2. Categorizes type numbers: 1,4,5,7 = bad; 2,3 = good; 6 = not_care; 8 = further_analysis
3. Sums counts for each category per algo/model
4. Ranks by true_label_vs_embedding_spearman (with *** = use number, without *** = -1)
5. Compares est_label_vs_embedding_spearman with true_label_vs_embedding_spearman
6. Outputs a comprehensive summary CSV
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

import pandas as pd

OUT_DIR = Path(__file__).resolve().parent / "grand_analysis_results"


def parse_spearman_value(spearman_str: str) -> tuple[float, int, bool]:
    """
    Parse spearman string to extract numeric value, number of stars, and whether it has stars.
    
    Returns:
        (numeric_value, num_stars, has_stars)
        - numeric_value: the numeric value (0.0 if NaN/invalid)
        - num_stars: number of * (0, 1, 2, or 3)
        - has_stars: True if has any *, False otherwise
    """
    if pd.isna(spearman_str) or spearman_str == "NaN" or str(spearman_str).strip() == "":
        return (0.0, 0, False)
    
    spearman_str = str(spearman_str).strip()
    
    # Count stars
    num_stars = 0
    if "***" in spearman_str:
        num_stars = 3
    elif "**" in spearman_str:
        num_stars = 2
    elif "*" in spearman_str:
        num_stars = 1
    
    has_stars = num_stars > 0
    
    # Extract numeric value
    match = re.search(r"([-+]?\d*\.?\d+)", spearman_str)
    if match:
        try:
            numeric_value = float(match.group(1))
            return (numeric_value, num_stars, has_stars)
        except ValueError:
            return (0.0, 0, False)
    
    return (0.0, 0, False)


def compare_spearman_values(val1_str: str, val2_str: str) -> int:
    """
    Compare two spearman values according to the rules:
    Priority order (best to worst):
    1. Positive numbers with stars (ranked by number of stars, then numeric value)
    2. Numbers without stars
    3. Negative numbers with stars (ranked by number of stars, then numeric value)
    
    Returns:
        -1 if val1 < val2 (val1 is worse)
        0 if val1 == val2
        1 if val1 > val2 (val1 is better)
    """
    val1_num, val1_stars, val1_has_stars = parse_spearman_value(val1_str)
    val2_num, val2_stars, val2_has_stars = parse_spearman_value(val2_str)
    
    val1_positive = val1_num > 0
    val2_positive = val2_num > 0
    
    # Determine categories:
    # 2 = positive with stars (best)
    # 1 = no stars (middle)
    # 0 = negative with stars (worst)
    val1_category = 2 if (val1_has_stars and val1_positive) else (1 if not val1_has_stars else 0)
    val2_category = 2 if (val2_has_stars and val2_positive) else (1 if not val2_has_stars else 0)
    
    # Rule 1: Compare categories (higher is better)
    if val1_category > val2_category:
        return 1  # val1 is better
    if val1_category < val2_category:
        return -1  # val1 is worse
    
    # Same category
    # If both are in category 1 (no stars), they're equal (or compare by numeric value if needed)
    if val1_category == 1:
        if val1_num > val2_num:
            return 1
        if val1_num < val2_num:
            return -1
        return 0
    
    # Both are in category 0 (negative with stars) or category 2 (positive with stars)
    # Rule 2: Number with more * wins
    if val1_stars > val2_stars:
        return 1  # val1 is better
    if val1_stars < val2_stars:
        return -1  # val1 is worse
    
    # Same number of stars
    # Rule 3: Compare number (larger wins)
    if val1_num > val2_num:
        return 1  # val1 is better
    if val1_num < val2_num:
        return -1  # val1 is worse
    
    return 0  # Equal


def get_ranking_value(spearman_str: str) -> tuple[int, int, float]:
    """
    Get a tuple for ranking purposes.
    
    Returns:
        (category_rank, stars_rank, numeric_value)
        - category_rank: 2 if positive with stars (best), 1 if no stars (middle), 0 if negative with stars (worst)
        - stars_rank: number of stars (0-3, higher is better, only relevant for category 0 and 2)
        - numeric_value: the numeric value (higher is better)
    
    This tuple can be used for sorting in descending order.
    """
    val_num, val_stars, val_has_stars = parse_spearman_value(spearman_str)
    
    val_positive = val_num > 0
    # Category: 2 = positive with stars, 1 = no stars, 0 = negative with stars
    category_rank = 2 if (val_has_stars and val_positive) else (1 if not val_has_stars else 0)
    
    return (category_rank, val_stars, val_num)


def compare_est_vs_true(est_str: str, true_str: str) -> bool:
    """
    Compare est_label_vs_embedding_spearman with true_label_vs_embedding_spearman.
    Returns True if est < true (est is worse than true).
    
    Uses the same comparison rules as ranking.
    """
    return compare_spearman_values(est_str, true_str) < 0


def process_summary_file(summary_path: Path) -> list[dict]:
    """
    Process a single grand_analysis_summary file.
    
    Returns:
        List of dictionaries, one per algo_model row
    """
    try:
        df = pd.read_csv(summary_path, index_col=0)
    except Exception as e:
        print(f"Warning: Failed to read {summary_path}: {e}")
        return []
    
    # Extract dataset and task from filename
    # Pattern: grand_analysis_summary_{dataset}_{task}_seed{seed}.csv
    stem = summary_path.stem
    match = re.match(r"grand_analysis_summary_(.+?)_(card|time)_seed\d+", stem)
    if not match:
        print(f"Warning: Could not parse dataset/task from filename: {summary_path.name}")
        return []
    
    dataset = match.group(1)
    task = match.group(2)
    
    results = []
    
    # Process each row (algo_model)
    for algo_model in df.index:
        row = df.loc[algo_model]
        
        # Sum type categories
        bad = (
            row.get("type_1", 0) + 
            row.get("type_4", 0) + 
            row.get("type_5", 0) + 
            row.get("type_7", 0)
        )
        good = row.get("type_2", 0) + row.get("type_3", 0)
        not_care = row.get("type_6", 0)
        further_analysis = row.get("type_8", 0)
        
        # Extract spearman values
        true_spearman_str = row.get("true_label_vs_embedding_spearman", "NaN")
        est_spearman_str = row.get("est_label_vs_embedding_spearman", "NaN")
        
        # Get ranking value tuple for sorting
        true_ranking_val = get_ranking_value(true_spearman_str)
        
        # Compare est vs true
        est_smaller_than_true = compare_est_vs_true(est_spearman_str, true_spearman_str)
        
        results.append({
            "dataset": dataset,
            "task": task,
            "algo_model": algo_model,
            "bad": int(bad),
            "good": int(good),
            "not_care": int(not_care),
            "further_analysis": int(further_analysis),
            "true_label_vs_embedding_spearman": true_spearman_str,
            "est_label_vs_embedding_spearman": est_spearman_str,
            "true_label_vs_embedding_spearman_ranking": true_ranking_val,
            "est_smaller_than_true": est_smaller_than_true,
        })
    
    return results


def main() -> None:
    """Main function to process all summary files and generate final summary."""
    if not OUT_DIR.exists():
        print(f"Error: Output directory {OUT_DIR} does not exist.")
        return
    
    # Find all grand_analysis_summary files
    pattern = "grand_analysis_summary_*_seed*.csv"
    summary_files = []
    
    for dataset_dir in OUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue
        
        # Look for summary files in this dataset directory
        files = list(dataset_dir.glob(pattern))
        summary_files.extend(files)
    
    if not summary_files:
        print(f"Warning: No grand_analysis_summary files found in {OUT_DIR}")
        return
    
    print(f"Found {len(summary_files)} summary files to process...")
    
    # Process all files
    all_results = []
    for summary_file in sorted(summary_files):
        results = process_summary_file(summary_file)
        all_results.extend(results)
        print(f"Processed {summary_file.name}: {len(results)} rows")
    
    if not all_results:
        print("Warning: No data collected from summary files.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    # Sort by dataset, task, and ranking tuple (descending)
    # The ranking tuple is (category_rank, stars_rank, numeric_value)
    # We need to sort by each component of the tuple
    df["_category"] = df["true_label_vs_embedding_spearman_ranking"].apply(lambda x: x[0])
    df["_stars"] = df["true_label_vs_embedding_spearman_ranking"].apply(lambda x: x[1])
    df["_numeric"] = df["true_label_vs_embedding_spearman_ranking"].apply(lambda x: x[2])
    
    # Sort by dataset, task, and ranking components (all descending except dataset/task)
    df = df.sort_values(
        by=["dataset", "task", "_category", "_stars", "_numeric"],
        ascending=[True, True, False, False, False]
    )
    
    # Add rank column (rank within each dataset/task group)
    # Create a composite ranking value for ranking
    df["_rank_value"] = (
        df["_category"] * 1000000 + 
        df["_stars"] * 10000 + 
        df["_numeric"] * 100
    )
    
    df["rank"] = (
        df.groupby(["dataset", "task"])["_rank_value"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    
    # Drop temporary columns
    df = df.drop(columns=["_category", "_stars", "_numeric", "_rank_value", "true_label_vs_embedding_spearman_ranking"])
    
    # Reorder columns for output
    output_columns = [
        "dataset",
        "task",
        "algo_model",
        "rank",
        "bad",
        "good",
        "not_care",
        "further_analysis",
        "true_label_vs_embedding_spearman",
        "est_label_vs_embedding_spearman",
        "est_smaller_than_true",
    ]
    
    df_output = df[output_columns].copy()
    
    # Save to CSV
    output_path = OUT_DIR / "grand_analysis_cross_dataset_summary.csv"
    df_output.to_csv(output_path, index=False)
    print(f"\nSaved cross-dataset summary to {output_path}")
    print(f"Total rows: {len(df_output)}")
    print(f"Datasets: {df_output['dataset'].nunique()}")
    print(f"Tasks: {df_output['task'].unique().tolist()}")


if __name__ == "__main__":
    main()

