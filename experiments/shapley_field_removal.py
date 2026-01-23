#!/usr/bin/env python3
"""
Calculate Shapley values for field category removal in query plans.

This script:
1. Checks for all required files
2. Reports missing files
3. Calculates Shapley values for each category's contribution to error
4. Reports results for 4 quantiles (50, 90, 95, max) averaged across 3 seeds

Usage:
    python shapley_field_removal.py [--test-categories CAT1 CAT2 ...]
    
    If --test-categories is specified, only those categories will be tested.
    Categories not specified will always remain present (never removed).
    
    Example:
        python shapley_field_removal.py --test-categories cost card cond meta
        # This tests cost, card, cond, meta while keeping ops always present
"""

import itertools
import pandas as pd
import numpy as np
import math
import argparse
from pathlib import Path
import re
from collections import defaultdict

# 5 categories (abbreviated names used in filenames)
ALL_CATEGORIES = ['ops', 'cost', 'card', 'cond', 'meta']
CATEGORY_FULL_NAMES = {
    'ops': 'operator_structure_and_config',
    'cost': 'cost',
    'card': 'cardinality',
    'cond': 'conditions_and_filters',
    'meta': 'metadata_and_config'
}

SEEDS = [42, 43, 44]
QUANTILES = [50, 90, 95, 'max']
BASE_DIR = Path(__file__).parent


def generate_all_combinations(categories_to_test):
    """Generate all 2^n - 1 combinations of categories to test."""
    n = len(categories_to_test)
    all_combinations = []
    for r in range(1, n + 1):  # 1 to n categories
        for combo in itertools.combinations(categories_to_test, r):
            all_combinations.append(tuple(sorted(combo)))
    return all_combinations


def find_files(categories_to_test, dataset, task, model_pattern):
    """Find all result files and organize by combination and seed."""
    all_combinations = generate_all_combinations(categories_to_test)
    
    # Construct directory paths based on dataset
    results_rm_dir = BASE_DIR / "results_rm" / dataset
    results_dir = BASE_DIR / "results" / dataset
    
    # Find files in results_rm
    found_files = {}
    if not results_rm_dir.exists():
        print(f"Warning: Directory {results_rm_dir} does not exist")
    else:
        for file_path in results_rm_dir.iterdir():
            if not file_path.is_file():
                continue
            name = file_path.name
            
            # Check if it matches our criteria
            if task not in name or model_pattern not in name or "cdf" not in name:
                continue
            if "_rm-" not in name:
                continue
            
            # Extract rm- part
            try:
                rm_part = name.split("_rm-")[1].split("_seed")[0]
                removed = tuple(sorted(rm_part.split('-')))
                
                # Filter: only include files that remove exactly the categories we're testing
                # (i.e., all removed categories must be in categories_to_test)
                if not all(cat in categories_to_test for cat in removed):
                    continue
                
                # Extract seed
                seed_match = re.search(r"_seed(\d+)\.csv", name)
                if seed_match:
                    seed = int(seed_match.group(1))
                    if removed not in found_files:
                        found_files[removed] = {}
                    found_files[removed][seed] = file_path
            except (IndexError, ValueError) as e:
                print(f"Warning: Could not parse filename {name}: {e}")
                continue
    
    # Find baseline file (no removal)
    baseline_files = {}
    if not results_dir.exists():
        print(f"Warning: Directory {results_dir} does not exist")
    else:
        for file_path in results_dir.iterdir():
            if not file_path.is_file():
                continue
            name = file_path.name
            if task not in name or model_pattern not in name or "cdf" not in name:
                continue
            if "_rm-" in name:  # Skip files with removal
                continue
            # Extract seed
            seed_match = re.search(r"_seed(\d+)\.csv", name)
            if seed_match:
                seed = int(seed_match.group(1))
                baseline_files[seed] = file_path
    
    return found_files, baseline_files, all_combinations


def check_missing_files(found_files, baseline_files, all_combinations):
    """Check which files are missing and report."""
    missing = []
    
    # Check baseline files
    for seed in SEEDS:
        if seed not in baseline_files:
            missing.append(("baseline", seed))
    
    # Check combination files
    for combo in all_combinations:
        if combo not in found_files:
            missing.append((combo, "all seeds"))
        else:
            for seed in SEEDS:
                if seed not in found_files[combo]:
                    missing.append((combo, seed))
    
    return missing


