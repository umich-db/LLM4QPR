#!/usr/bin/env python3
"""
Script to analyze the relationship between LLM model size and error.
Compares smallest, middle, and largest models within each LLM family
and calculates error differences, then averages across families.

Usage:
    python analyze_llm_size_vs_error.py [--input combined_timing_accuracy_report.csv] [--relative min|pg] [--x_axis rank|inference_time]
"""

import os
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import re
from collections import defaultdict
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.metrics import r2_score


def setup_mpl_params():
    """Setup matplotlib parameters to match generate_slim_plots.py style"""
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams['ps.useafm'] = True
    mpl.rcParams['pdf.use14corefonts'] = True
    mpl.rcParams['xtick.labelsize'] = 20
    mpl.rcParams['ytick.labelsize'] = 20
    # Enable LaTeX rendering for math expressions
    mpl.rcParams['text.usetex'] = False  # Use matplotlib's built-in LaTeX renderer instead
    mpl.rcParams['mathtext.default'] = 'regular'  # Use regular math text
    plt.style.use('seaborn-v0_8-ticks')


# Setup matplotlib parameters at module level
setup_mpl_params()


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


def get_llm_family(model_name):
    """
    Determine LLM family from model name.
    Returns: 'gemma', 'llama', 'qwen_embedding', 'qwen', 'bert', or 'other'
    """
    if not model_name:
        return 'other'
    
    model_lower = model_name.lower()
    
    if 'gemma' in model_lower:
        return 'gemma'
    elif 'llama' in model_lower:
        return 'llama'
    elif 'qwen' in model_lower:
        if 'embedding' in model_lower:
            return 'qwen_embedding'
        else:
            return 'qwen'
    elif 'bert' in model_lower or 'modernbert' in model_lower or 'sentence-transformers' in model_lower:
        return 'bert'
    else:
        return 'other'


