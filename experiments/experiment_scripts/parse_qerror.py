#!/usr/bin/env python3
"""
Extract Q-error percentile metrics from a CDF CSV file.

Usage:
    python parse_qerror.py <cdf_csv_path>

Outputs JSON to stdout:
    {"p50": 1.23, "p90": 4.56, "p95": 8.90, "max": 123.45}

The CDF CSV is expected to have columns: 'percentage' and 'Qerror'.
"""

import json
import sys

import pandas as pd


def parse_qerror(csv_path):
    df = pd.read_csv(csv_path).sort_values('percentage')
    result = {}
    for q in [50, 90, 95]:
        sub = df[df['percentage'] >= q]
        if not sub.empty:
            result[f'p{q}'] = float(sub.iloc[0]['Qerror'])
        else:
            result[f'p{q}'] = float(df['Qerror'].max())
    result['max'] = float(df['Qerror'].max())
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python parse_qerror.py <cdf_csv_path>", file=sys.stderr)
        sys.exit(1)
    result = parse_qerror(sys.argv[1])
    json.dump(result, sys.stdout)
    print()  # trailing newline
