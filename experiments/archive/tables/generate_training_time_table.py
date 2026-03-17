#!/usr/bin/env python3
"""
Generate LaTeX table showing training time consumption for different algorithms and models.

Reads from combined_timing_accuracy_report.csv and creates a table with:
- Rows: Non-LLM algorithms and LLM models
- Columns: Cost Estimation (time task) and Cardinality Estimation (card task)

Usage:
    python generate_training_time_table.py [--input combined_timing_accuracy_report.csv] [--output output.tex] [--group_by task|task_dataset]
"""

import pandas as pd
import numpy as np
import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, List, Tuple


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
    Format algorithm name for display.
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
    Format model name for display.
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


def format_time_value(time_ms):
    """
    Format time value in milliseconds.
    Uses scientific notation for numbers >= 1000.
    Returns formatted string (e.g., "123.45", "1.23e3", "-" for missing)
    """
    if pd.isna(time_ms) or time_ms is None:
        return "-"
    
    if time_ms == 0:
        return "0"
    
    # Use scientific notation for numbers >= 1000
    if abs(time_ms) >= 1000:
        return f"{time_ms:.2e}"
    else:
        return f"{time_ms:.2f}"


def get_exponent_from_formatted(formatted_str):
    """
    Extract exponent from formatted time string (e.g., "1.23e+05" -> 5).
    Returns None if not in scientific notation or if value is "-".
    """
    if formatted_str == "-" or formatted_str == "0":
        return None
    
    if 'e+' in formatted_str or 'e-' in formatted_str:
        try:
            # Extract the exponent part
            if 'e+' in formatted_str:
                exp_str = formatted_str.split('e+')[1]
            else:
                exp_str = formatted_str.split('e-')[1]
            return int(exp_str)
        except (ValueError, IndexError):
            return None
    
    return None


def get_green_color_for_exponent(exp):
    """
    Get green color level based on exponent.
    e+5 -> green1 (lightest), e+6 -> green2, e+7 -> green3, e+8 -> green4 (darkest)
    Returns None if no coloring should be applied.
    """
    if exp is None:
        return None
    
    if exp == 5:
        return "green1"
    elif exp == 6:
        return "green2"
    elif exp == 7:
        return "green3"
    elif exp == 8:
        return "green4"
    else:
        return None


def calculate_training_time(row):
    """
    Calculate total training time for a row.
    Formula: train_time_ms * 200 + llm_train_inference_ms
    For non-LLM algorithms, llm_train_inference_ms is typically NaN, so just use train_time_ms * 200
    """
    train_time = row.get('train_time_ms', 0)
    if pd.isna(train_time):
        train_time = 0
    else:
        train_time = float(train_time) or 0
    
    inference_time = row.get('llm_train_inference_ms', 0)
    if pd.isna(inference_time):
        inference_time = 0
    else:
        inference_time = float(inference_time) or 0
    
    # For training, multiply by 200 epochs
    # If train_time is 0 and inference_time is 0, return NaN to indicate no data
    if train_time == 0 and inference_time == 0:
        return np.nan
    
    total_time = train_time * 200 + inference_time
    return total_time


def load_and_process_data(csv_path: Path, group_by: str = "task"):
    """
    Load data from CSV and calculate training times.
    
    Args:
        csv_path: Path to combined_timing_accuracy_report.csv
        group_by: "task" to average across datasets, "task_dataset" to keep separate
    
    Returns:
        DataFrame with training times for time and card tasks
    """
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Rename columns for consistency
    if 'train_time_sum_ms' in df.columns:
        df.rename(columns={
            'train_time_sum_ms': 'train_time_ms',
            'test_time_sum_ms': 'test_time_ms'
        }, inplace=True)
    elif 'train_time_ms' not in df.columns:
        # If neither exists, check for other variations
        print(f"Warning: train_time_ms column not found. Available columns: {df.columns.tolist()}")
    
    # Calculate training time for each row
    df['training_time_ms'] = df.apply(calculate_training_time, axis=1)
    
    # Group data
    if group_by == "task":
        # Average across datasets for each task
        grouped = df.groupby(['task', 'algo', 'model'], dropna=False).agg({
            'training_time_ms': 'mean'
        }).reset_index()
    else:
        # Keep dataset separate
        grouped = df[['dataset', 'task', 'algo', 'model', 'training_time_ms']].copy()
    
    return grouped


