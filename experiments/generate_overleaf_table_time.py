#!/usr/bin/env python3
"""
Generate LaTeX/Overleaf result tables for the time (cost) task, one per
(system db, workload group). Modeled on archive/tables/generate_overleaf_table.py
(reuses its LaTeX tabular / quantile-column layout and display helpers).

Each table has EXACTLY 7 method rows (4 baselines + 3 PRICE+LLM mode-12 frzEvenAll
jointMLP models) and one group of datasets (3 datasets x 4 quantiles = 12 columns).

Usage:
    python generate_overleaf_table_time.py --db postgres \
        --datasets tpch,tpcds,syn --task time \
        --output tables/overleaf_table_time_postgres_g1.tex
"""

import argparse
import os
import re
from typing import Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Display helpers (reused / adapted from archive/tables/generate_overleaf_table.py)
# ---------------------------------------------------------------------------

def format_algo_name_for_display(algo_name: str) -> str:
    """Format a baseline algorithm name for display (from archived script)."""
    if not algo_name:
        return algo_name
    algo_name_map = {
        'aimai': 'AiMeetsAi',
        'alece': 'ALECE',
        'bao': 'Bao',
        'e2e': 'E2E-Cost',
        'e2e_cost': 'E2E-Cost',
        'mscn': 'MSCN',
        'postgres': 'PostgreSQL',
        'price': 'PRICE',
        'qf': 'QueryFormer',
    }
    return algo_name_map.get(algo_name.lower(), algo_name)


def format_model_name_for_display(model_name: str) -> str:
    """Format an LLM model name for display (from archived script, extended)."""
    if not model_name:
        return model_name
    model_lower = model_name.lower()
    if 'sentence' in model_lower or 'minilm' in model_lower:
        return 'SentBERT'
    if 'l-2_h-256' in model_lower or 'l-2-h-256' in model_lower:
        return 'BERT-2'
    if 'l-4_h-768' in model_lower or 'l-4-h-768' in model_lower:
        return 'BERT-4'
    if 'modernbert' in model_lower:
        return 'ModernBert'
    if 'bert-base-uncased' in model_lower:
        return 'Bert'
    return model_name


def format_number(value: float) -> str:
    """Format a Q-error value to 2 decimals for LaTeX display."""
    if value is None or pd.isna(value):
        return '-'
    return f"{value:.2f}"


DATASET_DISPLAY = {
    'tpch': 'TPC-H',
    'tpcds': 'TPC-DS',
    'syn': 'Synthetic',
    'job': 'JOB-light',
    'job_full': 'JOB',
    'stats': 'STATS',
}

# dataset -> training workload (imdb family trains on `job`)
TRAIN_WL = {
    'tpch': 'tpch',
    'tpcds': 'tpcds',
    'stats': 'stats',
    'syn': 'job',
    'job': 'job',
    'job_full': 'job',
}

QUANTILE_COLS = ['50', '90', '95', 'max']

# The 7 methods, in fixed order. Each entry: (key, display_label, kind, matcher_factory)
# matcher_factory(db) -> function(col) -> bool


def _baseline_matcher(prefix_regex):
    def factory(db):
        pat = re.compile(prefix_regex.format(db=re.escape(db)))
        return lambda col: bool(pat.match(col))
    return factory


def _qf_matcher(db):
    target = f'time_qf_1.0_cdf_{db}_0.001_b64_h256'
    return lambda col: col == target


def _llm_matcher(model_token):
    def factory(db):
        def match(col):
            return (
                'llm_price_finetune_lora_biCrossAttn' in col
                and model_token in col
                and 'frzEven999' in col
                and col.endswith('_cdf')
            )
        return match
    return factory


def _llm_retrain_matcher(model_token):
    """retrainMLP variant of mode-12 frzEvenAll: the priceBiCrossAttnJoint
    (inference-phase, pretrained-lora) cdf instead of the finetune-phase jointMLP.
    Used for cells named via --frzeven_retrainMLP_cells."""
    def match(col):
        return (
            'priceBiCrossAttnJoint' in col
            and model_token in col
            and 'frzEven999' in col
        )
    return match


# method key -> model token (LLM rows only); lets us build the retrainMLP matcher.
LLM_MODEL_TOKEN = {
    'bert2': 'google-bert_uncased_L-2_H-256_A-4',
    'bert4': 'google-bert_uncased_L-4_H-768_A-12',
    'sentBert': 'sentence-transformers-all-MiniLM-L12-v2',
}


