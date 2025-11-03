import os
import pandas as pd
import numpy as np
from collections import defaultdict
import glob


def load_data_from_directory(base_dir):
    """
    Load CSV data from the results_various directory structure.
    Returns a dictionary organized by dataset, task_type, and model.
    """
    data = {}
    
    # Find all dataset directories
    dataset_dirs = [d for d in os.listdir(base_dir) if d.startswith('results_Train_')]
    
    for dataset_dir in dataset_dirs:
        dataset_name = dataset_dir.replace('results_Train_', '').replace('_Test_', '_').replace('_ours', '')
        data[dataset_name] = {'card': {}, 'time': {}}
        
        dataset_path = os.path.join(base_dir, dataset_dir)
        
        # Find all CSV files in this dataset directory
        csv_files = glob.glob(os.path.join(dataset_path, "*.csv"))
        
        for csv_file in csv_files:
            filename = os.path.basename(csv_file)
            
            # Only process CDF files, skip length_vs_qerror files
            if 'length_vs_qerror' in filename:
                continue
            
            # Determine task type (card or time)
            if filename.startswith('card_'):
                task_type = 'card'
            elif filename.startswith('time_'):
                task_type = 'time'
            else:
                continue
            
            # Extract model name from filename
            if 'meta-llama-Llama-3.2-1B' in filename:
                model = '1B'
            elif 'meta-llama-Llama-3.2-3B' in filename:
                model = '3B'
            elif 'meta-llama-Llama-3.1-8B' in filename:
                model = '8B'
            elif 'meta-llama-Llama-3.1-70B' in filename:
                model = '70B'
            else:
                continue
            
            # Load the CSV data
            try:
                df = pd.read_csv(csv_file)
                data[dataset_name][task_type][filename] = df
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                continue
    
    return data


def calculate_quantiles(df, quantiles=[0.5, 0.9, 0.95, 1.0]):
    """
    Calculate specified quantiles of the error column.
    Handles both 'Qerror' and 'q_error' column names.
    """
    if 'Qerror' in df.columns:
        return df['Qerror'].quantile(quantiles)
    elif 'q_error' in df.columns:
        return df['q_error'].quantile(quantiles)
    else:
        raise ValueError(f"Neither 'Qerror' nor 'q_error' column found. Available columns: {list(df.columns)}")


def average_grouped_data(data):
    """
    Average multiple CSVs differing only in seed, and use the common prefix (excluding seed) as the key.
    """
    averaged_data = {}
    
    for dataset_name in data:
        averaged_data[dataset_name] = {'card': {}, 'time': {}}
        
        for task_type in ['card', 'time']:
            grouped_files = defaultdict(list)
            
            # Group by common prefix (removing '_seedXX.csv')
            for filename in data[dataset_name][task_type].keys():
                if filename.endswith('.csv') and '_seed' in filename:
                    key = filename.rsplit('_seed', 1)[0]
                    grouped_files[key].append(filename)
            
            # Average each group and store under the simplified key
            for group_key, file_list in grouped_files.items():
                if len(file_list) >= 3:  # Ensure we have all 3 seeds
                    dfs = [data[dataset_name][task_type][f] for f in file_list]
                    df_concat = pd.concat(dfs)
                    df_avg = df_concat.groupby(df_concat.index).mean()  # average by row
                    averaged_data[dataset_name][task_type][group_key] = df_avg
                else:
                    print(f"Warning: Only {len(file_list)} seeds found for {group_key}")
    
    return averaged_data


def compare_settings(data, quantiles=[0.5, 0.9, 0.95, 1.0]):
    """
    Compare different settings within each dataset and task type based on the quantiles and count the wins.
    """
    results = {}
    
    averaged_data = average_grouped_data(data)
    
    for dataset_name in averaged_data:
        results[dataset_name] = {}
        
        for task_type in ['card', 'time']:
            if not averaged_data[dataset_name][task_type]:
                continue
                
            wins = {filename: 0 for filename in averaged_data[dataset_name][task_type].keys()}
            quantile_errors = {}
            
            # Iterate over each quantile
            for quantile in quantiles:
                quantile_errors[quantile] = {}
                
                # Calculate quantile errors for all settings
                for filename, df in averaged_data[dataset_name][task_type].items():
                    quantile_errors[quantile][filename] = calculate_quantiles(df, [quantile])[quantile]
                
                # Do pairwise comparisons for this quantile
                settings = list(averaged_data[dataset_name][task_type].keys())
                for i, setting_a in enumerate(settings):
                    for j, setting_b in enumerate(settings):
                        if i < j:  # Avoid duplicate comparisons
                            error_a = quantile_errors[quantile][setting_a]
                            error_b = quantile_errors[quantile][setting_b]
                            
                            if error_a < error_b:
                                wins[setting_a] += 1
                            elif error_b < error_a:
                                wins[setting_b] += 1
                            # If equal, no one wins
            
            results[dataset_name][task_type] = {
                'wins': wins,
                'quantile_errors': quantile_errors
            }
    
    return results, averaged_data


