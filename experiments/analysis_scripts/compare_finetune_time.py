#!/usr/bin/env python3
"""
Script to compare finetuning time vs non-finetuning time for LLMs.

Usage:
    python compare_finetune_time.py [--logs_dir logs] [--csv combined_timing_accuracy_report.csv]
"""

import os
import re
import argparse
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple


def parse_args():
    parser = argparse.ArgumentParser(description="Compare finetuning vs non-finetuning time")
    parser.add_argument("--logs_dir", type=str, default="logs",
                        help="Root directory containing log folders (default: logs)")
    parser.add_argument("--csv", type=str, default="combined_timing_accuracy_report.csv",
                        help="CSV file with timing data (default: combined_timing_accuracy_report.csv)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV file (optional)")
    return parser.parse_args()


def extract_dataset_from_folder(folder_name):
    """Extract content between 'Train_' and '_Test' from folder name."""
    match = re.search(r'Train_(.+?)_Test', folder_name)
    if match:
        return match.group(1)
    return None


def parse_finetune_log(log_path):
    """
    Parse finetuning log file and extract total training time.
    Sums up all batch times from lines like: "[Train] Epoch 0 Batch 1 — 2106.97 ms"
    Returns: total_time_ms (float)
    """
    total_time = 0.0
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"    Error reading file {log_path}: {e}")
        return None
    
    # Parse training logs - sum all batch times (excluding DataLoad lines)
    for line in lines:
        # Skip DataLoad lines
        if 'DataLoad' in line:
            continue
        
        # Match: [Train] Epoch {epoch} Batch {batch_idx} — {batch_time} ms
        train_match = re.search(r'\[Train\]\s+Epoch\s+(\d+)\s+Batch\s+(\d+)\s+—\s+([\d.]+)\s+ms', line)
        if train_match:
            batch_time = float(train_match.group(3))
            total_time += batch_time
    
    return total_time


def find_finetune_logs(logs_dir, dataset, task):
    """
    Find finetune_last and finetune_lora log files for a given dataset and task.
    Returns: (last_log_path, lora_log_path) or (None, None) if not found
    """
    logs_path = Path(logs_dir)
    
    # Find folder matching the dataset
    folder_pattern = f"logs_Train_{dataset}_Test_{dataset}_ours"
    folder_path = logs_path / folder_pattern
    
    if not folder_path.exists():
        return None, None
    
    # Look for finetune log files (exclude inference.log files)
    # Pattern: {task}_llm_finetune_{mode}_postgres_0.0001_b1_h2048_meta-llama-Llama-3.1-8B_quant-4-bit.log
    last_pattern = f"{task}_llm_finetune_last_*meta-llama-Llama-3.1-8B*.log"
    lora_pattern = f"{task}_llm_finetune_lora_*meta-llama-Llama-3.1-8B*.log"
    
    last_logs = [f for f in folder_path.glob(last_pattern) if not f.name.endswith('inference.log')]
    lora_logs = [f for f in folder_path.glob(lora_pattern) if not f.name.endswith('inference.log')]
    
    # Prefer files with "quant-4-bit" in the name (standard configuration)
    def sort_key(f):
        name = f.name
        # Files with quant-4-bit get priority (lower sort key)
        if 'quant-4-bit' in name:
            return (0, name)
        else:
            return (1, name)
    
    last_logs_sorted = sorted(last_logs, key=sort_key)
    lora_logs_sorted = sorted(lora_logs, key=sort_key)
    
    last_log = last_logs_sorted[0] if last_logs_sorted else None
    lora_log = lora_logs_sorted[0] if lora_logs_sorted else None
    
    return last_log, lora_log


