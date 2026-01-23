#!/usr/bin/env python3
"""
Generate slim plots from bucket_analysis_overall.csv files.

For time task: plots for metrics from huber_slope_analysis_time.csv lines 2-8,
plus num_nested_loop and max_log_card_error.

For card task: plots for specific metrics from huber_slope_analysis_card.csv.

Only plots median (50th), p90 (90th), and p95 (95th) percentiles - NOT max error.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import HuberRegressor


def setup_mpl_params():
    """Setup matplotlib parameters to match plot_timing_accuracy.py style"""
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

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
INSIGHTS_DIR = Path(__file__).resolve().parent
BUCKET_RESULTS_DIR = INSIGHTS_DIR / "metric_bucket_results"
GRAND_ANALYSIS_DIR = INSIGHTS_DIR / "grand_analysis_results"

# Metrics to plot for time task (from huber_slope_analysis_time.csv lines 2-8, plus num_nested_loop and max_log_card_error)
TIME_METRICS = [
    "num_tables",
    "num_columns",
    "num_joins",
    "num_filters",
    "longest_path_len",
    "num_nodes",
    "join_tree_diameter",
    "num_nested_loop",
    "max_log_card_error",
    "plan_string_length",
    "log_filter_selectivity_product",
]

# Metrics to plot for card task
CARD_METRICS = [
    "num_tables",
    "num_columns",
    "num_joins",
    "num_filters",
    "longest_path_len",
    "num_nodes",
    "num_nested_loop",
    "num_highly_selective_filters",
    "max_log_card_error",
    "plan_string_length",
    "log_filter_selectivity_product",
]


def fit_huber_regression(x: np.ndarray, y: np.ndarray) -> tuple[HuberRegressor | None, float]:
    """Fit Huber regression and return model and R²."""
    if len(x) < 2 or len(y) < 2:
        return None, 0.0
    
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return None, 0.0
    
    # Reshape for sklearn
    x_clean = x_clean.reshape(-1, 1)
    
    try:
        reg = HuberRegressor(epsilon=1.35, max_iter=200, alpha=0.0)
        reg.fit(x_clean, y_clean)
        
        # Calculate R²
        y_pred = reg.predict(x_clean)
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return reg, r2
    except Exception:
        return None, 0.0


def plot_metric(
    metric: str,
    bucket_indices: np.ndarray,
    bucket_centers: np.ndarray,
    bucket_mins: np.ndarray,
    bucket_maxs: np.ndarray,
    medians: np.ndarray,
    p90s: np.ndarray,
    p95s: np.ndarray,
    output_path: Path,
    task: str = "time",
) -> None:
    """Plot median, p90, and p95 percentiles for a metric."""
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    
    # Use bucket indices for plotting (x-axis positions)
    x_positions = bucket_indices
    
    # Plot data points
    scatter_50 = ax.scatter(x_positions, medians, color='blue', marker='o', s=150, label='50th percentile', zorder=3, edgecolors='black', linewidths=0.5)
    scatter_90 = ax.scatter(x_positions, p90s, color='orange', marker='s', s=150, label='90th percentile', zorder=3, edgecolors='black', linewidths=0.5)
    scatter_95 = ax.scatter(x_positions, p95s, color='red', marker='^', s=150, label='95th percentile', zorder=3, edgecolors='black', linewidths=0.5)
    
    # Fit and plot regression lines
    reg_med, r2_med = fit_huber_regression(bucket_indices, medians)
    reg_p90, r2_p90 = fit_huber_regression(bucket_indices, p90s)
    reg_p95, r2_p95 = fit_huber_regression(bucket_indices, p95s)
    
    line_50 = None
    y_line_med = None
    if reg_med is not None:
        x_line = np.linspace(bucket_indices.min(), bucket_indices.max(), 100)
        y_line_med = reg_med.predict(x_line.reshape(-1, 1))
        line_50 = ax.plot(x_line, y_line_med, 'b-', alpha=0.6, linewidth=2, label='50th fit')[0]
    
    line_90 = None
    y_line_p90 = None
    if reg_p90 is not None:
        x_line = np.linspace(bucket_indices.min(), bucket_indices.max(), 100)
        y_line_p90 = reg_p90.predict(x_line.reshape(-1, 1))
        line_90 = ax.plot(x_line, y_line_p90, 'orange', linestyle='-', alpha=0.6, linewidth=2, label='90th fit')[0]
    
    line_95 = None
    y_line_p95 = None
    if reg_p95 is not None:
        x_line = np.linspace(bucket_indices.min(), bucket_indices.max(), 100)
        y_line_p95 = reg_p95.predict(x_line.reshape(-1, 1))
        line_95 = ax.plot(x_line, y_line_p95, 'r-', alpha=0.6, linewidth=2, label='95th fit')[0]
    
    # Set labels (no title)
    # Set appropriate x-axis label based on metric
    if metric == 'num_columns':
        ax.set_xlabel('# Columns', fontsize=24, weight='bold')
    elif metric == 'num_joins':
        ax.set_xlabel('# Joins', fontsize=24, weight='bold')
    elif metric == 'plan_string_length':
        ax.set_xlabel('Plan Length (×1000)', fontsize=24, weight='bold')
    elif metric == 'log_filter_selectivity_product':
        ax.set_xlabel('Log Selectivity', fontsize=24, weight='bold')
    elif metric == 'max_log_card_error':
        ax.set_xlabel('Log Q-Error', fontsize=24, weight='bold')
        # ax.set_xlabel('Max Log Card Error', fontsize=24, weight='bold')
    else:
        ax.set_xlabel('Metric Range', fontsize=24, weight='bold')
    ax.set_ylabel('Q-Error', fontsize=24, weight='bold')
    
    # Set x-axis ticks to show metric ranges instead of bucket indices
    if len(bucket_indices) > 0 and len(bucket_mins) > 0 and len(bucket_maxs) > 0:
        # Check for special formatting cases
        is_log_metric = (metric == 'log_filter_selectivity_product' or metric == 'max_log_card_error')
        is_integer_metric = (metric in ['num_columns', 'num_joins'])
        is_plan_string_length = (metric == 'plan_string_length')
        
        # Create tick labels showing the range [min, max] for each bucket
        tick_labels = []
        for i in range(len(bucket_indices)):
            min_val = bucket_mins[i]
            max_val = bucket_maxs[i]
            
            if is_plan_string_length:
                # For plan_string_length, divide by 1000 and show with 1 decimal place
                min_val_scaled = min_val / 1000.0
                max_val_scaled = max_val / 1000.0
                if abs(max_val_scaled - min_val_scaled) < 1e-6:
                    label = f'{min_val_scaled:.1f}'
                else:
                    min_str = f'{min_val_scaled:.1f}'
                    max_str = f'{max_val_scaled:.1f}'
                    label = f'[{min_str}, {max_str})'
            elif is_integer_metric:
                # For num_columns and num_joins, use integers (no decimal places)
                min_str = f'{int(round(min_val))}'
                max_str = f'{int(round(max_val))}'
                if abs(max_val - min_val) < 1e-6:
                    label = min_str
                else:
                    label = f'[{min_str}, {max_str})'
            elif is_log_metric:
                # Special formatting for log_filter_selectivity_product: one effective digit after decimal
                # Round properly:
                # - Values with abs >= 0.1: use 1 decimal place (e.g., -0.262... → -0.3)
                # - Values with 0.005 < abs < 0.1: use 2 decimal places (e.g., -0.027... → -0.03)
                # - Values with abs < 0.005: use "0"
                if abs(min_val) < 0.005:
                    min_str = '0'
                elif abs(min_val) >= 0.1:
                    # Round to 1 decimal place
                    min_str = f'{min_val:.1f}'
                else:
                    # Round to 2 decimal places
                    min_str = f'{min_val:.2f}'
                
                if abs(max_val) < 0.005:
                    max_str = '0'
                elif abs(max_val) >= 0.1:
                    # Round to 1 decimal place
                    max_str = f'{max_val:.1f}'
                else:
                    # Round to 2 decimal places
                    max_str = f'{max_val:.2f}'
                
                if abs(max_val - min_val) < 1e-6:
                    # If min and max are essentially the same, just show one value
                    label = min_str
                else:
                    # Show range [min, max) - left bracket, right parenthesis
                    label = f'[{min_str}, {max_str})'
            else:
                # Regular formatting for other metrics
                if abs(max_val - min_val) < 1e-6:
                    # If min and max are essentially the same, just show one value
                    if abs(min_val) < 0.01 or abs(min_val) >= 1000:
                        label = f'{min_val:.2e}'
                    else:
                        label = f'{min_val:.2f}'
                else:
                    # Show range [min, max]
                    if abs(min_val) < 0.01 or abs(min_val) >= 1000:
                        min_str = f'{min_val:.2e}'
                    elif min_val < 1:
                        min_str = f'{min_val:.3f}'
                    else:
                        min_str = f'{min_val:.2f}'
                    
                    if abs(max_val) < 0.01 or abs(max_val) >= 1000:
                        max_str = f'{max_val:.2e}'
                    elif max_val < 1:
                        max_str = f'{max_val:.3f}'
                    else:
                        max_str = f'{max_val:.2f}'
                    
                    label = f'[{min_str}, {max_str}]'
            tick_labels.append(label)
        
        # Set ticks and labels
        ax.set_xticks(bucket_indices)
        # Metrics that should be center-aligned
        center_aligned_metrics = ['num_joins', 'log_filter_selectivity_product', 'max_log_card_error', 'plan_string_length', 'num_columns']
        # For num_joins in card estimation, don't rotate labels; for num_joins in time estimation and others, rotate 20 degrees
        if metric == 'num_joins' and task == 'card':
            rotation_angle = 0
        else:
            rotation_angle = 20
        ha_alignment = 'center' if metric in center_aligned_metrics else 'right'
        ax.set_xticklabels(tick_labels, rotation=rotation_angle, ha=ha_alignment, fontsize=20)
    
    # Create legend with 3 columns: each column has percentile + fit
    # Arrange handles in strict order: percentile, fit, percentile, fit, percentile, fit
    handles = []
    labels = []
    
    # Strict order: percentile followed by its fit, repeated for each
    handles.append(scatter_50)
    labels.append('50th percentile')
    if line_50 is not None:
        handles.append(line_50)
        labels.append('50th fit')
    
    handles.append(scatter_90)
    labels.append('90th percentile')
    if line_90 is not None:
        handles.append(line_90)
        labels.append('90th fit')
    
    handles.append(scatter_95)
    labels.append('95th percentile')
    if line_95 is not None:
        handles.append(line_95)
        labels.append('95th fit')
    
    # Temporarily don't show legend
    # ax.legend(handles, labels, bbox_to_anchor=(0.5, 1.02), loc='lower center', 
    #           ncol=3, fontsize=20, frameon=True)
    ax.grid(True, alpha=0.3)
    
    # Set y-axis limits with outlier handling
    # Ensure lower bound doesn't cut through 50th percentile points and regression lines
    all_y_values = np.concatenate([medians, p90s, p95s])
    
    # Also include regression line values to ensure they're fully visible
    if y_line_med is not None:
        all_y_values = np.concatenate([all_y_values, y_line_med])
    if y_line_p90 is not None:
        all_y_values = np.concatenate([all_y_values, y_line_p90])
    if y_line_p95 is not None:
        all_y_values = np.concatenate([all_y_values, y_line_p95])
    
    all_y_values = all_y_values[~np.isnan(all_y_values)]
    
    # Get minimum of medians (50th percentile) and regression line to ensure they're visible
    medians_clean = medians[~np.isnan(medians)]
    min_median = np.min(medians_clean) if len(medians_clean) > 0 else 0
    if y_line_med is not None:
        min_line_med = np.min(y_line_med[~np.isnan(y_line_med)]) if len(y_line_med[~np.isnan(y_line_med)]) > 0 else min_median
        min_median = min(min_median, min_line_med)
    
    # Use the absolute minimum of all visible data (points + lines) for lower bound
    min_all_visible = np.min(all_y_values) if len(all_y_values) > 0 else 0
    
    if len(all_y_values) > 0:
        q1 = np.percentile(all_y_values, 25)
        q3 = np.percentile(all_y_values, 75)
        iqr = q3 - q1
        
        if iqr > 0:
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = (all_y_values < lower_bound) | (all_y_values > upper_bound)
            if np.any(outliers):
                # Cap y-axis at reasonable value
                y_max_capped = min(upper_bound * 2, np.percentile(all_y_values, 95) * 1.5)
                # Set lower bound so that y-axis range increases by 5%
                # If range is [y_min_orig, y_max], new range should be [y_min_new, y_max] where
                # (y_max - y_min_new) = 1.05 * (y_max - y_min_orig)
                # So: y_min_new = y_max - 1.05 * (y_max - y_min_orig) = 1.05 * y_min_orig - 0.05 * y_max
                y_min_orig = max(0, min_all_visible)
                y_min = 1.05 * y_min_orig - 0.05 * y_max_capped
                ax.set_ylim(y_min, y_max_capped)
            else:
                # Set lower bound so that y-axis range increases by 5%
                y_max = np.max(all_y_values) * 1.1
                y_min_orig = max(0, min_all_visible)
                y_min = 1.05 * y_min_orig - 0.05 * y_max
                ax.set_ylim(y_min, y_max)
        else:
            # Set lower bound so that y-axis range increases by 5%
            y_max = np.max(all_y_values) * 1.1
            y_min_orig = max(0, min_all_visible)
            y_min = 1.05 * y_min_orig - 0.05 * y_max
            ax.set_ylim(y_min, y_max)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)


def create_legend_only(output_dir: Path, task: str) -> None:
    """
    Create a legend-only PNG file for slim plots.
    
    Args:
        output_dir: Directory to save the legend PNG
        task: Task name ('card' or 'time')
    """
    print(f"\nCreating legend for slim plots ({task})...")
    
    # Create legend handles and labels
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
    output_path = output_dir / f'slim_plots_{task}_legend.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches='tight', pad_inches=0.01, facecolor='white')
    plt.close(fig)
    
    print(f"  Created legend: {output_path}")


def process_dataset_task(dataset: str, task: str) -> None:
    """Process a single dataset/task combination."""
    bucket_file = BUCKET_RESULTS_DIR / dataset / task / "bucket_analysis_overall_llm.csv"
    
    if not bucket_file.exists():
        print(f"Warning: {bucket_file} does not exist. Skipping.")
        return
    
    # Determine which metrics to plot
    if task == "time":
        metrics_to_plot = TIME_METRICS
    elif task == "card":
        metrics_to_plot = CARD_METRICS
    else:
        print(f"Warning: Unknown task {task}. Skipping.")
        return
    
    # Load bucket analysis data
    df = pd.read_csv(bucket_file)
    
    # Create output directory
    output_dir = BUCKET_RESULTS_DIR / dataset / task / "plots_slim"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each metric
    for metric in metrics_to_plot:
        row = df[df['metric'] == metric]
        if row.empty:
            print(f"Warning: Metric {metric} not found in {bucket_file}. Skipping.")
            continue
        
        # Parse bucket data
        bucket_indices = np.array(ast.literal_eval(row.iloc[0]['bucket_index']))
        bucket_centers = np.array(ast.literal_eval(row.iloc[0]['bucket_center']))
        # Try to read bucket_min and bucket_max, fall back to empty arrays if not present (for backward compatibility)
        try:
            bucket_mins = np.array(ast.literal_eval(row.iloc[0]['bucket_min']))
            bucket_maxs = np.array(ast.literal_eval(row.iloc[0]['bucket_max']))
        except (KeyError, ValueError):
            # If bucket_min/bucket_max not present, use bucket_centers as fallback
            bucket_mins = bucket_centers
            bucket_maxs = bucket_centers
        medians = np.array(ast.literal_eval(row.iloc[0]['median']))
        p90s = np.array(ast.literal_eval(row.iloc[0]['p90']))
        p95s = np.array(ast.literal_eval(row.iloc[0]['p95']))
        
        # Plot
        metric_safe = metric.replace("/", "_").replace("\\", "_")
        plot_path = output_dir / f"{metric_safe}_{dataset}_{task}.pdf"
        plot_metric(metric, bucket_indices, bucket_centers, bucket_mins, bucket_maxs, medians, p90s, p95s, plot_path, task)
        print(f"  Saved plot: {plot_path}")
    
    print(f"Completed {dataset}/{task}: {len(metrics_to_plot)} plots saved to {output_dir}")


def main() -> None:
    """Main function."""
    print("=" * 80)
    print("Generating slim plots from bucket_analysis_overall.csv files")
    print("=" * 80)
    
    # Find all dataset/task combinations
    if not BUCKET_RESULTS_DIR.exists():
        print(f"Error: Bucket results directory {BUCKET_RESULTS_DIR} does not exist.")
        return
    
    datasets = sorted([d.name for d in BUCKET_RESULTS_DIR.iterdir() if d.is_dir()])
    
    # Track which tasks we've processed to generate legends
    processed_tasks = set()
    
    for dataset in datasets:
        dataset_dir = BUCKET_RESULTS_DIR / dataset
        tasks = sorted([t.name for t in dataset_dir.iterdir() if t.is_dir()])
        
        for task in tasks:
            print(f"\nProcessing {dataset}/{task}...")
            process_dataset_task(dataset, task)
            processed_tasks.add(task)
    
    # Generate legend-only PNG files for each task
    print(f"\n{'='*60}")
    print("Generating legend-only PNG files...")
    print(f"{'='*60}")
    
    for task in sorted(processed_tasks):
        # Create legend in each dataset's plots_slim directory for this task
        # This makes it easy to find the legend alongside the plots
        for dataset in datasets:
            dataset_dir = BUCKET_RESULTS_DIR / dataset
            task_dir = dataset_dir / task
            if task_dir.exists():
                output_dir = task_dir / "plots_slim"
                if output_dir.exists():
                    create_legend_only(output_dir, task)
    
    print("\n" + "=" * 80)
    print("Completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

