#!/usr/bin/env python3
r"""
LaTeX table for the cross-engine averaged relative Q-error, one per LLM model
(bert2 / bert4 / sentbert) — the table form of cross_engine_aggregate.py's
create_relative_heatmap (..._simple_jointMLPonly_heatmap.png).

Per the user's request this is a SIMPLIFIED variant of the heatmap:
  - only the qf_priceConcat baseline is kept (aimai/bao/e2e_cost/qf dropped),
  - no baseline/LLM separator line,
  - jointMLP-only (the _retrainMLP columns are dropped, like the heatmap).

Coloring (matches the heatmap, via explicit \cellcolor[rgb]):
  - qf_priceConcat (the lone non-LLM): orange  rgb(1.0,0.5,0.0)
  - LLM rows: per-column green gradient, intensity 0.3 (best/lowest) -> 1.0 (worst),
    rgb(0.0,intensity,0.0); dark cells get white text for readability.
Annotation: an LLM name is bold-faced if it beats qf_priceConcat in >=2 columns.
(The heatmap's *** = "beats 2nd-best non-LLM" is dropped: with one baseline it is
degenerate.)

Usage:
    python generate_cross_engine_table.py --model bert4 \
        --output tables/cross_engine_table_time_bert4.tex
"""
import argparse
import os
from typing import Optional

import pandas as pd

QUANTILE_COLS = ['50', '90', '95', 'max']
NON_LLM = {'aimai', 'bao', 'e2e_cost', 'qf', 'qf_priceConcat', 'postgres'}
BASELINE = 'qf_priceConcat'
DEFAULT_VARIANT = 'frzEvenRetrain-bert2.duckdb.tpcds-sentbert.spark.tpcds'

MODEL_TITLE = {'bert2': 'bert2', 'bert4': 'bert4', 'sentbert': 'sentbert'}


def csv_path(model: str, anchor: str, variant: str, results_dir: str) -> str:
    fname = (f"relative_qerror_{model}_time_anchor{anchor}_{variant}_simple.csv")
    if os.path.isabs(results_dir):
        base = results_dir
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), results_dir)
    return os.path.join(base, "cross_engine", fname)


def fmt(value: float) -> str:
    """Match the heatmap: >=1000 -> scientific, else 2 decimals (LaTeX math sci)."""
    if value is None or pd.isna(value):
        return '-'
    if value >= 1000:
        mant = value
        exp = 0
        while mant >= 10:
            mant /= 10.0
            exp += 1
        return f"${mant:.2f}{{\\times}}10^{{{exp}}}$"
    return f"{value:.2f}"


def esc(s: str) -> str:
    return s.replace('_', '\\_').replace('%', '\\%')


def generate_table(model: str, anchor: str, variant: str, results_dir: str,
                   output_path: Optional[str]) -> str:
    path = csv_path(model, anchor, variant, results_dir)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df = df.set_index(df.columns[0])
    df.index = df.index.astype(str)

    cols = list(df.columns)
    # jointMLP-only: drop retrainMLP columns (like the heatmap's _jointMLPonly path)
    cols = [c for c in cols if '_retrainMLP' not in c]
    # keep qf_priceConcat + LLM columns only (drop the other baselines)
    llm_cols = [c for c in cols if c not in NON_LLM]
    if BASELINE not in cols:
        raise RuntimeError(f"{BASELINE} column not found in {path}")
    ordered = [BASELINE] + llm_cols          # baseline first, then LLMs (no separator)

    # values[method][q]
    vals = {m: {q: (float(df.loc[q, m]) if q in df.index and pd.notna(df.loc[q, m]) else None)
                for q in QUANTILE_COLS} for m in ordered}

    # bold LLMs that beat qf_priceConcat in >=2 columns
    bold = set()
    for m in llm_cols:
        wins = sum(1 for q in QUANTILE_COLS
                   if vals[m][q] is not None and vals[BASELINE][q] is not None
                   and vals[m][q] < vals[BASELINE][q])
        if wins >= 2:
            bold.add(m)

    # per-column LLM green intensity (rank ascending: best/lowest -> 0.3 darkest)
    green = {}   # (m, q) -> intensity
    for q in QUANTILE_COLS:
        present = sorted([(vals[m][q], m) for m in llm_cols if vals[m][q] is not None])
        n = len(present)
        for rank, (_v, m) in enumerate(present):
            green[(m, q)] = 0.3 + (rank / (n - 1)) * 0.7 if n > 1 else 0.65

    # ----- LaTeX -----
    col_spec = 'l|' + 'c' * len(QUANTILE_COLS)
    lines = []
    lines.append("% Requires \\usepackage[table]{xcolor} (for \\cellcolor) in the preamble.")
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\resizebox{\\linewidth}{!}{%")
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\toprule")
    lines.append("Method & 50th & 90th & 95th & Max \\\\")
    lines.append("\\midrule")

    for m in ordered:
        label = esc(m)
        if m in bold:
            label = f"\\textbf{{{label}}}"
        cells = [label]
        for q in QUANTILE_COLS:
            v = vals[m][q]
            cell = fmt(v)
            if v is None:
                cells.append(cell)
                continue
            if m == BASELINE:
                cell = f"\\cellcolor[rgb]{{1.0,0.5,0.0}}{{{cell}}}"
            else:
                inten = green[(m, q)]
                txt = "\\color{white}" if inten < 0.55 else ""
                cell = f"\\cellcolor[rgb]{{0.0,{inten:.3f},0.0}}{{{txt}{cell}}}"
            cells.append(cell)
        lines.append(" & ".join(cells) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}%")
    lines.append("}")
    lines.append(f"\\caption{{Averaged Relative Q-Error (time) --- {MODEL_TITLE.get(model, model)} "
                 f"$\\cdot$ simple avg. Orange: qf\\_priceConcat baseline; green: LLM "
                 f"(darkest = best per column); \\textbf{{bold}}: beats qf\\_priceConcat in $\\geq$2 columns.}}")
    lines.append(f"\\label{{tab:cross_engine_time_{model}}}")
    lines.append("\\end{table*}")
    latex = "\n".join(lines) + "\n"

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(latex)
        print(f"Wrote {output_path}")
    return latex


def main():
    p = argparse.ArgumentParser(description="Cross-engine averaged relative Q-error LaTeX table.")
    p.add_argument('--model', required=True, choices=['bert2', 'bert4', 'sentbert'])
    p.add_argument('--anchor', default='90', choices=['50', '90', '95', 'max'])
    p.add_argument('--variant', default=DEFAULT_VARIANT,
                   help='filename variant tag (default: the frzEvenRetrain canonical set)')
    p.add_argument('--results_dir', default='results')
    p.add_argument('--output', default=None)
    a = p.parse_args()
    latex = generate_table(a.model, a.anchor, a.variant, a.results_dir, a.output)
    if not a.output:
        print(latex)


if __name__ == '__main__':
    main()