METHODS = [
    ('aimai',    format_algo_name_for_display('aimai'),
     _baseline_matcher(r'^time_aimai_.*_cdf_{db}_')),
    ('bao',      format_algo_name_for_display('bao'),
     _baseline_matcher(r'^time_bao_.*_cdf_{db}_')),
    ('e2e_cost', format_algo_name_for_display('e2e_cost'),
     _baseline_matcher(r'^time_e2e_cost_.*_cdf_{db}_')),
    ('qf',       format_algo_name_for_display('qf'),
     lambda db: _qf_matcher(db)),
    ('bert2',    'PRICE+' + format_model_name_for_display('google-bert_uncased_L-2_H-256_A-4'),
     _llm_matcher('google-bert_uncased_L-2_H-256_A-4')),
    ('bert4',    'PRICE+' + format_model_name_for_display('google-bert_uncased_L-4_H-768_A-12'),
     _llm_matcher('google-bert_uncased_L-4_H-768_A-12')),
    ('sentBert', 'PRICE+' + format_model_name_for_display('sentence-transformers-all-MiniLM-L12-v2'),
     _llm_matcher('sentence-transformers-all-MiniLM-L12-v2')),
]


def find_quantile_csv(db: str, dataset: str, task: str,
                      results_dir: str) -> str:
    train_wl = TRAIN_WL[dataset]
    stem = f"results_Train_{train_wl}_Test_{dataset}_ours"
    fname = f"quantile_table_results_{db}_{stem}_{task}.csv"
    if os.path.isabs(results_dir):
        base = results_dir
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), results_dir)
    return os.path.join(base, db, stem, fname)


def load_dataset_values(db: str, dataset: str, task: str, results_dir: str,
                        retrain_cells=frozenset()):
    """Return (values, missing, substituted) where values[method_key][quantile] =
    float or None, missing is a list of method keys with no matching column, and
    substituted is the set of LLM keys that used the retrainMLP variant here
    (because (key, db, dataset) was named in --frzeven_retrainMLP_cells)."""
    path = find_quantile_csv(db, dataset, task, results_dir)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df = df.set_index(df.columns[0])
    df.index = df.index.astype(str)
    cols = list(df.columns)

    values = {}
    missing = []
    substituted = set()
    for key, _label, matcher_factory in METHODS:
        # For LLM rows named in --frzeven_retrainMLP_cells, swap jointMLP -> retrainMLP.
        if (key in LLM_MODEL_TOKEN
                and (key.lower(), db.lower(), dataset.lower()) in retrain_cells):
            match = _llm_retrain_matcher(LLM_MODEL_TOKEN[key])
            substituted.add(key)
        else:
            match = matcher_factory(db)
        matched = [c for c in cols if match(c)]
        if len(matched) != 1:
            missing.append(key)
            values[key] = {q: None for q in QUANTILE_COLS}
            if len(matched) > 1:
                print(f"  WARNING: {db}/{dataset}/{key}: {len(matched)} columns "
                      f"matched, expected 1: {matched}")
            continue
        col = matched[0]
        values[key] = {}
        for q in QUANTILE_COLS:
            if q in df.index:
                v = df.loc[q, col]
                values[key][q] = float(v) if pd.notna(v) else None
            else:
                values[key][q] = None
    return values, missing, substituted