def organize_algorithms(df):
    """
    Organize algorithms into non-LLM and LLM groups, sorted appropriately.
    
    Returns:
        Tuple of (non_llm_list, llm_dict_by_family, all_ordered_list)
    """
    # Get unique algorithms/models (average across tasks if needed)
    # Group by algo and model to get unique combinations
    unique_combos = df.groupby(['algo', 'model'], dropna=False).first().reset_index()
    
    # Separate non-LLM and LLM
    non_llm_rows = unique_combos[unique_combos['algo'] != 'llm'].copy()
    llm_rows = unique_combos[unique_combos['algo'] == 'llm'].copy()
    
    # Get unique non-LLM algorithms (exclude PostgreSQL)
    non_llm_algos = []
    seen_non_llm = set()
    for _, row in non_llm_rows.iterrows():
        algo = row['algo']
        # Skip PostgreSQL
        if algo.lower() == 'postgres' or algo.lower() == 'postgresql':
            continue
        display_name = format_algo_name_for_display(algo)
        if (algo, None) not in seen_non_llm:
            non_llm_algos.append((algo, None, display_name))
            seen_non_llm.add((algo, None))
    
    # Sort non-LLM alphabetically
    def sort_non_llm_key(item):
        algo, model, display_name = item
        return (0, display_name)
    
    non_llm_algos.sort(key=sort_non_llm_key)
    
    # Group LLM by family
    # Filter out Qwen models without "embedding" in the name (same as plot_timing_accuracy.py)
    llm_by_family = defaultdict(list)
    seen_llm = set()
    for _, row in llm_rows.iterrows():
        model = row['model']
        # Skip Qwen models without "embedding" in the name
        if model and 'qwen' in str(model).lower() and 'embedding' not in str(model).lower():
            continue
        if (model,) not in seen_llm:
            family = get_llm_family(model)
            display_name = format_model_name_for_display(model)
            llm_by_family[family].append((model, display_name))
            seen_llm.add((model,))
    
    # Sort LLM within each family
    def get_llm_sort_key(item):
        model, display_name = item
        model_lower = model.lower() if model else ""
        
        # Determine family order
        if 'sentence' in model_lower or 'bert' in model_lower:
            family_order = 0
            if 'sentence' in model_lower:
                size = 1
            elif 'modernbert' in model_lower or 'BERT' in model:
                size = 3
            else:
                size = 2
        elif 'gemma' in model_lower:
            family_order = 1
            size = extract_model_size(model) or 0
        elif 'llama' in model_lower:
            family_order = 2
            size = extract_model_size(model) or 0
        elif 'qwen' in model_lower and 'embedding' in model_lower:
            family_order = 3
            size = extract_model_size(model) or 0
        elif 'qwen' in model_lower:
            family_order = 4
            size = extract_model_size(model) or 0
        else:
            family_order = 5
            size = extract_model_size(model) or 0
        
        return (family_order, size)
    
    # Sort each family
    for family in llm_by_family:
        llm_by_family[family].sort(key=get_llm_sort_key)
    
    # Create ordered list: non-LLM first, then LLM by family
    all_ordered = []
    
    # Add non-LLM
    for algo, model, display_name in non_llm_algos:
        all_ordered.append(('non_llm', algo, model, display_name))
    
    # Add LLM by family order
    family_order = ['bert', 'gemma', 'llama', 'qwen_embedding', 'qwen', 'other']
    for family in family_order:
        if family in llm_by_family:
            for model, display_name in llm_by_family[family]:
                all_ordered.append(('llm', 'llm', model, display_name))
    
    # Add any remaining families
    for family, items in llm_by_family.items():
        if family not in family_order:
            for model, display_name in items:
                all_ordered.append(('llm', 'llm', model, display_name))
    
    return non_llm_algos, llm_by_family, all_ordered


