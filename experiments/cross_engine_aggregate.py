"""Cross-system aggregation of per-DB relative-Q-error CSVs from to_table_relative.py.

For each model family (bert2 / bert4 / sentbert), aggregate the per-DB
anchor-normalized CSVs across {postgres, duckdb, spark} into one table.

Two aggregation methods (both emitted):

  - simple:     arithmetic mean of the per-DB relative cells.

  - normalized: re-apply to_table_relative.py's anchor-min normalization
                within each (system, model-filtered) subset, then average.
                Filtering to one model family changes the within-system
                divisor (the best method at the anchor row of the filtered
                subset is usually NOT the same method that set divisor=1.0
                in the original full per-DB table), so this is not
                equivalent to simple averaging.

Inputs:
  results/<db>/relative_qerror_<db>_<task>{anchor_tag}.csv
    rows: 50, 90, 95, max
    cols: method display names

Outputs per model:
  results/cross_engine/relative_qerror_<model>_<task>{anchor_tag}_simple.csv
  results/cross_engine/relative_qerror_<model>_<task>{anchor_tag}_normalized.csv
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

DBS = ['postgres', 'duckdb', 'spark']
# Standard workload set the per-DB CSVs are built from (matches the default
# WORKLOADS in experiment_scripts/aggregate_tables.sh). Used when re-deriving a
# per-DB table for --exclude_workload, so stray dirs (e.g. jobm) aren't pulled in.
WORKLOADS = ['stats', 'syn', 'job', 'job_full', 'tpcds', 'tpch']
MODELS = {
    'bert2':    'L-2_H-256',
    'bert4':    'L-4_H-768',
    'sentbert': 'sentBert-all',
}


def col_is_llm(col):
    return any(tok in col for tok in MODELS.values())


def select_model_cols(cols, model_tok):
    """Keep non-LLM baselines + LLM columns matching this model's token."""
    return [c for c in cols if (not col_is_llm(c)) or (model_tok in c)]


def _workload_of(result_dir):
    """'results/duckdb/results_Train_job_Test_syn_ours' -> 'syn'."""
    m = re.search(r"_Test_(.+?)_ours/?$", os.path.basename(result_dir.rstrip('/')))
    return m.group(1) if m else None