def load_error_quantiles(file_path):
    """Load a CDF file and extract error quantiles."""
    try:
        df = pd.read_csv(file_path)
        
        # CDF files have 'percentage' and 'Qerror' columns
        # The percentage column is cumulative, Qerror is the error value
        if 'Qerror' not in df.columns or 'percentage' not in df.columns:
            # Fallback: try to find error column
            error_col = None
            for col in df.columns:
                if 'error' in col.lower() or 'qerror' in col.lower():
                    error_col = col
                    break
            
            if error_col is None:
                return None
            
            # If no percentage column, calculate quantiles directly
            errors = df[error_col].dropna()
            if len(errors) == 0:
                return None
            
            quantiles = {
                50: np.percentile(errors, 50),
                90: np.percentile(errors, 90),
                95: np.percentile(errors, 95),
                'max': np.max(errors)
            }
            return quantiles
        
        # CDF format: find Qerror values at specific percentiles
        # Interpolate to get exact percentile values
        percentage = df['percentage'].values
        qerror = df['Qerror'].values
        
        # For 50th, 90th, 95th percentiles, find closest or interpolate
        def get_error_at_percentile(target_pct):
            # Find the row where percentage is closest to target_pct
            idx = np.argmin(np.abs(percentage - target_pct))
            if percentage[idx] == target_pct:
                return qerror[idx]
            # Interpolate if needed
            if idx == 0:
                return qerror[0]
            if idx == len(percentage) - 1:
                return qerror[-1]
            # Linear interpolation
            if percentage[idx] < target_pct:
                p1, e1 = percentage[idx], qerror[idx]
                p2, e2 = percentage[idx + 1], qerror[idx + 1]
            else:
                p1, e1 = percentage[idx - 1], qerror[idx - 1]
                p2, e2 = percentage[idx], qerror[idx]
            if p2 == p1:
                return e1
            return e1 + (e2 - e1) * (target_pct - p1) / (p2 - p1)
        
        quantiles = {
            50: get_error_at_percentile(50.0),
            90: get_error_at_percentile(90.0),
            95: get_error_at_percentile(95.0),
            'max': np.max(qerror)
        }
        return quantiles
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def shapley_value(category, categories_to_test, error_dict):
    """
    Calculate Shapley value for a category.
    
    Shapley value formula:
    SV_i = sum_{S subset N\\{i}} [|S|!(|N|-|S|-1)!/|N|!] * [v(S U {i}) - v(S)]
    
    where:
    - N is the set of categories being tested
    - S is a subset of categories not containing i
    - v(S) is the error when categories in S are removed
    """
    n = len(categories_to_test)
    shapley = {q: 0.0 for q in QUANTILES}
    total_weight = {q: 0.0 for q in QUANTILES}
    
    # Get all subsets that don't contain this category
    other_categories = [c for c in categories_to_test if c != category]
    
    for subset_size in range(len(other_categories) + 1):
        for subset in itertools.combinations(other_categories, subset_size):
            s = tuple(sorted(subset))
            s_with_i = tuple(sorted(list(subset) + [category]))
            
            # Get errors for both subsets
            error_s = error_dict.get(s, None)
            error_s_with_i = error_dict.get(s_with_i, None)
            
            if error_s is None or error_s_with_i is None:
                continue
            
            # Weight: |S|!(n-|S|-1)!/n!
            weight = (math.factorial(len(s)) * 
                     math.factorial(n - len(s) - 1) / 
                     math.factorial(n))
            
            # Contribution: v(S U {i}) - v(S)
            for q in QUANTILES:
                if q in error_s and q in error_s_with_i:
                    contribution = error_s_with_i[q] - error_s[q]
                    shapley[q] += weight * contribution
                    total_weight[q] += weight
    
    # Normalize if weights don't sum to 1 (due to missing combinations)
    for q in QUANTILES:
        if total_weight[q] > 0:
            shapley[q] = shapley[q] / total_weight[q]
    
    return shapley


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Calculate Shapley values for field category removal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all 5 categories with default settings (stats dataset, card task, Llama-3.1-8B)
  python shapley_field_removal.py
  
  # Test only cost, card, cond, meta (keep ops always present)
  python shapley_field_removal.py --test-categories cost card cond meta
  
  # Specify dataset, task, and model
  python shapley_field_removal.py --dataset results_Train_tpch_Test_tpch_ours --task time --model gemma-3-1b-pt
  
  # Combine custom settings with specific categories
  python shapley_field_removal.py --dataset results_Train_job_Test_job_ours --task card --model Llama-3.1-8B --test-categories cost card
        """
    )
    parser.add_argument(
        '--test-categories',
        nargs='+',
        choices=ALL_CATEGORIES,
        default=ALL_CATEGORIES,
        help='Categories to test (others will always remain present). Default: all categories'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='results_Train_stats_Test_stats_ours',
        help='Dataset directory name (e.g., results_Train_stats_Test_stats_ours). Default: results_Train_stats_Test_stats_ours'
    )
    parser.add_argument(
        '--task',
        type=str,
        choices=['card', 'time'],
        default='card',
        help='Task to analyze (card or time). Default: card'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='Llama-3.1-8B',
        help='Model pattern to match in filenames (e.g., Llama-3.1-8B, gemma-3-1b-pt). Default: Llama-3.1-8B'
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    categories_to_test = sorted(args.test_categories)
    fixed_categories = sorted([c for c in ALL_CATEGORIES if c not in categories_to_test])
    dataset = args.dataset
    task = args.task
    model_pattern = args.model
    
    print("=" * 80)
    print("Shapley Value Analysis for Field Category Removal")
    print("=" * 80)
    print(f"\nDataset: {dataset}")
    print(f"Task: {task}")
    print(f"Model: {model_pattern}")
    print(f"\nCategories to test: {', '.join([CATEGORY_FULL_NAMES[c] for c in categories_to_test])}")
    if fixed_categories:
        print(f"Categories always present: {', '.join([CATEGORY_FULL_NAMES[c] for c in fixed_categories])}")
    print(f"Total combinations to test: {2**len(categories_to_test) - 1}")
    
    # Find files
    print("\n1. Finding files...")
    found_files, baseline_files, all_combinations = find_files(categories_to_test, dataset, task, model_pattern)
    
    print(f"   Found {len(found_files)} unique combinations")
    print(f"   Found {len(baseline_files)} baseline files (seeds: {sorted(baseline_files.keys())})")
    print(f"   Expected {len(all_combinations)} combinations")
    
    # Check missing files
    print("\n2. Checking for missing files...")
    missing = check_missing_files(found_files, baseline_files, all_combinations)
    
    if missing:
        print(f"\n   MISSING FILES ({len(missing)}):")
        for item in missing:
            if isinstance(item[0], tuple):
                combo_str = '-'.join(item[0])
                print(f"     rm-{combo_str}, seed {item[1]}")
            else:
                print(f"     {item[0]}, seed {item[1]}")
        print("\n   WARNING: Some files are missing. Shapley values will be calculated")
        print("   using only available combinations, which may affect accuracy.")
        proceed = input("\n   Proceed with available data? (y/n): ").strip().lower()
        if proceed != 'y':
            return
    else:
        print("   All required files found!")
    
    # Load errors for all combinations
    print("\n3. Loading error quantiles from files...")
    error_dict = {}
    
    # Load baseline (empty set - no categories removed)
    # Baseline = files with no categories removed (all categories present)
    baseline_errors = {}
    for seed in SEEDS:
        if seed in baseline_files:
            quantiles = load_error_quantiles(baseline_files[seed])
            if quantiles:
                baseline_errors[seed] = quantiles
    
    # Average baseline across seeds (seeds 42, 43, 44 are random seeds)
    if baseline_errors:
        baseline_avg = {q: np.mean([baseline_errors[s][q] for s in SEEDS if s in baseline_errors]) 
                       for q in QUANTILES}
        error_dict[tuple()] = baseline_avg
        print(f"   Baseline (no removals): averaged across {len(baseline_errors)} seeds")
    
    # Load errors for all combinations
    for combo in all_combinations:
        if combo not in found_files:
            continue  # Skip completely missing combinations
        combo_errors = {}
        for seed in SEEDS:
            if seed in found_files[combo]:
                quantiles = load_error_quantiles(found_files[combo][seed])
                if quantiles:
                    combo_errors[seed] = quantiles
        
        # Average across seeds (only if we have at least one seed)
        if combo_errors:
            combo_avg = {q: np.mean([combo_errors[s][q] for s in SEEDS if s in combo_errors]) 
                        for q in QUANTILES}
            error_dict[combo] = combo_avg
    
    print(f"   Loaded errors for {len(error_dict)} combinations")
    
    # Calculate Shapley values
    print("\n4. Calculating Shapley values...")
    shapley_values = {}
    for category in categories_to_test:
        shapley_values[category] = shapley_value(category, categories_to_test, error_dict)
    
    # Report results
    print("\n" + "=" * 80)
    print("Shapley Values (Contribution of REMOVING each category to error)")
    print("=" * 80)
    print("\nInterpretation:")
    print("  The Shapley value measures: error_after_removal - error_before_removal")
    print("  Negative values: Removing this category REDUCES error")
    print("                   → Having this category INCREASES error (harmful)")
    print("  Positive values: Removing this category INCREASES error")
    print("                   → Having this category REDUCES error (beneficial)")
    print("\n" + f"{'Category':<30} {'50th':>12} {'90th':>12} {'95th':>12} {'Max':>12}")
    print("-" * 80)
    
    for category in categories_to_test:
        full_name = CATEGORY_FULL_NAMES[category]
        sv = shapley_values[category]
        # Format max value (might be very large)
        max_val = sv['max']
        if abs(max_val) > 1e10:
            max_str = f"{max_val:.2e}"
        else:
            max_str = f"{max_val:.4f}"
        print(f"{full_name:<30} {sv[50]:>12.4f} {sv[90]:>12.4f} {sv[95]:>12.4f} {max_str:>12}")
    
    # Save to CSV
    # Create a descriptive filename based on parameters
    safe_dataset = dataset.replace('/', '_').replace('\\', '_')
    safe_model = model_pattern.replace('/', '_').replace('\\', '_')
    output_file = BASE_DIR / f"shapley_field_removal_results_{safe_dataset}_{task}_{safe_model}.csv"
    results_df = pd.DataFrame({
        'category': [CATEGORY_FULL_NAMES[c] for c in categories_to_test],
        'shapley_50th': [shapley_values[c][50] for c in categories_to_test],
        'shapley_90th': [shapley_values[c][90] for c in categories_to_test],
        'shapley_95th': [shapley_values[c][95] for c in categories_to_test],
        'shapley_max': [shapley_values[c]['max'] for c in categories_to_test],
    })
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