def convert_to_relative_error(df, error_col='error', mode='pg'):
    """
    Convert errors to relative errors.
    
    Args:
        df: DataFrame with error column and algo column
        error_col: Name of the error column
        mode: 'pg' to use postgres as baseline,
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


def analyze_llm_families(df, metrics=['q50', 'q90', 'q95', 'qmax'], relative_mode=None):
    """
    Analyze error differences between smallest, middle, and largest models in each LLM family.
    
    Args:
        df: DataFrame with columns [dataset, task, algo, model, q50, q90, q95, qmax]
        metrics: List of metrics to analyze
        relative_mode: None for absolute error, 'pg' for postgres baseline, 'min' for minimum baseline
    
    Returns:
        Dictionary with analysis results
    """
    # Filter for LLM algorithms only
    llm_df = df[df['algo'] == 'llm'].copy()
    
    if llm_df.empty:
        print("No LLM data found")
        return {}
    
    # Add family and size information
    llm_df['family'] = llm_df['model'].apply(get_llm_family)
    llm_df['size'] = llm_df['model'].apply(extract_model_size)
    
    # Filter out models without size information or in 'other' family
    llm_df = llm_df[llm_df['size'].notna() & (llm_df['family'] != 'other')].copy()
    
    # Group by dataset, task, and family
    results = {}
    
    for (dataset, task, family), group in llm_df.groupby(['dataset', 'task', 'family']):
        # Skip job_full/card combination (not used in card estimation)
        if dataset == 'job_full' and task == 'card':
            continue
        
        # Sort by size
        group_sorted = group.sort_values('size')
        
        # Need at least 2 models to compare adjacent sizes
        if len(group_sorted) < 2:
            continue
        
        # Calculate relative error if needed
        for metric in metrics:
            if metric not in group_sorted.columns:
                continue
            
            # Get error values and inference times for all models
            model_errors = []
            for idx, row in group_sorted.iterrows():
                error_val = row[metric]
                if pd.isna(error_val) or np.isinf(error_val):
                    continue
                
                # Calculate inference time: test_time_ms + llm_test_inference_ms
                test_time = row.get('test_time_ms', 0) if pd.notna(row.get('test_time_ms')) else 0
                llm_inference_time = row.get('llm_test_inference_ms', 0) if pd.notna(row.get('llm_test_inference_ms')) else 0
                inference_time = test_time + llm_inference_time
                
                model_errors.append({
                    'model': row['model'],
                    'size': row['size'],
                    'error': error_val,
                    'inference_time': inference_time
                })
            
            # Skip if we don't have at least 2 valid errors
            if len(model_errors) < 2:
                continue
            
            # Convert to relative error if requested
            if relative_mode:
                # Prepare data for relative error calculation (all models in this group + postgres)
                metric_df = group_sorted[['algo', 'model', metric]].copy()
                metric_df.rename(columns={metric: 'error'}, inplace=True)
                
                # Add postgres if available
                postgres_row = df[(df['dataset'] == dataset) & 
                                 (df['task'] == task) & 
                                 (df['algo'] == 'postgres')]
                if not postgres_row.empty and metric in postgres_row.columns:
                    postgres_data = pd.DataFrame({
                        'algo': ['postgres'],
                        'model': [None],
                        'error': [postgres_row[metric].iloc[0]]
                    })
                    metric_df = pd.concat([metric_df, postgres_data], ignore_index=True)
                
                try:
                    metric_df = convert_to_relative_error(metric_df, error_col='error', mode=relative_mode)
                    
                    # Update error values from relative error calculation
                    for model_error in model_errors:
                        model_name = model_error['model']
                        rel_error_row = metric_df[metric_df['model'] == model_name]
                        if not rel_error_row.empty:
                            model_error['error'] = rel_error_row['error'].iloc[0]
                        else:
                            model_error['error'] = None
                    
                    # Remove models with None error
                    model_errors = [me for me in model_errors if me['error'] is not None]
                    
                    if len(model_errors) < 2:
                        continue
                except ValueError as e:
                    print(f"Warning: Could not convert to relative error for {dataset}/{task}/{family}/{metric}: {e}")
                    continue
            
            # Calculate differences between adjacent sizes
            adjacent_differences = []
            for i in range(len(model_errors) - 1):
                smaller = model_errors[i]
                larger = model_errors[i + 1]
                diff = larger['error'] - smaller['error']
                adjacent_differences.append({
                    'from_model': smaller['model'],
                    'from_size': smaller['size'],
                    'from_error': smaller['error'],
                    'to_model': larger['model'],
                    'to_size': larger['size'],
                    'to_error': larger['error'],
                    'difference': diff,
                    'transition': f"{i+1}_to_{i+2}"
                })
            
            # Store error values and inference times at each position for plotting
            position_errors = {}
            position_times = {}
            for i, model_error in enumerate(model_errors):
                position = i + 1  # Position 1, 2, 3, 4, etc.
                position_errors[position] = model_error['error']
                position_times[position] = model_error['inference_time']
            
            # Store results with all adjacent differences and position errors/times
            key = (dataset, task, family, metric)
            results[key] = {
                'num_models': len(model_errors),
                'adjacent_differences': adjacent_differences,
                'position_errors': position_errors,  # {position: error_value}
                'position_times': position_times,  # {position: inference_time}
            }
    
    return results


def aggregate_results(results):
    """
    Aggregate results by averaging across datasets, separately for time and card tasks.
    For time estimation: averages across 6 datasets (job, job_full, syn, stats, tpch, tpcds)
    For card estimation: averages across 3 datasets (job, syn, stats)
    
    Args:
        results: Dictionary from analyze_llm_families
    
    Returns:
        Dictionary with aggregated statistics, separated by task
    """
    # Filter out job_full/card combination (not used in card estimation)
    filtered_results = {}
    for (dataset, task, family, metric), data in results.items():
        if dataset == 'job_full' and task == 'card':
            continue  # Skip job_full/card
        filtered_results[(dataset, task, family, metric)] = data
    
    # Log which datasets are being used for each task
    datasets_by_task = defaultdict(set)
    for (dataset, task, family, metric), data in filtered_results.items():
        datasets_by_task[task].add(dataset)
    
    print("\n" + "="*80)
    print("Dataset Usage for Aggregation:")
    print("="*80)
    for task in ['time', 'card']:
        datasets = sorted(datasets_by_task.get(task, set()))
        expected_count = 6 if task == 'time' else 3
        actual_count = len(datasets)
        print(f"{task.upper()} estimation: {actual_count} dataset(s) - {', '.join(datasets)}")
        if actual_count != expected_count:
            print(f"  WARNING: Expected {expected_count} datasets, found {actual_count}")
    print("="*80 + "\n")
    
    # Group by metric, task, and family, preserving dataset information
    by_metric_task_family = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    # Track datasets for each family
    family_datasets = defaultdict(lambda: defaultdict(set))  # {task: {family: {datasets}}}
    
    for (dataset, task, family, metric), data in filtered_results.items():
        by_metric_task_family[metric][task][family].append(data)
        family_datasets[task][family].add(dataset)
    
    # Calculate averages
    aggregated = {}
    
    for metric in ['q50', 'q90', 'q95', 'qmax']:
        if metric not in by_metric_task_family:
            continue
        
        aggregated[metric] = {}
        
        # Process each task separately
        for task in ['time', 'card']:
            if task not in by_metric_task_family[metric]:
                continue
            
            aggregated[metric][task] = {}
            
            # Per-family averages for this task
            for family, family_data in by_metric_task_family[metric][task].items():
                if len(family_data) == 0:
                    continue
                
                # Get datasets used for this family/task combination
                datasets_used = family_datasets[task].get(family, set())
                
                # Collect all adjacent differences by transition position
                transition_diffs = defaultdict(list)  # {transition: [differences]}
                # Collect errors by position
                position_errors_by_family = defaultdict(list)  # {position: [errors]}
                # Collect inference times by position
                position_times_by_family = defaultdict(list)  # {position: [inference_times]}
                
                for data in family_data:
                    for adj_diff in data['adjacent_differences']:
                        transition = adj_diff['transition']
                        transition_diffs[transition].append(adj_diff['difference'])
                    
                    # Collect position errors
                    for position, error_val in data.get('position_errors', {}).items():
                        position_errors_by_family[position].append(error_val)
                    
                    # Collect position inference times
                    for position, time_val in data.get('position_times', {}).items():
                        position_times_by_family[position].append(time_val)
                
                # Calculate averages for each transition
                # num_observations is the number of dataset/family/metric combinations
                family_agg = {
                    'num_observations': len(family_data),
                    'num_datasets': len(datasets_used),
                    'datasets': sorted(datasets_used),
                }
                for transition, diffs in transition_diffs.items():
                    family_agg[transition] = np.mean(diffs)
                
                # Calculate average error at each position
                for position, errors in position_errors_by_family.items():
                    family_agg[f'pos_{position}_error'] = np.mean(errors)
                
                # Calculate average inference time at each position
                for position, times in position_times_by_family.items():
                    family_agg[f'pos_{position}_time'] = np.mean(times)
                
                aggregated[metric][task][family] = family_agg
            
            # Overall average across all families for this task
            all_transition_diffs = defaultdict(list)  # {transition: [all differences]}
            all_datasets_used = set()
            
            for family_data in by_metric_task_family[metric][task].values():
                for data in family_data:
                    for adj_diff in data['adjacent_differences']:
                        transition = adj_diff['transition']
                        all_transition_diffs[transition].append(adj_diff['difference'])
            
            # Collect all datasets used across all families for this task
            for (ds, ts, fam, met), data in filtered_results.items():
                if ts == task and met == metric:
                    all_datasets_used.add(ds)
            
            if len(all_transition_diffs) > 0:
                overall_agg = {
                    'num_observations': sum(len(family_data) for family_data in by_metric_task_family[metric][task].values()),
                    'num_datasets': len(all_datasets_used),
                    'datasets': sorted(all_datasets_used),
                }
                for transition, diffs in all_transition_diffs.items():
                    overall_agg[transition] = np.mean(diffs)
                aggregated[metric][task]['overall'] = overall_agg
    
    return aggregated


def print_results(results, aggregated):
    """
    Print analysis results in a readable format.
    """
    print("\n" + "="*80)
    print("LLM Model Size vs Error Analysis")
    print("="*80)
    
    print("\nDetailed Results (per dataset/task/family):")
    print("-"*80)
    
    for (dataset, task, family, metric), data in sorted(results.items()):
        print(f"\n{dataset}/{task}/{family}/{metric} ({data['num_models']} models):")
        for adj_diff in data['adjacent_differences']:
            print(f"  {adj_diff['from_model']} ({adj_diff['from_size']}B) → {adj_diff['to_model']} ({adj_diff['to_size']}B): {adj_diff['difference']:+.4f}")
    
    print("\n" + "="*80)
    print("Aggregated Results (averaged across datasets/tasks)")
    print("="*80)
    
    for metric in ['q50', 'q90', 'q95', 'qmax']:
        if metric not in aggregated:
            continue
        
        print(f"\n{metric.upper()} Error:")
        print("="*80)
        
        # Process each task separately
        for task in ['time', 'card']:
            if task not in aggregated[metric]:
                continue
            
            print(f"\n{task.upper()} Estimation:")
            print("-"*80)
            
            # Per-family results
            for family in sorted(aggregated[metric][task].keys()):
                if family == 'overall':
                    continue
                
                data = aggregated[metric][task][family]
                print(f"\n  {family.upper()} Family (n={data['num_observations']}, datasets={data.get('num_datasets', 'N/A')}):")
                # Print transitions in order (1_to_2, 2_to_3, 3_to_4, etc.)
                # Exclude metadata keys: num_observations, num_datasets, datasets, and position errors
                transitions = sorted([k for k in data.keys() 
                                    if k not in ['num_observations', 'num_datasets', 'datasets'] 
                                    and not k.startswith('pos_') 
                                    and '_to_' in k], 
                                    key=lambda x: (int(x.split('_')[0]), int(x.split('_')[2])))
                for transition in transitions:
                    print(f"    {transition}: {data[transition]:+.4f}")
            
            # Overall average
            if 'overall' in aggregated[metric][task]:
                data = aggregated[metric][task]['overall']
                print(f"\n  OVERALL AVERAGE (n={data['num_observations']}):")
                # Exclude metadata keys: num_observations, num_datasets, datasets, and position errors
                transitions = sorted([k for k in data.keys() 
                                    if k not in ['num_observations', 'num_datasets', 'datasets'] 
                                    and not k.startswith('pos_')
                                    and '_to_' in k],
                                    key=lambda x: (int(x.split('_')[0]), int(x.split('_')[2])))
                for transition in transitions:
                    print(f"    {transition}: {data[transition]:+.4f}")


def fit_linear_regression(x: np.ndarray, y: np.ndarray):
    """Fit classic linear regression and return model and R² score."""
    if len(x) < 2:
        return None, 0.0
    
    X = x.reshape(-1, 1)
    y_vals = y
    
    # Remove NaN values only
    valid_mask = ~(np.isnan(X.flatten()) | np.isnan(y_vals))
    X_clean = X[valid_mask]
    y_clean = y_vals[valid_mask]
    
    if len(X_clean) < 2:
        return None, 0.0
    
    # Fit linear regression
    reg = LinearRegression()
    reg.fit(X_clean, y_clean)
    
    y_pred = reg.predict(X_clean)
    r2 = r2_score(y_clean, y_pred)
    
    return reg, r2


def fit_huber_regression(x: np.ndarray, y: np.ndarray):
    """Fit Huber regression and return model and R² score."""
    if len(x) < 2:
        return None, 0.0
    
    X = x.reshape(-1, 1)
    y_vals = y
    
    # Remove NaN values only
    valid_mask = ~(np.isnan(X.flatten()) | np.isnan(y_vals))
    X_clean = X[valid_mask]
    y_clean = y_vals[valid_mask]
    
    if len(X_clean) < 2:
        return None, 0.0
    
    # Fit Huber regression on all data (including outliers)
    reg = HuberRegressor()
    reg.fit(X_clean, y_clean)
    
    y_pred = reg.predict(X_clean)
    r2 = r2_score(y_clean, y_pred)
    
    return reg, r2


def plot_error_trends(aggregated, output_dir=None, relative_mode=None, regression_type='linear', x_axis='rank'):
    """
    Plot error trends by model size position (1, 2, 3, 4) or inference time, averaging across families.
    Each graph shows 3 quantiles (q50, q90, q95) with separate graphs for time and card.
    
    Args:
        aggregated: Dictionary from aggregate_results
        output_dir: Directory to save plots (optional)
        relative_mode: Relative error mode for filename
        regression_type: Type of regression ('linear' or 'huber')
        x_axis: 'rank' for model size rank (1,2,3,4) or 'inference_time' for average inference time
    """
    # Color map for quantiles (matching generate_slim_plots.py)
    quantile_colors = {
        'q50': 'blue',
        'q90': 'orange',
        'q95': 'red',
    }
    
    # Marker map for quantiles (matching generate_slim_plots.py)
    quantile_markers = {
        'q50': 'o',  # Circle
        'q90': 's',  # Square
        'q95': '^',  # Triangle
    }
    
    # Store x-axis values for printing at the end
    x_axis_data = {}  # {task: [x_values]}
    
    # Create separate plots for time and card
    for task in ['time', 'card']:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        
        # Store scatter and line objects for legend
        scatter_50 = None
        line_50 = None
        scatter_90 = None
        line_90 = None
        scatter_95 = None
        line_95 = None
        
        # Collect all x-values for setting x-axis limits when using inference_time
        all_x_values = []
        
        # Process each quantile (excluding qmax)
        for metric in ['q50', 'q90', 'q95']:
            if metric not in aggregated:
                continue
            if task not in aggregated[metric]:
                continue
            
            # Collect position errors and times across all families for this metric and task
            position_errors_dict = defaultdict(list)  # {position: [errors from all families]}
            position_times_dict = defaultdict(list)  # {position: [inference_times from all families]}
            
            for family in aggregated[metric][task].keys():
                if family == 'overall':
                    continue
                
                data = aggregated[metric][task][family]
                
                # Extract position errors and inference times
                for key, value in data.items():
                    if key.startswith('pos_') and key.endswith('_error'):
                        position = int(key.replace('pos_', '').replace('_error', ''))
                        position_errors_dict[position].append(value)
                    elif key.startswith('pos_') and key.endswith('_time'):
                        position = int(key.replace('pos_', '').replace('_time', ''))
                        position_times_dict[position].append(value)
            
            if not position_errors_dict:
                continue
            
            # Calculate average error at each position across all families
            positions = []
            avg_errors = []
            avg_times = []
            for position in sorted(position_errors_dict.keys()):
                errors = position_errors_dict[position]
                # Average across families
                avg_error = np.mean(errors)
                positions.append(position)
                avg_errors.append(avg_error)
                
                # Calculate average inference time at this position (if available)
                if position in position_times_dict:
                    times = position_times_dict[position]
                    avg_time = np.mean(times)
                    avg_times.append(avg_time)
                else:
                    avg_times.append(None)
            
            if not positions:
                continue
            
            # Choose x-axis values based on x_axis parameter
            if x_axis == 'inference_time':
                # Use inference times, but filter out None values
                x_values = []
                y_values = []
                for i, (pos, err, time) in enumerate(zip(positions, avg_errors, avg_times)):
                    if time is not None and not np.isnan(time) and time > 0:
                        x_values.append(time)
                        y_values.append(err)
                
                if len(x_values) == 0:
                    continue  # Skip this metric if no valid inference times
                
                x_arr = np.array(x_values)
                y_arr = np.array(y_values)
                # Collect x-values for setting axis limits
                all_x_values.extend(x_values)
                # Store x-values for this task (will be deduplicated later)
                if task not in x_axis_data:
                    x_axis_data[task] = []
                x_axis_data[task].extend(x_values)
            else:  # x_axis == 'rank'
                # Use positions (1, 2, 3, 4)
                x_arr = np.array(positions)
                y_arr = np.array(avg_errors)
            
            # Fit regression based on selected type
            if regression_type == 'huber':
                reg, r2 = fit_huber_regression(x_arr, y_arr)
            else:  # default to linear
                reg, r2 = fit_linear_regression(x_arr, y_arr)
            
            # Plot with quantile-specific color and marker (matching generate_slim_plots.py style)
            color = quantile_colors.get(metric, 'gray')
            marker = quantile_markers.get(metric, 'o')
            
            # Plot the data points (matching generate_slim_plots.py style)
            scatter = ax.scatter(x_arr, y_arr, marker=marker, color=color, s=150, 
                     zorder=3, edgecolors='black', linewidths=0.5)
            
            # Store scatter objects for legend
            if metric == 'q50':
                scatter_50 = scatter
            elif metric == 'q90':
                scatter_90 = scatter
            elif metric == 'q95':
                scatter_95 = scatter
            
            # Plot the regression line if we have a valid model (matching generate_slim_plots.py style)
            if reg is not None and len(x_arr) > 0:
                # Create smooth line for plotting
                x_line = np.linspace(x_arr.min(), x_arr.max(), 100)
                y_line = reg.predict(x_line.reshape(-1, 1))
                line = ax.plot(x_line, y_line, color=color, linestyle='-', alpha=0.6, 
                       linewidth=2)[0]
                
                # Store line objects for legend
                if metric == 'q50':
                    line_50 = line
                elif metric == 'q90':
                    line_90 = line
                elif metric == 'q95':
                    line_95 = line
        
        # Formatting (matching generate_slim_plots.py style)
        if x_axis == 'inference_time':
            ax.set_xlabel('Time (ms)', fontsize=24, weight='bold')
        else:
            ax.set_xlabel('Model Size Rank', fontsize=24, weight='bold')
        ylabel = 'Relative Q-Error'
        # if relative_mode:
        #     ylabel += f' (Relative, {relative_mode})'
        ax.set_ylabel(ylabel, fontsize=24, weight='bold')
        # No title (matching generate_slim_plots.py)
        
        # Set x-axis ticks and limits based on x_axis parameter
        if x_axis == 'inference_time':
            # Set x-axis limits to start at 0 and cover all data points with padding on the right
            if len(all_x_values) > 0:
                all_x_array = np.array(all_x_values)
                x_max = np.max(all_x_array)
                # Add 5% padding on the right side, but start at 0
                padding = max(x_max * 0.05, x_max * 0.01)  # At least 1% of max value as padding
                ax.set_xlim(0, x_max + padding)
            else:
                # If no data, still set lower limit to 0
                ax.set_xlim(0, 1)
            # Auto-scale for inference time (no fixed ticks)
            ax.tick_params(axis='x', labelsize=20)
        else:
            # Fixed ticks for model rank
            ax.set_xticks([1, 2, 3, 4])
            ax.set_xticklabels(['1', '2', '3', '4'], fontsize=20)
            ax.set_xlim(0.5, 4.5)
        
        # Create legend with 3 columns: each column has percentile + fit
        # Arrange handles in strict order: percentile, fit, percentile, fit, percentile, fit
        handles = []
        labels = []
        
        # Strict order: percentile followed by its fit, repeated for each
        if scatter_50 is not None:
            handles.append(scatter_50)
            labels.append('50th percentile')
        if line_50 is not None:
            handles.append(line_50)
            labels.append('50th fit')
        
        if scatter_90 is not None:
            handles.append(scatter_90)
            labels.append('90th percentile')
        if line_90 is not None:
            handles.append(line_90)
            labels.append('90th fit')
        
        if scatter_95 is not None:
            handles.append(scatter_95)
            labels.append('95th percentile')
        if line_95 is not None:
            handles.append(line_95)
            labels.append('95th fit')
        
        # Temporarily don't show legend (matching generate_slim_plots.py)
        # ax.legend(handles, labels, bbox_to_anchor=(0.5, 1.02), loc='lower center', 
        #           ncol=3, fontsize=20, frameon=True)
        
        ax.grid(True, alpha=0.3)
        
        # Set y-axis limits with outlier handling (similar to generate_slim_plots.py)
        all_y_values = []
        for metric in ['q50', 'q90', 'q95']:
            if metric not in aggregated or task not in aggregated[metric]:
                continue
            
            # Collect position errors across all families for this metric and task
            position_errors_dict = defaultdict(list)
            for family in aggregated[metric][task].keys():
                if family == 'overall':
                    continue
                data = aggregated[metric][task][family]
                for key, value in data.items():
                    if key.startswith('pos_') and key.endswith('_error'):
                        position_errors_dict[int(key.replace('pos_', '').replace('_error', ''))].append(value)
            
            # Calculate average error at each position
            for position in sorted(position_errors_dict.keys()):
                errors = position_errors_dict[position]
                avg_error = np.mean(errors)
                all_y_values.append(avg_error)
        
        all_y_values = np.array(all_y_values)
        all_y_values = all_y_values[~np.isnan(all_y_values)]
        
        if len(all_y_values) > 0:
            q1 = np.percentile(all_y_values, 25)
            q3 = np.percentile(all_y_values, 75)
            iqr = q3 - q1
            
            if iqr > 0:
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = (all_y_values < lower_bound) | (all_y_values > upper_bound)
                if np.any(outliers):
                    y_max_capped = min(upper_bound * 2, np.percentile(all_y_values, 95) * 1.5)
                    y_min_orig = max(0, np.min(all_y_values))
                    y_min = 1.05 * y_min_orig - 0.05 * y_max_capped
                    ax.set_ylim(y_min, y_max_capped)
                else:
                    y_max = np.max(all_y_values) * 1.1
                    y_min_orig = max(0, np.min(all_y_values))
                    y_min = 1.05 * y_min_orig - 0.05 * y_max
                    ax.set_ylim(y_min, y_max)
            else:
                y_max = np.max(all_y_values) * 1.1
                y_min_orig = max(0, np.min(all_y_values))
                y_min = 1.05 * y_min_orig - 0.05 * y_max
                ax.set_ylim(y_min, y_max)
        
        plt.tight_layout()
        
        # Save figure (matching generate_slim_plots.py DPI)
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            rel_suffix = f"_{relative_mode}" if relative_mode else ""
            x_suffix = f"_{x_axis}" if x_axis != 'rank' else ""
            filename = f"error_trend_by_position_{task}{rel_suffix}{x_suffix}.pdf"
            filepath = output_path / filename
            plt.savefig(filepath, bbox_inches='tight')
            print(f"  Saved plot to: {filepath}")
        else:
            plt.show()
        
        plt.close(fig)
    
    # Print x-axis values and relative numbers at the end
    if x_axis == 'inference_time' and x_axis_data:
        print("\n" + "="*80)
        print("X-Axis Values (Inference Time) and Relative to Minimum:")
        print("="*80)
        for task in ['time', 'card']:
            if task not in x_axis_data or len(x_axis_data[task]) == 0:
                continue
            
            # Get unique sorted x-values for this task
            x_values = sorted(set(x_axis_data[task]))
            if len(x_values) == 0:
                continue
            
            x_min = min(x_values)
            
            print(f"\n{task.upper()} Estimation:")
            print(f"  X-axis values (ms): {[f'{x:.2f}' for x in x_values]}")
            print(f"  Relative to minimum ({x_min:.2f} ms): {[f'{x/x_min:.2f}' for x in x_values]}")
            
            # Print detailed breakdown showing the reduction
            print(f"\n  DETAILED BREAKDOWN - Tracing the 7x → 2x reduction:")
            print(f"  {'-'*76}")
            
            # Show per-family values at each position
            for metric in ['q50']:  # Just show q50 for clarity
                if metric not in aggregated or task not in aggregated[metric]:
                    continue
                
                # Collect position times by family
                family_position_times = defaultdict(dict)  # {family: {position: time}}
                for family in sorted(aggregated[metric][task].keys()):
                    if family == 'overall':
                        continue
                    data = aggregated[metric][task][family]
                    for key, value in data.items():
                        if key.startswith('pos_') and key.endswith('_time'):
                            position = int(key.replace('pos_', '').replace('_time', ''))
                            family_position_times[family][position] = value
                
                # Show per-family ratios and values
                print(f"\n  Per-family values and ratios:")
                for family in sorted(family_position_times.keys()):
                    times = family_position_times[family]
                    rank4_str = f"{times[4]:12.2f} ms" if 4 in times else "N/A"
                    rank3_str = f"{times[3]:12.2f} ms" if 3 in times else "N/A"
                    if 4 in times and 3 in times:
                        ratio = times[4] / times[3]
                        print(f"    {family:15s} | Rank 4: {rank4_str:>15s} | Rank 3: {rank3_str:>15s} | Ratio: {ratio:.2f}x")
                    else:
                        # Show values even if ratio can't be calculated
                        ratio_str = "N/A (no rank 4)" if 4 not in times else "N/A (no rank 3)"
                        print(f"    {family:15s} | Rank 4: {rank4_str:>15s} | Rank 3: {rank3_str:>15s} | Ratio: {ratio_str}")
                
                # Show final averaged values
                print(f"\n  Final averaged values (across all families):")
                position_avg_times = defaultdict(list)
                for family, times in family_position_times.items():
                    for pos, time_val in times.items():
                        position_avg_times[pos].append(time_val)
                
                for pos in sorted(position_avg_times.keys()):
                    if pos >= 3:
                        avg_time = np.mean(position_avg_times[pos])
                        families = ', '.join([f for f in family_position_times.keys() if pos in family_position_times[f]])
                        print(f"    Rank {pos}: {avg_time:12.2f} ms (from: {families})")
                
                # Calculate final ratio
                if 4 in position_avg_times and 3 in position_avg_times:
                    rank4_avg = np.mean(position_avg_times[4])
                    rank3_avg = np.mean(position_avg_times[3])
                    final_ratio = rank4_avg / rank3_avg
                    print(f"\n  Final ratio (Rank 4 / Rank 3): {final_ratio:.2f}x")
                    print(f"  This is the result of averaging across families with different ratios!")
        print("="*80 + "\n")


def create_legend_only(output_dir, task, relative_mode=None):
    """
    Create a legend-only PNG file for error trend plots.
    
    Args:
        output_dir: Directory to save the legend PNG
        task: Task name ('card' or 'time')
        relative_mode: Relative error mode for filename suffix
    """
    print(f"\nCreating legend for error trend plots ({task})...")
    
    # Create legend handles and labels (matching generate_slim_plots.py)
    handles = []
    labels = []
    
    # 50th percentile (blue circle)
    handles.append(plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor='blue', markersize=18, 
                              markeredgecolor='black', markeredgewidth=0.5))
    labels.append('50th percentile')
    
    # 50th fit (blue solid line)
    handles.append(plt.Line2D([0], [0], color='blue', linestyle='-', 
                              linewidth=2, alpha=0.6))
    labels.append('50th fit')
    
    # 90th percentile (orange square)
    handles.append(plt.Line2D([0], [0], marker='s', color='w', 
                              markerfacecolor='orange', markersize=18, 
                              markeredgecolor='black', markeredgewidth=0.5))
    labels.append('90th percentile')
    
    # 90th fit (orange solid line)
    handles.append(plt.Line2D([0], [0], color='orange', linestyle='-', 
                              linewidth=2, alpha=0.6))
    labels.append('90th fit')
    
    # 95th percentile (red triangle)
    handles.append(plt.Line2D([0], [0], marker='^', color='w', 
                              markerfacecolor='red', markersize=18, 
                              markeredgecolor='black', markeredgewidth=0.5))
    labels.append('95th percentile')
    
    # 95th fit (red solid line)
    handles.append(plt.Line2D([0], [0], color='red', linestyle='-', 
                              linewidth=2, alpha=0.6))
    labels.append('95th fit')
    
    # Determine number of columns for legend (3 columns to match the plot layout)
    ncol = 3
    
    # Create figure with just the legend
    fig = plt.figure(figsize=(12, 0.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')  # Hide axes
    
    # Create legend with spacing between rows
    legend = ax.legend(handles, labels, loc='center', ncol=ncol, fontsize=20, frameon=True,
                      handletextpad=0.3, labelspacing=0.4, columnspacing=0.5)
    
    # Ensure legend frame is visible (using default edge color and linewidth)
    legend_frame = legend.get_frame()
    legend_frame.set_facecolor('white')
    legend_frame.set_alpha(1.0)  # Ensure fully opaque
    
    # Remove all margins and padding from subplot
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Render to ensure legend is drawn
    fig.canvas.draw()
    
    # Save legend with small padding to ensure frame border is fully visible
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    rel_suffix = f"_{relative_mode}" if relative_mode else ""
    filename = f"error_trend_by_position_{task}{rel_suffix}_legend.pdf"
    filepath = output_path / filename
    fig.savefig(filepath, bbox_inches='tight', pad_inches=0.01, facecolor='white')
    plt.close(fig)
    
    print(f"  Created legend: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Analyze LLM model size vs error relationship")
    parser.add_argument("--input", type=str, default="combined_timing_accuracy_report.csv",
                        help="Input CSV file (default: combined_timing_accuracy_report.csv)")
    parser.add_argument("--relative", type=str, choices=["pg", "min"], default=None,
                        help="Use relative error. 'pg' for postgres baseline, 'min' for minimum baseline.")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV file (optional)")
    parser.add_argument("--plot_dir", type=str, default=None,
                        help="Directory to save plots (optional)")
    parser.add_argument("--regression", type=str, default='linear', choices=['linear', 'huber'],
                        help="Regression type: 'linear' (default) or 'huber'")
    parser.add_argument("--x_axis", type=str, default='rank', choices=['rank', 'inference_time'],
                        help="X-axis type: 'rank' for model size rank (default) or 'inference_time' for average inference time")
    
    args = parser.parse_args()
    
    # Read the CSV
    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"Error: Input file {csv_path} not found")
        return
    
    print(f"Reading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Rename columns for consistency
    if 'train_time_sum_ms' in df.columns:
        df.rename(columns={
            'train_time_sum_ms': 'train_time_ms',
            'test_time_sum_ms': 'test_time_ms'
        }, inplace=True)
    
    print(f"Loaded {len(df)} rows")
    
    # Calculate relative error if requested
    relative_mode = args.relative
    if relative_mode:
        print(f"\nCalculating relative error ({relative_mode}) for each dataset/task...")
        df_list = []
        for (dataset, task), group in df.groupby(['dataset', 'task']):
            group = group.copy()
            for metric in ['q50', 'q90', 'q95', 'qmax']:
                temp_df = group[['algo', metric]].rename(columns={metric: 'error'})
                try:
                    converted = convert_to_relative_error(temp_df, error_col='error', mode=relative_mode)
                    group[metric] = converted['error']
                except ValueError as exc:
                    print(f"    Warning: Skipping {dataset}/{task}/{metric} - {exc}")
            df_list.append(group)
        df = pd.concat(df_list, ignore_index=True)
        print("Relative error calculated")
    
    # Analyze LLM families
    print("\nAnalyzing LLM families...")
    results = analyze_llm_families(df, metrics=['q50', 'q90', 'q95', 'qmax'], relative_mode=relative_mode)
    
    if not results:
        print("No results found. Make sure there are LLM models with size information in the data.")
        return
    
    # Aggregate results
    aggregated = aggregate_results(results)
    
    # Print results
    print_results(results, aggregated)
    
    # Plot error trends if requested
    if args.plot_dir:
        print("\nGenerating error trend plots...")
        plot_error_trends(aggregated, output_dir=args.plot_dir, relative_mode=relative_mode, 
                         regression_type=args.regression, x_axis=args.x_axis)
        
        # Generate legend-only PNG files for each task
        print(f"\n{'='*60}")
        print("Generating legend-only PNG files...")
        print(f"{'='*60}")
        
        for task in ['time', 'card']:
            # Check if we have data for this task
            has_data = False
            for metric in ['q50', 'q90', 'q95']:
                if metric in aggregated and task in aggregated[metric]:
                    has_data = True
                    break
            
            if has_data:
                create_legend_only(args.plot_dir, task, relative_mode=relative_mode)
    
    # Save to CSV if requested
    if args.output:
        # Create DataFrame from aggregated results
        output_data = []
        for metric in ['q50', 'q90', 'q95', 'qmax']:
            if metric not in aggregated:
                continue
            for task in ['time', 'card']:
                if task not in aggregated[metric]:
                    continue
                for family, data in aggregated[metric][task].items():
                    row = {
                        'metric': metric,
                        'task': task,
                        'family': family,
                        'num_observations': data['num_observations'],
                        'num_datasets': data.get('num_datasets', ''),
                        'datasets': ', '.join(data.get('datasets', [])) if data.get('datasets') else ''
                    }
                    # Add all transition columns (1_to_2, 2_to_3, etc.) - exclude position errors and metadata
                    transitions = sorted([k for k in data.keys() 
                                        if k not in ['num_observations', 'num_datasets', 'datasets'] 
                                        and not k.startswith('pos_') 
                                        and '_to_' in k],
                                        key=lambda x: (int(x.split('_')[0]), int(x.split('_')[2])))
                    for transition in transitions:
                        row[transition] = data[transition]
                    output_data.append(row)
        
        output_df = pd.DataFrame(output_data)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(output_path, index=False)
        print(f"\n✓ Results saved to: {output_path}")


if __name__ == "__main__":
    main()