def per_db_relative_excluding(db, exclude, task, anchor, results_dir):
    """Re-derive a DB's anchor-normalized relative table from the raw per-workload
    cdfs, dropping the workloads in `exclude` (a set of test-names, e.g. {'syn'}).

    cross_engine's normal inputs (relative_qerror_<db>_...csv) are ALREADY averaged
    over a DB's workloads, so a workload cannot be removed from them after the fact.
    Instead we re-run to_table_relative.py on the remaining per-(db, workload) dirs.
    The dirs are staged as symlinks under a temp dir so to_table_relative writes its
    output INTO the temp dir (its out path = dirname(dirs[0])), never overwriting the
    real per-DB CSV; the temp dir is removed afterwards."""
    here = os.path.dirname(os.path.abspath(__file__))
    all_dirs = sorted(glob.glob(os.path.join(results_dir, db, "results_Train_*_Test_*_ours")))
    # restrict to the standard workload set (minus excluded); ignore stray dirs (jobm, etc.)
    keep = [d for d in all_dirs if _workload_of(d) in WORKLOADS and _workload_of(d) not in exclude]
    dropped = sorted({_workload_of(d) for d in all_dirs if _workload_of(d) in WORKLOADS and _workload_of(d) in exclude})
    if not keep:
        raise SystemExit(f"[{db}] no workload dirs left after excluding {sorted(exclude)}")
    tmp = tempfile.mkdtemp(prefix="xwl_", dir=os.path.join(results_dir, db))
    try:
        staged = []
        for d in keep:
            link = os.path.join(tmp, os.path.basename(d))
            os.symlink(os.path.abspath(d), link)
            staged.append(link)
        anchor_tag = "" if str(anchor) == "50" else f"_anchor{anchor}"
        subprocess.run([sys.executable, os.path.join(here, "to_table_relative.py"),
                        "--task", task, "--anchor", str(anchor), "--dirs", *staged],
                       check=True, capture_output=True, text=True)
        out = os.path.join(tmp, f"relative_qerror_{os.path.basename(tmp)}_{task}{anchor_tag}.csv")
        df = pd.read_csv(out, index_col=0)
        df.index = [r if r == "max" else int(r) for r in df.index.astype(str)]
        print(f"[{db}] re-derived from {len(keep)} workloads "
              f"({', '.join(sorted(_workload_of(d) for d in keep))}); excluded {dropped}")
        return df
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Workloads in which the frzEven999 jointMLP value is replaced by its
# frzEven999 retrainMLP value when --frzeven_tpcx_use_retrainMLP is set.
FRZEVEN_SWAP_WORKLOADS = ('tpch', 'tpcds')
# Raw model token (in cdf filenames) -> display token used in the per-DB columns.
_RAW2DISPLAY = {
    'google-bert_uncased_L-2_H-256_A-4': 'L-2_H-256',
    'google-bert_uncased_L-4_H-768_A-12': 'L-4_H-768',
    'sentence-transformers-all-MiniLM-L12-v2': 'sentBert-all',
}
# display token -> model key ('bert2'/'bert4'/'sentbert'); inverse of MODELS.
_DISPLAY2KEY = {v: k for k, v in MODELS.items()}
# accepted model-key spellings -> canonical key.
_MODEL_ALIASES = {
    'bert2': 'bert2', 'bert4': 'bert4',
    'sentbert': 'sentbert', 'bertsent': 'sentbert', 'sent': 'sentbert',
    'minilm': 'sentbert',
}


def _model_key_of_raw(raw_model):
    """Raw cdf model token -> model key ('bert2'/'bert4'/'sentbert'), or None."""
    return _DISPLAY2KEY.get(_RAW2DISPLAY.get(raw_model))


def _cdf_quantiles(path):
    """{50,90,95,'max'} -> Q-error, mirroring to_table_relative.build_quantile_table
    (first row at percentage>=q; 'max' = max Q-error)."""
    df = pd.read_csv(path).sort_values('percentage')
    out = {}
    for q in (50, 90, 95):
        sub = df[df['percentage'] >= q]
        out[q] = float(sub.iloc[0]['Qerror']) if not sub.empty else float(df['Qerror'].max())
    out['max'] = float(df['Qerror'].max())
    return out


