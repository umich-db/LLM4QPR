#!/usr/bin/env python3
"""
Generate the Llama-8B vs Llama-8B+PRICE comparison tables (50th/95th Q-error).

Cost table  (full width):  TPC-H, TPC-DS, Synthetic, JOB-light, JOB, STATS
    methods: E2E-Cost, QueryFormer (3-seed averages from DOUG_RESULTS quantile
    tables), Llama-8B (mode 1, same source), Llama-8B + PRICE (mode 8b:
    frozen LLM + priceB; retrainMLP head, except JOB-full which uses the
    jointMLP head — see --jointmlp_workloads).
Card table  (half width):  Synthetic, JOB-light, STATS
    methods: ALECE, PRICE (from combined_timing_accuracy_report.csv),
    Llama-8B, Llama-8B + PRICE (retrainMLP).

Llama-8B + PRICE values are averaged over every seed found on disk
(_seed42/43/44 result CDFs); the per-table comment records the seed count.
The card table is wrapped in \\resizebox{0.5\\textwidth}{!}{...} so it takes
half the text width instead of the whole row.

Usage:
    python generate_llama8b_price_tables.py
        [--doug_results /root/doug/results]
        [--report /root/doug/combined_timing_accuracy_report.csv]
        [--results /root/LLM4QPR/experiments/results/postgres]
        [--out_dir /root/LLM4QPR/experiments/tables]
"""

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd

TIME_DS = ['tpch', 'tpcds', 'syn', 'job', 'job_full', 'stats']
CARD_DS = ['syn', 'job', 'stats']
DISP = {'tpch': 'TPC-H', 'tpcds': 'TPC-DS', 'syn': 'Synthetic',
        'job': 'JOB-light', 'job_full': 'JOB', 'stats': 'STATS'}
JOINTMLP_WORKLOADS = {('time', 'job_full')}   # use the jointMLP head here
TIME_QUANTS = (50, 90, 95, 'max')
CARD_QUANTS = (50, 90, 95, 'max')


def qlabel(q):
    return 'Max' if q == 'max' else f'{q}th'


def cdf_quantiles(path, quants):
    df = pd.read_csv(path).sort_values('percentage')
    out = []
    for t in quants:
        if t == 'max':
            out.append(float(df.Qerror.max()))
            continue
        sub = df[df.percentage >= t]
        out.append(float(sub.iloc[0].Qerror) if not sub.empty else float(df.Qerror.max()))
    return out


def doug_quantiles(doug_results, ds, task, col_prefix, must_contain=None, quants=TIME_QUANTS):
    f = (Path(doug_results) / f'results_Train_{ds}_Test_{ds}_ours' /
         f'quantile_table_results_results_Train_{ds}_Test_{ds}_ours_{task}.csv')
    df = pd.read_csv(f, index_col=0)
    df.index = df.index.map(str)
    cands = [c for c in df.columns if c.startswith(col_prefix)
             and (must_contain is None or must_contain in c)]
    if not cands:
        return None
    c = cands[0]
    return [float(df.loc[str(q), c]) for q in quants]


def mode8b_quantiles(results_dir, task, ds, quants=TIME_QUANTS):
    """Average across all seeds found. Returns (values, n_seeds)."""
    tr = 'job' if ds in ('job', 'syn', 'job_full') else ds
    d = Path(results_dir) / f'results_Train_{tr}_Test_{ds}_ours'
    prefix = 'card' if task == 'card' else 'time'
    use_joint = (prefix, ds) in JOINTMLP_WORKLOADS
    if use_joint:
        pat = str(d / f'{prefix}_llm_price_finetune_frozen*Llama-3.1-8B*priceB*.csv')
    else:
        pat = str(d / f'{prefix}_llm_price_pretrained-None_priceFTwithLLM*Llama-3.1-8B*priceB*.csv')
    files = [f for f in glob.glob(pat) if 'length' not in f]
    if not files:
        return None, 0
    per_seed = [cdf_quantiles(f, quants) for f in sorted(files)]
    return list(np.mean(per_seed, axis=0)), len(per_seed)


def fmt(v):
    if v >= 1000 or (v < 0.01 and v != 0):
        return f"{v:.2e}"
    if v < 100:
        return f"{v:.3f}"
    return f"{v:.2f}"


