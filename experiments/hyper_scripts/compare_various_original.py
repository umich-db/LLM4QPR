import os
import pandas as pd
import numpy as np
from collections import defaultdict


def load_data(_1B_card, _1B_time, _3B_card, _3B_time, _8B_card, _8B_time, _70B_card, _70B_time):
    """
    Load CSV data from a list of files.
    """
    data = {'_1B_card': {}, '_1B_time': {},
            '_3B_card': {}, '_3B_time': {},
            '_8B_card': {}, '_8B_time': {},
            '_70B_card': {}, '_70B_time': {}}

    for file in _1B_card:
        df = pd.read_csv(file)
        data['_1B_card'][file] = df

    for file in _1B_time:
        df = pd.read_csv(file)
        data['_1B_time'][file] = df

    for file in _3B_card:
        df = pd.read_csv(file)
        data['_3B_card'][file] = df

    for file in _3B_time:
        df = pd.read_csv(file)
        data['_3B_time'][file] = df

    for file in _8B_card:
        df = pd.read_csv(file)
        data['_8B_card'][file] = df

    for file in _8B_time:
        df = pd.read_csv(file)
        data['_8B_time'][file] = df

    for file in _70B_card:
        df = pd.read_csv(file)
        data['_70B_card'][file] = df

    for file in _70B_time:
        df = pd.read_csv(file)
        data['_70B_time'][file] = df
    
    
    return data

def calculate_quantiles(df, quantiles=[0.5, 0.9, 0.95, 1.0]):
    """
    Calculate specified quantiles of the 'abs_error' column.
    """
    return df['q_error'].quantile(quantiles)

def average_grouped_data(data):
    """
    Average multiple CSVs differing only in seed, and use the common prefix (excluding seed) as the key.
    """
    averaged_data = {}

    for category in data:
        grouped_files = defaultdict(list)

        # Group by common prefix (removing '_seedXX.csv')
        for file in data[category].keys():
            basename = os.path.basename(file)
            if basename.endswith('.csv') and '_seed' in basename:
                key = basename.rsplit('_seed', 1)[0]
                grouped_files[key].append(file)

        averaged_data[category] = {}

        # Average each group and store under the simplified key
        for group_key, file_list in grouped_files.items():
            dfs = [data[category][f] for f in file_list]
            df_concat = pd.concat(dfs)
            df_avg = df_concat.groupby(df_concat.index).mean()  # average by row
            averaged_data[category][group_key] = df_avg

    return averaged_data

def compare_settings(data, quantiles=[0.5, 0.9, 0.95, 1.0]):
    """
    Compare different settings within each category based on the quantiles and count the wins.
    """
    results = {}
    
    averaged_data = average_grouped_data(data)
    
    # Iterate over 'card' and 'time' categories
    for category in averaged_data:


        wins = {file: 0 for file in averaged_data[category].keys()}
        
        # Iterate over each quantile
        for quantile in quantiles:
            # For each quantile, find the setting with the minimum error
            for file_a, df_a in averaged_data[category].items():
                for file_b, df_b in averaged_data[category].items():
                    if file_a != file_b:
                        # Compare the quantile errors
                        quantile_a = df_a['q_error'].quantile(quantile)
                        quantile_b = df_b['q_error'].quantile(quantile)
                        
                        if quantile_a < quantile_b:
                            wins[file_a] += 1
                        elif quantile_b < quantile_a:
                            wins[file_b] += 1


            quantile_errors = {file: calculate_quantiles(df, [quantile])[quantile] for file, df in averaged_data[category].items()}

            # Find the winner of this round
            # winner = min(quantile_errors, key=quantile_errors.get)
            
            # Increment the win for the setting with the smallest error
            # wins[winner] += 1
            
        results[category] = [wins, quantile_errors]
    
    return results, averaged_data

def main(directory):
    """
    Main function to process all CSV files in the directory and determine the best setting.
    """

    _1B_card = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('1B') and f.startswith('card')]
    _1B_time = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('1B') and f.startswith('time')]
    _3B_card = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('3B') and f.startswith('card')]
    _3B_time = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('3B') and f.startswith('time')]

    _8B_card = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('8B') and f.startswith('card')]
    _8B_time = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('8B') and f.startswith('time')]

    _70B_card = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('70B') and f.startswith('card')]
    _70B_time = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and f.__contains__('qerror') and f.__contains__('70B') and f.startswith('time')]

    # Load all data
    data = load_data(_1B_card, _1B_time, _3B_card, _3B_time, _8B_card, _8B_time, _70B_card, _70B_time)

    # Compare the settings and get the wins
    results, averaged_data = compare_settings(data)
    
    for category, w in results.items():
        wins = w[0]
        best_setting = max(wins, key=wins.get)
        print(f"The best setting for category {category} is: {best_setting} with {wins[best_setting]} wins")

        # os.path.join(directory, f'{best_setting}_')
        print(calculate_quantiles(averaged_data[category][best_setting]))

        print()

        
    output_file = "best_settings_summary.txt"

    with open(output_file, "w") as f:
        for category, w in results.items():
            wins = w[0]
            best_setting = max(wins, key=wins.get)
            f.write(f"The best setting for category {category} is: {best_setting} with {wins[best_setting]} wins\n")

            quantiles = calculate_quantiles(averaged_data[category][best_setting])
            f.write(f"{quantiles}\n\n")



        # print(f"Win counts: {wins}")


main("results/root/query-plan-representation/experiments/results/results_Train_stats_Test_stats_ours")