def patch_frzeven_tpcx_retrain(db, table, task, anchor, results_dir, exclude,
                               wl_models):
    """In-place: replace the frzEven999 *jointMLP* column's contribution with the
    frzEven999 *retrainMLP* cdf's data, for the cells described by `wl_models`
    (a dict {workload: set_of_model_keys}, workloads a subset of tpch/tpcds, model
    keys among 'bert2'/'bert4'/'sentbert'). Only the listed models are swapped in
    each listed workload.

    Surgical, not a re-derivation: tpch/tpcds get NO priceB<-priceN staging in the
    canonical aggregate_tables.sh pipeline, so each workload's anchor-row min (the
    relative-normalization reference `ref`) computed here from the raw cdfs matches
    the value baked into the canonical CSV. The frzEven999 retrainMLP cdf is already
    one of the methods feeding that min, and the frzEven999 jointMLP value is not the
    per-workload min, so swapping the jointMLP value leaves `ref` (hence every other
    column) unchanged. We therefore only adjust the one column:

        new_perDB[col] = old_perDB[col]
                       + (1/N) * sum_{w in workloads} (q_retrain[w] - q_joint[w]) / ref[w]

    where N = number of workloads the canonical per-DB table averaged over (the
    standard set minus `exclude`), and ref[w] is the anchor-row min over all methods
    in workload w. Workloads MUST be a subset of FRZEVEN_SWAP_WORKLOADS — on any
    other workload the priceB staging would make the computed ref disagree with the
    canonical table, so the surgical identity no longer holds. `table` is mutated in
    place; a list of (model, wl, col) patched is returned for logging."""
    bad = set(wl_models) - set(FRZEVEN_SWAP_WORKLOADS)
    if bad:
        raise ValueError(f"frzEven retrainMLP swap only valid on "
                         f"{FRZEVEN_SWAP_WORKLOADS}; got {sorted(bad)}")
    n_workloads = len([w for w in WORKLOADS if w not in exclude])
    patched = []
    for wl, models in wl_models.items():
        if wl in exclude:
            continue
        d = os.path.join(results_dir, db, f"results_Train_{wl}_Test_{wl}_ours")
        all_cdfs = [f for f in glob.glob(os.path.join(d, f"{task}*cdf*seed*.csv"))
                    if not any(t in os.path.basename(f)
                               for t in ('_rm-', 'downstream', 'trueEmb', 'length_vs'))]
        if not all_cdfs:
            print(f"  [frzEven swap] WARN {db}/{wl}: no cdfs found; skipping")
            continue
        ref = min(_cdf_quantiles(f)[anchor] for f in all_cdfs)

        joints = glob.glob(os.path.join(
            d, f"{task}_llm_price_finetune_lora_biCrossAttn_*frzEven999*cdf*seed*.csv"))
        # retrainMLP name has '_cdf_' BEFORE 'frzEven999'; keep cdf in glob to avoid
        # the 'length_vs_qerror' companion.
        retrains = glob.glob(os.path.join(
            d, f"{task}_llm_price_pretrained-lora_priceBiCrossAttnJoint_*cdf*frzEven999*seed*.csv"))

        def _key(bn, after):  # (raw_model, seed)
            mm = re.search(rf"h2048_(.+?)_{after}", bn)
            ss = re.search(r"seed(\d+)", bn)
            return (mm.group(1), ss.group(1)) if mm and ss else None
        retrain_by_key = {}
        for r in retrains:
            k = _key(os.path.basename(r), "emb")
            if k:
                retrain_by_key[k] = r

        for j in joints:
            k = _key(os.path.basename(j), "quant")
            if not k or k not in retrain_by_key:
                print(f"  [frzEven swap] WARN {db}/{wl}: no retrainMLP twin for {k}; "
                      f"leaving jointMLP")
                continue
            raw_model, _seed = k
            if _model_key_of_raw(raw_model) not in models:
                continue  # this model not requested for this cell
            disp = _RAW2DISPLAY.get(raw_model)
            cols = [c for c in table.columns
                    if disp and disp in c and 'frzEven999' in c and '_jointMLP' in c]
            if len(cols) != 1:
                print(f"  [frzEven swap] WARN {db}/{wl}: expected 1 frzEven jointMLP "
                      f"column for {raw_model}, found {len(cols)}; skipping")
                continue
            col = cols[0]
            qj = _cdf_quantiles(j)
            qr = _cdf_quantiles(retrain_by_key[k])
            for row in table.index:
                delta = (qr[row] - qj[row]) / ref / n_workloads
                table.loc[row, col] += delta
            patched.append((raw_model, wl, col))
    if patched:
        models = sorted({m for m, _, _ in patched})
        wls = sorted({w for _, w, _ in patched})
        print(f"[{db}] frzEven999 jointMLP <- retrainMLP on {wls} for models "
              f"{models} (averaged over {n_workloads} workloads)")
    return patched


