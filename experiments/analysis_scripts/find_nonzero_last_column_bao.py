#!/usr/bin/env python3
"""
Script to find rows in bao CSV files where the last column is not zero.

Usage:
    python find_nonzero_last_column_bao.py <csv_file> [--threshold 1e-10] [--output output.csv]
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path


def find_nonzero_rows(csv_file, threshold=1e-10, treat_zero_as_zero=True):
    """
    Find rows where the last column is not zero.
    
    Args:
        csv_file: Path to CSV file
        threshold: Threshold for considering a value as zero (default: 1e-10)
        treat_zero_as_zero: If True, treat 0.0 as zero. If False, only exact 0 is zero.
    
    Returns:
        DataFrame with rows where last column is not zero, and statistics
    """
    # Read CSV file (skip first row as it contains column names)
    df = pd.read_csv(csv_file, header=None, skiprows=1)
    
    # Get last column
    last_col = df.iloc[:, -1]
    last_col_idx = len(df.columns) - 1
    
    # Determine zero mask based on treatment
    if treat_zero_as_zero:
        # Treat values with absolute value < threshold as zero
        zero_mask = last_col.abs() < threshold
    else:
        # Only exact 0.0 is zero
        zero_mask = (last_col == 0.0)
    
    # Find non-zero rows
    non_zero_mask = ~zero_mask
    non_zero_rows = df[non_zero_mask].copy()
    
    # Statistics
    stats = {
        'total_rows': len(df),
        'zero_rows': zero_mask.sum(),
        'non_zero_rows': non_zero_mask.sum(),
        'last_col_idx': last_col_idx,
        'last_col_min': last_col.min(),
        'last_col_max': last_col.max(),
        'last_col_mean': last_col.mean(),
        'exact_zeros': (last_col == 0.0).sum(),
        'near_zeros': ((last_col.abs() < threshold) & (last_col != 0.0)).sum(),
    }
    
    return non_zero_rows, stats


def main():
    parser = argparse.ArgumentParser(description="Find rows where last column is not zero")
    parser.add_argument("csv_file", type=str, help="Path to bao CSV file")
    parser.add_argument("--threshold", type=float, default=1e-10,
                        help="Threshold for considering value as zero (default: 1e-10)")
    parser.add_argument("--exact-only", action="store_true",
                        help="Only treat exact 0.0 as zero (not 0.0 with floating point)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV file to save non-zero rows (optional)")
    parser.add_argument("--show-values", action="store_true",
                        help="Show the actual non-zero values")
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        return
    
    print(f"Analyzing: {csv_path.name}")
    print("="*80)
    
    # Find non-zero rows
    treat_zero_as_zero = not args.exact_only
    non_zero_rows, stats = find_nonzero_rows(csv_path, threshold=args.threshold, 
                                            treat_zero_as_zero=treat_zero_as_zero)
    
    # Print statistics
    print(f"\nFile Statistics:")
    print(f"  Total rows: {stats['total_rows']}")
    print(f"  Total columns: {stats['last_col_idx'] + 1}")
    print(f"  Last column index: {stats['last_col_idx']}")
    print(f"\nLast Column Analysis:")
    print(f"  Rows with zero last column: {stats['zero_rows']} ({100*stats['zero_rows']/stats['total_rows']:.1f}%)")
    print(f"  Rows with non-zero last column: {stats['non_zero_rows']} ({100*stats['non_zero_rows']/stats['total_rows']:.1f}%)")
    print(f"  Exact zeros (== 0.0): {stats['exact_zeros']}")
    print(f"  Near zeros (abs < {args.threshold} but != 0.0): {stats['near_zeros']}")
    print(f"  Last column min value: {stats['last_col_min']:.6f}")
    print(f"  Last column max value: {stats['last_col_max']:.6f}")
    print(f"  Last column mean value: {stats['last_col_mean']:.6f}")
    
    if treat_zero_as_zero:
        print(f"\n  Treatment: Values with abs < {args.threshold} are treated as zero")
    else:
        print(f"\n  Treatment: Only exact 0.0 is treated as zero")
    
    # Print non-zero rows
    if len(non_zero_rows) > 0:
        print(f"\n" + "="*80)
        print(f"Rows with Non-Zero Last Column ({len(non_zero_rows)} rows):")
        print("="*80)
        
        if args.show_values:
            print(f"\nRow Index | Last Column Value")
            print("-" * 40)
            for idx, row in non_zero_rows.iterrows():
                last_val = row.iloc[-1]
                print(f"  {idx:8d} | {last_val:.10f}")
        else:
            print(f"\nRow indices with non-zero last column:")
            non_zero_indices = non_zero_rows.index.tolist()
            if len(non_zero_indices) <= 50:
                print(f"  {non_zero_indices}")
            else:
                print(f"  First 50: {non_zero_indices[:50]}")
                print(f"  ... and {len(non_zero_indices) - 50} more")
                print(f"  Total: {len(non_zero_indices)} rows")
        
        # Show sample of actual values
        print(f"\nSample of non-zero values in last column:")
        sample_values = non_zero_rows.iloc[:10, -1].tolist()
        for i, val in enumerate(sample_values):
            print(f"  Row {non_zero_rows.index[i]}: {val:.10f}")
    else:
        print(f"\n✓ All rows have zero (or near-zero) values in the last column")
    
    # Save to output file if requested
    if args.output and len(non_zero_rows) > 0:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        non_zero_rows.to_csv(output_path, index=True, header=False)
        print(f"\n✓ Non-zero rows saved to: {output_path}")


if __name__ == "__main__":
    main()

