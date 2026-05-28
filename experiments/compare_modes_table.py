"""Build a 3-row × 9-column table summarising three mode-vs-mode comparisons
across {postgres, duckdb, spark} × {bert2, bert4, sentbert}.

Rows (comparisons):
  R1: mode 7  beats mode 7b   (priceN-or vs priceB, no inflate, no biCross)
  R2: mode 12 beats mode 7    (with frzLLM5+pwm5 schedule)
  R3: mode 12 beats mode 12w  (mode 12 has the schedule, mode 12w doesn't)

Workloads: stats, tpch, tpcds, syn, job, job_full (train workload auto-mapped:
syn/job/job_full → train=job; others → train=self).

Scoring (per cell = db × model × comparison):
  For each quantile in {50, 90, 95, max}:
    1. Average A's Q-error across the 6 workloads → A_q_avg
    2. Average B's Q-error across the 6 workloads → B_q_avg
    3. +1 if A_q_avg < B_q_avg  (A is the "should-beat" side)
       -1 if A_q_avg > B_q_avg
        0 if equal
  Sum across 4 quantiles → cell ∈ [-4, +4].

Outputs the 3×9 table + per-column total + grand total.
"""
import csv, os, re, sys

DBS = ['postgres', 'duckdb', 'spark']
MODELS = {
    'bert2':    'google-bert_uncased_L-2_H-256_A-4',
    'bert4':    'google-bert_uncased_L-4_H-768_A-12',
    'sentbert': 'sentence-transformers-all-MiniLM-L12-v2',
}
WORKLOADS = [('stats','stats'), ('tpch','tpch'), ('tpcds','tpcds'),
             ('job','syn'), ('job','job'), ('job','job_full')]
QUANTS = [50, 90, 95, 'max']

# File pattern templates: <db> and <model> are substituted; <bs> is the
# finetune batch size (4 for tpch/tpcds, 24 for stats/imdb). Workload dirs
# follow `results/<db>/results_Train_<train>_Test_<test>_ours/`.
def fpath(db, model, train, test, mode):
    bs = '4' if train in ('tpch','tpcds') else '24'
    d = f'results/{db}/results_Train_{train}_Test_{test}_ours'
    if mode == 'M7':
        # mode 7: priceN_priceNor joint without biCross/inflate
        return f'{d}/time_llm_price_finetune_lora_{db}_0.0001_b{bs}_h2048_{model}_quant-4-bit_priceN_priceNor_randInit_e30_cdf_seed42.csv'
    elif mode == 'M7b':
        return f'{d}/time_llm_price_finetune_lora_{db}_0.0001_b{bs}_h2048_{model}_quant-4-bit_priceB_randInit_e30_cdf_seed42.csv'
    elif mode == 'M12':
        # mode 12 = the one WITH frzLLM5_pwm5 schedule (per repo convention)
        return f'{d}/time_llm_price_finetune_lora_biCrossAttn_{db}_0.0001_b{bs}_h2048_{model}_quant-4-bit_priceN_priceNor_inflatePRICE_randInit_cx4_frzLLM5_pwm5_e30_cdf_seed42.csv'
    elif mode == 'M12w':
        # mode 12w = NO warmup/freeze schedule (no frzLLM5/pwm5 tokens)
        return f'{d}/time_llm_price_finetune_lora_biCrossAttn_{db}_0.0001_b{bs}_h2048_{model}_quant-4-bit_priceN_priceNor_inflatePRICE_randInit_cx4_e30_cdf_seed42.csv'
    raise ValueError(f"unknown mode {mode}")

def read_quants(path):
    """Return {50, 90, 95, 'max'} from a CDF CSV. None if file missing."""
    if not os.path.isfile(path): return None
    with open(path) as f:
        r = csv.reader(f); next(r)
        rows = [(float(x[0]), float(x[1])) for x in r]
    if not rows: return None
    rows.sort()
    out = {}
    for q in [50, 90, 95]:
        for p, v in rows:
            if p >= q: out[q] = v; break
        else:
            out[q] = rows[-1][1]
    out['max'] = max(v for _, v in rows)
    return out

COMPARISONS = [
    ('M7  beats M7b',  'M7',  'M7b'),
    ('M12 beats M7',   'M12', 'M7'),
    ('M12 beats M12w', 'M12', 'M12w'),
]

# Build 3×9 table.  Score = sum over 4 quantiles of sign(B_avg − A_avg),
# where A_avg / B_avg are averages of Q-error across the 6 workloads.
table = {}
detail = {}  # (W, L, T, n_workloads_with_pair)
for rlbl, a_mode, b_mode in COMPARISONS:
    for db in DBS:
        for mlbl, mvar in MODELS.items():
            # Collect per-quantile lists across workloads where BOTH modes have data
            a_vals = {q: [] for q in QUANTS}
            b_vals = {q: [] for q in QUANTS}
            n_pairs = 0
            for tr, ts in WORKLOADS:
                a = read_quants(fpath(db, mvar, tr, ts, a_mode))
                b = read_quants(fpath(db, mvar, tr, ts, b_mode))
                if a is None or b is None:
                    continue
                for q in QUANTS:
                    a_vals[q].append(a[q])
                    b_vals[q].append(b[q])
                n_pairs += 1
            cell = 0; W = L = T = 0
            for q in QUANTS:
                if not a_vals[q]:
                    T += 1; continue
                am = sum(a_vals[q]) / len(a_vals[q])
                bm = sum(b_vals[q]) / len(b_vals[q])
                if am < bm:   cell += 1; W += 1
                elif am > bm: cell -= 1; L += 1
                else:         T += 1
            table[(rlbl, db, mlbl)] = cell
            detail[(rlbl, db, mlbl)] = (W, L, T, n_pairs)

# Render
col_labels = [f'{db}/{m}' for db in DBS for m in MODELS.keys()]
print(f"{'Comparison':<18} | " + " | ".join(f'{c:>12}' for c in col_labels) + " | row_sum")
print('-' * (18 + 13 * 9 + 12))
row_sums = []
for rlbl, _, _ in COMPARISONS:
    cells = [table[(rlbl, db, m)] for db in DBS for m in MODELS]
    rsum = sum(cells)
    row_sums.append(rsum)
    cell_strs = [f'{c:+d}' for c in cells]
    print(f"{rlbl:<18} | " + " | ".join(f'{s:>12}' for s in cell_strs) + f" | {rsum:+d}")

# Column sums
col_sums = []
for col_idx, (db, m) in enumerate([(d, m) for d in DBS for m in MODELS]):
    col_sums.append(sum(table[(r, db, m)] for r, _, _ in COMPARISONS))
print('-' * (18 + 13 * 9 + 12))
print(f"{'COL SUM':<18} | " + " | ".join(f'{s:+12d}' for s in col_sums) + f" | {sum(row_sums):+d}")
print()
print("Detail (per cell W / L / T over 4 quantiles, averaged across workloads):")
for rlbl, _, _ in COMPARISONS:
    print(f"\n  {rlbl}:")
    for db in DBS:
        line = f"    {db:<9}"
        for mlbl in MODELS:
            W,L,T,n = detail[(rlbl, db, mlbl)]
            line += f"  {mlbl:<8} W={W}/L={L}/T={T} (n={n}wl)"
        print(line)