def create_relative_heatmap(table, output_path, task, llm_methods, title_extra=""):
    """Heatmap rendering ported from to_table_relative.py.

    Non-LLM: dark orange for lowest, light orange for 2nd lowest per column.
    LLM:     green shades by per-column rank.
    Bold LLM names that beat the lowest non-LLM in >=2 columns.
    '***' prefix for LLM names that beat the 2nd-lowest non-LLM in >=2 columns.
    """
    llm_cols = [col for col in table.columns if col in llm_methods]
    non_llm_cols = [col for col in table.columns if col not in llm_methods]

    ordered_cols = non_llm_cols + llm_cols
    table = table[ordered_cols]
    table_T = table.T

    lowest_non_llm = {}
    second_lowest_non_llm = {}
    for col in table_T.columns:
        non_llm_values = table_T.loc[non_llm_cols, col].sort_values()
        if len(non_llm_values) >= 1:
            lowest_non_llm[col] = non_llm_values.iloc[0]
        if len(non_llm_values) >= 2:
            second_lowest_non_llm[col] = non_llm_values.iloc[1]

    llm_beats_lowest = {llm: 0 for llm in llm_cols}
    llm_beats_second = {llm: 0 for llm in llm_cols}
    for col in table_T.columns:
        for llm in llm_cols:
            llm_value = table_T.loc[llm, col]
            if col in lowest_non_llm and llm_value < lowest_non_llm[col]:
                llm_beats_lowest[llm] += 1
            if col in second_lowest_non_llm and llm_value < second_lowest_non_llm[col]:
                llm_beats_second[llm] += 1

    y_labels = []
    for method in table_T.index:
        label = method
        if method in llm_cols:
            if llm_beats_lowest[method] >= 2:
                label_escaped = label.replace('_', '\\_')
                label = f"$\\mathbf{{{label_escaped}}}$"
            if llm_beats_second[method] >= 2:
                label = f"***{label}"
        y_labels.append(label)

    max_label_length = max(len(str(l)) for l in y_labels)
    fig_width = max(12, len(table_T.columns) * 1.5 + max_label_length * 0.1)
    fig_height = max(8, len(table_T.index) * 0.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    n_rows, n_cols = table_T.shape
    colors = np.zeros((n_rows, n_cols, 4))

    for i, method in enumerate(table_T.index):
        for j, percentile in enumerate(table_T.columns):
            value = table_T.iloc[i, j]

            if method in non_llm_cols:
                non_llm_values = table_T.loc[non_llm_cols, percentile].sort_values()
                if len(non_llm_values) >= 1 and value == non_llm_values.iloc[0]:
                    colors[i, j] = [1.0, 0.5, 0.0, 1.0]
                elif len(non_llm_values) >= 2 and value == non_llm_values.iloc[1]:
                    colors[i, j] = [1.0, 0.8, 0.4, 1.0]
                else:
                    colors[i, j] = [1.0, 1.0, 1.0, 1.0]
            else:
                llm_values = table_T.loc[llm_cols, percentile].sort_values()
                rank = list(llm_values.values).index(value)
                if len(llm_values) > 1:
                    intensity = 0.3 + (rank / (len(llm_values) - 1)) * 0.7
                else:
                    intensity = 0.65
                colors[i, j] = [0.0, intensity, 0.0, 1.0]

    ax.imshow(colors, aspect='auto')

    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(table_T.columns, fontsize=12)
    ax.set_yticklabels(y_labels, fontsize=10)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(n_rows):
        for j in range(n_cols):
            value = table_T.iloc[i, j]
            if value >= 1000:
                text_str = f'{value:.2e}'
            else:
                text_str = f'{value:.2f}'
            ax.text(j, i, text_str, ha="center", va="center", color="black", fontsize=8)

    legend_elements = [
        mpatches.Patch(facecolor=[1.0, 0.5, 0.0, 1.0], label='Non-LLM: Lowest'),
        mpatches.Patch(facecolor=[1.0, 0.8, 0.4, 1.0], label='Non-LLM: 2nd Lowest'),
        mpatches.Patch(facecolor=[0.0, 0.3, 0.0, 1.0], label='LLM: Best'),
        mpatches.Patch(facecolor=[0.0, 0.65, 0.0, 1.0], label='LLM: Middle'),
        mpatches.Patch(facecolor=[0.0, 1.0, 0.0, 1.0], label='LLM: Worst'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)

    if len(non_llm_cols) > 0 and len(llm_cols) > 0:
        separator_y = len(non_llm_cols) - 0.5
        ax.axhline(y=separator_y, color='black', linewidth=2, linestyle='--')

    ax.set_xlabel('Percentile', fontsize=14, fontweight='bold')
    ax.set_ylabel('Method', fontsize=14, fontweight='bold')
    title = f'Averaged Relative Q-Error ({task})'
    if title_extra:
        title += f' — {title_extra}'
    title += '\n(Bold: beats best non-LLM in ≥2 cols, ***: beats 2nd-best in ≥2 cols)'
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", default="90", choices=["50", "90", "95", "max"],
                        help="Which anchor's per-DB CSV to read; also the anchor used "
                             "in the normalized-averaging method.")
    parser.add_argument("--results_dir", default="results",
                        help="Root results dir; expects "
                             "results/<db>/relative_qerror_<db>_<task>...csv")
    parser.add_argument("--task", default="time")
    parser.add_argument("--out_dir", default=None,
                        help="Output dir (default: <results_dir>/cross_engine).")
    parser.add_argument("--jointmlp_only", action="store_true",
                        help="Drop the _retrainMLP variants from the heatmap, keeping the "
                             "_jointMLP price modes AND the baselines that have no MLP suffix "
                             "(mode 1 = pretrained-None inference, non-LLM baselines). Mirrors "
                             "to_table_relative.py --exclude_retrain_mlp. CSVs still contain "
                             "every column.")
    parser.add_argument("--exclude_workload", nargs="+", default=None, metavar="WL",
                        help="Workload test-name(s) to drop before aggregating, e.g. 'syn'. "
                             "The per-DB CSVs are already workload-averaged, so this re-derives "
                             "each per-DB table from the raw per-(db,workload) cdfs by re-running "
                             "to_table_relative.py on the remaining workloads. Outputs are tagged "
                             "_excl-<wl> so they don't overwrite the full-workload tables.")
    parser.add_argument("--frzeven_tpcx_use_retrainMLP", action="store_true",
                        help="Only valid with --jointmlp_only. For the frzEven999 method, use "
                             "its retrainMLP result in place of its jointMLP result on the tpch "
                             "and tpcds workloads (all systems); every other method/workload is "
                             "left exactly as in the canonical per-DB tables. Implemented as a "
                             "surgical patch of the frzEven999 jointMLP column (tpch/tpcds carry "
                             "no priceB staging, so their per-workload normalization reference is "
                             "unchanged by the swap). Outputs are tagged _frzEvenTPCxRetrain.")
    parser.add_argument("--frzeven_retrainMLP_cells", nargs="+", default=None,
                        metavar="[MODEL:]DB:WL",
                        help="Like --frzeven_tpcx_use_retrainMLP but restricted to the given "
                             "cells, e.g. 'spark:tpcds duckdb:tpcds'. Each entry is "
                             "'<db>:<workload>' (all models) or '<model>:<db>:<workload>' for a "
                             "single model, e.g. 'bert2:duckdb:tpcds sentbert:spark:tpcds'. "
                             "MODEL in {bert2,bert4,sentbert} (aliases: bertSent/sent->sentbert). "
                             "The frzEven999 jointMLP -> retrainMLP swap is applied ONLY in those "
                             "(model,db,workload) cells; everything else stays canonical. WL must "
                             "be tpch or tpcds (the only workloads without priceB staging, where "
                             "the surgical patch is exact). Requires --jointmlp_only; mutually "
                             "exclusive with --frzeven_tpcx_use_retrainMLP. Outputs are tagged "
                             "_frzEvenRetrain-<...>.")
    args = parser.parse_args()

    if args.frzeven_tpcx_use_retrainMLP and args.frzeven_retrainMLP_cells:
        parser.error("--frzeven_tpcx_use_retrainMLP and --frzeven_retrainMLP_cells "
                     "are mutually exclusive")
    if (args.frzeven_tpcx_use_retrainMLP or args.frzeven_retrainMLP_cells) \
            and not args.jointmlp_only:
        parser.error("--frzeven_tpcx_use_retrainMLP / --frzeven_retrainMLP_cells "
                     "require --jointmlp_only")

    ALL_MODELS = set(MODELS)  # {'bert2','bert4','sentbert'}
    # swap_targets: db -> {workload -> set(model_keys)}. Empty unless a frzEven flag
    # is set. The frzEven999 jointMLP of each listed model is replaced by retrainMLP.
    swap_targets = {db: {} for db in DBS}
    if args.frzeven_tpcx_use_retrainMLP:
        for db in DBS:
            for wl in FRZEVEN_SWAP_WORKLOADS:
                swap_targets[db][wl] = set(ALL_MODELS)
    elif args.frzeven_retrainMLP_cells:
        for spec in args.frzeven_retrainMLP_cells:
            parts = spec.split(":")
            if len(parts) == 2:
                model_key, (db, wl) = None, parts
            elif len(parts) == 3:
                msp, db, wl = parts
                model_key = _MODEL_ALIASES.get(msp.lower())
                if model_key is None:
                    parser.error(f"unknown model '{msp}' in '{spec}' "
                                 f"(choose from {sorted(ALL_MODELS)})")
            else:
                parser.error(f"entry '{spec}' must be 'DB:WL' or 'MODEL:DB:WL'")
            if db not in DBS:
                parser.error(f"unknown db '{db}' in '{spec}' (choose from {DBS})")
            if wl not in FRZEVEN_SWAP_WORKLOADS:
                parser.error(f"workload '{wl}' in '{spec}' must be one of "
                             f"{list(FRZEVEN_SWAP_WORKLOADS)}")
            models = {model_key} if model_key else set(ALL_MODELS)
            swap_targets[db].setdefault(wl, set()).update(models)

    do_swap = any(swap_targets[db] for db in DBS)
    if args.frzeven_tpcx_use_retrainMLP:
        swap_tag = "_frzEvenTPCxRetrain"
    elif do_swap:
        # tag encodes every (model,db,wl) cell so distinct invocations don't collide.
        cells = []
        for db in DBS:
            for wl in sorted(swap_targets[db]):
                ms = swap_targets[db][wl]
                mtag = "all" if ms == ALL_MODELS else "+".join(sorted(ms))
                cells.append(f"{mtag}.{db}.{wl}")
        swap_tag = "_frzEvenRetrain-" + "-".join(sorted(cells))
    else:
        swap_tag = ""

    anchor_tag = "" if args.anchor == "50" else f"_anchor{args.anchor}"
    anchor_key = args.anchor if args.anchor == "max" else int(args.anchor)

    excl = set(args.exclude_workload or [])
    tables = {}
    for db in DBS:
        if excl:
            df = per_db_relative_excluding(db, excl, args.task, anchor_key,
                                           args.results_dir)
        else:
            path = os.path.join(args.results_dir, db,
                                f"relative_qerror_{db}_{args.task}{anchor_tag}.csv")
            if not os.path.isfile(path):
                raise SystemExit(f"missing per-DB CSV: {path}")
            df = pd.read_csv(path, index_col=0)
            # CSV round-trip turns the index into strings; coerce 50/90/95 back to int
            # so the anchor lookup matches to_table_relative.py's index labels.
            df.index = [r if r == "max" else int(r) for r in df.index.astype(str)]
        # Surgical frzEven999 jointMLP <- retrainMLP swap on the requested
        # (model, tpch/tpcds) cells (only valid with --jointmlp_only). Patches just
        # that one column per cell; see the function doc.
        if swap_targets[db]:
            patch_frzeven_tpcx_retrain(db, df, args.task, anchor_key,
                                       args.results_dir, excl,
                                       wl_models=swap_targets[db])
        tables[db] = df

    out_dir = args.out_dir or os.path.join(args.results_dir, "cross_engine")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[anchor] {anchor_key}  (per-DB CSVs already normalized to this anchor)")
    print(f"[systems] {', '.join(DBS)}")
    print()

    for model_label, model_tok in MODELS.items():
        filtered = {}
        for db, df in tables.items():
            keep = select_model_cols(df.columns, model_tok)
            if not keep:
                print(f"[{model_label}/{db}] no matching columns; skipping model")
                filtered = None
                break
            filtered[db] = df[keep]
        if filtered is None:
            continue

        common = sorted(set.intersection(*[set(t.columns) for t in filtered.values()]))
        dropped = {db: sorted(set(t.columns) - set(common))
                   for db, t in filtered.items()}
        if not common:
            print(f"[{model_label}] no columns common to all systems; skipping")
            continue
        aligned = {db: t[common] for db, t in filtered.items()}

        # 1. simple: arithmetic mean across systems.
        simple = sum(aligned.values()) / len(aligned)

        # 2. normalized: re-normalize each system by min(anchor row) of the
        #    model-filtered subset, then average. Same recipe as
        #    to_table_relative.compute_relative_qerror, applied at the
        #    cross-system level.
        renormed = {}
        for db, t in aligned.items():
            ref = t.loc[anchor_key].min()
            renormed[db] = (t / ref) if ref > 0 else t.copy()
        normalized = sum(renormed.values()) / len(renormed)

        excl_tag = f"_excl-{'-'.join(sorted(excl))}" if excl else ""
        base = f"relative_qerror_{model_label}_{args.task}{anchor_tag}{excl_tag}{swap_tag}"
        simple_path = os.path.join(out_dir, f"{base}_simple.csv")
        norm_path   = os.path.join(out_dir, f"{base}_normalized.csv")
        simple.to_csv(simple_path)
        normalized.to_csv(norm_path)

        # Heatmap per CSV. All current cols are LLM (no non-LLM baselines in
        # the cross-engine inputs); the function still works — every cell
        # gets green coloring and the non-LLM legend entries are unused.
        if args.jointmlp_only:
            # Keep jointMLP price modes + baselines (mode 1 has no MLP suffix);
            # drop only the _retrainMLP duplicates. Matches to_table_relative.py
            # --exclude_retrain_mlp, so mode 1 stays in the heatmap.
            heatmap_cols = [c for c in common if '_retrainMLP' not in c]
            png_suffix = "_jointMLPonly_heatmap.png"
        else:
            heatmap_cols = list(common)
            png_suffix = "_heatmap.png"

        if not heatmap_cols:
            print(f"[{model_label}] no non-retrainMLP columns left after --jointmlp_only "
                  f"filter; skipping heatmap")
            simple_png = norm_png = None
        else:
            llm_methods = {c for c in heatmap_cols if col_is_llm(c)}
            simple_png = os.path.join(out_dir, f"{base}_simple{png_suffix}")
            norm_png   = os.path.join(out_dir, f"{base}_normalized{png_suffix}")
            create_relative_heatmap(simple[heatmap_cols], simple_png, args.task,
                                    llm_methods,
                                    title_extra=f"{model_label} · simple avg")
            create_relative_heatmap(normalized[heatmap_cols], norm_png, args.task,
                                    llm_methods,
                                    title_extra=f"{model_label} · normalized "
                                                f"(anchor={anchor_key})")

        print(f"[{model_label}] {len(common)} common methods")
        for db, drop in dropped.items():
            if drop:
                print(f"  dropped from {db} (not in all systems): {len(drop)}")
                for c in drop:
                    print(f"    - {c}")
        print(f"  simple     → {simple_path}")
        if simple_png:
            print(f"             + {simple_png}")
        print(f"  normalized → {norm_path}")
        if norm_png:
            print(f"             + {norm_png}")
        print()


if __name__ == "__main__":
    main()
