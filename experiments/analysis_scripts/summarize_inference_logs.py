#!/usr/bin/env python3
"""
Script to traverse inference log folders and extract timing summaries.

Usage:
    python summarize_inference_logs.py --log_dir logs
"""

import os
import re
import argparse
import pandas as pd
from pathlib import Path
from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize inference logs")
    parser.add_argument("--log_dir", type=str, default="logs",
                        help="Root directory containing log folders (default: logs)")
    parser.add_argument("--check_missing", action="store_true",
                        help="Check for missing dat_paths for each model")
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


def extract_model_from_filename(filename):
    """Extract content between 'h{number}_' and '_emb{number}' in filename."""
    h_pattern = r'_h(\d+)_'
    emb_pattern = r'_emb(\d+)'
    
    h_match = re.search(h_pattern, filename)
    emb_match = re.search(emb_pattern, filename)
    
    if h_match and emb_match:
        start_pos = h_match.end()
        end_pos = emb_match.start()
        model = filename[start_pos:end_pos]
        return model
    return None


def extract_dat_path_suffix(dat_path):
    """Extract content after the last 'postgres' in dat_path."""
    parts = dat_path.split('postgres')
    if len(parts) > 1:
        # Get the last part after 'postgres' and strip leading slashes/dashes/underscores
        suffix = parts[-1].lstrip('/-_')
        # Remove trailing .csv if present
        if suffix.endswith('.csv'):
            suffix = suffix[:-4]
        return suffix
    # If no 'postgres' found, strip leading _ and trailing .csv
    result = dat_path.lstrip('_')
    if result.endswith('.csv'):
        result = result[:-4]
    return result


def parse_inference_log(log_path):
    """Parse inference log file and extract timing information."""
    results = []
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for "Creating new embedding file for dat_path:"
        if "Creating new embedding file for dat_path:" in line:
            # Extract dat_path
            dat_path_match = re.search(r'Creating new embedding file for dat_path:\s*(.+)$', line)
            if dat_path_match:
                full_dat_path = dat_path_match.group(1).strip()
                dat_path = extract_dat_path_suffix(full_dat_path)
                
                # Skip the next line and start looking for prompt timings
                i += 2
                
                # Collect prompt timings
                total_time = 0.0
                prompt_count = 0
                expected_prompt_num = 0
                
                while i < len(lines):
                    prompt_line = lines[i].strip()
                    # Match pattern: [Infer] Prompt {i} took {float} ms
                    prompt_match = re.search(r'\[Infer\]\s+Prompt\s+(\d+)\s+took\s+([\d.]+)\s+ms', prompt_line)
                    
                    if prompt_match:
                        prompt_num = int(prompt_match.group(1))
                        time_ms = float(prompt_match.group(2))
                        
                        # Check if prompt number increases by 1
                        if prompt_num == expected_prompt_num:
                            total_time += time_ms
                            prompt_count += 1
                            expected_prompt_num += 1
                        else:
                            # Sequence broken, record and break
                            break
                    else:
                        # Not a prompt line, break
                        break
                    
                    i += 1
                
                # Record the result if we found any prompts
                if prompt_count > 0:
                    results.append({
                        'dat_path': dat_path,
                        'total_time_ms': round(total_time, 2),  # Round to 2 decimal places
                        'max_prompt_num': prompt_count  # total count (0-indexed, so count = max_i + 1)
                    })
                
                continue
        
        i += 1
    
    return results


