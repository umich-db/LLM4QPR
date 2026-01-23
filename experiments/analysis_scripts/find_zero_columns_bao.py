#!/usr/bin/env python3
"""
Script to find the first column in bao CSV files where all values become 0.

For each bao CSV file in embeddings/non-llm, this script checks each column
from left to right and identifies the first column where all values are 0
(or remain 0 from that point forward).
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse


def find_first_all_zero_column(df, threshold=1e-10):
    """
    Find the first column index where all values are 0.
    Checks columns from left to right.
    
    Args:
        df: DataFrame to analyze
        threshold: Threshold for considering a value as zero (default: 1e-10)
    
    Returns:
        Column index (int) of first column where all values are 0, or None if no such column
    """
    for col_idx in range(len(df.columns)):
        col = df.iloc[:, col_idx]
        
        # Check if all values in this column are 0 (or very close to 0 due to floating point)
        if col.abs().max() < threshold:
            return col_idx
    
    return None


def find_first_mostly_zero_column(df, zero_percentage=90.0, threshold=1e-10):
    """
    Find the first column index where a certain percentage of values are zero.
    
    Args:
        df: DataFrame to analyze
        zero_percentage: Percentage of zeros required (default: 90.0)
        threshold: Threshold for considering a value as zero (default: 1e-10)
    
    Returns:
        Column index (int) of first column meeting the criteria, or None
    """
    for col_idx in range(len(df.columns)):
        col = df.iloc[:, col_idx]
        
        # Count zeros
        num_zeros = (col.abs() < threshold).sum()
        pct_zeros = 100.0 * num_zeros / len(col)
        
        if pct_zeros >= zero_percentage:
            return col_idx, pct_zeros
    
    return None, None


def find_first_consistently_zero_column(df):
    """
    Find the first column index where all values are 0 AND all subsequent columns are also 0.
    This finds where the data "ends" and everything becomes zero.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Column index (int) of first column where all values are 0 and remain 0, or None
    """
    for col_idx in range(len(df.columns)):
        col = df.iloc[:, col_idx]
        
        # Check if all values in this column are 0
        if col.abs().max() < 1e-10:
            # Check if all subsequent columns are also 0
            all_subsequent_zero = True
            for next_col_idx in range(col_idx + 1, len(df.columns)):
                next_col = df.iloc[:, next_col_idx]
                if next_col.abs().max() >= 1e-10:
                    all_subsequent_zero = False
                    break
            
            if all_subsequent_zero:
                return col_idx
    
    return None


def analyze_bao_files(directory="embeddings/non-llm", check_consistency=True):
    """
    Analyze all bao CSV files in the specified directory.
    
    Args:
        directory: Directory containing bao CSV files
        check_consistency: If True, check that all subsequent columns are also zero
                          If False, just find first column with all zeros
    
    Returns:
        Dictionary with results for each file
    """
    dir_path = Path(directory)
    bao_files = sorted(list(dir_path.glob("bao*.csv")))
    
    if len(bao_files) == 0:
        print(f"No bao CSV files found in {directory}")
        return {}
    
    print(f"Found {len(bao_files)} bao CSV files\n")
    print("="*80)
    print("Analysis Results")
    print("="*80)
    
    results = {}
    
    for bao_file in bao_files:
        try:
            # Read CSV file
            # Skip first row as it contains column names
            df = pd.read_csv(bao_file, header=None, skiprows=1)
            
            # Get file info
            num_rows, num_cols = df.shape
            
            # Find first zero column
            if check_consistency:
                first_zero_col = find_first_consistently_zero_column(df)
                description = "first column where all values are 0 AND all subsequent columns remain 0"
            else:
                first_zero_col = find_first_all_zero_column(df)
                description = "first column where all values are 0"
            
            # Also find when values become mostly zero (90% threshold)
            mostly_zero_col, mostly_zero_pct = find_first_mostly_zero_column(df, zero_percentage=90.0)
            
            # Find when values become mostly zero (50% threshold)
            mostly_zero_50_col, mostly_zero_50_pct = find_first_mostly_zero_column(df, zero_percentage=50.0)
            
            # Store results
            results[str(bao_file)] = {
                'file': bao_file.name,
                'num_rows': num_rows,
                'num_cols': num_cols,
                'first_zero_col': first_zero_col,
                'first_mostly_zero_90_col': mostly_zero_col,
                'first_mostly_zero_90_pct': mostly_zero_pct,
                'first_mostly_zero_50_col': mostly_zero_50_col,
                'first_mostly_zero_50_pct': mostly_zero_50_pct,
                'description': description
            }
            
            # Print results
            print(f"\nFile: {bao_file.name}")
            print(f"  Shape: {num_rows} rows × {num_cols} columns")
            
            if first_zero_col is not None:
                print(f"  {description.capitalize()}: Column {first_zero_col} (index {first_zero_col})")
                print(f"  Columns before zero: {first_zero_col}")
                print(f"  Columns that are zero: {num_cols - first_zero_col}")
                
                # Verify by checking a few columns around the transition
                if first_zero_col > 0:
                    prev_col = df.iloc[:, first_zero_col - 1]
                    print(f"  Column {first_zero_col - 1} (before): max abs value = {prev_col.abs().max():.6f}")
                zero_col = df.iloc[:, first_zero_col]
                print(f"  Column {first_zero_col} (zero): max abs value = {zero_col.abs().max():.6e}")
            else:
                print(f"  No column found where all values are 0")
            
            # Print mostly zero information
            if mostly_zero_50_col is not None:
                print(f"  First column with ≥50% zeros: Column {mostly_zero_50_col} ({mostly_zero_50_pct:.1f}% zeros)")
            if mostly_zero_col is not None:
                print(f"  First column with ≥90% zeros: Column {mostly_zero_col} ({mostly_zero_pct:.1f}% zeros)")
            
            # Check last column
            last_col = df.iloc[:, -1]
            last_col_zeros = (last_col.abs() < 1e-10).sum()
            last_col_zero_pct = 100.0 * last_col_zeros / len(last_col)
            last_col_max = last_col.abs().max()
            last_col_idx = num_cols - 1
            max_equals_idx = abs(last_col_max - last_col_idx) < 0.01
            print(f"  Last column ({last_col_idx}): max abs = {last_col_max:.6f}, {last_col_zero_pct:.1f}% zeros, max==index: {max_equals_idx}")
            
            # Check if max value pattern changes (when max stops equaling column index)
            print(f"  Note: In these files, max value typically equals column index")
            print(f"        So even with high % zeros, there's at least one value = column_index")
        
        except Exception as e:
            print(f"\nError processing {bao_file.name}: {e}")
            results[str(bao_file)] = {
                'file': bao_file.name,
                'error': str(e)
            }
    
    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    
    # Summary for mostly zero columns
    mostly_zero_50_results = [r for r in results.values() if 'first_mostly_zero_50_col' in r and r['first_mostly_zero_50_col'] is not None]
    mostly_zero_90_results = [r for r in results.values() if 'first_mostly_zero_90_col' in r and r['first_mostly_zero_90_col'] is not None]
    
    if len(mostly_zero_50_results) > 0:
        cols_50 = [r['first_mostly_zero_50_col'] for r in mostly_zero_50_results]
        print(f"\nFiles with ≥50% zeros: {len(mostly_zero_50_results)}/{len(results)}")
        print(f"First column with ≥50% zeros statistics:")
        print(f"  Minimum: {min(cols_50)}")
        print(f"  Maximum: {max(cols_50)}")
        print(f"  Average: {np.mean(cols_50):.1f}")
        print(f"  Median: {int(np.median(cols_50))}")
        print(f"  Most common: {max(set(cols_50), key=cols_50.count)} (appears {cols_50.count(max(set(cols_50), key=cols_50.count))} times)")
    
    if len(mostly_zero_90_results) > 0:
        cols_90 = [r['first_mostly_zero_90_col'] for r in mostly_zero_90_results]
        print(f"\nFiles with ≥90% zeros: {len(mostly_zero_90_results)}/{len(results)}")
        print(f"First column with ≥90% zeros statistics:")
        print(f"  Minimum: {min(cols_90)}")
        print(f"  Maximum: {max(cols_90)}")
        print(f"  Average: {np.mean(cols_90):.1f}")
        print(f"  Median: {int(np.median(cols_90))}")
        print(f"  Most common: {max(set(cols_90), key=cols_90.count)} (appears {cols_90.count(max(set(cols_90), key=cols_90.count))} times)")
    
    # Check for all-zero columns
    valid_results = [r for r in results.values() if 'first_zero_col' in r and r['first_zero_col'] is not None]
    if len(valid_results) > 0:
        first_zero_cols = [r['first_zero_col'] for r in valid_results]
        print(f"\nFiles with 100% zero columns: {len(valid_results)}/{len(results)}")
        print(f"First 100% zero column statistics:")
        print(f"  Minimum: {min(first_zero_cols)}")
        print(f"  Maximum: {max(first_zero_cols)}")
        print(f"  Average: {np.mean(first_zero_cols):.1f}")
        print(f"  Median: {int(np.median(first_zero_cols))}")
    else:
        print("\nNo files found with 100% zero columns")
        print("Note: Even when 100% of values are zero, the max value may equal the column index")
        print("      This suggests sparse data where most values are zero but max equals column number")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Find first zero column in bao CSV files")
    parser.add_argument("--directory", type=str, default="embeddings/non-llm",
                        help="Directory containing bao CSV files (default: embeddings/non-llm)")
    parser.add_argument("--check-consistency", action="store_true", default=True,
                        help="Check that all subsequent columns are also zero (default: True)")
    parser.add_argument("--no-consistency", action="store_false", dest="check_consistency",
                        help="Only find first column with all zeros, don't check subsequent columns")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV file to save results (optional)")
    
    args = parser.parse_args()
    
    # Analyze files
    results = analyze_bao_files(args.directory, args.check_consistency)
    
    # Save to CSV if requested
    if args.output and results:
        output_data = []
        for file_path, data in results.items():
            if 'error' not in data:
                output_data.append({
                    'file': data['file'],
                    'num_rows': data['num_rows'],
                    'num_cols': data['num_cols'],
                    'first_zero_col': data.get('first_zero_col'),
                })
        
        if output_data:
            output_df = pd.DataFrame(output_data)
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_df.to_csv(output_path, index=False)
            print(f"\n✓ Results saved to: {output_path}")


if __name__ == "__main__":
    main()