def get_non_finetune_time(csv_path, dataset, task, model_name="meta-llama-Llama-3.1-8B"):
    """
    Get non-finetuning time from CSV file.
    Returns: llm_train_inference_ms value or None if not found
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file {csv_path}: {e}")
        return None
    
    # Filter for matching row
    mask = (df['dataset'] == dataset) & \
           (df['task'] == task) & \
           (df['algo'] == 'llm') & \
           (df['model'] == model_name)
    
    matching_rows = df[mask]
    
    if matching_rows.empty:
        return None
    
    # Get llm_train_inference_ms (should be the same for all matching rows)
    llm_train_inference_ms = matching_rows['llm_train_inference_ms'].iloc[0]
    
    return llm_train_inference_ms if pd.notna(llm_train_inference_ms) else None


def main():
    args = parse_args()
    logs_dir = Path(args.logs_dir)
    csv_path = Path(args.csv)
    
    if not logs_dir.exists():
        print(f"Error: Log directory '{logs_dir}' does not exist")
        return
    
    if not csv_path.exists():
        print(f"Error: CSV file '{csv_path}' does not exist")
        return
    
    print("="*80)
    print("Comparing Finetuning vs Non-Finetuning Time")
    print("="*80)
    
    # Define datasets and their corresponding tasks
    datasets_config = [
        ('tpch', 'time'),
        ('tpcds', 'time'),
        ('stats', 'card'),
        ('job_full', 'time'),
    ]
    
    results = []
    
    for dataset, task in datasets_config:
        print(f"\nProcessing {dataset}/{task}...")
        
        # Find finetune log files
        last_log, lora_log = find_finetune_logs(logs_dir, dataset, task)
        
        if last_log is None and lora_log is None:
            print(f"  Warning: No finetune log files found for {dataset}/{task}")
            continue
        
        # Parse finetune times
        last_time = None
        lora_time = None
        
        if last_log:
            print(f"  Found last log: {last_log.name}")
            last_time = parse_finetune_log(last_log)
            if last_time is not None:
                print(f"    Last finetune time: {last_time:.2f} ms")
            else:
                print(f"    Failed to parse last log")
        
        if lora_log:
            print(f"  Found lora log: {lora_log.name}")
            lora_time = parse_finetune_log(lora_log)
            if lora_time is not None:
                print(f"    LoRA finetune time: {lora_time:.2f} ms")
            else:
                print(f"    Failed to parse lora log")
        
        # Get non-finetune time from CSV
        non_finetune_time = get_non_finetune_time(csv_path, dataset, task)
        
        if non_finetune_time is None:
            print(f"  Warning: No non-finetune time found in CSV for {dataset}/{task}")
            continue
        
        print(f"  Non-finetune time (from CSV): {non_finetune_time:.2f} ms")
        
        # Calculate ratios
        if last_time is not None:
            last_ratio = last_time / non_finetune_time if non_finetune_time > 0 else None
            print(f"  Last finetune ratio: {last_ratio:.4f}x" if last_ratio else "  Last finetune ratio: N/A")
            
            results.append({
                'dataset': dataset,
                'task': task,
                'mode': 'last',
                'finetune_time_ms': last_time,
                'non_finetune_time_ms': non_finetune_time,
                'ratio': last_ratio
            })
        
        if lora_time is not None:
            lora_ratio = lora_time / non_finetune_time if non_finetune_time > 0 else None
            print(f"  LoRA finetune ratio: {lora_ratio:.4f}x" if lora_ratio else "  LoRA finetune ratio: N/A")
            
            results.append({
                'dataset': dataset,
                'task': task,
                'mode': 'lora',
                'finetune_time_ms': lora_time,
                'non_finetune_time_ms': non_finetune_time,
                'ratio': lora_ratio
            })
    
    # Print summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"{'Dataset':<12} {'Task':<8} {'Mode':<8} {'Finetune (ms)':<15} {'Non-Finetune (ms)':<18} {'Ratio':<10}")
    print("-"*80)
    
    for result in results:
        finetune_str = f"{result['finetune_time_ms']:.2f}" if result['finetune_time_ms'] is not None else "N/A"
        non_finetune_str = f"{result['non_finetune_time_ms']:.2f}" if result['non_finetune_time_ms'] is not None else "N/A"
        ratio_str = f"{result['ratio']:.4f}" if result['ratio'] is not None else "N/A"
        print(f"{result['dataset']:<12} {result['task']:<8} {result['mode']:<8} {finetune_str:<15} {non_finetune_str:<18} {ratio_str:<10}")
    
    # Save to CSV if requested
    if args.output:
        output_df = pd.DataFrame(results)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(output_path, index=False)
        print(f"\n✓ Results saved to: {output_path}")


if __name__ == "__main__":
    main()

