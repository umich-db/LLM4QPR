#!/usr/bin/env python3
r"""
ONE combined LaTeX table for the cross-engine averaged relative Q-error across the
three LLM models (bert2, bert4, sentbert) -- the table form of the
cross_engine_aggregate.py _simple_jointMLPonly heatmaps, merged.

Layout: columns = 3 models x 4 quantiles (50/90/95/max), with the model name in
the column-group header (\multicolumn). Rows = 6 methods with fixed display names:
    QF + Canon (concat)         -> qf_priceConcat
    FT LLM + PRICE (concat)     -> [JointPrice] ..._priceB_..._jointMLP
    FT LLM + Canon (concat)     -> [JointPrice] ..._priceN-or_..._jointMLP (no biCrossAttn)
    FT LLM + Canon (cross-attn) -> [JointPrice] ..._priceN-or_...frzEven999_biCrossAttn..._jointMLP
    FT LLM                      -> <model>_quant-4-bit_jointMLP
    PT LLM                      -> <model>_quant-4-bit

Coloring (per model x quantile column, matching the heatmap, via \cellcolor[rgb]):
    QF + Canon (the lone non-LLM): orange rgb(1.0,0.5,0.0)
    the 5 LLM rows: green gradient, intensity 0.3 (best/lowest) -> 1.0 (worst),
        rgb(0.0,intensity,0.0); dark cells get white text.

Usage:
    python generate_cross_engine_combined_table.py \
        --output tables/cross_engine_table_time_combined.tex
"""
import argparse
import os
from typing import Optional

import pandas as pd

QUANTILE_COLS = ['50', '90', '95', 'max']
DEFAULT_VARIANT = 'frzEvenRetrain-bert2.duckdb.tpcds-sentbert.spark.tpcds'
MODELS = [('bert2', 'BERT-2'), ('bert4', 'BERT-4'), ('sentbert', 'SentBERT')]


def _m_qf(c):          return c == 'qf_priceConcat'
def _m_price_concat(c): return 'priceB' in c and 'jointMLP' in c and '_retrainMLP' not in c
def _m_canon_concat(c): return ('priceN-or' in c and 'jointMLP' in c
                                and 'biCrossAttn' not in c and '_retrainMLP' not in c)
def _m_canon_cross(c):  return 'priceN-or' in c and 'biCrossAttn' in c and '_retrainMLP' not in c
def _m_ft_llm(c):       return (c.endswith('_quant-4-bit_jointMLP')
                                and 'price' not in c.lower() and 'JointPrice' not in c)
def _m_pt_llm(c):       return (c.endswith('_quant-4-bit')
                                and 'jointMLP' not in c and 'price' not in c.lower())

# (display label, matcher, is_llm) in the requested row order
METHODS = [
    ('QF + Canon (concat)',         _m_qf,           False),
    ('FT LLM + PRICE (concat)',     _m_price_concat, True),
    ('FT LLM + Canon (concat)',     _m_canon_concat, True),
    ('FT LLM + Canon (cross-attn)', _m_canon_cross,  True),
    ('FT LLM',                      _m_ft_llm,       True),
    ('PT LLM',                      _m_pt_llm,       True),
]


def csv_path(model, anchor, variant, results_dir):
    fname = f"relative_qerror_{model}_time_anchor{anchor}_{variant}_simple.csv"
    base = results_dir if os.path.isabs(results_dir) else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), results_dir)
    return os.path.join(base, "cross_engine", fname)


def fmt(v):
    if v is None or pd.isna(v):
        return '-'
    if v >= 1000:
        mant, exp = v, 0
        while mant >= 10:
            mant /= 10.0; exp += 1
        return f"${mant:.2f}{{\\times}}10^{{{exp}}}$"
    return f"{v:.2f}"


