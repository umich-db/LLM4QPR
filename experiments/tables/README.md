# LaTeX Table Generator

This script generates LaTeX/Overleaf table code from quantile table CSV files.

## Usage

```bash
python generate_overleaf_table.py --datasets <dataset1,dataset2,...> --task <time|card> [--output <output_file>] [--results_dir <dir>]
```

## Arguments

- `--datasets`: Comma-separated list of datasets (required, e.g., `tpch,tpcds,stats`)
- `--task`: Task type, either `time` or `card` (required)
- `--results_dir`: Results directory path (default: `results`)
- `--output`: Output file path (optional, defaults to stdout)

## Supported Datasets

- `tpch`: TPC-H
- `tpcds`: TPC-DS
- `stats`: STATS
- `syn`: SYN
- `job`: JOB
- `job_full`: JOB Full

## Features

- **Table Structure**:
  - **Rows**: Algorithms/models (non-LLM first, then LLM grouped by family)
  - **Columns**: Quantiles (50th, 90th, 95th, Max) for each dataset
- Combines multiple datasets into a single table
- Each dataset appears as a column group with 4 quantile columns
- Separates non-LLM and LLM algorithms with a double separator (`\midrule`)
- Groups LLM models by family (Llama, Qwen, Gemma, BERT) with single separators between families
- Colors top-3 non-LLM models per quantile per dataset: orange1 (3rd best) to orange3 (best)
- Colors top-5 LLM models per quantile per dataset: green1 (5th best) to green5 (best)
- Bolds the minimum value for each algorithm in each dataset (across all quantiles)

## Example

```bash
# Single dataset
python generate_overleaf_table.py \
  --datasets tpch \
  --task time \
  --output tpch_time_table.tex

# Multiple datasets
python generate_overleaf_table.py \
  --datasets tpch,tpcds,stats \
  --task time \
  --output combined_table.tex
```

## Output Format

The generated LaTeX table includes:
- Header rows with group names (Non-LLM, LLM)
- Data rows for quantiles: 50th, 90th, 95th, and max
- Proper column separators
- Color coding for top performers
- Bold formatting for minimum values

