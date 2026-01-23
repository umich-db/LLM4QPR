#!/usr/bin/env python3
"""
Analyze the distribution of query plan lengths in a CSV file.

This script reads a CSV file containing query plans, calculates the length
of each plan (as character count of the JSON string), and reports the length
and index number at various percentiles (10th, 20th, ..., 90th, max).
"""

import argparse
import csv
import json
import numpy as np
from pathlib import Path


def calculate_plan_length(json_str):
    """
    Calculate the length of a query plan.
    
    Args:
        json_str: JSON string representation of the query plan
        
    Returns:
        Length of the plan (character count)
    """
    return len(json_str)


def find_percentile_of_index(lengths, indices, target_index):
    """
    Find the percentile of a query plan at a given index.
    
    Args:
        lengths: Array of plan lengths
        indices: Array of corresponding indices (1-indexed)
        target_index: The index to find the percentile for (1-indexed)
        
    Returns:
        Dictionary with percentile information, or None if index not found
    """
    # Find the position of the target index
    index_positions = np.where(indices == target_index)[0]
    
    if len(index_positions) == 0:
        return None
    
    # Get the length of the plan at this index
    target_length = lengths[index_positions[0]]
    
    # Calculate percentile: percentage of plans with length <= target_length
    # Using the "inclusive" method: (rank - 1) / (n - 1) * 100
    # where rank is the position when sorted (1-indexed)
    sorted_lengths = np.sort(lengths)
    rank = np.searchsorted(sorted_lengths, target_length, side='right')  # Number of values <= target
    
    if len(lengths) == 1:
        percentile = 100.0
    else:
        # Percentile = (rank - 1) / (n - 1) * 100
        percentile = (rank - 1) / (len(lengths) - 1) * 100
    
    return {
        'index': int(target_index),
        'length': int(target_length),
        'percentile': percentile,
        'rank': int(rank),
        'total': len(lengths)
    }


def analyze_plan_lengths(csv_path, query_index=None):
    """
    Analyze query plan lengths and find percentiles.
    
    Args:
        csv_path: Path to the CSV file containing query plans
        query_index: Optional index to query for its percentile
        
    Returns:
        Dictionary with percentile information and data for further queries
    """
    lengths = []
    indices = []
    
    print(f"Reading query plans from: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, start=1):  # Start from 1 for 1-indexed
            json_str = row.get('json', '')
            if json_str:
                length = calculate_plan_length(json_str)
                lengths.append(length)
                indices.append(idx)
    
    if not lengths:
        print("No query plans found in the file.")
        return None
    
    lengths = np.array(lengths)
    indices = np.array(indices)
    
    # If querying a specific index, find its percentile
    if query_index is not None:
        percentile_info = find_percentile_of_index(lengths, indices, query_index)
        if percentile_info is None:
            print(f"\nError: Index {query_index} not found in the file.")
            return None
        
        print("\n" + "="*60)
        print(f"Percentile Information for Index {query_index}:")
        print("="*60)
        print(f"Index:        {percentile_info['index']}")
        print(f"Length:       {percentile_info['length']:,} characters")
        print(f"Percentile:   {percentile_info['percentile']:.2f}th")
        print(f"Rank:         {percentile_info['rank']} out of {percentile_info['total']}")
        print("="*60)
        return percentile_info
    
    # Sort by length to find percentiles
    sorted_indices = np.argsort(lengths)
    sorted_lengths = lengths[sorted_indices]
    sorted_original_indices = indices[sorted_indices]
    
    # Calculate percentiles
    percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    results = {}
    
    for p in percentiles:
        # Calculate the percentile value
        percentile_value = np.percentile(lengths, p)
        
        # Find the index of the plan with length closest to (but >=) the percentile value
        # This gives us the actual plan at or above this percentile
        percentile_idx = np.searchsorted(sorted_lengths, percentile_value, side='left')
        percentile_idx = min(percentile_idx, len(sorted_lengths) - 1)  # Ensure within bounds
        
        results[p] = {
            'length': int(sorted_lengths[percentile_idx]),
            'index': int(sorted_original_indices[percentile_idx])
        }
    
    # Find max
    max_idx = len(sorted_lengths) - 1
    results['max'] = {
        'length': int(sorted_lengths[max_idx]),
        'index': int(sorted_original_indices[max_idx])
    }
    
    # Store data for potential future queries
    results['_data'] = {
        'lengths': lengths.tolist(),
        'indices': indices.tolist()
    }
    
    # Print statistics
    print(f"\nTotal number of query plans: {len(lengths)}")
    print(f"Min length: {int(np.min(lengths))} (index: {int(indices[np.argmin(lengths)])})")
    print(f"Max length: {int(np.max(lengths))} (index: {int(indices[np.argmax(lengths)])})")
    print(f"Mean length: {np.mean(lengths):.2f}")
    print(f"Median length: {np.median(lengths):.2f}")
    
    print("\n" + "="*60)
    print("Percentile Distribution:")
    print("="*60)
    print(f"{'Percentile':<12} {'Length':<15} {'Index':<10}")
    print("-"*60)
    
    for p in percentiles:
        print(f"{p}th{'':<8} {results[p]['length']:<15} {results[p]['index']:<10}")
    
    print(f"{'Max':<12} {results['max']['length']:<15} {results['max']['index']:<10}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Analyze query plan length distribution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_query_plan_lengths.py queryPlans/tpcds/postgres/long_raw_postgres_tpcds.csv
  python analyze_query_plan_lengths.py queryPlans/tpcds/postgres/long_raw_postgres_tpcds.csv --query-index 798
        """
    )
    parser.add_argument(
        'csv_file',
        type=str,
        help='Path to CSV file containing query plans (with id and json columns)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Optional: Path to save results as JSON file'
    )
    parser.add_argument(
        '--query-index',
        type=int,
        default=None,
        help='Optional: Query the percentile of a specific index (1-indexed)'
    )
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        return 1
    
    results = analyze_plan_lengths(csv_path, query_index=args.query_index)
    
    if results and args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove internal data before saving
        output_results = {k: v for k, v in results.items() if k != '_data'}
        
        with open(output_path, 'w') as f:
            json.dump(output_results, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == '__main__':
    exit(main())

