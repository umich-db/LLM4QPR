#!/usr/bin/env python3
"""
Analyze q_error for specific query indices across models and seeds.

Usage:
    python analyze_specific_queries.py --verbose_dir <verbose_dir> --indices 11 172
"""

import pandas as pd
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np


def find_verbose_files(verbose_dir: Path, model_patterns: List[str], seeds: List[int], task: str = "card") -> Dict[str, Dict[int, Path]]:
    """
    Find verbose CSV files for specified models and seeds.
    
    Args:
        verbose_dir: Directory containing verbose files
        model_patterns: List of model name patterns to search for
        seeds: List of seeds to search for
        task: Task type - "card" or "time" (default: "card")
    
    Returns:
        {model_name: {seed: file_path}}
    """
    files = {}
    
    for model_pattern in model_patterns:
        model_name = model_pattern.replace('*', '').replace('_', '-')
        files[model_name] = {}
        
        for seed in seeds:
            # Pattern: {task}_llm_pretrained-None_1.0_*{model_pattern}*_seed{seed}.csv
            pattern = f"{task}_llm_pretrained-None_1.0_*{model_pattern}*_seed{seed}.csv"
            
            matching_files = list(verbose_dir.glob(pattern))
            if matching_files:
                files[model_name][seed] = matching_files[0]
            else:
                print(f"Warning: Could not find file for {model_name}, seed {seed}")
    
    return files


def extract_q_errors(file_path: Path, indices: List[int]) -> Dict[int, float]:
    """
    Extract q_error values for specified indices from a CSV file.
    
    Returns:
        {idx: q_error}
    """
    try:
        df = pd.read_csv(file_path)
        results = {}
        
        for idx in indices:
            # Find row with matching idx
            row = df[df['idx'] == idx]
            if not row.empty:
                q_error = row['q_error'].iloc[0]
                results[idx] = float(q_error)
            else:
                print(f"Warning: idx {idx} not found in {file_path.name}")
                results[idx] = None
        
        return results
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {idx: None for idx in indices}


def main():
    parser = argparse.ArgumentParser(description="Analyze q_error for specific query indices")
    parser.add_argument("--verbose_dir", type=str, 
                        default="verbose/verbose_Train_stats_Test_stats_ours",
                        help="Directory containing verbose CSV files")
    parser.add_argument("--indices", type=int, nargs="+", default=[11, 172],
                        help="Query indices to analyze (default: 11 172)")
    parser.add_argument("--models", type=str, nargs="+",
                        default=["google-gemma-3-4b-pt", "meta-llama-Llama-3.1-8B", "Qwen-Qwen3-Embedding-8B"],
                        help="Model patterns to search for")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44],
                        help="Seeds to analyze (default: 42 43 44)")
    parser.add_argument("--task", type=str, default="card", choices=["card", "time"],
                        help="Task type: card or time (default: card)")
    
    args = parser.parse_args()
    
    verbose_dir = Path(args.verbose_dir)
    if not verbose_dir.exists():
        print(f"Error: Verbose directory {verbose_dir} does not exist")
        return
    
    print("="*80)
    print("Analyzing q_error for specific query indices")
    print("="*80)
    print(f"Verbose directory: {verbose_dir}")
    print(f"Task: {args.task}")
    print(f"Indices: {args.indices}")
    print(f"Models: {args.models}")
    print(f"Seeds: {args.seeds}")
    print()
    
    # Find all files
    files = find_verbose_files(verbose_dir, args.models, args.seeds, task=args.task)
    
    # Collect all q_error values
    all_errors = {idx: [] for idx in args.indices}  # {idx: [list of q_errors]}
    error_details = []  # List of (model, seed, idx, q_error) tuples
    
    for model_name, seed_files in files.items():
        for seed, file_path in seed_files.items():
            if file_path is None:
                continue
            
            print(f"Processing: {model_name}, seed {seed}")
            q_errors = extract_q_errors(file_path, args.indices)
            
            for idx, q_error in q_errors.items():
                if q_error is not None:
                    all_errors[idx].append(q_error)
                    error_details.append((model_name, seed, idx, q_error))
                    print(f"  idx={idx}: q_error={q_error:.6f}")
    
    print()
    print("="*80)
    print("Summary: All q_error values")
    print("="*80)
    print(f"{'Model':<30} {'Seed':<6} {'Idx':<6} {'q_error':<15}")
    print("-"*80)
    
    for model, seed, idx, q_error in error_details:
        print(f"{model:<30} {seed:<6} {idx:<6} {q_error:<15.6f}")
    
    print()
    print("="*80)
    print("Average q_error across models and seeds")
    print("="*80)
    
    for idx in args.indices:
        if all_errors[idx]:
            avg_error = np.mean(all_errors[idx])
            std_error = np.std(all_errors[idx])
            count = len(all_errors[idx])
            print(f"idx={idx}:")
            print(f"  Count: {count}")
            print(f"  Average q_error: {avg_error:.6f}")
            print(f"  Std deviation: {std_error:.6f}")
            print(f"  Min: {min(all_errors[idx]):.6f}")
            print(f"  Max: {max(all_errors[idx]):.6f}")
            print()
        else:
            print(f"idx={idx}: No data found")
            print()


if __name__ == "__main__":
    main()

