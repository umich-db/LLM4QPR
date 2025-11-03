#!/usr/bin/env python3
"""
Script to traverse training/evaluation log folders and extract batch timing summaries.

Usage:
    python summarize_train_eval_logs.py --log_dir logs
"""

import os
import re
import argparse
import pandas as pd
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize training/evaluation logs")
    parser.add_argument("--log_dir", type=str, default="logs",
                        help="Root directory containing log folders (default: logs)")
    return parser.parse_args()


def extract_dataset_from_folder(folder_name):
    """Extract content between 'Train_' and '_Test' from folder name."""
    match = re.search(r'Train_(.+?)_Test', folder_name)
    if match:
        return match.group(1)
    return None


def extract_task_from_filename(filename):
    """Extract content before first '_' in filename."""
    parts = filename.split('_')
    if parts:
        return parts[0]
    return None


def extract_algo_and_model_from_filename(filename):
    """
    Extract algo name and model name (if LLM) from filename.
    Returns: (algo, model_name or None)
    """
    # Check if it's an LLM model
    if '_llm_pretrained' in filename or filename.startswith('card_llm_') or filename.startswith('time_llm_'):
        # It's an LLM model
        algo = 'llm'
        
        # Extract model name between h{number}_ and _emb{number}
        h_pattern = r'_h(\d+)_'
        emb_pattern = r'_emb(\d+)'
        
        h_match = re.search(h_pattern, filename)
        emb_match = re.search(emb_pattern, filename)
        
        if h_match and emb_match:
            start_pos = h_match.end()
            end_pos = emb_match.start()
            model = filename[start_pos:end_pos]
            return algo, model
        return algo, None
    else:
        # Non-LLM model - extract algo name (second part after first _)
        parts = filename.split('_')
        if len(parts) >= 2:
            algo = parts[1]
            return algo, None
        return None, None


def extract_seed_from_filename(filename):
    """Extract seed number from filename."""
    match = re.search(r'seed(\d+)', filename)
    if match:
        return int(match.group(1))
    return None


def parse_train_eval_log(log_path):
    """
    Parse training/evaluation log file and extract batch timing information.
    Returns: (train_time_sum, train_max_batch, test_time_sum, test_max_batch)
    """
    train_time_sum = 0.0
    train_max_batch = 0
    test_time_sum = 0.0
    test_max_batch = 0
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"    Error reading file: {e}")
        return train_time_sum, train_max_batch, test_time_sum, test_max_batch
    
    # Parse training logs (Epoch 0 only)
    expected_train_batch = 1
    for line in lines:
        # Skip DataLoad lines
        if 'DataLoad' in line:
            continue
        
        # Match: [Train] Epoch {epoch} Batch {batch_idx} — {batch_time} ms
        train_match = re.search(r'\[Train\]\s+Epoch\s+(\d+)\s+Batch\s+(\d+)\s+—\s+([\d.]+)\s+ms', line)
        if train_match:
            epoch = int(train_match.group(1))
            batch_idx = int(train_match.group(2))
            batch_time = float(train_match.group(3))
            
            # Only process epoch 0 and sequential batches
            if epoch == 0 and batch_idx == expected_train_batch:
                train_time_sum += batch_time
                train_max_batch = batch_idx
                expected_train_batch += 1
    
    # Parse testing logs
    expected_test_batch = 1
    for line in lines:
        # Skip DataLoad lines
        if 'DataLoad' in line:
            continue
        
        # Match: [Test] Batch {batch_idx} — {batch_time} ms
        test_match = re.search(r'\[Test\]\s+Batch\s+(\d+)\s+—\s+([\d.]+)\s+ms', line)
        if test_match:
            batch_idx = int(test_match.group(1))
            batch_time = float(test_match.group(2))
            
            # Only process sequential batches
            if batch_idx == expected_test_batch:
                test_time_sum += batch_time
                test_max_batch = batch_idx
                expected_test_batch += 1
    
    return train_time_sum, train_max_batch, test_time_sum, test_max_batch


def main():
    args = parse_args()
    log_dir = Path(args.log_dir)
    
    if not log_dir.exists():
        print(f"Error: Log directory '{log_dir}' does not exist")
        return
    
    print(f"Scanning log directory: {log_dir}")
    
    # Traverse folders under log_dir
    for folder_path in log_dir.iterdir():
        if not folder_path.is_dir():
            continue
        
        folder_name = folder_path.name
        dataset = extract_dataset_from_folder(folder_name)
        
        if dataset is None:
            print(f"Skipping folder (no dataset found): {folder_name}")
            continue
        
        print(f"\nProcessing folder: {folder_name} (dataset: {dataset})")
        
        # Find all .log files that don't end with inference.log
        all_logs = list(folder_path.glob('*.log'))
        train_eval_logs = [f for f in all_logs if not f.name.endswith('inference.log')]
        
        if not train_eval_logs:
            print(f"  No training/evaluation log files found")
            continue
        
        print(f"  Found {len(train_eval_logs)} training/evaluation log files")
        
        # Collect all results for this folder
        all_results = []
        
        for log_path in train_eval_logs:
            filename = log_path.name
            task = extract_task_from_filename(filename)
            algo, model = extract_algo_and_model_from_filename(filename)
            seed = extract_seed_from_filename(filename)
            
            if task is None or algo is None or seed is None:
                print(f"  Skipping {filename} (could not extract task, algo, or seed)")
                continue
            
            print(f"  Processing: {filename}")
            print(f"    Task: {task}, Algo: {algo}, Model: {model}, Seed: {seed}")
            
            # Parse the log file
            train_time, train_max_batch, test_time, test_max_batch = parse_train_eval_log(log_path)
            
            result = {
                'task': task,
                'algo': algo,
                'seed': seed,
                'train_time_sum_ms': round(train_time, 2),
                'train_max_batch': train_max_batch,
                'test_time_sum_ms': round(test_time, 2),
                'test_max_batch': test_max_batch
            }
            
            # Add model column if it's LLM
            if algo == 'llm' and model:
                result['model'] = model
            else:
                result['model'] = ''
            
            all_results.append(result)
            
            print(f"    Train: {train_max_batch} batches, {train_time:.2f} ms | Test: {test_max_batch} batches, {test_time:.2f} ms")
        
        # Write summary CSV for this folder
        if all_results:
            summary_df = pd.DataFrame(all_results)
            # Reorder columns
            summary_df = summary_df[['task', 'algo', 'model', 'seed', 'train_time_sum_ms', 'train_max_batch', 'test_time_sum_ms', 'test_max_batch']]
            # Sort by task, algo, model, seed
            summary_df = summary_df.sort_values(by=['task', 'algo', 'model', 'seed'])
            
            summary_path = folder_path / f"A_Train_Eva_{dataset}.csv"
            summary_df.to_csv(summary_path, index=False)
            print(f"  ✓ Wrote summary to: {summary_path}")
            print(f"    Total rows: {len(summary_df)}")
        else:
            print(f"  No results to write")


if __name__ == "__main__":
    main()