def generate_table(db: str, datasets, task: str, results_dir: str,
                   output_path: Optional[str], retrain_cells=frozenset()) -> str:
    # Load every dataset
    dataset_values = {}
    coverage_gaps = []  # (db, dataset, method_key)
    substituted = {}    # dataset -> set of LLM keys using retrainMLP
    for ds in datasets:
        vals, missing, subst = load_dataset_values(
            db, ds, task, results_dir, retrain_cells)
        dataset_values[ds] = vals
        substituted[ds] = subst
        for m in missing:
            coverage_gaps.append((db, ds, m))

    # Per (dataset, quantile) column: color the top-5 (lowest Q-error = best) cells
    # with the user's Overleaf-defined named colors green1..green5
    # (best -> green5, 2nd -> green4, ..., 5th -> green1). No bold.
    N_TOP = 5
    greennum = {}  # (dataset, quantile, method_key) -> 1..5 (5 = best)
    for ds in datasets:
        for q in QUANTILE_COLS:
            present = [(dataset_values[ds][k][q], k) for k, _l, _m in METHODS
                       if dataset_values[ds][k][q] is not None]
            present.sort(key=lambda t: t[0])   # ascending: best (lowest) first
            for pos, (_v, k) in enumerate(present[:N_TOP]):
                greennum[(ds, q, k)] = N_TOP - pos   # pos0->green5 (best) ... pos4->green1

    # ----- Build LaTeX -----
    col_spec = 'l' + ''.join('|' + 'c' * len(QUANTILE_COLS) for _ in datasets)

    db_display = {'postgres': 'PostgreSQL', 'duckdb': 'DuckDB',
                  'spark': 'Spark'}.get(db, db)
    group_names = ', '.join(DATASET_DISPLAY.get(d, d.upper()) for d in datasets)

    lines = []
    lines.append("% Requires \\usepackage[table]{xcolor} and \\definecolor{green1..green5} "
                 "(green5=best) in the preamble.")
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    _cap = f"Time Q-error on {db_display} ({group_names})"
    if any(substituted.values()):
        _cap += " ($^{r}$: retrainMLP variant)"
    lines.append(f"\\caption{{{_cap}}}")
    lines.append(f"\\label{{tab:overleaf_time_{db}_{'_'.join(datasets)}}}")
    lines.append("\\resizebox{\\linewidth}{!}{%")
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\toprule")

    # Header row 1: dataset names
    header1 = "\\multirow{2}{*}{Method}"
    for ds in datasets:
        disp = DATASET_DISPLAY.get(ds, ds.upper().replace('_', '-'))
        header1 += f" & \\multicolumn{{{len(QUANTILE_COLS)}}}{{c|}}{{{disp}}}"
    # trim the trailing '|' on the last multicolumn for nicer rendering
    header1 = header1.rstrip()
    if header1.endswith("{c|}{" + DATASET_DISPLAY.get(datasets[-1],
                        datasets[-1].upper().replace('_', '-')) + "}"):
        pass  # keep as-is; harmless visually
    lines.append(header1 + " \\\\")

    # Header row 2: quantile labels
    header2_parts = []
    for ds in datasets:
        for q in QUANTILE_COLS:
            header2_parts.append('Max' if q == 'max' else f"{q}th")
    lines.append(" & " + " & ".join(header2_parts) + " \\\\")
    lines.append("\\midrule")

    n_baselines = 4
    for i, (key, label, _matcher) in enumerate(METHODS):
        if i == n_baselines:
            lines.append("\\midrule")
        row_parts = [label]
        for ds in datasets:
            for q in QUANTILE_COLS:
                v = dataset_values[ds][key][q]
                cell = format_number(v)
                if v is not None and key in substituted.get(ds, ()):
                    cell += "$^{r}$"
                g = greennum.get((ds, q, key))
                if g is not None:
                    cell = f"\\cellcolor{{green{g}}}{{{cell}}}"
                row_parts.append(cell)
        lines.append(" & ".join(row_parts) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}%")
    lines.append("}")
    lines.append("\\end{table*}")

    latex = "\n".join(lines) + "\n"

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(latex)
        print(f"Wrote {output_path}")

    if coverage_gaps:
        print("Coverage gaps (db, dataset, method):")
        for g in coverage_gaps:
            print("  ", g)

    return latex


def main():
    parser = argparse.ArgumentParser(
        description='Generate a LaTeX overleaf time-task table for one (db, dataset-group).')
    parser.add_argument('--db', required=True, choices=['postgres', 'duckdb', 'spark'])
    parser.add_argument('--datasets', required=True,
                        help='Comma-separated datasets, e.g. tpch,tpcds,syn')
    parser.add_argument('--task', default='time', choices=['time'])
    parser.add_argument('--results_dir', default='results')
    parser.add_argument('--output', default=None, help='Output .tex path')
    parser.add_argument('--frzeven_retrainMLP_cells', nargs='*', default=[],
                        metavar='MODEL:DB:WORKLOAD',
                        help='Use the retrainMLP (priceBiCrossAttnJoint) frzEven999 '
                             'result instead of jointMLP for these cells, e.g. '
                             '--frzeven_retrainMLP_cells bert2:duckdb:tpcds sentbert:spark:tpcds')
    args = parser.parse_args()

    # parse MODEL:DB:WORKLOAD triples -> set of (model_lower, db_lower, wl_lower)
    retrain_cells = set()
    for spec in args.frzeven_retrainMLP_cells:
        parts = spec.split(':')
        if len(parts) != 3:
            parser.error(f"--frzeven_retrainMLP_cells entry must be MODEL:DB:WORKLOAD, got {spec!r}")
        retrain_cells.add((parts[0].lower(), parts[1].lower(), parts[2].lower()))

    datasets = [d.strip() for d in args.datasets.split(',') if d.strip()]
    latex = generate_table(args.db, datasets, args.task, args.results_dir,
                           args.output, retrain_cells)
    if not args.output:
        print(latex)


if __name__ == '__main__':
    main()
