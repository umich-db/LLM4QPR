import pandas as pd
import glob
import os
import argparse
import re
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument("--dir", type=str)
parser.add_argument("--task", type=str)
args = parser.parse_args()

def strip_seed(filename):
    """Removes seed information to group files with same prefix"""
    return re.sub(r'_seed\d+', '', filename)

def build_quantile_table(csv_folder, quantiles=[50, 75, 90, 99]):
    """
    Aggregates quantiles across seed files by averaging values with the same prefix.
    """
    # 1. Find all CSV files
    csv_paths = glob.glob(os.path.join(csv_folder, f'{args.task}*cdf*seed*.csv'))

    # 2. Group files by prefix
    grouped_paths = defaultdict(list)
    for path in csv_paths:
        base = os.path.splitext(os.path.basename(path))[0]
        prefix = strip_seed(base)
        grouped_paths[prefix].append(path)

    # 3. Initialize table
    idx = quantiles + ['max']
    table = pd.DataFrame(index=idx, columns=grouped_paths.keys(), dtype=float)

    # 4. Compute average quantiles per group
    for prefix, paths in grouped_paths.items():
        quant_accumulator = {q: [] for q in quantiles}
        max_accumulator = []

        for path in paths:
            df = pd.read_csv(path).sort_values('percentage')
            max_q = df['Qerror'].max()
            max_accumulator.append(max_q)
            for q in quantiles:
                sub = df[df['percentage'] >= q]
                value = sub.iloc[0]['Qerror'] if not sub.empty else max_q
                quant_accumulator[q].append(value)

        for q in quantiles:
            table.at[q, prefix] = sum(quant_accumulator[q]) / len(quant_accumulator[q])
        table.at['max', prefix] = sum(max_accumulator) / len(max_accumulator)

    return table

csv_folder = args.dir
quant_table = build_quantile_table(csv_folder, [50, 90, 95])
quant_table = quant_table.reindex(sorted(quant_table.columns), axis=1)
quant_table.to_csv(csv_folder + f'/quantile_table_{args.dir.replace("/", "_")}_{args.task}.txt')
print(csv_folder, "\n", quant_table.to_markdown())
