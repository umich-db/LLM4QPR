#!/usr/bin/env python3
"""
Generate LaTeX table from Shapley field removal results.

Reads two CSV files and creates a table with:
- Rows: Categories (cardinality, conditions_and_filters, cost, metadata_and_config)
- Columns: 8 columns total
  - First 4: job_full time estimation (50th, 90th, 95th, max)
  - Second 4: stats card estimation (50th, 90th, 95th, max)

Usage:
    python generate_shapley_table.py --time_file <time_file.csv> --card_file <card_file.csv> [--output <output.tex>]
"""

import pandas as pd
import argparse
from pathlib import Path
from typing import Optional


def format_category_name(category):
    """
    Format category name for display.
    """
    category_map = {
        'cardinality': 'Cardinality',
        'conditions_and_filters': 'Conditions and Filters',
        'cost': 'Cost',
        'metadata_and_config': 'Metadata and Configuration'
    }
    return category_map.get(category, category.replace('_', ' ').title())


def format_value(value):
    """
    Format numerical value for display.
    Uses scientific notation for large numbers (>= 1e6 or <= -1e6).
    """
    if pd.isna(value):
        return "-"
    
    # Handle very large or very small numbers
    if abs(value) >= 1e6 or (abs(value) < 1e-3 and value != 0):
        formatted = f"{value:.2e}"
        # Remove + sign from scientific notation
        return formatted.replace('e+', 'e').replace('e-', 'e-')
    else:
        return f"{value:.2f}"


def assign_green_color(value: float, sorted_values: list) -> str:
    """
    Assign green color based on value's rank (larger = better = larger green number).
    
    Args:
        value: The value to color
        sorted_values: List of all values sorted in ascending order (smallest to largest)
    
    Returns:
        Green color name (green1 to green5, where green5 is largest/best)
    """
    if len(sorted_values) == 0:
        return ''
    
    # Remove duplicates and sort
    unique_values = sorted(set(sorted_values))
    n_unique = len(unique_values)
    
    if n_unique == 1:
        # All values are the same
        return 'green3'
    
    # Find rank of value (0 = smallest, n-1 = largest)
    try:
        rank = unique_values.index(value)
    except ValueError:
        # Value not in list, find closest
        rank = min(range(len(unique_values)), key=lambda i: abs(unique_values[i] - value))
    
    # Map rank to green color (green5 = largest/best, green1 = smallest/worst)
    # For 4 values: rank 0->green1, 1->green2, 2->green3, 3->green4
    # For 5 values: rank 0->green1, 1->green2, 2->green3, 3->green4, 4->green5
    if n_unique == 4:
        color_map = {0: 'green1', 1: 'green2', 2: 'green3', 3: 'green4'}
    elif n_unique == 5:
        color_map = {0: 'green1', 1: 'green2', 2: 'green3', 3: 'green4', 4: 'green5'}
    elif n_unique == 3:
        color_map = {0: 'green1', 1: 'green2', 2: 'green3'}
    elif n_unique == 2:
        color_map = {0: 'green1', 1: 'green2'}
    else:
        # For 1 or more than 5, use linear mapping
        if rank == 0:
            return 'green1'
        elif rank == n_unique - 1:
            return 'green5'
        else:
            # Interpolate between green1 and green5
            ratio = rank / (n_unique - 1)
            if ratio < 0.25:
                return 'green1'
            elif ratio < 0.5:
                return 'green2'
            elif ratio < 0.75:
                return 'green3'
            elif ratio < 1.0:
                return 'green4'
            else:
                return 'green5'
    
    return color_map.get(rank, 'green3')