def render(data, ds_list, methods, sep_after, header_label="Algorithm", quants=TIME_QUANTS):
    n = len(ds_list)
    lines = []
    lines.append("\\begin{tabular}{l|" + "|".join(["c" * len(quants)] * n) + "}")
    lines.append("\\toprule")
    h1 = f"\\multirow{{2}}{{*}}{{{header_label}}}"
    for i, ds in enumerate(ds_list):
        bar = '|' if i < n - 1 else ''
        h1 += f" & \\multicolumn{{{len(quants)}}}{{c{bar}}}{{{DISP[ds]}}}"
    lines.append(h1 + " \\\\")
    _qh = " & ".join(qlabel(q) for q in quants)
    lines.append(" & " + " & ".join([_qh] * n) + " \\\\")
    lines.append("\\midrule")
    # Per-column rank -> green shading: best=green4, 2nd=green3, 3rd=green2,
    # 4th=green1 (requires the green1..green4 color definitions used by the
    # other overleaf tables).
    ranks = {}
    for ds in ds_list:
        for qi in range(len(quants)):
            vals = sorted({data[ds][m][qi] for m in methods if data[ds].get(m)})
            for m in methods:
                if data[ds].get(m):
                    r = vals.index(data[ds][m][qi])  # 0 = best
                    ranks[(ds, qi, m)] = max(1, 4 - r)  # green4..green1
    for m in methods:
        cells = [m]
        for ds in ds_list:
            vals = data[ds].get(m)
            for qi in range(len(quants)):
                if vals is None:
                    cells.append('-')
                    continue
                g = ranks[(ds, qi, m)]
                cells.append(f"\\cellcolor{{green{g}}}{{{fmt(vals[qi])}}}")
        lines.append(" & ".join(cells) + " \\\\")
        if m == sep_after:
            lines.append("\\midrule")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--doug_results', default='/root/doug/results')
    ap.add_argument('--report', default='/root/doug/combined_timing_accuracy_report.csv')
    ap.add_argument('--results', default='/root/LLM4QPR/experiments/results/postgres')
    ap.add_argument('--out_dir', default=str(Path(__file__).parent))
    args = ap.parse_args()

    # ---- cost ----
    time_data, time_seeds = {}, {}
    for ds in TIME_DS:
        time_data[ds] = {
            'E2E-Cost': doug_quantiles(args.doug_results, ds, 'time', 'time_e2e_cost_1.0'),
            'QueryFormer': doug_quantiles(args.doug_results, ds, 'time', 'time_qf_1.0'),
            'Llama-8B': doug_quantiles(args.doug_results, ds, 'time',
                                       'time_llm_pretrained-None_1.0', 'Llama-3.1-8B'),
        }
        time_data[ds]['Llama-8B + Statistics'], time_seeds[ds] = \
            mode8b_quantiles(args.results, 'time', ds)

    # ---- card ----
    rep = pd.read_csv(args.report)
    card_data, card_seeds = {}, {}
    for ds in CARD_DS:
        d = {}
        for label, algo in [('ALECE', 'alece'), ('PRICE', 'price')]:
            r = rep[(rep.dataset == ds) & (rep.task == 'card') & (rep.algo == algo)]
            d[label] = ([float(r.iloc[0].q50), float(r.iloc[0].q90),
                         float(r.iloc[0].q95), float(r.iloc[0].qmax)] if len(r) else None)
        d['Llama-8B'] = doug_quantiles(args.doug_results, ds, 'card',
                                       'card_llm_pretrained-None_1.0', 'Llama-3.1-8B',
                                       quants=CARD_QUANTS)
        d['Llama-8B + Statistics'], card_seeds[ds] = mode8b_quantiles(
            args.results, 'card', ds, quants=CARD_QUANTS)
        card_data[ds] = d

    t_time = render(time_data, TIME_DS,
                    ['E2E-Cost', 'QueryFormer', 'Llama-8B', 'Llama-8B + Statistics'],
                    'QueryFormer', header_label='\\textbf{Cost Estimation}')
    t_card = render(card_data, CARD_DS,
                    ['ALECE', 'PRICE', 'Llama-8B', 'Llama-8B + Statistics'],
                    'PRICE', header_label='\\textbf{Cardinality Estimation}',
                    quants=CARD_QUANTS)

    out = Path(args.out_dir)
    hdr_t = ("% Cost estimation, 50th/95th Q-error. Baselines + Llama-8B: 3-seed avgs from\n"
             f"% {args.doug_results}. Llama-8B+PRICE: mode 8b (frozen LLM, priceB), avg over\n"
             f"% seeds found per cell: {[(d, time_seeds[d]) for d in TIME_DS]}.\n"
             "% JOB uses the jointMLP head; all other cells retrainMLP.\n")
    hdr_c = ("% Cardinality estimation, 50th/95th Q-error. ALECE/PRICE from\n"
             f"% {args.report}; Llama-8B: 3-seed avg. Llama-8B+PRICE: mode 8b retrainMLP,\n"
             f"% avg over seeds found per cell: {[(d, card_seeds[d]) for d in CARD_DS]}.\n"
             "% Cells shaded green4 (best) .. green1 (4th) per column.\n")
    (out / 'overleaf_table_llama8b_price_time.tex').write_text(hdr_t + t_time + "\n")
    (out / 'overleaf_table_llama8b_price_card.tex').write_text(hdr_c + t_card + "\n")
    print(t_time)
    print()
    print(t_card)
    print(f"\nSeeds per cell — time: {time_seeds}  card: {card_seeds}")
    print(f"Saved to {out}/overleaf_table_llama8b_price_{{time,card}}.tex")


if __name__ == '__main__':
    main()
