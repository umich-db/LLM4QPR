#!/usr/bin/env python3
"""
Script to plot timing vs accuracy graphs from combined_timing_accuracy_report.csv

Usage:
    python plot_timing_accuracy.py [--group_by task|task_dataset]
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from pathlib import Path
import re
import colorsys


def setup_mpl_params():
    """Setup matplotlib parameters to match training-data.py style"""
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams['ps.useafm'] = True
    mpl.rcParams['pdf.use14corefonts'] = True
    mpl.rcParams['xtick.labelsize'] = 20
    mpl.rcParams['ytick.labelsize'] = 20
    plt.style.use('seaborn-v0_8-ticks')


# Setup matplotlib parameters at module level
setup_mpl_params()


def parse_args():
    parser = argparse.ArgumentParser(description="Plot timing vs accuracy graphs")
    parser.add_argument("--group_by", type=str, default="task_dataset", 
                        choices=["task", "task_dataset"],
                        help="Group by 'task' only (averages across datasets) or 'task_dataset' (default: task_dataset)")
    parser.add_argument("--input", type=str, default="combined_timing_accuracy_report.csv",
                        help="Input CSV file (default: combined_timing_accuracy_report.csv)")
    parser.add_argument("--output_dir", type=str, default="graphs",
                        help="Output directory for graphs (default: graphs)")
    parser.add_argument("--outlier_nth", type=int, default=3,
                        help="Use nth highest value for outlier filtering (default: 3). Outliers are filtered if > 10x this value.")
    parser.add_argument("--relative", type=str, choices=["pg", "min"], default=None,
                        help="Plot relative error. Use 'pg' for postgres baseline (current behavior) "
                             "or 'min' to use the smallest error as baseline.")
    parser.add_argument("--midwest", action="store_true",
                        help="Temporary override: label y-axis 'Average Q-Error' instead of 'Relative Q-Error'.")
    return parser.parse_args()


_MIDWEST_LABEL = False


def extract_model_size(model_name):
    """
    Extract model size in billions from model name.
    Looks for patterns like "3B", "0.6B", "12b", etc.
    Returns the size as a float, or None if not found.
    """
    if not model_name:
        return None
    
    # Split by "-" and look for {number}b or {number}B pattern
    parts = model_name.split('-')
    for part in parts:
        # Match patterns like "3B", "0.6B", "12b", "1.5b"
        match = re.search(r'(\d+\.?\d*)[bB]', part)
        if match:
            return float(match.group(1))
    
    return None


def format_algo_name_for_display(algo_name):
    """
    Format algorithm name for display in legend.
    Renames non-LLM algorithms to their display names.
    """
    if not algo_name:
        return algo_name
    
    algo_lower = algo_name.lower()
    
    # Map non-LLM algorithm names
    algo_name_map = {
        'aimai': 'AiMeetsAi',
        'alece': 'ALECE',
        'bao': 'Bao',
        'e2e': 'E2E-Cost',
        'mscn': 'MSCN',
        'postgres': 'PostgreSQL',
        'price': 'PRICE',
        'qf': 'QueryFormer',
    }
    
    return algo_name_map.get(algo_lower, algo_name)


def format_model_name_for_display(model_name):
    """
    Format model name for display in legend.
    Renames models to shorter, cleaner names.
    """
    if not model_name:
        return model_name
    
    model_lower = model_name.lower()
    
    # Handle BERT family models
    if 'sentence' in model_lower or 'sentence-transformers' in model_lower:
        return 'SentenceBert'
    elif 'bert-base-uncased' in model_lower:
        return 'Bert'
    elif 'modernbert' in model_lower or 'answerdotai-modernbert' in model_lower:
        return 'ModernBert'
    
    # Handle Qwen models
    if 'qwen' in model_lower and 'embedding' in model_lower:
        size = extract_model_size(model_name)
        if size:
            return f'Qwen-{size:.0f}B' if size >= 1 else f'Qwen-{size}B'
        return 'Qwen-8B'  # Default for Qwen-Qwen3-Embedding-8B
    
    # Handle Llama models
    if 'llama' in model_lower:
        size = extract_model_size(model_name)
        if size:
            return f'Llama-{size:.0f}B' if size >= 1 else f'Llama-{size}B'
        return 'Llama'
    
    # Handle Gemma models
    if 'gemma' in model_lower:
        size = extract_model_size(model_name)
        if size:
            return f'Gemma-{size:.0f}B' if size >= 1 else f'Gemma-{size}B'
        return 'Gemma'
    
    # Return original if no match
    return model_name


def get_color_for_model(algo, model, all_models_in_group):
    """
    Assign color based on algo and model name.
    
    Rules:
    - Non-LLM algos: Distinct colors (purple for aimai, pink for bao, cyan for e2e, deepskyblue for qf, grey for postgres, orange for mscn, dark teal for alece, orangered for price)
    - LLM with "sentence": Darkest red (high saturation, low brightness)
    - LLM with "bert" (lowercase): Medium red (medium saturation and brightness)
    - LLM with "BERT" or "ModernBERT": Lightest red (low saturation, high brightness)
    - LLM with "gemma": Different shades of blue (varying saturation/brightness by model size)
    - LLM with "llama": Different shades of green (varying saturation/brightness by model size)
    - LLM with "Qwen" and "Embedding": Different shades of orange (varying saturation/brightness by model size)
    - LLM with "Qwen" but no "Embedding": Different shades of red (varying saturation/brightness by model size)
    """
    if algo != 'llm':
        # Non-LLM: explicit color assignment for each algorithm
        algo_color_map = {
            'aimai': (0.6, 0.0, 0.8),   # Purple
            'bao': 'plum',     # Pink
            # 'bao': (1.0, 0.4, 0.7),     # Pink
            'e2e': (0.0, 0.8, 0.8),     # Cyan
            'qf': 'khaki',        # Deep Sky Blue (matplotlib named color)
            'postgres': (0.4, 0.4, 0.4), # Grey
            'mscn': (1.0, 0.65, 0.0),   # Orange
            'alece': (0.0, 0.5, 0.5),   # Dark Teal
            'price': 'darkkhaki',       # Orange Red (matplotlib named color)
        }
        # Return the mapped color, or a default if algo not found
        return algo_color_map.get(algo, (0.5, 0.5, 0.5))
    
    # For LLM, extract size
    size = extract_model_size(model)
    if size is None:
        size = 1.0  # Default size if not found
    
    # Determine base hue based on model name
    model_lower = model.lower()
    
    # Special handling for sentence/bert/BERT models (assign fixed colors based on name)
    # REVERSED: largest = darkest
    if 'sentence' in model_lower or 'bert' in model_lower:
        hue = 0.0  # Red hue for sentence/bert/BERT models
        # Assign specific saturation and value based on model type
        # Order: SentenceBert (smallest) -> Bert (medium) -> ModernBert (largest)
        if 'sentence' in model_lower:
            # Lightest red for sentence models (smallest)
            saturation = 0.6
            value = 1.0
        elif 'modernbert' in model_lower or model.count('BERT') > 0:
            # Darkest red for ModernBERT (largest)
            saturation = 1.0
            value = 0.5
        else:
            # Medium red for bert models (medium size)
            saturation = 0.8
            value = 0.75
        
        # Convert HSV to RGB and return early
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return (r, g, b)
    
    if 'gemma' in model_lower:
        hue = 0.6  # Blue hue
    elif 'llama' in model_lower:
        hue = 0.33  # Green hue
    elif 'qwen' in model_lower and 'embedding' in model_lower:
        hue = 0.08  # Orange hue
    elif 'qwen' in model_lower:
        hue = 0.0  # Red hue
    else:
        # Default to purple for unknown LLM models
        hue = 0.75
    
    # Find all models in this group with the same base color
    same_color_models = []
    for other_model in all_models_in_group:
        other_model_lower = other_model.lower()
        if 'gemma' in model_lower and 'gemma' in other_model_lower:
            same_color_models.append(other_model)
        elif 'llama' in model_lower and 'llama' in other_model_lower:
            same_color_models.append(other_model)
        elif 'qwen' in model_lower and 'embedding' in model_lower and \
             'qwen' in other_model_lower and 'embedding' in other_model_lower:
            same_color_models.append(other_model)
        elif 'qwen' in model_lower and 'embedding' not in model_lower and \
             'qwen' in other_model_lower and 'embedding' not in other_model_lower:
            same_color_models.append(other_model)
    
    # Get sizes for all same-color models and create size-to-model mapping
    model_sizes = []
    for m in same_color_models:
        s = extract_model_size(m)
        if s is not None:
            model_sizes.append((s, m))
    
    if not model_sizes or len(model_sizes) == 1:
        # Single model or no size info: use mid-range saturation and brightness
        saturation = 0.8
        value = 0.8
    else:
        # Sort by size to get ranks (smallest to largest)
        model_sizes.sort(key=lambda x: x[0])
        sorted_sizes = [s for s, m in model_sizes]
        
        # Find the rank of the current model (0-indexed, where 0 is smallest)
        rank = None
        for idx, (s, m) in enumerate(model_sizes):
            if m == model:
                rank = idx
                break
        
        if rank is None:
            # Current model not found in sorted list, use mid-range
            saturation = 0.8
            value = 0.8
        else:
            num_models = len(model_sizes)
            is_largest = (rank == num_models - 1)
            
            if is_largest:
                # Largest model gets the darkest color (highest saturation, lowest brightness)
                saturation = 1.0
                value = 0.5  # Darker than before (was 0.6)
            else:
                # Normalize rank to [0, 1] range (excluding the largest model)
                # rank 0 (smallest) -> 0.0, rank (num_models-2) (second-largest) -> 1.0
                if num_models == 2:
                    # Only 2 models: smallest gets normalized rank 0
                    normalized_rank = 0.0
                else:
                    # For 3+ models: normalize ranks 0 to (num_models-2) to [0, 1]
                    normalized_rank = rank / (num_models - 2)
                
                # REVERSED: larger models = darker (higher saturation, lower brightness)
                # Vary saturation: larger models have higher saturation (0.6 to 0.95)
                saturation = 0.6 + 0.35 * normalized_rank
                
                # Vary value/brightness: larger models have LOWER brightness (1.0 to 0.65) - REVERSED
                value = 1.0 - 0.35 * normalized_rank
    
    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (r, g, b)


def filter_extreme_outliers(df, error_col='error', nth_highest=3, 
                            group_name=None, phase=None, metric=None, 
                            output_dir=None, relative_mode=None, postgres_error=None):
    """
    Filter out extreme outliers based on log-scale distance criterion:
    The distance between the smallest and 5th smallest error values (on log scale)
    must be at least 1/5 of the total range (on log scale).
    If including a point would violate this, filter it out from the top (largest values).
    
    IMPORTANT: Any algorithm with error value smaller than postgres_error will NOT be filtered.
    
    Args:
        df: DataFrame with error column
        error_col: Name of the error column
        nth_highest: Not used in new logic (kept for compatibility)
        group_name: Name of the group (for file output)
        phase: Phase name (for file output)
        metric: Metric name (for file output)
        output_dir: Output directory (for file output)
        relative_mode: Relative mode if applicable (for file output)
        postgres_error: Postgres error value - algorithms with smaller errors won't be filtered
    
    Returns:
        Tuple of (filtered_df, outliers_df)
    """
    if len(df) == 0:
        return df, pd.DataFrame()
    
    # Separate protected algorithms (those with error < postgres_error) from others
    protected_df = pd.DataFrame()
    if postgres_error is not None and pd.notna(postgres_error) and not np.isinf(postgres_error):
        protected_df = df[df[error_col] < postgres_error].copy()
        df = df[df[error_col] >= postgres_error].copy()
    
    # If all algorithms are protected, return all data
    if len(df) == 0:
        if group_name is not None and phase is not None and metric is not None and output_dir is not None:
            # Calculate metrics from protected data for reporting
            protected_sorted = protected_df[error_col].sort_values(ascending=True).values
            if len(protected_sorted) >= 5:
                smallest = protected_sorted[0]
                fifth_smallest = protected_sorted[4]
                max_error = protected_sorted[-1]
                if smallest > 0:
                    log_range = np.log(max_error) - np.log(smallest)
                else:
                    log_range = max_error - smallest
            else:
                smallest = protected_sorted[0] if len(protected_sorted) > 0 else None
                fifth_smallest = None
                log_range = None
            write_outlier_info_to_file(pd.DataFrame(), None, None, None,
                                     group_name, phase, metric, output_dir, relative_mode, error_col,
                                     smallest=smallest, fifth_smallest=fifth_smallest, total_range=log_range,
                                     use_log_scale=(smallest is not None and smallest > 0) if smallest is not None else True)
        return pd.concat([protected_df, df], ignore_index=False), pd.DataFrame()
    
    # For distance criterion, we need to check ALL points (protected + non-protected)
    # But we can only filter from non-protected points
    all_df = pd.concat([protected_df, df], ignore_index=False) if len(protected_df) > 0 else df.copy()
    all_sorted_errors = all_df[error_col].sort_values(ascending=True).values
    
    # Need at least 5 data points total for this method
    if len(all_sorted_errors) < 5:
        # Not enough data points, return all data (including protected)
        if len(protected_df) > 0:
            df = pd.concat([protected_df, df], ignore_index=False)
        if group_name is not None and phase is not None and metric is not None and output_dir is not None:
            write_outlier_info_to_file(pd.DataFrame(), None, None, None,
                                     group_name, phase, metric, output_dir, relative_mode, error_col,
                                     smallest=None, fifth_smallest=None, total_range=None)
        return df, pd.DataFrame()
    
    # Get sorted error values from ALL points (for distance criterion calculation)
    sorted_errors = all_sorted_errors
    
    # Get smallest (1st) and 5th smallest error values
    smallest = sorted_errors[0]
    fifth_smallest = sorted_errors[4]  # 0-indexed, so 4 is the 5th element
    
    # Check for negative or zero values (can't take log)
    has_negative_or_zero = smallest <= 0
    
    if has_negative_or_zero:
        # For relative mode with negative values, use linear scale instead
        # Calculate distance and range on linear scale
        distance = fifth_smallest - smallest
        total_range = sorted_errors[-1] - smallest  # max - min
        
        if total_range <= 0:
            # All values are the same, no filtering needed
            # Combine back with protected algorithms
            if len(protected_df) > 0:
                df = pd.concat([protected_df, df], ignore_index=False)
            if group_name is not None and phase is not None and metric is not None and output_dir is not None:
                write_outlier_info_to_file(pd.DataFrame(), None, None, None,
                                         group_name, phase, metric, output_dir, relative_mode, error_col,
                                         smallest=smallest, fifth_smallest=fifth_smallest, total_range=total_range,
                                         use_log_scale=False)
            return df, pd.DataFrame()
        
        # Required minimum distance is 1/5 of total range
        required_distance = total_range / 5.0
        
        # If current distance is less than required, filter from top
        if distance < required_distance:
            # Filter out largest values until condition is met
            outliers_df = pd.DataFrame()
            current_df = df.copy()  # Only non-protected points can be filtered
            
            # Keep removing largest points until condition is satisfied
            while len(current_df) > 0:
                # Calculate current metrics on ALL points (protected + non-protected)
                current_all_df = pd.concat([protected_df, current_df], ignore_index=False) if len(protected_df) > 0 else current_df
                current_all_sorted = current_all_df[error_col].sort_values(ascending=True).values
                
                # Need at least 5 points total to check distance criterion
                if len(current_all_sorted) < 5:
                    break
                
                current_smallest = current_all_sorted[0]
                current_fifth = current_all_sorted[4]
                current_max = current_all_sorted[-1]
                
                current_distance = current_fifth - current_smallest
                current_range = current_max - current_smallest
                current_required = current_range / 5.0 if current_range > 0 else 0
                
                # Check if condition is satisfied
                if current_distance >= current_required:
                    break
                
                # Condition not satisfied, remove largest point from non-protected
                # But never remove points that are protected (error < postgres_error)
                if len(current_df) == 0:
                    break
                
                largest_idx = current_df[error_col].idxmax()
                largest_error = current_df.loc[largest_idx, error_col]
                
                # Check if this point should be protected (shouldn't happen since current_df only has non-protected)
                if postgres_error is not None and pd.notna(postgres_error) and not np.isinf(postgres_error):
                    if largest_error < postgres_error:
                        # This point is protected, can't remove it - stop filtering
                        break
                
                outliers_df = pd.concat([outliers_df, current_df.loc[[largest_idx]]], ignore_index=False)
                current_df = current_df.drop(index=largest_idx)
            
            filtered_df = current_df
            
            # Combine back with protected algorithms
            if len(protected_df) > 0:
                filtered_df = pd.concat([protected_df, filtered_df], ignore_index=False)
            
            num_filtered = len(outliers_df)
            if num_filtered > 0:
                print(f"    Filtered out {num_filtered} extreme outlier(s) (linear scale distance criterion)")
            
            # Write to .txt file if output parameters are provided
            if group_name is not None and phase is not None and metric is not None and output_dir is not None:
                final_sorted = filtered_df[error_col].sort_values(ascending=True).values
                final_smallest = final_sorted[0] if len(final_sorted) > 0 else smallest
                final_fifth = final_sorted[4] if len(final_sorted) >= 5 else fifth_smallest
                final_range = final_sorted[-1] - final_sorted[0] if len(final_sorted) > 0 else total_range
                write_outlier_info_to_file(outliers_df, None, None, None,
                                         group_name, phase, metric, output_dir, relative_mode, error_col,
                                         smallest=final_smallest, fifth_smallest=final_fifth, total_range=final_range,
                                         use_log_scale=False)
            
            return filtered_df, outliers_df
        else:
            # Condition already satisfied, no filtering needed
            # Combine back with protected algorithms
            if len(protected_df) > 0:
                df = pd.concat([protected_df, df], ignore_index=False)
            if group_name is not None and phase is not None and metric is not None and output_dir is not None:
                write_outlier_info_to_file(pd.DataFrame(), None, None, None,
                                         group_name, phase, metric, output_dir, relative_mode, error_col,
                                         smallest=smallest, fifth_smallest=fifth_smallest, total_range=total_range,
                                         use_log_scale=False)
            return df, pd.DataFrame()
    else:
        # All values are positive, use log scale
        # Calculate log distance between 5th smallest and smallest
        log_distance = np.log(fifth_smallest) - np.log(smallest)
        
        # Calculate total log range
        max_error = sorted_errors[-1]
        log_range = np.log(max_error) - np.log(smallest)
        
        if log_range <= 0:
            # All values are the same, no filtering needed
            # Combine back with protected algorithms
            if len(protected_df) > 0:
                df = pd.concat([protected_df, df], ignore_index=False)
            if group_name is not None and phase is not None and metric is not None and output_dir is not None:
                write_outlier_info_to_file(pd.DataFrame(), None, None, None,
                                         group_name, phase, metric, output_dir, relative_mode, error_col,
                                         smallest=smallest, fifth_smallest=fifth_smallest, total_range=log_range,
                                         use_log_scale=True)
            return df, pd.DataFrame()
        
        # Required minimum log distance is 1/5 of total log range
        required_log_distance = log_range / 5.0
        
        # If current log distance is less than required, filter from top
        if log_distance < required_log_distance:
            # Filter out largest values until condition is met
            outliers_df = pd.DataFrame()
            current_df = df.copy()  # Only non-protected points can be filtered
            
            # Keep removing largest points until condition is satisfied
            while len(current_df) > 0:
                # Calculate current metrics on ALL points (protected + non-protected)
                current_all_df = pd.concat([protected_df, current_df], ignore_index=False) if len(protected_df) > 0 else current_df
                current_all_sorted = current_all_df[error_col].sort_values(ascending=True).values
                
                # Need at least 5 points total to check distance criterion
                if len(current_all_sorted) < 5:
                    break
                
                current_smallest = current_all_sorted[0]
                current_fifth = current_all_sorted[4]
                current_max = current_all_sorted[-1]
                
                # Ensure all values are positive for log
                if current_smallest <= 0:
                    break
                
                current_log_distance = np.log(current_fifth) - np.log(current_smallest)
                current_log_range = np.log(current_max) - np.log(current_smallest)
                current_required = current_log_range / 5.0 if current_log_range > 0 else 0
                
                # Check if condition is satisfied
                if current_log_distance >= current_required:
                    break
                
                # Condition not satisfied, remove largest point from non-protected
                # But never remove points that are protected (error < postgres_error)
                if len(current_df) == 0:
                    break
                
                largest_idx = current_df[error_col].idxmax()
                largest_error = current_df.loc[largest_idx, error_col]
                
                # Check if this point should be protected (shouldn't happen since current_df only has non-protected)
                if postgres_error is not None and pd.notna(postgres_error) and not np.isinf(postgres_error):
                    if largest_error < postgres_error:
                        # This point is protected, can't remove it - stop filtering
                        break
                
                outliers_df = pd.concat([outliers_df, current_df.loc[[largest_idx]]], ignore_index=False)
                current_df = current_df.drop(index=largest_idx)
            
            filtered_df = current_df
            
            # Combine back with protected algorithms
            if len(protected_df) > 0:
                filtered_df = pd.concat([protected_df, filtered_df], ignore_index=False)
            
            num_filtered = len(outliers_df)
            if num_filtered > 0:
                print(f"    Filtered out {num_filtered} extreme outlier(s) (log scale distance criterion)")
            
            # Write to .txt file if output parameters are provided
            if group_name is not None and phase is not None and metric is not None and output_dir is not None:
                final_sorted = filtered_df[error_col].sort_values(ascending=True).values
                final_smallest = final_sorted[0] if len(final_sorted) > 0 else smallest
                final_fifth = final_sorted[4] if len(final_sorted) >= 5 else fifth_smallest
                final_max = final_sorted[-1] if len(final_sorted) > 0 else max_error
                final_log_range = np.log(final_max) - np.log(final_smallest) if len(final_sorted) > 0 and final_smallest > 0 else log_range
                write_outlier_info_to_file(outliers_df, None, None, None,
                                         group_name, phase, metric, output_dir, relative_mode, error_col,
                                         smallest=final_smallest, fifth_smallest=final_fifth, total_range=final_log_range,
                                         use_log_scale=True)
            
            return filtered_df, outliers_df
        else:
            # Condition already satisfied, no filtering needed
            # Combine back with protected algorithms
            if len(protected_df) > 0:
                df = pd.concat([protected_df, df], ignore_index=False)
            if group_name is not None and phase is not None and metric is not None and output_dir is not None:
                write_outlier_info_to_file(pd.DataFrame(), None, None, None,
                                         group_name, phase, metric, output_dir, relative_mode, error_col,
                                         smallest=smallest, fifth_smallest=fifth_smallest, total_range=log_range,
                                         use_log_scale=True)
            return df, pd.DataFrame()


def write_outlier_info_to_file(outliers_df, threshold, reference_value, nth_highest,
                              group_name, phase, metric, output_dir, relative_mode, error_col,
                              smallest=None, fifth_smallest=None, total_range=None, use_log_scale=True):
    """
    Write outlier filtering information to a .txt file.
    
    Args:
        outliers_df: DataFrame with filtered outliers (may be empty)
        threshold: Threshold value used for filtering (deprecated, kept for compatibility)
        reference_value: Reference value used to calculate threshold (deprecated, kept for compatibility)
        nth_highest: Which highest value was used as reference (deprecated, kept for compatibility)
        group_name: Name of the group
        phase: Phase name (train/test)
        metric: Metric name (q50/q90/q95/qmax)
        output_dir: Output directory
        relative_mode: Relative mode if applicable
        error_col: Name of the error column
        smallest: Smallest error value (after filtering)
        fifth_smallest: 5th smallest error value (after filtering)
        total_range: Total range (on log scale if use_log_scale=True, linear otherwise)
        use_log_scale: Whether log scale was used for calculations
    """
    # Create output directory if needed
    output_path = Path(output_dir) / group_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    if relative_mode:
        filename_suffix = f'_relative-{relative_mode}'
    else:
        filename_suffix = ''
    txt_filename = f'{phase}_{metric}{filename_suffix}_outliers.txt'
    txt_path = output_path / txt_filename
    
    # Write to file
    with open(txt_path, 'w') as f:
        f.write(f"Outlier Filtering Information\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Group: {group_name}\n")
        f.write(f"Phase: {phase}\n")
        f.write(f"Metric: {metric}\n")
        if relative_mode:
            f.write(f"Relative Mode: {relative_mode}\n")
        f.write(f"\n")
        f.write(f"Filtering Method:\n")
        f.write(f"  Distance-based filtering on {'log' if use_log_scale else 'linear'} scale\n")
        f.write(f"  Ensures distance between smallest and 5th smallest >= 1/5 of total range\n")
        f.write(f"\n")
        f.write(f"Filtering Parameters:\n")
        if smallest is not None:
            f.write(f"  Smallest error value: {smallest:.6f}\n")
        if fifth_smallest is not None:
            f.write(f"  5th smallest error value: {fifth_smallest:.6f}\n")
        if smallest is not None and fifth_smallest is not None:
            if use_log_scale and smallest > 0 and fifth_smallest > 0:
                distance = np.log(fifth_smallest) - np.log(smallest)
                f.write(f"  Distance (log scale): {distance:.6f}\n")
            else:
                distance = fifth_smallest - smallest
                f.write(f"  Distance (linear scale): {distance:.6f}\n")
        if total_range is not None:
            scale_type = "log" if use_log_scale else "linear"
            f.write(f"  Total range ({scale_type} scale): {total_range:.6f}\n")
            if total_range > 0:
                required_distance = total_range / 5.0
                f.write(f"  Required minimum distance: {required_distance:.6f} (1/5 of range)\n")
        f.write(f"\n")
        
        if len(outliers_df) > 0:
            f.write(f"Filtered Outliers ({len(outliers_df)} data point(s)):\n")
            f.write(f"{'-'*60}\n")
            for idx, row in outliers_df.iterrows():
                label = f"{row['algo']}-{row['model']}" if pd.notna(row.get('model')) and row.get('model') else row['algo']
                error_val = row[error_col]
                if 'time_ms' in row and pd.notna(row['time_ms']):
                    time_val = row['time_ms']
                    f.write(f"  {label}: error={error_val:.6f}, time_ms={time_val:.2f}\n")
                else:
                    f.write(f"  {label}: error={error_val:.6f}, time_ms=N/A\n")
        else:
            f.write(f"No outliers were filtered (distance criterion already satisfied)\n")


def get_marker_for_model(algo, model):
    """
    Assign marker shape based on algo and model family.
    
    Rules:
    - Non-LLM algos: 'o' (circle)
    - Bert family (sentence, bert, ModernBERT): '^' (triangle)
    - Gemma family: 's' (square/rectangle)
    - Llama family: 'D' (diamond/rhombus)
    - Qwen family: 'X' (X shape)
    """
    if algo != 'llm':
        # Non-LLM: circle
        return 'X'
    
    if pd.isna(model) or not model:
        return 'X'  # Default to circle if no model
    
    model_lower = model.lower()
    
    # Bert family: triangle
    if 'sentence' in model_lower or 'bert' in model_lower:
        return '^'
    
    # Gemma family: square/rectangle
    if 'gemma' in model_lower:
        return 's'
    
    # Llama family: diamond/rhombus
    if 'llama' in model_lower:
        return 'D'
    
    # Qwen family: X shape
    if 'qwen' in model_lower:
        return 'o'
    
    # Default to circle for unknown LLM models
    return 'X'


def assign_colors_to_dataframe(df, all_llm_models_in_group):
    """
    Assign colors to each row in the dataframe based on algo and model.
    Returns a list of colors in the same order as df.
    
    Args:
        df: DataFrame with data to assign colors to
        all_llm_models_in_group: List of ALL LLM models in the group (before filtering)
    """
    colors = []
    for _, row in df.iterrows():
        color = get_color_for_model(row['algo'], row['model'], all_llm_models_in_group)
        colors.append(color)
    
    return colors


def assign_markers_to_dataframe(df):
    """
    Assign marker shapes to each row in the dataframe based on algo and model.
    Returns a list of markers in the same order as df.
    
    Args:
        df: DataFrame with data to assign markers to
    """
    markers = []
    for _, row in df.iterrows():
        marker = get_marker_for_model(row['algo'], row['model'])
        markers.append(marker)
    
    return markers


def convert_to_relative_error(df, error_col='error', mode='pg'):
    """
    Convert errors to relative errors.
    
    Args:
        df: DataFrame with error column and algo column
        error_col: Name of the error column
        mode: 'pg' to use postgres as baseline (current behavior),
              'min' to use the smallest error as baseline.
    
    Returns:
        DataFrame with relative errors
    """
    df = df.copy()
    
    if mode == 'pg':
        # Find postgres error
        postgres_rows = df[df['algo'] == 'postgres']
        if postgres_rows.empty or pd.isna(postgres_rows[error_col].iloc[0]):
            raise ValueError("No postgres error found or postgres error is NaN, cannot compute relative error")
        
        postgres_error = postgres_rows[error_col].iloc[0]
        
        # Handle special cases
        if postgres_error == 0:
            raise ValueError("Postgres error is 0, cannot compute relative error")
        
        if postgres_error == np.inf:
            raise ValueError("Postgres error is inf, cannot compute relative error")
        
        # Convert all errors to relative errors (postgres baseline becomes 0)
        df[error_col] = df[error_col] / postgres_error - postgres_error / df[error_col]
    elif mode == 'min':
        # Use the smallest non-NaN, non-negative error as baseline
        errors = df[error_col].dropna()
        if errors.empty:
            raise ValueError("Cannot compute relative error - all errors are NaN")
        
        # Prefer strictly positive minimum to avoid divide-by-zero; fallback to zero if all zeros
        positive_errors = errors[errors > 0]
        if not positive_errors.empty:
            baseline = positive_errors.min()
        else:
            # If all errors are zero, relative comparison is undefined
            raise ValueError("Cannot compute relative error - all errors are zero")
        
        df[error_col] = df[error_col] / baseline
    else:
        raise ValueError(f"Unsupported relative mode: {mode}")
    
    return df


def create_scatter_plot(df, phase, metric, group_name, output_dir, all_llm_models_in_group,
                        nth_highest=3, relative_mode=None, convert_relative=False):
    """
    Create a scatter plot for a specific phase (train/test) and metric (q50/q90/q95/qmax).
    
    Args:
        df: DataFrame with columns [time_ms, error, algo, model, label]
        phase: 'train' or 'test'
        metric: 'q50', 'q90', 'q95', or 'qmax'
        group_name: Name of the group (for title and filename)
        output_dir: Directory to save the plot
        all_llm_models_in_group: List of ALL LLM models in the group (before filtering)
        nth_highest: Which highest value to use for outlier filtering (default: 3)
        relative_mode: None for absolute error, 'pg' for postgres baseline, 'min' for minimum baseline
        convert_relative: If True, convert to relative error (default: False, used when data is not already relative)
    """
    # Filter out rows with missing data and exclude postgres
    # First, identify rows with missing data
    missing_time = df['time_ms'].isna()
    missing_error = df['error'].isna()
    missing_rows = df[missing_time | missing_error]
    
    if not missing_rows.empty:
        print(f"  Rows with missing data in {group_name}/{phase}_{metric}:")
        for idx, row in missing_rows.iterrows():
            missing_fields = []
            if pd.isna(row['time_ms']):
                missing_fields.append('time_ms')
            if pd.isna(row['error']):
                missing_fields.append(metric)
            print(f"    {row['algo']}-{row['model'] if row['model'] else ''}: missing {', '.join(missing_fields)}")
    
    # Convert to relative error if requested and not already converted
    if convert_relative:
        df = convert_to_relative_error(df, error_col='error', mode=relative_mode if relative_mode else 'pg')
    
    # Separate postgres rows (may have NaN time)
    postgres_rows = df[df['algo'] == 'postgres'].copy()
    df_clean = df[df['algo'] != 'postgres'].copy()
    
    # Separate rows with inf error
    inf_rows = df_clean[df_clean['error'] == np.inf].copy()
    df_clean = df_clean[df_clean['error'] != np.inf].copy()
    
    # Drop rows with missing error (but keep rows with missing time for now)
    df_clean = df_clean.dropna(subset=['error']).copy()
    
    # Temporarily disable Qwen without Embedding models
    def is_qwen_without_embedding(row):
        if row['algo'] == 'llm' and pd.notna(row['model']) and row['model']:
            if 'qwen' in row['model'].lower():
                return 'embedding' not in row['model'].lower()
        return False
    
    df_clean = df_clean[~df_clean.apply(is_qwen_without_embedding, axis=1)]
    
    # Check if df_clean still has data and time_ms column before filtering
    if df_clean.empty or 'time_ms' not in df_clean.columns:
        print(f"  Skipping {group_name}/{phase}_{metric}.pdf - no data after filtering Qwen models")
        return
    
    # Now drop rows with missing time
    df_clean = df_clean.dropna(subset=['time_ms']).copy()
    
    if df_clean.empty:
        print(f"  Skipping {group_name}/{phase}_{metric}.pdf - no valid data")
        return
    
    # Handle postgres separately: extract its error value for horizontal line
    # Don't add postgres to df_clean - we'll draw it as a horizontal line instead
    postgres_error = None
    if not postgres_rows.empty:
        # Separate postgres into normal and inf
        postgres_clean = postgres_rows.dropna(subset=['error'])
        postgres_inf = postgres_clean[postgres_clean['error'] == np.inf].copy()
        postgres_normal = postgres_clean[postgres_clean['error'] != np.inf].copy()
        
        # Get postgres error value for horizontal line
        if not postgres_normal.empty:
            postgres_error = postgres_normal['error'].iloc[0]
        
        # Add inf postgres to inf_rows (if any)
        if not postgres_inf.empty:
            inf_rows = pd.concat([inf_rows, postgres_inf], ignore_index=True)
    
    # Filter extreme outliers (top 2 if they're > 10x the nth highest)
    # Pass postgres_error so algorithms with smaller errors won't be filtered
    df_clean, df_outliers = filter_extreme_outliers(
        df_clean, 
        error_col='error', 
        nth_highest=nth_highest,
        group_name=group_name,
        phase=phase,
        metric=metric,
        output_dir=output_dir,
        relative_mode=relative_mode,
        postgres_error=postgres_error
    )
    
    # Separate postgres from df_clean (we'll draw it as a horizontal line, not a point)
    df_clean_no_pg = df_clean[df_clean['algo'] != 'postgres'].copy()
    
    if df_clean_no_pg.empty and postgres_error is None:
        print(f"  Skipping {group_name}/{phase}_{metric}.pdf - no data after filtering outliers")
        return
    
    # Print the number of data points and their coordinates
    print(f"  Plotting {len(df_clean_no_pg)} data points in {group_name}/{phase}_{metric}:")
    
    # Prepare data for CSV export
    csv_data = []
    for idx, row in df_clean_no_pg.iterrows():
        label = f"{row['algo']}-{row['model']}" if row['model'] else row['algo']
        print(f"    {label}: x={row['time_ms']:.2f}, y={row['error']:.2f}")
        csv_data.append({
            'label': label,
            'time': row['time_ms'],
            'error': row['error'],
            'filtered': False
        })
    
    # Add PostgreSQL to CSV as a horizontal line (no time value)
    if postgres_error is not None and pd.notna(postgres_error) and postgres_error != np.inf:
        print(f"    PostgreSQL: horizontal line at y={postgres_error:.2f}")
        csv_data.append({
            'label': 'PostgreSQL',
            'time': None,
            'error': postgres_error,
            'filtered': False
        })
    
    # Add filtered outliers to CSV
    if not df_outliers.empty:
        print(f"  Filtered outliers (shown in legend with 'x' marker):")
        for idx, row in df_outliers.iterrows():
            label = f"{row['algo']}-{row['model']}" if row['model'] else row['algo']
            print(f"    {label}: x={row['time_ms']:.2f}, y={row['error']:.2f} (filtered)")
            csv_data.append({
                'label': label,
                'time': row['time_ms'],
                'error': row['error'],
                'filtered': True
            })
    
    # Add rows with inf error to CSV
    if not inf_rows.empty:
        print(f"  Algorithms with inf error (shown in legend with 'x' marker):")
        for idx, row in inf_rows.iterrows():
            label = f"{row['algo']}-{row['model']}" if row['model'] else row['algo']
            print(f"    {label}: x={row['time_ms']:.2f}, y=inf (filtered)")
            csv_data.append({
                'label': label,
                'time': row['time_ms'],
                'error': row['error'],
                'filtered': True
            })
    
    # Save data to CSV
    csv_df = pd.DataFrame(csv_data)
    if relative_mode:
        filename_suffix = f'_relative-{relative_mode}'
    else:
        filename_suffix = ''
    csv_output_path = Path(output_dir) / group_name / f'{phase}_{metric}{filename_suffix}_data.csv'
    csv_output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_df.to_csv(csv_output_path, index=False)
    
    # Assign colors and markers to each row (excluding postgres)
    colors = assign_colors_to_dataframe(df_clean_no_pg, all_llm_models_in_group)
    df_clean_no_pg['color'] = colors
    markers = assign_markers_to_dataframe(df_clean_no_pg)
    df_clean_no_pg['marker'] = markers
    
    # Create figure
    fig, ax = plt.subplots(figsize=(6, 4.5))
    
    # Plot each point with its assigned color and marker (excluding postgres)
    for idx, row in df_clean_no_pg.iterrows():
        ax.scatter(row['time_ms'], row['error'], 
                  color=row['color'], marker=row['marker'], s=150, alpha=0.7, edgecolors='black', linewidths=0.5)
    
    # Draw horizontal dotted line for PostgreSQL if we have its error value
    if postgres_error is not None and pd.notna(postgres_error) and postgres_error != np.inf:
        # Get PostgreSQL color
        postgres_color = get_color_for_model('postgres', None, all_llm_models_in_group)
        # Draw horizontal dotted line across the entire plot width
        ax.axhline(y=postgres_error, color=postgres_color, linestyle='--', linewidth=2, alpha=0.7, label='_nolegend_')
    
    # Create legend by grouping similar models
    # Group by algo for non-LLM, and by model family for LLM
    non_llm_entries = {}  # {formatted_name: {'color': color, 'time': time_ms, 'marker': marker}}
    llm_entries = {}  # {formatted_name: {'color': color, 'model': original_model}}
    
    # Add entries from df_clean_no_pg (non-filtered, excluding postgres)
    for idx, row in df_clean_no_pg.iterrows():
        if row['algo'] != 'llm':
            key = format_algo_name_for_display(row['algo'])
            if key not in non_llm_entries:
                non_llm_entries[key] = {'color': row['color'], 'time': row['time_ms'], 'marker': row['marker']}
        else:
            # For LLM, use formatted model name as legend key
            key = format_model_name_for_display(row['model'])
            if key not in llm_entries:
                llm_entries[key] = {'color': row['color'], 'model': row['model']}
    
    # Add filtered outliers to legend at their normal positions (no special treatment)
    if not df_outliers.empty:
        # Get colors and markers for outliers
        outlier_colors = assign_colors_to_dataframe(df_outliers, all_llm_models_in_group)
        outlier_markers = assign_markers_to_dataframe(df_outliers)
        for i, (idx, row) in enumerate(df_outliers.iterrows()):
            if row['algo'] != 'llm':
                key = format_algo_name_for_display(row['algo'])
                if key not in non_llm_entries:
                    non_llm_entries[key] = {'color': outlier_colors[i], 'time': row['time_ms'], 'marker': outlier_markers[i]}
            else:
                key = format_model_name_for_display(row['model'])
                if key not in llm_entries:
                    llm_entries[key] = {'color': outlier_colors[i], 'model': row['model']}
    
    # Add inf error rows to legend at their normal positions (no special treatment)
    if not inf_rows.empty:
        # Get colors and markers for inf error rows
        inf_colors = assign_colors_to_dataframe(inf_rows, all_llm_models_in_group)
        inf_markers = assign_markers_to_dataframe(inf_rows)
        for i, (idx, row) in enumerate(inf_rows.iterrows()):
            if row['algo'] != 'llm':
                key = format_algo_name_for_display(row['algo'])
                if key not in non_llm_entries:
                    # Use a default time if missing (for sorting)
                    time_val = row.get('time_ms', 0) if 'time_ms' in row and pd.notna(row.get('time_ms')) else 0
                    non_llm_entries[key] = {'color': inf_colors[i], 'time': time_val, 'marker': inf_markers[i]}
            else:
                key = format_model_name_for_display(row['model'])
                if key not in llm_entries:
                    llm_entries[key] = {'color': inf_colors[i], 'model': row['model']}
    
    # Create legend handles: non-LLM first, then LLM
    handles = []
    labels = []
    
    # Add PostgreSQL first with a dotted line style (if we have its error value)
    if postgres_error is not None and pd.notna(postgres_error) and postgres_error != np.inf:
        postgres_color = get_color_for_model('postgres', None, all_llm_models_in_group)
        handles.append(plt.Line2D([0], [0], color=postgres_color, linestyle='--', linewidth=2, alpha=0.7))
        labels.append('PostgreSQL')
    
    # Add other non-LLM entries (sorted by time consumption, fastest to slowest)
    def sort_non_llm_key(item):
        label, entry = item
        # Others sorted by time
        return entry['time']
    
    sorted_non_llm = sorted(non_llm_entries.items(), key=sort_non_llm_key)
    for label, entry in sorted_non_llm:
        # Use the marker from entry (should be 'o' for non-LLM)
        marker = entry.get('marker', 'o')
        handles.append(plt.Line2D([0], [0], marker=marker, color='w', 
                                  markerfacecolor=entry['color'], markersize=10, markeredgecolor='black', markeredgewidth=0.5, alpha=0.7))
        labels.append(label)
    
    # Add LLM entries (sorted by family, then by size within family)
    def get_llm_sort_key(model_name):
        """
        Create a sort key for LLM models.
        Returns (family_order, size) tuple for sorting.
        For BERT family: SentenceBert (smallest) -> Bert (medium) -> ModernBert (largest)
        """
        model_lower = model_name.lower()
        
        # Determine family order
        if 'sentence' in model_lower or 'bert' in model_lower:
            family_order = 0
            # For BERT family, assign sizes: SentenceBert=1, Bert=2, ModernBert=3
            if 'sentence' in model_lower:
                size = 1  # Smallest
            elif 'modernbert' in model_lower or 'BERT' in model_name:
                size = 3  # Largest
            else:
                size = 2  # Medium
        elif 'gemma' in model_lower:
            family_order = 1
            size = extract_model_size(model_name) or 0
        elif 'llama' in model_lower:
            family_order = 2
            size = extract_model_size(model_name) or 0
        elif 'qwen' in model_lower and 'embedding' in model_lower:
            family_order = 3
            size = extract_model_size(model_name) or 0
        elif 'qwen' in model_lower:
            family_order = 4
            size = extract_model_size(model_name) or 0
        else:
            family_order = 5
            size = extract_model_size(model_name) or 0
        
        return (family_order, size)
    
    # Sort LLM entries by family and size
    # Need to map formatted names back to original for sorting
    # Create reverse mapping from formatted to original
    formatted_to_original = {}
    # Add from df_clean
    for idx, row in df_clean.iterrows():
        if row['algo'] == 'llm' and pd.notna(row['model']):
            formatted = format_model_name_for_display(row['model'])
            if formatted not in formatted_to_original:
                formatted_to_original[formatted] = row['model']
    # Add from outliers
    if not df_outliers.empty:
        for idx, row in df_outliers.iterrows():
            if row['algo'] == 'llm' and pd.notna(row['model']):
                formatted = format_model_name_for_display(row['model'])
                if formatted not in formatted_to_original:
                    formatted_to_original[formatted] = row['model']
    # Add from inf_rows
    if not inf_rows.empty:
        for idx, row in inf_rows.iterrows():
            if row['algo'] == 'llm' and pd.notna(row['model']):
                formatted = format_model_name_for_display(row['model'])
                if formatted not in formatted_to_original:
                    formatted_to_original[formatted] = row['model']
    
    # Sort by original model name, but use formatted name for display
    sorted_llm = sorted(llm_entries.items(), 
                        key=lambda x: get_llm_sort_key(formatted_to_original.get(x[0], x[0])))
    
    for label, entry in sorted_llm:
        # Get marker shape based on original model name
        original_model = entry.get('model', formatted_to_original.get(label, label))
        # Find the algo for this model (should be 'llm')
        marker = get_marker_for_model('llm', original_model)
        handles.append(plt.Line2D([0], [0], marker=marker, color='w', 
                                  markerfacecolor=entry['color'], markersize=10, markeredgecolor='black', markeredgewidth=0.5, alpha=0.7))
        labels.append(label)
    
    # Filtered algorithms are now included in non_llm_entries and llm_entries above
    # They will appear in their normal positions based on sorting
    
    # Set log scale for x-axis (time), but use linear scale for y-axis in relative mode
    # (because relative error can be negative or zero)
    ax.set_xscale('log')
    # For absolute errors and min-relative mode use log scale; for postgres-relative mode keep linear (values can be negative)
    if not relative_mode or relative_mode == 'min':
        ax.set_yscale('log')
    else:
        # In postgres-relative mode, values can be negative; keep linear scale and show baseline at 0
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    if relative_mode == 'min':
        ax.axhline(y=1, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Labels (matching training-data.py style)
    # TEXT SIZE CONFIGURATION:
    # - X-axis label: fontsize=18 (line below)
    # - Y-axis label: fontsize=16 (line below)
    # - Legend: fontsize=15 (see ax.legend below)
    # - Tick labels: fontsize=20 (configured in setup_mpl_params() at top of file)
    ax.set_xlabel('Inference Time (ms)' if _MIDWEST_LABEL else 'Time (ms)',
                  fontsize=24, weight='bold')
    if relative_mode == 'pg':
        error_label = f'Relative Q-Error vs Postgres ({metric})'
    elif relative_mode == 'min':
        error_label = f'Relative Q-Error'
        # error_label = f'Relative Q-Error vs Min ({metric})'
    else:
        error_label = f'Q-Error ({metric})'
    if _MIDWEST_LABEL:
        error_label = 'Average Q-Error'
    ax.set_ylabel(error_label, fontsize=24, weight='bold')
    if relative_mode == 'pg':
        title_suffix = ' (Relative to Postgres)'
    elif relative_mode == 'min':
        title_suffix = ' (Relative to Min Error)'
    else:
        title_suffix = ''
    # Title removed as requested
    # ax.set_title(f'{group_name} - {phase.capitalize()} - {metric.upper()}{title_suffix}', fontsize=16, weight='bold')
    
    # Legend at top with 8 entries in first row, 9 in second row
    # Arrange row-by-row: rearrange items so matplotlib's column-fill creates row-wise visual
    # Matplotlib fills column-wise, so to get row-wise visual we need to transpose the arrangement
    total_entries = len(handles)
    if total_entries <= 8:
        ncol = total_entries
        legend_handles = handles
        legend_labels = labels
    # elif total_entries == 17:
    #     # For exactly 17 entries: rearrange for 8-9 row layout
    #     # To get row-wise visual with 8 in row1 and 9 in row2:
    #     # We want: Row1 = items[0-7], Row2 = items[8-16]
    #     # With ncol=8, matplotlib fills column-wise, so we arrange items in row order
    #     # Items are already in the desired order [0-16], so we just use ncol=8
    #     # This will visually show: Row1=8 items (0-7), Row2=9 items (8-16, with last column having 2)
    #     # Actually, with ncol=8: Col0 gets items[0,8], Col1 gets items[1,9], etc.
    #     # So visually: Row1 = [0,1,2,3,4,5,6,7], Row2 = [8,9,10,11,12,13,14,15], Row3 = [16]
    #     # To get 8-9, we need to rearrange so items fill row-wise
    #     # Solution: rearrange items to [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16] and use ncol=9
    #     # With ncol=9: Col0=[0,9], Col1=[1,10], ..., Col7=[7,16], Col8=[8]
    #     # Visual: Row1=[0,1,2,3,4,5,6,7,8] (9 items) - not what we want
        
    #     # Better: Use ncol=8 and rearrange items to get row-wise fill
    #     # We want: Row1=[0-7], Row2=[8-16]
    #     # With ncol=8 column-fill, we need: Col0=[0,8], Col1=[1,9], ..., Col7=[7,15,16]
    #     # So we arrange: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16] - items are already in this order!
    #     # But this gives Row1=8, Row2=8, Row3=1
        
    #     # To get exactly 8-9, we rearrange items so first 8 appear in row1, next 9 in row2
    #     # With ncol=8: we interleave - take first 8, then next 9, interleaved
    #     # Actually, items are already in row order, so we just need the right ncol
    #     # Let's try ncol=9 and see if we can rearrange
        
    #     # Final solution: Use ncol=8, items in order [0-16]
    #     # This gives us row-wise appearance: Row1=8 items, Row2=8 items, Row3=1 item
    #     # To get Row2=9 items, we can add a spacer or accept the layout
    #     # Actually, the simplest is to use ncol=8 and the items will appear row-wise
    #     legend_handles = handles
    #     legend_labels = labels
    #     ncol = 8  # This will create row-wise visual with items in order
    else:
        # For other counts, use 9 columns
        ncol = 10
        legend_handles = handles
        legend_labels = labels
    
    # ax.legend(legend_handles, legend_labels, bbox_to_anchor=(0.5, 1.02), loc='lower center', 
    #           ncol=ncol, fontsize=20, frameon=True,
    #           handletextpad=0.3,  # Decrease distance between icon and text
    #           labelspacing=0.3,   # Decrease distance between rows
    #           columnspacing=0.5) # Decrease distance between columns
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Extract task from group_name
    # For task_dataset grouping: group_name is "{dataset}_{task}"
    # For task grouping: group_name is "{task}_averaged"
    if group_name.endswith('_averaged'):
        task = group_name.replace('_averaged', '')
    else:
        # Extract task from "{dataset}_{task}" format
        parts = group_name.split('_')
        if len(parts) >= 2:
            task = parts[-1]  # Last part is the task
        else:
            task = group_name  # Fallback
    
    # Save figure with task in filename
    output_path = Path(output_dir) / group_name / f'{task}_{phase}_{metric}{filename_suffix}.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    print(f"  Created: {output_path}")


def create_legend_only(group_df, group_name, output_dir, all_llm_models_in_group, relative_mode=None):
    """
    Create a legend-only PNG file for a specific group.
    
    Args:
        group_df: DataFrame with all data for the group
        group_name: Name of the group (e.g., 'card_averaged', 'time_averaged')
        output_dir: Directory to save the legend PNG
        all_llm_models_in_group: List of ALL LLM models in the group
        relative_mode: None for absolute error, 'pg' for postgres baseline, 'min' for minimum baseline
    """
    print(f"\nCreating legend for {group_name}...")
    
    # Collect all unique algo/model combinations from all metrics and phases
    # We'll use one metric/phase combination to get the full list
    # Use test phase and q50 metric as representative
    phase = 'test'
    metric = 'q50'
    
    # Determine time column
    time_col = 'test_time_ms'
    inference_col = 'llm_test_inference_ms'
    
    # Calculate time_ms
    group_df_copy = group_df.copy()
    group_df_copy['time_ms'] = group_df_copy[time_col].fillna(0) + group_df_copy[inference_col].fillna(0)
    
    # Prepare data
    plot_df = group_df_copy[['time_ms', metric, 'algo', 'model']].copy()
    plot_df.rename(columns={metric: 'error'}, inplace=True)
    
    # Convert to relative error if needed
    if relative_mode:
        try:
            plot_df = convert_to_relative_error(plot_df, error_col='error', mode=relative_mode)
        except ValueError as e:
            print(f"  Warning: Could not convert to relative error: {e}")
            return
    
    # Filter out rows with missing data
    # For PostgreSQL, we only need error (not time_ms), so handle it separately
    postgres_rows = plot_df[plot_df['algo'] == 'postgres'].copy()
    plot_df_no_pg = plot_df[plot_df['algo'] != 'postgres'].copy()
    plot_df_no_pg = plot_df_no_pg.dropna(subset=['time_ms', 'error']).copy()
    
    # For PostgreSQL, only require error (not time_ms)
    postgres_rows = postgres_rows.dropna(subset=['error']).copy()
    
    # Combine back
    plot_df = pd.concat([plot_df_no_pg, postgres_rows], ignore_index=True)
    
    # Filter out inf errors and Qwen without Embedding
    plot_df = plot_df[plot_df['error'] != np.inf].copy()
    
    def is_qwen_without_embedding(row):
        if row['algo'] == 'llm' and pd.notna(row['model']) and row['model']:
            if 'qwen' in row['model'].lower():
                return 'embedding' not in row['model'].lower()
        return False
    
    plot_df = plot_df[~plot_df.apply(is_qwen_without_embedding, axis=1)]
    
    if plot_df.empty:
        print(f"  Warning: No data available for legend in {group_name}")
        return
    
    # Assign colors and markers
    colors = assign_colors_to_dataframe(plot_df, all_llm_models_in_group)
    plot_df['color'] = colors
    markers = assign_markers_to_dataframe(plot_df)
    plot_df['marker'] = markers
    
    # Create legend entries (same logic as create_scatter_plot)
    # Separate PostgreSQL from other entries
    postgres_entry = None
    non_llm_entries = {}
    llm_entries = {}
    
    for idx, row in plot_df.iterrows():
        if row['algo'] != 'llm':
            key = format_algo_name_for_display(row['algo'])
            if key == 'PostgreSQL':
                # Store PostgreSQL separately for line style
                postgres_entry = {'color': row['color']}
            else:
                if key not in non_llm_entries:
                    non_llm_entries[key] = {'color': row['color'], 'time': row['time_ms'], 'marker': row['marker']}
        else:
            key = format_model_name_for_display(row['model'])
            if key not in llm_entries:
                llm_entries[key] = {'color': row['color'], 'model': row['model']}
    
    # Create legend handles and labels
    handles = []
    labels = []
    
    # Add PostgreSQL first with a dotted line style
    if postgres_entry is not None:
        handles.append(plt.Line2D([0], [0], color=postgres_entry['color'], linestyle='--', linewidth=2, alpha=0.7))
        labels.append('PostgreSQL')
    
    # Add other non-LLM entries (sorted by time consumption, fastest to slowest)
    def sort_non_llm_key(item):
        label, entry = item
        return entry['time']
    
    sorted_non_llm = sorted(non_llm_entries.items(), key=sort_non_llm_key)
    for label, entry in sorted_non_llm:
        marker = entry.get('marker', 'o')
        handles.append(plt.Line2D([0], [0], marker=marker, color='w', 
                                  markerfacecolor=entry['color'], markersize=18, markeredgecolor='black', markeredgewidth=0.5, alpha=0.7))
        labels.append(label)
    
    # Add LLM entries
    def get_llm_sort_key(model_name):
        model_lower = model_name.lower()
        if 'sentence' in model_lower or 'bert' in model_lower:
            family_order = 0
            if 'sentence' in model_lower:
                size = 1
            elif 'modernbert' in model_lower or 'BERT' in model_name:
                size = 3
            else:
                size = 2
        elif 'gemma' in model_lower:
            family_order = 1
            size = extract_model_size(model_name) or 0
        elif 'llama' in model_lower:
            family_order = 2
            size = extract_model_size(model_name) or 0
        elif 'qwen' in model_lower and 'embedding' in model_lower:
            family_order = 3
            size = extract_model_size(model_name) or 0
        elif 'qwen' in model_lower:
            family_order = 4
            size = extract_model_size(model_name) or 0
        else:
            family_order = 5
            size = extract_model_size(model_name) or 0
        return (family_order, size)
    
    formatted_to_original = {}
    for idx, row in plot_df.iterrows():
        if row['algo'] == 'llm' and pd.notna(row['model']):
            formatted = format_model_name_for_display(row['model'])
            if formatted not in formatted_to_original:
                formatted_to_original[formatted] = row['model']
    
    sorted_llm = sorted(llm_entries.items(), 
                        key=lambda x: get_llm_sort_key(formatted_to_original.get(x[0], x[0])))
    
    for label, entry in sorted_llm:
        original_model = entry.get('model', formatted_to_original.get(label, label))
        marker = get_marker_for_model('llm', original_model)
        handles.append(plt.Line2D([0], [0], marker=marker, color='w', 
                                  markerfacecolor=entry['color'], markersize=18, markeredgecolor='black', markeredgewidth=0.5, alpha=0.7))
        labels.append(label)
    
    def _render_legend(hs, lbs, out_path, figsize):
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
        legend = ax.legend(hs, lbs, loc='center', ncol=len(hs) if hs else 1,
                           fontsize=20, frameon=True,
                           handletextpad=0.3, labelspacing=0.4, columnspacing=0.5)
        frm = legend.get_frame()
        frm.set_facecolor('white'); frm.set_alpha(1.0)
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        fig.canvas.draw()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, bbox_inches='tight', pad_inches=0.01, facecolor='white')
        plt.close(fig)

    if _MIDWEST_LABEL:
        # Split into 5 separate single-row legends by family.
        baseline_hs, baseline_lbs = [], []
        llama_hs, llama_lbs = [], []
        gemma_hs, gemma_lbs = [], []
        qwen_hs, qwen_lbs = [], []
        bert_hs, bert_lbs = [], []

        for h, lb in zip(handles, labels):
            if lb in ('PostgreSQL', 'Bao', 'E2E-Cost', 'QueryFormer'):
                baseline_hs.append(h); baseline_lbs.append(lb)
                continue
            orig = formatted_to_original.get(lb, lb)
            ol = orig.lower()
            if 'llama' in ol:
                llama_hs.append(h); llama_lbs.append(lb)
            elif 'gemma' in ol:
                gemma_hs.append(h); gemma_lbs.append(lb)
            elif 'qwen' in ol:
                qwen_hs.append(h); qwen_lbs.append(lb)
            elif 'sentence' in ol or 'bert' in ol:
                bert_hs.append(h); bert_lbs.append(lb)

        def _order_baselines(hs, lbs):
            order = {'PostgreSQL': 0, 'Bao': 1, 'E2E-Cost': 2, 'QueryFormer': 3}
            pairs = sorted(zip(hs, lbs), key=lambda p: order.get(p[1], 99))
            return [p[0] for p in pairs], [p[1] for p in pairs]
        baseline_hs, baseline_lbs = _order_baselines(baseline_hs, baseline_lbs)

        subgroups = [
            ('baselines', baseline_hs, baseline_lbs),
            ('llama',     llama_hs,    llama_lbs),
            ('gemma',     gemma_hs,    gemma_lbs),
            ('qwen',      qwen_hs,     qwen_lbs),
            ('bert',      bert_hs,     bert_lbs),
        ]
        for sub_name, hs, lbs in subgroups:
            if not hs:
                print(f"  Skipping empty legend: {group_name}_legend_{sub_name}")
                continue
            out_path = Path(output_dir) / group_name / f'{group_name}_legend_{sub_name}.svg'
            _render_legend(hs, lbs, out_path, figsize=(max(4, 2 * len(hs)), 0.5))
            print(f"  Created legend: {out_path}")
        return

    # Default: single combined legend (unchanged).
    total_entries = len(handles)
    if total_entries <= 8:
        ncol = total_entries
    else:
        ncol = 11
    fig = plt.figure(figsize=(12, 0.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    legend = ax.legend(handles, labels, loc='center', ncol=ncol, fontsize=20, frameon=True,
                      handletextpad=0.3, labelspacing=0.4, columnspacing=0.5)
    legend_frame = legend.get_frame()
    legend_frame.set_facecolor('white')
    legend_frame.set_alpha(1.0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.canvas.draw()
    output_path = Path(output_dir) / group_name / f'{group_name}_legend.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches='tight', pad_inches=0.01, facecolor='white')
    plt.close(fig)
    print(f"  Created legend: {output_path}")


def process_group(group_df, group_name, output_dir, nth_highest=3, relative_mode=None, already_relative=False):
    """Process a group and create all 8 plots."""
    print(f"\nProcessing group: {group_name}")
    
    # Get all LLM models in this group (before any filtering) for consistent color assignment
    all_llm_models_in_group = group_df[group_df['algo'] == 'llm']['model'].dropna().unique().tolist()
    
    metrics = ['q50', 'q90', 'q95', 'qmax']
    phases = ['train', 'test']
    
    for phase in phases:
        # Determine time column
        if phase == 'train':
            time_col = 'train_time_ms'
            inference_col = 'llm_train_inference_ms'
        else:
            time_col = 'test_time_ms'
            inference_col = 'llm_test_inference_ms'
        
        # Calculate total time (sum of time_sum_ms and llm_inference_ms)
        # For training, multiply by 200 epochs
        if phase == 'train':
            group_df['time_ms'] = group_df[time_col].fillna(0) * 200 + group_df[inference_col].fillna(0)
        else:
            group_df['time_ms'] = group_df[time_col].fillna(0) + group_df[inference_col].fillna(0)
        
        for metric in metrics:
            # Prepare data for this plot
            plot_df = group_df[['time_ms', metric, 'algo', 'model']].copy()
            plot_df.rename(columns={metric: 'error'}, inplace=True)
            
            # Create label for each point (algo-model combination)
            plot_df['label'] = plot_df.apply(
                lambda row: f"{row['algo']}-{row['model']}" if pd.notna(row['model']) and row['model'] else row['algo'], 
                axis=1
            )
            
            # Create the plot
            # Pass convert_relative flag: only convert if relative is True and data is not already relative
            create_scatter_plot(
                plot_df,
                phase,
                metric,
                group_name,
                output_dir,
                all_llm_models_in_group,
                nth_highest=nth_highest,
                relative_mode=relative_mode,
                convert_relative=(relative_mode is not None and not already_relative)
            )


def main():
    args = parse_args()
    
    # Read the CSV
    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"Error: Input file {csv_path} not found")
        return
    
    print(f"Reading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows")
    print(f"Grouping by: {args.group_by}")
    
    # Rename columns for consistency
    df.rename(columns={
        'train_time_sum_ms': 'train_time_ms',
        'test_time_sum_ms': 'test_time_ms'
    }, inplace=True)
    
    # Remove job_full/card combination (applies to both grouping modes)
    print("\nFiltering out job_full/card combination...")
    original_len = len(df)
    df = df[~((df['dataset'] == 'job_full') & (df['task'] == 'card'))].copy()
    filtered_count = original_len - len(df)
    print(f"Removed {filtered_count} rows with job_full/card")
    
    # If grouping by task only, automatically average across datasets
    relative_mode = args.relative
    global _MIDWEST_LABEL
    _MIDWEST_LABEL = bool(getattr(args, 'midwest', False))

    if _MIDWEST_LABEL:
        before = len(df)
        df = df[df['algo'] != 'aimai'].copy()
        print(f"[midwest] Dropped {before - len(df)} AiMeetsAi rows")

    if args.group_by == "task":
        # If relative mode, calculate relative error for each dataset first, then average
        if relative_mode:
            print(f"\nCalculating relative error ({relative_mode}) for each dataset before averaging...")
            df_list = []
            for (dataset, task), group in df.groupby(['dataset', 'task']):
                # Make a copy to avoid modifying the view
                group = group.copy()
                # Convert each metric to relative error for this dataset
                for metric in ['q50', 'q90', 'q95', 'qmax']:
                    temp_df = group[['algo', metric]].rename(columns={metric: 'error'})
                    try:
                        converted = convert_to_relative_error(temp_df, error_col='error', mode=relative_mode)
                        group[metric] = converted['error']
                    except ValueError as exc:
                        print(f"    Warning: Skipping {dataset}/{task}/{metric} - {exc}")
                df_list.append(group)
            df = pd.concat(df_list, ignore_index=True)
            print("Relative error calculated for each dataset")
        
        print("\nAveraging Q-error and time across all datasets for each task...")
        # Group by task, algo, model and compute averages
        # Use dropna=False to keep groups where model is NaN (non-LLM algorithms)
        avg_df = df.groupby(['task', 'algo', 'model'], dropna=False).agg({
            'train_time_ms': 'mean',
            'test_time_ms': 'mean',
            'llm_train_inference_ms': 'mean',
            'llm_test_inference_ms': 'mean',
            'q50': 'mean',
            'q90': 'mean',
            'q95': 'mean',
            'qmax': 'mean'
        }).reset_index()
        df = avg_df
        print(f"After averaging: {len(df)} rows (averaged across datasets)")
    
    # Group the data
    if args.group_by == "task":
        groups = df.groupby('task')
    else:  # task_dataset
        groups = df.groupby(['dataset', 'task'])
    
    # Process each group
    output_dir = Path(args.output_dir)
    
    # Adjust output directory name if grouping by task (which averages)
    if args.group_by == "task":
        output_dir = output_dir / "averaged_by_task"
        print(f"Results will be saved to: {output_dir}")
    
    total_groups = len(groups)
    
    print(f"\nFound {total_groups} groups to process")
    
    for group_key, group_df in groups:
        # Create group name
        if args.group_by == "task":
            group_name = f"{str(group_key)}_averaged"
        else:  # task_dataset
            dataset, task = group_key
            group_name = f"{dataset}_{task}"
        
        # Process this group
        # If we're grouping by task and in relative mode, the data is already relative
        already_relative = (args.group_by == "task" and relative_mode is not None)
        process_group(
            group_df,
            group_name,
            output_dir,
            nth_highest=args.outlier_nth,
            relative_mode=relative_mode,
            already_relative=already_relative
        )
    
    print(f"\n✓ All graphs saved to: {output_dir.absolute()}")
    print(f"  Total groups processed: {total_groups}")
    print(f"  Expected total plots: {total_groups * 8}")
    
    # Generate legend-only PNG files for card_averaged and time_averaged
    if args.group_by == "task":
        print(f"\n{'='*60}")
        print("Generating legend-only PNG files...")
        print(f"{'='*60}")
        
        for task_name in ['card', 'time']:
            group_name = f"{task_name}_averaged"
            # Get the group data
            if task_name in df['task'].values:
                group_df = df[df['task'] == task_name].copy()
                # Get all LLM models in this group
                all_llm_models_in_group = group_df[group_df['algo'] == 'llm']['model'].dropna().unique().tolist()
                
                # Create legend
                create_legend_only(
                    group_df,
                    group_name,
                    output_dir,
                    all_llm_models_in_group,
                    relative_mode=relative_mode
                )
            else:
                print(f"  Warning: {task_name} task not found, skipping legend generation")


if __name__ == "__main__":
    main()

