"""Build a 3-row × 9-column table summarising three mode-vs-mode comparisons
across {postgres, duckdb, spark} × {bert2, bert4, sentbert}.

Rows (comparisons):
  R1: mode 7  beats mode 7b   (priceN-or vs priceB, no inflate, no biCross)
  R2: mode 12 beats mode 7    (with frzLLM5+pwm5 schedule)
  R3: mode 12 beats mode 12w  (mode 12 has the schedule, mode 12w doesn't)

Data source: the per-db `relative_qerror_<db>_time_anchor<ANCHOR>.csv` files
produced by to_table_relative.py. These already contain the workload-averaged
relative Q-error (per-row normalisation by the anchor-quantile minimum across
methods, then averaged across the db's workloads). We just look up the two
method columns per comparison and sign-compare their values at each of the
4 quantile rows {50, 90, 95, max}.

Scoring (per cell = db × model × comparison):
  Count how many of the 4 quantiles {50, 90, 95, max} A wins on (A_q < B_q)
  and how many B wins on. Cell ∈ {-1, 0, +1}:
    +1 if A wins more quantiles
    -1 if B wins more
     0 if tied (equal win count)

Override the source anchor with ANCHOR=50|90|95|max (env var).
"""
import csv, os, sys

ANCHOR = os.environ.get('ANCHOR', '90')

DBS = ['postgres', 'duckdb', 'spark']
# (label, model token as it appears in the relative-table column names)
MODELS = {
    'bert2':    'google-bert_uncased_L-2_H-256_A-4',
    'bert4':    'google-bert_uncased_L-4_H-768_A-12',
    'sentbert': 'sentBert-all',
}

# Column names per mode (slot into the model token).
def col_name(model_tok, mode):
    """The exact display name to_table_relative.py uses for each jointMLP method."""
    base = f'[JointPrice] {model_tok}_quant-4-bit'
    if mode == 'M7':
        return f'{base}_priceN-or_randInit_jointMLP'
    if mode == 'M7b':
        return f'{base}_priceB_randInit_jointMLP'
    if mode == 'M12':
        # frzLLM5/pwm5 schedule
        return f'{base}_priceN-or_randInit_frzLLM5_pwm5_biCrossAttn_cx4_inflatePRICE_jointMLP'
    if mode == 'M12w':
        # No warmup/freeze schedule
        return f'{base}_priceN-or_randInit_biCrossAttn_cx4_inflatePRICE_jointMLP'
    raise ValueError(f'unknown mode {mode}')

def load_table(db):
    """Return {row_label: {col: value}} from the db's anchor CSV."""
    suffix = '' if ANCHOR == '50' else f'_anchor{ANCHOR}'
    # The db-tagged filename is the canonical (newer); fall back to the older un-tagged name.
    for cand in (f'results/{db}/relative_qerror_{db}_time{suffix}.csv',
                 f'results/{db}/relative_qerror_time{suffix}.csv'):
        if os.path.isfile(cand):
            with open(cand) as f:
                r = csv.reader(f)
                header = next(r)
                cols = header[1:]
                tbl = {}
                for row in r:
                    rlbl = row[0]
                    tbl[rlbl] = {c: float(v) if v else float('nan') for c, v in zip(cols, row[1:])}
            return cand, tbl
    return None, None

COMPARISONS = [
    ('M7  beats M7b',  'M7',  'M7b'),
    ('M12 beats M7',   'M12', 'M7'),
    ('M12 beats M12w', 'M12', 'M12w'),
]
QUANTS = ['50', '90', '95', 'max']

# Load all dbs once
tables = {}
sources = {}
for db in DBS:
    src, tbl = load_table(db)
    if tbl is None:
        print(f'! missing relative table for {db} (looked for relative_qerror_*time_anchor{ANCHOR}.csv)', file=sys.stderr)
        sys.exit(1)
    tables[db] = tbl
    sources[db] = src

print(f"Source files (ANCHOR={ANCHOR}):")
for db, src in sources.items():
    print(f"  {db:<9} → {src}")
print()

table = {}; detail = {}
for rlbl, a_mode, b_mode in COMPARISONS:
    for db in DBS:
        for mlbl, mtok in MODELS.items():
            ac = col_name(mtok, a_mode); bc = col_name(mtok, b_mode)
            W = L = T = 0
            missing = False
            for q in QUANTS:
                row = tables[db].get(q)
                if row is None or ac not in row or bc not in row:
                    missing = True; break
                av, bv = row[ac], row[bc]
                if av < bv:   W += 1
                elif av > bv: L += 1
                else:         T += 1
            if missing:
                table[(rlbl, db, mlbl)] = None
                detail[(rlbl, db, mlbl)] = (ac, bc)
            else:
                # New scoring: just one of {-1, 0, +1} based on which side
                # wins MORE quantiles. Ties (W==L) → 0.
                if   W >  L: cell = 1
                elif W <  L: cell = -1
                else:        cell = 0
                table[(rlbl, db, mlbl)] = cell
                detail[(rlbl, db, mlbl)] = (W, L, T)

# Render
col_labels = [f'{db}/{m}' for db in DBS for m in MODELS.keys()]
print(f"{'Comparison':<18} | " + " | ".join(f'{c:>14}' for c in col_labels) + " | row_sum")
print('-' * (18 + 16 * 9 + 12))
row_sums = []
for rlbl, _, _ in COMPARISONS:
    cells = [table[(rlbl, db, m)] for db in DBS for m in MODELS]
    valid = [c for c in cells if c is not None]
    rsum = sum(valid)
    row_sums.append(rsum)
    cell_strs = [(f'{c:+d}' if c is not None else 'NA') for c in cells]
    print(f"{rlbl:<18} | " + " | ".join(f'{s:>14}' for s in cell_strs) + f" | {rsum:+d}")

col_sums = []
for db in DBS:
    for m in MODELS:
        vals = [table[(r, db, m)] for r, _, _ in COMPARISONS]
        col_sums.append(sum(v for v in vals if v is not None))
print('-' * (18 + 16 * 9 + 12))
print(f"{'COL SUM':<18} | " + " | ".join(f'{s:+14d}' for s in col_sums) + f" | {sum(row_sums):+d}")

print()
print("Detail (W / L / T over 4 quantiles per cell):")
for rlbl, _, _ in COMPARISONS:
    print(f"\n  {rlbl}:")
    for db in DBS:
        line = f"    {db:<9}"
        for mlbl in MODELS:
            d = detail[(rlbl, db, mlbl)]
            if table[(rlbl, db, mlbl)] is None:
                line += f"  {mlbl:<8} MISSING"
            else:
                W, L, T = d
                line += f"  {mlbl:<8} W={W}/L={L}/T={T}"
        print(line)
