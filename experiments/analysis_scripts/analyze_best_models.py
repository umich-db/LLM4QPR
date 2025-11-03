#!/usr/bin/env python3
"""
Script to analyze which LLM models beat non-LLM methods across evaluation points.

Usage:
    python analyze_best_models.py [--dir BASE_DIR] [--threshold N]
    
Arguments:
    --dir: Base directory path (default: current directory)
           The script will look for graphs/averaged_by_task/ within this directory
    --threshold: Number of evaluation points (out of 4: q50, q90, q95, qmax) where 
                 an LLM model must beat all non-LLM models to be considered winning
                 (default: 4, meaning all evaluation points)
"""

import pandas as pd
from pathlib import Path
import numpy as np
import argparse


def analyze_csv_file(csv_path):
    """
    Analyze a single CSV file to find LLM models that beat all non-LLM methods.
    
    Returns:
        tuple: (set of LLM model names that beat all non-LLM methods, 
                best non-LLM error,
                dict of non-LLM algorithm errors,
                dict of LLM model errors)
    """
    df = pd.read_csv(csv_path)
    
    # DO NOT filter by 'filtered' column - include all algorithms even outliers
    # Filtering is only for visualization, not for performance analysis
    
    # Clean up labels: remove "-nan" suffix from non-LLM algorithms
    df['label'] = df['label'].str.replace('-nan', '', regex=False)
    
    # Separate LLM and non-LLM
    llm_rows = df[df['label'].str.startswith('llm-')]
    non_llm_rows = df[~df['label'].str.startswith('llm-')]
    
    if llm_rows.empty or non_llm_rows.empty:
        return set(), None, {}, {}
    
    # Get the best (minimum) non-LLM error
    best_non_llm_error = non_llm_rows['error'].min()
    
    # Get all non-LLM errors as a dictionary
    non_llm_errors = dict(zip(non_llm_rows['label'], non_llm_rows['error']))
    
    # Get all LLM errors as a dictionary (remove 'llm-' prefix from labels)
    llm_errors = {}
    for idx, row in llm_rows.iterrows():
        model_name = row['label'].replace('llm-', '', 1)
        llm_errors[model_name] = row['error']
    
    # Find LLM models that beat this
    better_llm = llm_rows[llm_rows['error'] < best_non_llm_error]
    
    # Extract model names (remove 'llm-' prefix)
    better_llm_models = set(better_llm['label'].str.replace('llm-', '', regex=False).tolist())
    
    return better_llm_models, best_non_llm_error, non_llm_errors, llm_errors


def filter_models_by_threshold(results_dict, threshold):
    """
    Filter models based on how many evaluation points they beat non-LLM in.
    
    Args:
        results_dict: Dictionary mapping evaluation point names to sets of winning models
        threshold: Minimum number of evaluation points a model must win to be included
        
    Returns:
        Dictionary mapping model names to the count of evaluation points they won
    """
    from collections import Counter
    
    # Count how many evaluation points each model beats non-LLM in
    model_counts = Counter()
    for models_set in results_dict.values():
        for model in models_set:
            model_counts[model] += 1
    
    # Filter by threshold
    winning_models = {model: count for model, count in model_counts.items() 
                      if count >= threshold}
    
    return winning_models