def load_model(model, anchor, variant, results_dir):
    """Return values[row_label][quantile] = float|None for one model."""
    path = csv_path(model, anchor, variant, results_dir)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df = df.set_index(df.columns[0]); df.index = df.index.astype(str)
    cols = [c for c in df.columns if '_retrainMLP' not in c]
    out = {}
    for label, matcher, _is_llm in METHODS:
        matched = [c for c in cols if matcher(c)]
        if len(matched) != 1:
            print(f"  WARNING: {model}/{label}: matched {len(matched)} cols: {matched}")
            out[label] = {q: None for q in QUANTILE_COLS}
            continue
        col = matched[0]
        out[label] = {q: (float(df.loc[q, col]) if q in df.index and pd.notna(df.loc[q, col])
                          else None) for q in QUANTILE_COLS}
    return out


def generate(anchor, variant, results_dir, output_path: Optional[str]) -> str:
    per_model = {m: load_model(m, anchor, variant, results_dir) for m, _disp in MODELS}

    # green intensity per (model, quantile, llm_label): rank ascending among LLM rows
    llm_labels = [lab for lab, _m, is_llm in METHODS if is_llm]
    green = {}
    for m, _disp in MODELS:
        for q in QUANTILE_COLS:
            present = sorted([(per_model[m][lab][q], lab) for lab in llm_labels
                              if per_model[m][lab][q] is not None])
            n = len(present)
            for rank, (_v, lab) in enumerate(present):
                green[(m, q, lab)] = 0.3 + (rank / (n - 1)) * 0.7 if n > 1 else 0.65

    col_spec = 'l' + ''.join('|' + 'c' * len(QUANTILE_COLS) for _ in MODELS)
    lines = []
    lines.append("% Requires \\usepackage[table]{xcolor} (for \\cellcolor) in the preamble.")
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\resizebox{\\linewidth}{!}{%")
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\toprule")
    h1 = "\\multirow{2}{*}{Method}"
    for _m, disp in MODELS:
        h1 += f" & \\multicolumn{{{len(QUANTILE_COLS)}}}{{c|}}{{{disp}}}"
    lines.append(h1 + " \\\\")
    h2 = ""
    for _m, _disp in MODELS:
        h2 += " & 50th & 90th & 95th & Max"
    lines.append(h2 + " \\\\")
    lines.append("\\midrule")

    for label, _matcher, is_llm in METHODS:
        cells = [label]
        for m, _disp in MODELS:
            for q in QUANTILE_COLS:
                v = per_model[m][label][q]
                cell = fmt(v)
                if v is not None:
                    if not is_llm:
                        cell = f"\\cellcolor[rgb]{{1.0,0.5,0.0}}{{{cell}}}"
                    else:
                        inten = green[(m, q, label)]
                        txt = "\\color{white}" if inten < 0.55 else ""
                        cell = f"\\cellcolor[rgb]{{0.0,{inten:.3f},0.0}}{{{txt}{cell}}}"
                cells.append(cell)
        lines.append(" & ".join(cells) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}%")
    lines.append("}")
    lines.append("\\caption{Averaged relative Q-error (time), cross-engine simple average, "
                 "by LLM model. Orange: QF+Canon baseline; green: LLM variants "
                 "(darkest = best per column).}")
    lines.append("\\label{tab:cross_engine_time_combined}")
    lines.append("\\end{table*}")
    latex = "\n".join(lines) + "\n"

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(latex)
        print(f"Wrote {output_path}")
    return latex


def main():
    p = argparse.ArgumentParser(description="Combined cross-engine relative Q-error table (3 models).")
    p.add_argument('--anchor', default='90', choices=['50', '90', '95', 'max'])
    p.add_argument('--variant', default=DEFAULT_VARIANT)
    p.add_argument('--results_dir', default='results')
    p.add_argument('--output', default=None)
    a = p.parse_args()
    latex = generate(a.anchor, a.variant, a.results_dir, a.output)
    if not a.output:
        print(latex)


if __name__ == '__main__':
    main()