def generate_latex_table(df: pd.DataFrame, output_path: Optional[Path] = None) -> str:
    """
    Generate LaTeX table with training times for cost and cardinality estimation.
    
    Args:
        df: DataFrame with training_time_ms, task, algo, model columns
        output_path: Optional path to save the LaTeX file
    
    Returns:
        LaTeX table code as string
    """
    # Organize algorithms
    non_llm_algos, llm_by_family, all_ordered = organize_algorithms(df)
    
    # Create lookup dictionary: (algo, model) -> {task: training_time_ms}
    # Average across datasets if there are multiple entries
    time_lookup = {}
    for _, row in df.iterrows():
        algo = row['algo']
        model_val = row.get('model')
        # Convert NaN to None for consistent key matching
        model = None if pd.isna(model_val) else model_val
        task = row['task']
        time_ms = row['training_time_ms']
        
        key = (algo, model)
        if key not in time_lookup:
            time_lookup[key] = {}
        
        # If multiple entries for same key+task, average them
        if task in time_lookup[key]:
            # Average with existing value
            existing = time_lookup[key][task]
            if pd.notna(existing) and pd.notna(time_ms):
                time_lookup[key][task] = (existing + time_ms) / 2
            elif pd.notna(time_ms):
                time_lookup[key][task] = time_ms
        else:
            time_lookup[key][task] = time_ms
    
    
    # Generate LaTeX
    lines = []
    lines.append("\\begin{tabular}{lcc}")
    lines.append("")
    lines.append("\\toprule")
    lines.append("")
    lines.append("Algorithm & Cost Estimation & Cardinality Estimation \\\\")
    lines.append("")
    lines.append("\\midrule")
    lines.append("")
    
    # Track if we've added separator between non-LLM and LLM
    prev_type = None
    
    for item in all_ordered:
        algo_type = item[0]
        if algo_type == 'non_llm':
            algo, model, display_name = item[1], item[2], item[3]
        else:
            # For LLM: ('llm', 'llm', model, display_name)
            algo, model, display_name = item[1], item[2], item[3]
        
        # Add separator between non-LLM and LLM
        if prev_type == 'non_llm' and algo_type == 'llm':
            lines.append("\\midrule")
            lines.append("")
        
        # Get training times
        if algo_type == 'non_llm':
            key = (algo, None)
        else:
            # For LLM, model is the actual model name from the dataframe
            key = ('llm', model)
        
        time_time = time_lookup.get(key, {}).get('time', None)
        card_time = time_lookup.get(key, {}).get('card', None)
        
        # Format times
        time_str = format_time_value(time_time)
        card_str = format_time_value(card_time)
        
        # Skip if display_name is None or empty
        if not display_name or display_name == 'None':
            continue
        
        # Create row (no coloring)
        row_line = f"{display_name} & {time_str} & {card_str} \\\\"
        lines.append(row_line)
        
        prev_type = algo_type
    
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
    parser = argparse.ArgumentParser(description="Generate LaTeX table for training time consumption")
    parser.add_argument("--input", type=str, default="combined_timing_accuracy_report.csv",
                        help="Input CSV file (default: combined_timing_accuracy_report.csv)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output LaTeX file (optional, defaults to stdout)")
    parser.add_argument("--group_by", type=str, default="task", choices=["task", "task_dataset"],
                        help="Group by 'task' (average across datasets) or 'task_dataset' (default: task)")
    
    args = parser.parse_args()
    
    # Load and process data
    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"Error: Input file {csv_path} not found")
        return
    
    print(f"Reading data from: {csv_path}")
    df = load_and_process_data(csv_path, group_by=args.group_by)
    
    print(f"Loaded {len(df)} rows")
    print(f"Grouping by: {args.group_by}")
    
    # Generate LaTeX table
    output_path = Path(args.output) if args.output else None
    latex_code = generate_latex_table(df, output_path)
    
    if not args.output:
        print("\n" + "="*80)
        print("LaTeX Table Code:")
        print("="*80)
        print(latex_code)


if __name__ == "__main__":
    main()