def rank_algorithms(errors_by_metric):
    """
    Rank algorithms by averaging their ranks across different evaluation points.
    
    Args:
        errors_by_metric: Dictionary mapping metric names to dictionaries of {algo/model: error}
        
    Returns:
        Tuple of (ranks_by_metric, avg_ranks)
        - ranks_by_metric: Dictionary mapping metric names to {algo/model: rank}
        - avg_ranks: Dictionary mapping algorithm/model names to their average rank
    """
    # Collect all algorithms/models
    all_algos = set()
    for errors_dict in errors_by_metric.values():
        all_algos.update(errors_dict.keys())
    
    if not all_algos:
        return {}, {}
    
    # Rank algorithms for each metric
    ranks_by_metric = {}
    algo_ranks = {algo: [] for algo in all_algos}
    
    for metric_name, errors_dict in errors_by_metric.items():
        # Sort algorithms by error (ascending, lower is better)
        sorted_algos = sorted(errors_dict.items(), key=lambda x: x[1])
        
        # Store ranks for this metric
        metric_ranks = {}
        # Assign ranks (1-indexed)
        for rank, (algo, error) in enumerate(sorted_algos, start=1):
            metric_ranks[algo] = rank
            algo_ranks[algo].append(rank)
        
        ranks_by_metric[metric_name] = metric_ranks
    
    # Calculate average rank for each algorithm
    avg_ranks = {}
    for algo, ranks in algo_ranks.items():
        if ranks:
            avg_ranks[algo] = sum(ranks) / len(ranks)
        else:
            avg_ranks[algo] = float('inf')  # Algorithm missing from all metrics
    
    return ranks_by_metric, avg_ranks


# Keep the old function name for backwards compatibility
def rank_non_llm_algorithms(non_llm_errors_by_metric):
    """
    Rank non-LLM algorithms by averaging their ranks across different evaluation points.
    (Wrapper for rank_algorithms)
    """
    return rank_algorithms(non_llm_errors_by_metric)