def check_missing_datpaths(log_dir):
    """Check which dat_paths are missing for each model across all Asummary files."""
    expected_datpaths = {
        'tpch',
        'tpcds',
        'imdb',
        'imdb_job_sub',
        'imdb_job',
        'imdb_job_full',
        'imdb_job_full_sub_selected',
        'stats',
        'stats_statsCEB_sub',
        'stats_statsCEB'
    }
    
    log_dir_path = Path(log_dir)
    all_summary_files = list(log_dir_path.glob('*/A_LLM_summary_*.csv'))
    
    if not all_summary_files:
        print("No A_LLM_summary files found")
        return
    
    print(f"\n{'='*80}")
    print("CHECKING MISSING DAT_PATHS FOR EACH MODEL")
    print(f"{'='*80}\n")
    
    # Collect all data from all summary files
    all_data = []
    for summary_file in all_summary_files:
        df = pd.read_csv(summary_file)
        all_data.append(df)
    
    if not all_data:
        print("No data found in summary files")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Group by model only (don't care about task - if dat_path exists in either time or card, it's fine)
    grouped = combined_df.groupby('model')
    
    missing_report = []
    
    for model, group in grouped:
        present_datpaths = set(group['dat_path'].unique())
        missing_datpaths = expected_datpaths - present_datpaths
        
        if missing_datpaths:
            missing_report.append({
                'model': model,
                'missing_count': len(missing_datpaths),
                'missing_datpaths': ', '.join(sorted(missing_datpaths))
            })
    
    # Always generate report file (even if empty)
    if missing_report:
        missing_df = pd.DataFrame(missing_report)
        missing_df = missing_df.sort_values(['model'])
    else:
        # Create empty DataFrame with correct columns
        missing_df = pd.DataFrame(columns=['model', 'missing_count', 'missing_datpaths'])
    
    # Save to file
    output_path = Path(log_dir) / 'missing_LLM_datpaths_report.csv'
    missing_df.to_csv(output_path, index=False)
    print(f"Missing dat_paths report saved to: {output_path}\n")
    
    # Print summary
    if len(missing_df) > 0:
        print(f"Found {len(missing_df)} models with missing dat_paths:\n")
        for _, row in missing_df.iterrows():
            model_str = str(row['model'])
            print(f"  {model_str:40s} | Missing {row['missing_count']:2d}: {row['missing_datpaths']}")
    else:
        print("✓ All models have all expected dat_paths (across time and card tasks)!")
    
    print(f"\n{'='*80}\n")


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
        
        # Find all *seed42_inference.log files in this folder
        all_inference_logs = list(folder_path.glob('*seed42_inference.log'))
        
        # Filter out files with _rm- (removed fields experiments)
        inference_logs = [log for log in all_inference_logs if '_rm-' not in log.name]
        
        if not inference_logs:
            filtered_count = len(all_inference_logs) - len(inference_logs)
            if filtered_count > 0:
                print(f"  No seed42_inference.log files found (filtered out {filtered_count} files with _rm-)")
            else:
                print(f"  No seed42_inference.log files found")
            continue
        
        filtered_count = len(all_inference_logs) - len(inference_logs)
        if filtered_count > 0:
            print(f"  Found {len(inference_logs)} inference log files (filtered out {filtered_count} with _rm-)")
        else:
            print(f"  Found {len(inference_logs)} inference log files")
        
        # Collect all results for this folder
        all_results = []
        
        for log_path in inference_logs:
            filename = log_path.name
            task = extract_task_from_filename(filename)
            model = extract_model_from_filename(filename)
            
            if task is None or model is None:
                print(f"  Skipping {filename} (could not extract task or model)")
                continue
            
            print(f"  Processing: {filename}")
            print(f"    Task: {task}, Model: {model}")
            
            # Parse the log file
            log_results = parse_inference_log(log_path)
            
            # Add task and model to each result
            for result in log_results:
                result['task'] = task
                result['model'] = model
                all_results.append(result)
            
            print(f"    Found {len(log_results)} dat_path entries")
        
        # Write summary CSV for this folder
        if all_results:
            summary_df = pd.DataFrame(all_results)
            # Reorder columns
            summary_df = summary_df[['task', 'model', 'dat_path', 'total_time_ms', 'max_prompt_num']]
            # Sort by task, then model, then dat_path
            summary_df = summary_df.sort_values(by=['task', 'model', 'dat_path'])
            
            summary_path = folder_path / f"A_LLM_summary_{dataset}.csv"
            summary_df.to_csv(summary_path, index=False)
            print(f"  ✓ Wrote summary to: {summary_path}")
            print(f"    Total rows: {len(summary_df)}")
        else:
            print(f"  No results to write")
    
    # Check for missing dat_paths if requested
    if args.check_missing:
        check_missing_datpaths(log_dir)


if __name__ == "__main__":
    main()