def extract_hyperparameters(filename):
    """
    Extract hyperparameters from filename for better display.
    """
    parts = filename.split('_')
    hyperparams = {}
    
    for part in parts:
        if part.startswith('b') and part[1:].isdigit():
            hyperparams['batch_size'] = int(part[1:])
        elif part.startswith('h') and part[1:].isdigit():
            hyperparams['hidden_units'] = int(part[1:])
        elif part.startswith('emb') and part[3:].isdigit():
            hyperparams['embed_size'] = int(part[3:])
        elif 'meta-llama-Llama' in part:
            if '1B' in part:
                hyperparams['model'] = 'Llama-3.2-1B'
            elif '3B' in part:
                hyperparams['model'] = 'Llama-3.2-3B'
            elif '8B' in part:
                hyperparams['model'] = 'Llama-3.1-8B'
            elif '70B' in part:
                hyperparams['model'] = 'Llama-3.1-70B'
    
    return hyperparams


def main(base_dir):
    """
    Main function to process all CSV files in the results_various directory and determine the best settings.
    """
    print(f"Loading data from {base_dir}...")
    data = load_data_from_directory(base_dir)
    
    print("Comparing settings...")
    results, averaged_data = compare_settings(data)
    
    # Print results grouped by dataset+model+task
    for dataset_name in results:
        print(f"\n{'='*60}")
        print(f"DATASET: {dataset_name}")
        print(f"{'='*60}")
        
        for task_type in ['card', 'time']:
            if task_type not in results[dataset_name]:
                continue
                
            print(f"\n{task_type.upper()} TASK:")
            print("-" * 40)
            
            wins = results[dataset_name][task_type]['wins']
            if not wins:
                print("No results found.")
                continue
            
            # Group by model
            model_groups = {}
            for filename, win_count in wins.items():
                hyperparams = extract_hyperparameters(filename)
                model = hyperparams.get('model', 'Unknown')
                if model not in model_groups:
                    model_groups[model] = []
                model_groups[model].append((filename, win_count))
            
            # Sort each model group by wins and show top 3
            for model_name in sorted(model_groups.keys()):
                print(f"\n--- {model_name} ---")
                model_settings = model_groups[model_name]
                sorted_model_settings = sorted(model_settings, key=lambda x: x[1], reverse=True)
                
                print("Top 3 settings:")
                for rank, (filename, win_count) in enumerate(sorted_model_settings[:3], 1):
                    hyperparams = extract_hyperparameters(filename)
                    embed_size = hyperparams.get('embed_size', 'N/A')
                    batch_size = hyperparams.get('batch_size', 'N/A')
                    hidden_units = hyperparams.get('hidden_units', 'N/A')
                    
                    print(f"  Rank {rank}: {win_count} wins")
                    print(f"    Embed Size: {embed_size}, Batch Size: {batch_size}, Hidden Units: {hidden_units}")
                    
                    quantile_errors = results[dataset_name][task_type]['quantile_errors']
                    print("    Quantile Errors:")
                    for quantile in [0.5, 0.9, 0.95, 1.0]:
                        error = quantile_errors[quantile][filename]
                        print(f"      {quantile}: {error:.6f}")
                    print()
    
    # Save results to file
    output_file = "hyperparameter_comparison_results.txt"
    with open(output_file, "w") as f:
        f.write("HYPERPARAMETER COMPARISON RESULTS - TOP 3 PER DATASET+MODEL+TASK\n")
        f.write("="*70 + "\n\n")
        
        for dataset_name in results:
            f.write(f"DATASET: {dataset_name}\n")
            f.write("="*50 + "\n\n")
            
            for task_type in ['card', 'time']:
                if task_type not in results[dataset_name]:
                    continue
                    
                f.write(f"{task_type.upper()} TASK:\n")
                f.write("-" * 30 + "\n")
                
                wins = results[dataset_name][task_type]['wins']
                if not wins:
                    f.write("No results found.\n\n")
                    continue
                
                # Group by model
                model_groups = {}
                for filename, win_count in wins.items():
                    hyperparams = extract_hyperparameters(filename)
                    model = hyperparams.get('model', 'Unknown')
                    if model not in model_groups:
                        model_groups[model] = []
                    model_groups[model].append((filename, win_count))
                
                # Sort each model group by wins and show top 3
                for model_name in sorted(model_groups.keys()):
                    f.write(f"\n--- {model_name} ---\n")
                    model_settings = model_groups[model_name]
                    sorted_model_settings = sorted(model_settings, key=lambda x: x[1], reverse=True)
                    
                    f.write("Top 3 settings:\n")
                    for rank, (filename, win_count) in enumerate(sorted_model_settings[:3], 1):
                        hyperparams = extract_hyperparameters(filename)
                        embed_size = hyperparams.get('embed_size', 'N/A')
                        batch_size = hyperparams.get('batch_size', 'N/A')
                        hidden_units = hyperparams.get('hidden_units', 'N/A')
                        
                        f.write(f"  Rank {rank}: {win_count} wins\n")
                        f.write(f"    Embed Size: {embed_size}, Batch Size: {batch_size}, Hidden Units: {hidden_units}\n")
                        f.write(f"    Filename: {filename}\n")
                        
                        quantile_errors = results[dataset_name][task_type]['quantile_errors']
                        f.write("    Quantile Errors:\n")
                        for quantile in [0.5, 0.9, 0.95, 1.0]:
                            error = quantile_errors[quantile][filename]
                            f.write(f"      {quantile}: {error:.6f}\n")
                        f.write("\n")
                
                f.write("\n")
    
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    base_directory = "results_various"
    main(base_directory)