def generate_latex_table(time_file: Path, card_file: Path, output_path: Optional[Path] = None) -> str:
    """
    Generate LaTeX table from Shapley field removal results.
    
    Args:
        time_file: Path to time estimation CSV file
        card_file: Path to cardinality estimation CSV file
        output_path: Optional path to save the LaTeX file
    
    Returns:
        LaTeX table code as string
    """
    # Read CSV files
    time_df = pd.read_csv(time_file)
    card_df = pd.read_csv(card_file)
    
    # Ensure category column exists and set as index for easier lookup
    if 'category' not in time_df.columns or 'category' not in card_df.columns:
        raise ValueError("CSV files must have a 'category' column")
    
    time_df = time_df.set_index('category')
    card_df = card_df.set_index('category')
    
    # Define categories in order: Cost, Cardinality, Conditions and filters, Metadata and Configuration
    categories = ['cost', 'cardinality', 'conditions_and_filters', 'metadata_and_config']
    
    # Define quantile columns
    quantile_cols = ['50th', '90th', '95th', 'max']
    quantile_keys = ['shapley_50th', 'shapley_90th', 'shapley_95th', 'shapley_max']
    
    # Calculate green colors for each column
    # For each column (time/card + quantile), rank all category values
    column_colors = {}  # {(dataset_type, quantile_key, category): color}
    
    # Time estimation columns
    for key in quantile_keys:
        values = []
        for category in categories:
            if category in time_df.index:
                value = time_df.loc[category, key]
                if pd.notna(value):
                    values.append((category, value))
        
        if len(values) > 0:
            # Sort by value (ascending - smallest to largest)
            values_sorted = sorted(values, key=lambda x: x[1])
            sorted_value_list = [v[1] for v in values_sorted]
            
            # Assign colors (larger value = larger green number)
            for category, value in values:
                color = assign_green_color(value, sorted_value_list)
                column_colors[('time', key, category)] = color
    
    # Card estimation columns
    for key in quantile_keys:
        values = []
        for category in categories:
            if category in card_df.index:
                value = card_df.loc[category, key]
                if pd.notna(value):
                    values.append((category, value))
        
        if len(values) > 0:
            # Sort by value (ascending - smallest to largest)
            values_sorted = sorted(values, key=lambda x: x[1])
            sorted_value_list = [v[1] for v in values_sorted]
            
            # Assign colors (larger value = larger green number)
            for category, value in values:
                color = assign_green_color(value, sorted_value_list)
                column_colors[('card', key, category)] = color
    
    # Generate LaTeX
    lines = []
    lines.append("\\begin{tabular}{l|cccc|cccc}")
    lines.append("")
    lines.append("\\toprule")
    lines.append("")
    
    # Header row 1: Dataset names
    header1 = "\\multirow{2}{*}{Category}"
    header1 += " & \\multicolumn{4}{c|}{JOB-FULL (Time)}"
    header1 += " & \\multicolumn{4}{c|}{STATS (Card)}"
    lines.append(header1 + " \\\\")
    lines.append("")
    
    # Header row 2: Quantile labels
    header2_parts = []
    for _ in range(2):  # Two datasets
        for quantile in quantile_cols:
            if quantile == 'max':
                header2_parts.append('Max')
            else:
                header2_parts.append(f"{quantile}")
    
    lines.append(" & " + " & ".join(header2_parts) + " \\\\")
    lines.append("")
    lines.append("\\midrule")
    lines.append("")
    
    # Data rows
    for category in categories:
        if category not in time_df.index or category not in card_df.index:
            continue
        
        # Format category name
        category_display = format_category_name(category)
        
        # Get values from both dataframes
        row_parts = [category_display]
        
        # Add time estimation values
        for key in quantile_keys:
            value = time_df.loc[category, key]
            formatted = format_value(value)
            
            # Add green color if available
            color_key = ('time', key, category)
            if color_key in column_colors:
                color = column_colors[color_key]
                cell = f"\\cellcolor{{{color}}}{formatted}"
            else:
                cell = formatted
            
            row_parts.append(cell)
        
        # Add card estimation values (separator is in column spec, not as a cell)
        for key in quantile_keys:
            value = card_df.loc[category, key]
            formatted = format_value(value)
            
            # Add green color if available
            color_key = ('card', key, category)
            if color_key in column_colors:
                color = column_colors[color_key]
                cell = f"\\cellcolor{{{color}}}{formatted}"
            else:
                cell = formatted
            
            row_parts.append(cell)
        
        lines.append(" & ".join(row_parts) + " \\\\")
    
    lines.append("")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    
    latex_code = "\n".join(lines)
    
    # Save to file if specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(latex_code)
        print(f"LaTeX table saved to: {output_path}")
    
    return latex_code


def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX table from Shapley field removal results")
    parser.add_argument("--time_file", type=str, required=True,
                        help="Path to time estimation CSV file")
    parser.add_argument("--card_file", type=str, required=True,
                        help="Path to cardinality estimation CSV file")
    parser.add_argument("--output", type=str, default=None,
                        help="Output LaTeX file (optional, defaults to stdout)")
    
    args = parser.parse_args()
    
    # Load files
    time_file = Path(args.time_file)
    card_file = Path(args.card_file)
    
    if not time_file.exists():
        print(f"Error: Time file {time_file} not found")
        return
    
    if not card_file.exists():
        print(f"Error: Card file {card_file} not found")
        return
    
    print(f"Reading time file: {time_file}")
    print(f"Reading card file: {card_file}")
    
    # Generate LaTeX table
    output_path = Path(args.output) if args.output else None
    latex_code = generate_latex_table(time_file, card_file, output_path)
    
    if not args.output:
        print("\n" + "="*80)
        print("LaTeX Table Code:")
        print("="*80)
        print(latex_code)


if __name__ == "__main__":
    main()