def main():
    parser = argparse.ArgumentParser(description='Analyze which LLM models beat non-LLM methods')
    parser.add_argument('--dir', type=str, default='.',
                        help='Base directory path (default: current directory)')
    parser.add_argument('--threshold', type=int, default=4,
                        help='Number of evaluation points (out of 4: q50, q90, q95, qmax) where LLM must beat non-LLM (default: 4)')
    parser.add_argument('--relative', action='store_true',
                        help='Evaluate relative error (reads files with "relative" in the name)')
    args = parser.parse_args()
    
    # Validate threshold
    if args.threshold < 1 or args.threshold > 4:
        parser.error("threshold must be between 1 and 4")
    
    threshold = args.threshold
    
    # Combine the directory prefix with the base path
    base_path = Path(args.dir) / 'graphs/averaged_by_task'
    
    # Determine file pattern based on relative flag
    file_suffix = '_relative' if args.relative else ''
    error_type = 'relative error' if args.relative else 'absolute error'
    
    print(f"Analyzing data from: {base_path.absolute()}")
    print(f"Evaluating {error_type}")
    print(f"Threshold: LLM must beat non-LLM in at least {threshold} out of 4 evaluation points (q50, q90, q95, qmax)\n")
    
    # Analyze card_averaged
    card_path = base_path / 'card_averaged'
    card_results = {}
    card_non_llm_errors = {}
    card_llm_errors = {}
    
    print("="*80)
    print("CARD TASK ANALYSIS")
    print("="*80)
    
    # Only analyze test evaluation points (q50, q90, q95, qmax)
    # Get all matching files and filter based on suffix to avoid double-counting
    all_csv_files = sorted(card_path.glob('test_*_data.csv'))
    
    if file_suffix:
        # In relative mode, only keep files with the suffix
        csv_files = [f for f in all_csv_files if file_suffix in f.stem]
    else:
        # In non-relative mode, exclude files with "_relative" to avoid double-counting
        csv_files = [f for f in all_csv_files if '_relative' not in f.stem]
    
    for csv_file in csv_files:
        filename = csv_file.stem.replace('_data', '')
        better_models, best_non_llm, non_llm_errors, llm_errors = analyze_csv_file(csv_file)
        card_results[filename] = better_models
        card_non_llm_errors[filename] = non_llm_errors
        card_llm_errors[filename] = llm_errors
        
        print(f"\n{filename}:")
        print(f"  Best non-LLM error: {best_non_llm:.2f}")
        if better_models:
            print(f"  LLM models beating non-LLM: {len(better_models)}")
            for model in sorted(better_models):
                print(f"    - {model}")
        else:
            print(f"  No LLM models beat non-LLM")
    
    # Find models that meet the threshold across card files
    if card_results:
        winning_card = filter_models_by_threshold(card_results, threshold)
        print(f"\n{'='*80}")
        print(f"LLM models that beat non-LLM in at least {threshold} card evaluation points:")
        print(f"{'='*80}")
        if winning_card:
            for model in sorted(winning_card.keys()):
                print(f"  ✓ {model} ({winning_card[model]}/4 points)")
        else:
            print(f"  None - no LLM model beats non-LLM in at least {threshold} card evaluation points")
        common_card = winning_card
    else:
        common_card = {}
    
    # Rank non-LLM algorithms for card task
    if card_non_llm_errors:
        card_ranks_by_metric, card_rankings = rank_non_llm_algorithms(card_non_llm_errors)
        print(f"\n{'='*80}")
        print(f"Non-LLM Algorithm Rankings (Card Task):")
        print(f"{'='*80}")
        
        # Display ranks for each evaluation point
        print("\nRanks by evaluation point:")
        # Sort metrics to ensure consistent order (q50, q90, q95, qmax)
        metric_order = {'q50': 0, 'q90': 1, 'q95': 2, 'qmax': 3}
        sorted_metrics = sorted(card_ranks_by_metric.keys(), 
                               key=lambda x: metric_order.get(x.split('_')[1], 999))
        for metric in sorted_metrics:
            print(f"\n  {metric}:")
            sorted_metric = sorted(card_ranks_by_metric[metric].items(), key=lambda x: x[1])
            for algo, rank in sorted_metric:
                print(f"    {rank}. {algo}")
        
        print("\n" + "-"*80)
        print("Average rank across all evaluation points (q50, q90, q95, qmax)")
        print("(Lower average rank is better)\n")
        
        # Sort by average rank
        sorted_rankings = sorted(card_rankings.items(), key=lambda x: x[1])
        for rank, (algo, avg_rank) in enumerate(sorted_rankings, start=1):
            print(f"  {rank}. {algo}: avg rank = {avg_rank:.2f}")
    else:
        print(f"\n{'='*80}")
        print(f"Non-LLM Algorithm Rankings (Card Task): No data available")
        print(f"{'='*80}")
    
    # Rank LLM models for card task
    card_llm_rankings = {}
    if card_llm_errors:
        card_llm_ranks_by_metric, card_llm_rankings = rank_algorithms(card_llm_errors)
        print(f"\n{'='*80}")
        print(f"LLM Model Rankings (Card Task):")
        print(f"{'='*80}")
        
        # Display ranks for each evaluation point
        print("\nRanks by evaluation point:")
        sorted_metrics = sorted(card_llm_ranks_by_metric.keys(), 
                               key=lambda x: metric_order.get(x.split('_')[1], 999))
        for metric in sorted_metrics:
            print(f"\n  {metric}:")
            sorted_metric = sorted(card_llm_ranks_by_metric[metric].items(), key=lambda x: x[1])
            for model, rank in sorted_metric:
                print(f"    {rank}. {model}")
        
        print("\n" + "-"*80)
        print("Average rank across all evaluation points (q50, q90, q95, qmax)")
        print("(Lower average rank is better)\n")
        
        # Sort by average rank
        sorted_rankings = sorted(card_llm_rankings.items(), key=lambda x: x[1])
        for rank, (model, avg_rank) in enumerate(sorted_rankings, start=1):
            print(f"  {rank}. {model}: avg rank = {avg_rank:.2f}")
    else:
        print(f"\n{'='*80}")
        print(f"LLM Model Rankings (Card Task): No data available")
        print(f"{'='*80}")
    
    print("\n\n" + "="*80)
    print("TIME TASK ANALYSIS")
    print("="*80)
    
    # Analyze time_averaged
    time_path = base_path / 'time_averaged'
    time_results = {}
    time_non_llm_errors = {}
    time_llm_errors = {}
    
    # Only analyze test evaluation points (q50, q90, q95, qmax)
    # Get all matching files and filter based on suffix to avoid double-counting
    all_csv_files = sorted(time_path.glob('test_*_data.csv'))
    
    if file_suffix:
        # In relative mode, only keep files with the suffix
        csv_files = [f for f in all_csv_files if file_suffix in f.stem]
    else:
        # In non-relative mode, exclude files with "_relative" to avoid double-counting
        csv_files = [f for f in all_csv_files if '_relative' not in f.stem]
    
    for csv_file in csv_files:
        filename = csv_file.stem.replace('_data', '')
        better_models, best_non_llm, non_llm_errors, llm_errors = analyze_csv_file(csv_file)
        time_results[filename] = better_models
        time_non_llm_errors[filename] = non_llm_errors
        time_llm_errors[filename] = llm_errors
        
        print(f"\n{filename}:")
        print(f"  Best non-LLM error: {best_non_llm:.2f}")
        if better_models:
            print(f"  LLM models beating non-LLM: {len(better_models)}")
            for model in sorted(better_models):
                print(f"    - {model}")
        else:
            print(f"  No LLM models beat non-LLM")
    
    # Find models that meet the threshold across time files
    if time_results:
        winning_time = filter_models_by_threshold(time_results, threshold)
        print(f"\n{'='*80}")
        print(f"LLM models that beat non-LLM in at least {threshold} time evaluation points:")
        print(f"{'='*80}")
        if winning_time:
            for model in sorted(winning_time.keys()):
                print(f"  ✓ {model} ({winning_time[model]}/4 points)")
        else:
            print(f"  None - no LLM model beats non-LLM in at least {threshold} time evaluation points")
        common_time = winning_time
    else:
        common_time = {}
    
    # Rank non-LLM algorithms for time task
    if time_non_llm_errors:
        time_ranks_by_metric, time_rankings = rank_non_llm_algorithms(time_non_llm_errors)
        print(f"\n{'='*80}")
        print(f"Non-LLM Algorithm Rankings (Time Task):")
        print(f"{'='*80}")
        
        # Display ranks for each evaluation point
        print("\nRanks by evaluation point:")
        # Sort metrics to ensure consistent order (q50, q90, q95, qmax)
        metric_order = {'q50': 0, 'q90': 1, 'q95': 2, 'qmax': 3}
        sorted_metrics = sorted(time_ranks_by_metric.keys(), 
                               key=lambda x: metric_order.get(x.split('_')[1], 999))
        for metric in sorted_metrics:
            print(f"\n  {metric}:")
            sorted_metric = sorted(time_ranks_by_metric[metric].items(), key=lambda x: x[1])
            for algo, rank in sorted_metric:
                print(f"    {rank}. {algo}")
        
        print("\n" + "-"*80)
        print("Average rank across all evaluation points (q50, q90, q95, qmax)")
        print("(Lower average rank is better)\n")
        
        # Sort by average rank
        sorted_rankings = sorted(time_rankings.items(), key=lambda x: x[1])
        for rank, (algo, avg_rank) in enumerate(sorted_rankings, start=1):
            print(f"  {rank}. {algo}: avg rank = {avg_rank:.2f}")
    else:
        print(f"\n{'='*80}")
        print(f"Non-LLM Algorithm Rankings (Time Task): No data available")
        print(f"{'='*80}")
    
    # Rank LLM models for time task
    time_llm_rankings = {}
    if time_llm_errors:
        time_llm_ranks_by_metric, time_llm_rankings = rank_algorithms(time_llm_errors)
        print(f"\n{'='*80}")
        print(f"LLM Model Rankings (Time Task):")
        print(f"{'='*80}")
        
        # Display ranks for each evaluation point
        print("\nRanks by evaluation point:")
        sorted_metrics = sorted(time_llm_ranks_by_metric.keys(), 
                               key=lambda x: metric_order.get(x.split('_')[1], 999))
        for metric in sorted_metrics:
            print(f"\n  {metric}:")
            sorted_metric = sorted(time_llm_ranks_by_metric[metric].items(), key=lambda x: x[1])
            for model, rank in sorted_metric:
                print(f"    {rank}. {model}")
        
        print("\n" + "-"*80)
        print("Average rank across all evaluation points (q50, q90, q95, qmax)")
        print("(Lower average rank is better)\n")
        
        # Sort by average rank
        sorted_rankings = sorted(time_llm_rankings.items(), key=lambda x: x[1])
        for rank, (model, avg_rank) in enumerate(sorted_rankings, start=1):
            print(f"  {rank}. {model}: avg rank = {avg_rank:.2f}")
    else:
        print(f"\n{'='*80}")
        print(f"LLM Model Rankings (Time Task): No data available")
        print(f"{'='*80}")
    
    # Overall summary
    print("\n\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    
    if common_card:
        print(f"\n✓ LLM models beating non-LLM in ≥{threshold} card evaluation points ({len(common_card)}):")
        for model in sorted(common_card.keys()):
            print(f"  - {model} ({common_card[model]}/4)")
    else:
        print(f"\n✗ No LLM model beats non-LLM in at least {threshold} card evaluation points")
    
    if common_time:
        print(f"\n✓ LLM models beating non-LLM in ≥{threshold} time evaluation points ({len(common_time)}):")
        for model in sorted(common_time.keys()):
            print(f"  - {model} ({common_time[model]}/4)")
    else:
        print(f"\n✗ No LLM model beats non-LLM in at least {threshold} time evaluation points")
    
    # Find models that beat non-LLM in both card AND time (with threshold)
    if common_card and common_time:
        both_models = set(common_card.keys()).intersection(set(common_time.keys()))
        print(f"\n{'='*80}")
        print(f"LLM models beating non-LLM in BOTH card AND time (≥{threshold} points each):")
        print(f"{'='*80}")
        if both_models:
            for model in sorted(both_models):
                print(f"  ⭐ {model} (card: {common_card[model]}/4, time: {common_time[model]}/4)")
        else:
            print("  None")
    
    # Overall LLM model rankings (average of card and time)
    if card_llm_rankings or time_llm_rankings:
        print(f"\n{'='*80}")
        print(f"Overall LLM Model Rankings (Average of Card and Time Tasks):")
        print(f"{'='*80}")
        print("Ranked by average rank across both tasks and all evaluation points")
        print("(Lower average rank is better)\n")
        
        # Collect all LLM models from both tasks
        all_llm_models = set(card_llm_rankings.keys()).union(set(time_llm_rankings.keys()))
        
        # Calculate overall average rank for each model
        overall_llm_ranks = {}
        for model in all_llm_models:
            ranks = []
            if model in card_llm_rankings:
                ranks.append(card_llm_rankings[model])
            if model in time_llm_rankings:
                ranks.append(time_llm_rankings[model])
            
            if ranks:
                overall_llm_ranks[model] = sum(ranks) / len(ranks)
        
        # Sort by overall average rank
        sorted_overall = sorted(overall_llm_ranks.items(), key=lambda x: x[1])
        for rank, (model, avg_rank) in enumerate(sorted_overall, start=1):
            # Show individual task ranks if available
            card_rank = f"{card_llm_rankings[model]:.2f}" if model in card_llm_rankings else "N/A"
            time_rank = f"{time_llm_rankings[model]:.2f}" if model in time_llm_rankings else "N/A"
            print(f"  {rank}. {model}: avg rank = {avg_rank:.2f} (card: {card_rank}, time: {time_rank})")


if __name__ == "__main__":
    main()

