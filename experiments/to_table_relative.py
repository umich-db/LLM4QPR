import pandas as pd
import glob
import os
import argparse
import re
from collections import defaultdict
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--dirs", type=str, nargs="+", required=True,
                    help="Result directories (datasets), e.g. results/duckdb/results_Train_job_Test_job_ours results/duckdb/results_Train_stats_Test_stats_ours")
parser.add_argument("--task", type=str, default="time")
parser.add_argument("--sentbert_only", action="store_true",
                    help="Only show sentence-transformers/all-MiniLM-L12-v2 (sentBert) variants "
                         "(plus non-LLM baselines) in .png")
parser.add_argument("--bert_only", "--bert4_only", dest="bert_only", action="store_true",
                    help="Only show google/bert_uncased_L-4_H-768_A-12 variants (plus non-LLM baselines) "
                         "in .png. --bert4_only is an alias.")
parser.add_argument("--bert2_only", action="store_true",
                    help="Only show google/bert_uncased_L-2_H-256_A-4 variants (plus non-LLM baselines) "
                         "in .png.")
parser.add_argument("--exclude_retrain_mlp", action="store_true",
                    help="Drop _retrainMLP (inference-phase pretrained-lora) variants from the .png heatmap.")
parser.add_argument("--retrain_mlp_only", action="store_true",
                    help="For modes 7 / 7b / 12 / 12w, keep only the _retrainMLP variants — i.e. drop the "
                         "_jointMLP columns from the heatmap. Modes 1 (LLM inference) and 2 (LoRA retrainMLP) "
                         "remain since they don't have a jointMLP variant. Mutually exclusive with "
                         "--exclude_retrain_mlp.")
parser.add_argument("--special_set1", action="store_true",
                    help="Special set 1: only the 4 setups from master_cross_engine_comparison.sh spark section "
                         "(Mode 1 pretrained, Mode 2 LoRA, Mode 7 JointPrice priceS, Mode 12 inflatePRICE cx4) "
                         "plus non-LLM baselines.")
parser.add_argument("--anchor", choices=["50", "90", "95", "max"], default="50",
                    help="Per-dataset normalization anchor: divide every value in a dataset by the minimum "
                         "Q-error across methods at this quantile. Default: 50 (matches the original behaviour). "
                         "Picking a higher quantile (e.g. 'max') anchors the divisor to the best tail performer "
                         "in each dataset, which makes the averaged table more sensitive to tail differences.")
args = parser.parse_args()


def _matches_special_set1(filename):
    """True if filename matches one of the 4 setups from master_cross_engine_comparison.sh:
      1) Mode 1: pretrained-None (no finetune, no price)
      2) Mode 2: pretrained-lora (LoRA LLM finetune, no price)
      3) Mode 7: pretrained-lora + priceS (JointPrice with pretrained PRICE, no randInit)
      4) Mode 12 inflatePRICE: biCrossAttn + inflatePRICE + randInit + cx4
    """
    if "length_vs_qerror" in filename:
        return False

    # Reject retrainMLP variants from all modes.
    if "retrainMLP" in filename:
        return False

    # Mode 12 inflatePRICE must be checked BEFORE cross-attn rejection,
    # because the filename contains "BiCrossAttnJoint" (which has "CrossAttnJoint" as substring).
    if "inflatePRICE" in filename:
        return ("randInit" in filename
                and "cx4" in filename
                and ("biCrossAttn" in filename or "priceBiCrossAttnJoint" in filename))

    if any(x in filename for x in (
        "CrossAttnJoint", "RevCrossAttnJoint",
        "revCrossAttn", "biCrossAttn",
        "tripleConcat", "refinedPool", "gated",
    )):
        return False

    if any(x in filename for x in (
        "priceNoFT", "priceLLMOnly", "priceM", "retrainMLP",
        "_statTok", "frozenInit",
    )):
        return False

    if any(x in filename for x in ("_pL", "_ffn", "maxq-")):
        return False

    if "pretrained-None" in filename and "price" not in filename:
        return True

    if "pretrained-lora" in filename and "price" not in filename:
        return True

    if "pretrained-lora" in filename and "priceS" in filename and "randInit" not in filename:
        return True

    return False


def strip_seed(filename):
    """Removes seed information to group files with same prefix"""
    return re.sub(r'_seed\d+', '', filename)


def _price_n_qrt_suffix(col_name):
    """Compact display suffix for the PRICE_N family + QRT cross-attn.

    Mirrors utilsLLM._price_flags_cache_tag's collapsing rules so the row name
    in the heatmap/table reflects which PRICE_N sub-flags + QRT were active:

        --price_n                                  → '_priceN'
        --price_n --price_n_or                     → '_priceN-or'
        --price_n --price_n_or --use_qrt_cross_attn → '_priceN-or-qrt'
        --price_n_filter --price_n_fanout          → '_priceN-flt-fan'
        --use_qrt_cross_attn alone                 → '_qrt'
        (none)                                     → ''

    Detection is by substring match on the PRICE save-path tokens
    (_priceNflt, _priceNfan, _priceNpw, _priceNprs, _priceNor, _qrt).
    """
    subs = []
    # train._price_path_suffix collapses the full PRICE_N set to "_priceN"
    # (and emits individual sub-tokens only for partial subsets).
    if re.search(r'_priceN(?![a-zA-Z])', col_name):
        subs.extend(['flt', 'fan', 'pw', 'prs'])
    else:
        if '_priceNflt' in col_name: subs.append('flt')
        if '_priceNfan' in col_name: subs.append('fan')
        if '_priceNpw'  in col_name: subs.append('pw')
        if '_priceNprs' in col_name: subs.append('prs')
    if '_priceNor'  in col_name: subs.append('or')
    has_qrt = '_qrt' in col_name
    out = []
    if subs:
        core = {'flt', 'fan', 'pw', 'prs'}
        s = set(subs)
        if s == core:
            out.append('priceN')
        elif s == core | {'or'}:
            out.append('priceN-or')
        else:
            out.append('priceN-' + '-'.join(subs))
    if has_qrt:
        out.append('qrt')
    return ('_' + '-'.join(out)) if out else ''


def extract_display_name(col_name):
    """Extract display name from column name"""
    if 'llm' in col_name:
        match = re.search(r'h\d+_(.+?)(?:_emb|_quant)', col_name)
        if match:
            model = match.group(1)
            if 'sentence-transformers' in model:
                if 'paraphrase' in model:
                    model = 'sentBert-para'
                elif 'all-MiniLM' in model:
                    model = 'sentBert-all'
                else:
                    model = 'sentBert'
            quant_match = re.search(r'quant-([^_]+)', col_name)
            if quant_match:
                display_name = f"{model}_quant-{quant_match.group(1)}"
            else:
                display_name = model

            rm_match = re.search(r'(_rm-[a-z\-]+)', col_name)
            if rm_match:
                display_name += rm_match.group(1)

            if 'llm_price' in col_name:
                price_mode_match = re.search(
                    r'(priceNoFT|priceLLMOnly|pricePRICEOnly|priceBothSep|priceFTwithLLM|priceFTthenJoint|priceGatedJoint)',
                    col_name)
                if price_mode_match:
                    display_name = f"[{price_mode_match.group(1)}] {display_name}"
                else:
                    display_name = f"[JointPrice] {display_name}"

            # priceB = original-PRICE-design (equi-join + col-op-literal only).
            # Negative lookahead `(?!i)` excludes `priceBi…` (mode 12 / BiCrossAttnJoint).
            price_variant_match = re.search(r'_(priceM|priceS|priceB)(?!i)', col_name)
            if price_variant_match:
                display_name += f"_{price_variant_match.group(1)}"

            # Extract PRICE_N family + QRT (compact form, e.g. _priceN-or-qrt).
            display_name += _price_n_qrt_suffix(col_name)

            # Restrict to letters: filenames continue with `_<train_ratio>_…`,
            # and `\w` would greedily eat the `_1` of `_1.0_cdf_…` → "_pt-None_1".
            pretrained_match = re.search(r'pretrained-([A-Za-z]+)', col_name)
            if pretrained_match:
                pt_status = pretrained_match.group(1)
                if pt_status != 'None':
                    display_name += f"_pt-{pt_status}"

            # Extract randInit flag
            if '_randInit' in col_name:
                display_name += '_randInit'

            # Extract freeze-llm-until-epoch (_frzLLM{N}) and PRICE-warmup-epochs
            # (_pwm{N}). Both indicate the mode-12 warmup schedule. Filenames
            # include them only when the value is non-zero, so absence == 0.
            frz_match = re.search(r'_frzLLM(\d+)', col_name)
            if frz_match:
                display_name += f"_frzLLM{frz_match.group(1)}"
            # Cross-attn block freezes (added by --freeze_odd_blocks_until_epoch and
            # --freeze_all_blocks_until_epoch). frzAll means "both directions";
            # frzOdd means "LLM←PRICE direction only". Filenames include them only
            # when value > 0.
            frz_all_match = re.search(r'_frzAll(\d+)', col_name)
            if frz_all_match:
                display_name += f"_frzAll{frz_all_match.group(1)}"
            frz_odd_match = re.search(r'_frzOdd(\d+)', col_name)
            if frz_odd_match:
                display_name += f"_frzOdd{frz_odd_match.group(1)}"
            # frzEven freezes the even-indexed cross-attn blocks (PRICE←LLM
            # direction). Filenames include it only when value > 0.
            frz_even_match = re.search(r'_frzEven(\d+)', col_name)
            if frz_even_match:
                display_name += f"_frzEven{frz_even_match.group(1)}"
            pwm_match = re.search(r'_pwm(\d+)', col_name)
            if pwm_match:
                display_name += f"_pwm{pwm_match.group(1)}"

            # Extract PRICE n_layers (e.g., _pL3, _pL12)
            pl_match = re.search(r'_pL(\d+)', col_name)
            if pl_match:
                display_name += f"_pL{pl_match.group(1)}"

            # Extract PRICE learning-rate ablation (e.g., _pLR0.0001). Must be
            # captured: otherwise a `_pLR…` ablation collapses to the SAME
            # display name as the canonical run, which trips the collision →
            # raw-prefix rename in step 2 and drops BOTH from the cross-workload
            # intersection (the raw prefix carries the b24/b4 micro-batch token,
            # so it isn't even consistent across a db's workloads). `_pL(\d+)`
            # above does not match `_pLR` (the 'R' isn't a digit), so order is safe.
            plr_match = re.search(r'_pLR([\d.]+)', col_name)
            if plr_match:
                display_name += f"_pLR{plr_match.group(1)}"

            # Extract FFN ratio (e.g., _ffn2)
            ffn_match = re.search(r'_ffn([\d.]+)', col_name)
            if ffn_match:
                display_name += f"_ffn{ffn_match.group(1)}"

            # Extract cross-attention suffix
            if '_biCrossAttn' in col_name:
                display_name += '_biCrossAttn'
            elif '_revCrossAttn' in col_name:
                display_name += '_revCrossAttn'
            elif '_crossAttn' in col_name:
                display_name += '_crossAttn'

            # Extract cross-attention layer count (e.g., _cx4)
            cx_match = re.search(r'_cx(\d+)', col_name)
            if cx_match:
                display_name += f"_cx{cx_match.group(1)}"

            # Extract refinedPool / tripleConcat / inflatePRICE flag
            if '_refinedPool' in col_name:
                display_name += '_refinedPool'
            if '_tripleConcat' in col_name:
                display_name += '_tripleConcat'
            if '_inflatePRICE' in col_name:
                display_name += '_inflatePRICE'

            # Extract finetune epoch count (e.g., _e20, _e30)
            ft_epoch_match = re.search(r'_e(\d+)_ftb', col_name)
            if ft_epoch_match:
                display_name += f"_e{ft_epoch_match.group(1)}"

            # Extract retrainMLP flag
            if '_retrainMLP' in col_name:
                display_name += '_retrainMLP'

            # Distinguish finetune-phase MLP (joint MLP, saved during
            # llm_price_finetune) from inference-phase MLP (retrained on
            # cached embeddings at inference time, _pretrained-lora_ files).
            if '_llm_price_finetune_' in col_name or '_finetune_lora_' in col_name:
                display_name += '_jointMLP'
            elif '_pretrained-lora_' in col_name:
                display_name += '_retrainMLP'

            # Best-val variant: synthesised 4-row CDF CSV emitted by
            # /tmp/synthesize_bestval_csv.py, which scrapes the test-eval
            # block at the epoch with min val p90 from the training log.
            # Tag distinct from the final-epoch CSV so the heatmap shows
            # them side-by-side.
            if '_bestval_cdf' in col_name:
                display_name += '_bestval'

            return display_name
        return 'LLM'
    else:
        match = re.search(r'_(aimai|qf|e2e_cost|bao|postgres)_', col_name)
        if match:
            algo = match.group(1)
            feat_match = re.search(r'_f(\d+)', col_name)
            if feat_match and algo == 'aimai':
                algo = f"{algo}_f{feat_match.group(1)}"
            # --baseline_price_concat runs carry a _priceConcat tag; keep them as a
            # DISTINCT method (e.g. qf_priceConcat) so they don't collapse onto the
            # plain baseline column and get dropped by the collision handler.
            if 'priceConcat' in col_name:
                algo = f"{algo}_priceConcat"
            return algo
        return col_name


def build_quantile_table(csv_folder, task, quantiles=[50, 90, 95]):
    """
    Aggregates quantiles across seed files by averaging values with the same prefix.
    Returns a DataFrame with index=[50, 90, 95, 'max'] and columns=method prefixes.
    """
    csv_paths = glob.glob(os.path.join(csv_folder, f'{task}*cdf*seed*.csv'))

    # Filter out ablation / downstream / trueEmb files
    filtered_paths = []
    for path in csv_paths:
        filename = os.path.basename(path)
        if "_rm-" in filename or "downstream" in filename or "trueEmb" in filename:
            continue
        if args.special_set1:
            is_llm = "llm" in filename
            if is_llm and not _matches_special_set1(filename):
                continue
        filtered_paths.append(path)
    csv_paths = filtered_paths

    # Group files by prefix (strip seed)
    grouped_paths = defaultdict(list)
    for path in csv_paths:
        base = os.path.splitext(os.path.basename(path))[0]
        prefix = strip_seed(base)
        grouped_paths[prefix].append(path)

    idx = quantiles + ['max']
    table = pd.DataFrame(index=idx, columns=list(grouped_paths.keys()), dtype=float)

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


def compute_relative_qerror(tables_by_dataset, anchor=50):
    """
    Given {dataset_name: quantile_table}, compute relative Q-error:
    For each dataset, divide ALL values by a single scalar — the minimum
    value in the `anchor` row (one of 50, 90, 95, or 'max'). Using one
    divisor per dataset preserves monotonicity across percentiles
    (p50 <= p90 <= p95 <= max).

    `anchor` accepts the int values 50/90/95 or the string 'max', matching
    the table's index labels.

    Returns {dataset_name: relative_table} with same structure.
    """
    relative_tables = {}
    for ds_name, table in tables_by_dataset.items():
        if anchor not in table.index:
            raise KeyError(f"anchor {anchor!r} not in quantile table index "
                           f"{list(table.index)} for dataset {ds_name}")
        ref_scalar = table.loc[anchor].min()
        if ref_scalar > 0:
            rel = table / ref_scalar
        else:
            rel = table.copy()
        relative_tables[ds_name] = rel
    return relative_tables


# --- Main ---

quantiles = [50, 90, 95]
percentile_idx = quantiles + ['max']

# 1. Build per-dataset quantile tables, mapping display_name -> raw prefix
tables_by_dataset = {}
display_name_map = {}  # prefix -> display_name (consistent across datasets)

for csv_folder in args.dirs:
    ds_name = os.path.basename(csv_folder.rstrip('/'))
    table = build_quantile_table(csv_folder, args.task, quantiles)
    if table.empty:
        print(f"Warning: no CDF files found in {csv_folder}, skipping.")
        continue
    tables_by_dataset[ds_name] = table
    for col in table.columns:
        if col not in display_name_map:
            display_name_map[col] = extract_display_name(col)

if not tables_by_dataset:
    print("No data found. Check --dirs and --task arguments.")
    exit(1)

# 2. Rename columns to display names (resolve collisions by keeping prefix).
#    A collision is real only if a single dataset has multiple distinct prefixes
#    mapping to the same display name (e.g. two LLM variants the display fn
#    would label identically). The SAME display name appearing across MULTIPLE
#    dirs (e.g. mode-7 jointMLP on stats vs tpch where one's prefix has _b24_
#    and the other has _b4_ because of compare_modes_lib's micro-batch override)
#    is the intended aggregation — do NOT flag those as collisions, or the
#    intersection step below ends up empty for everything except mode 1.
within_dir_dn_to_prefixes = defaultdict(set)  # display_name -> {prefixes in any single dir with >1 prefix}
for ds_name, table in tables_by_dataset.items():
    per_dir = defaultdict(list)
    for col in table.columns:
        dn = display_name_map[col]
        per_dir[dn].append(col)
    for dn, prefixes in per_dir.items():
        if len(prefixes) > 1:
            within_dir_dn_to_prefixes[dn].update(prefixes)

final_name_map = {}
for prefix, dn in display_name_map.items():
    if dn in within_dir_dn_to_prefixes:
        final_name_map[prefix] = prefix  # real collision → keep full prefix
    else:
        final_name_map[prefix] = dn

# Track which display names are LLM methods (check original prefix before rename)
llm_display_names = set()
for prefix, display_name in final_name_map.items():
    if 'llm' in prefix:
        llm_display_names.add(display_name)

# Rename columns in all tables
for ds_name in tables_by_dataset:
    table = tables_by_dataset[ds_name]
    new_cols = {col: final_name_map.get(col, col) for col in table.columns}
    tables_by_dataset[ds_name] = table.rename(columns=new_cols)

# 3. Find methods present in ALL datasets
all_methods_sets = [set(t.columns) for t in tables_by_dataset.values()]
common_methods = set.intersection(*all_methods_sets)

removed_methods = set()
for methods in all_methods_sets:
    removed_methods |= methods - common_methods

if removed_methods:
    print(f"Removed (not in all datasets): {sorted(removed_methods)}")
    print()

if not common_methods:
    print("No methods common to all datasets.")
    exit(1)

# Filter to common methods, sorted
common_methods = sorted(common_methods)
for ds_name in tables_by_dataset:
    tables_by_dataset[ds_name] = tables_by_dataset[ds_name][common_methods]

# 4. Compute relative Q-error per dataset
#    `--anchor` arrives as a string from argparse; coerce 50/90/95 back to int
#    so it matches the quantile-table index (the 'max' label stays a string).
anchor_key = int(args.anchor) if args.anchor != "max" else "max"
relative_tables = compute_relative_qerror(tables_by_dataset, anchor=anchor_key)
print(f"\n[anchor] dividing each dataset's Q-errors by the best method's {anchor_key} value")

# 5. Average relative Q-error across datasets
avg_relative = pd.DataFrame(0.0, index=percentile_idx, columns=common_methods)
for ds_name, rel_table in relative_tables.items():
    avg_relative += rel_table
avg_relative /= len(relative_tables)

# 6. Print per-dataset tables, then the averaged relative table
for ds_name in sorted(tables_by_dataset.keys()):
    print(f"\n{'='*60}")
    print(f"  {ds_name} — Raw Q-Error")
    print(f"{'='*60}")
    raw = tables_by_dataset[ds_name]
    print(raw.to_markdown())

    print(f"\n  {ds_name} — Relative Q-Error")
    rel = relative_tables[ds_name]
    print(rel.round(3).to_markdown())

print(f"\n{'='*60}")
print(f"  AVERAGED Relative Q-Error across {len(tables_by_dataset)} datasets")
ds_list = sorted(tables_by_dataset.keys())
print(f"  Datasets: {', '.join(ds_list)}")
print(f"{'='*60}")
print(avg_relative.round(3).to_markdown())

# 7. Save to CSV
out_dir = os.path.dirname(args.dirs[0].rstrip('/')) or '.'
# Tag the output filename with the db (parent-dir basename) so postgres / duckdb /
# spark outputs are distinguishable even when copied out of their results/<db>/
# directory. If the dirs span multiple dbs (typically a misuse), the tag falls
# back to dirs[0]'s db.
db_name = os.path.basename(out_dir) or 'mixed'
db_tag = f'_{db_name}' if db_name not in ('results', '', '.', 'mixed') else ''
# Include the anchor in the filename so different --anchor runs don't overwrite each other
# (omit "_anchor50" since 50 was the original implicit anchor and we want to preserve
#  backwards-compatible filenames for the default case).
anchor_tag = "" if args.anchor == "50" else f"_anchor{args.anchor}"
out_path = os.path.join(out_dir, f'relative_qerror{db_tag}_{args.task}{anchor_tag}.csv')
avg_relative.to_csv(out_path)
print(f"\nSaved averaged relative Q-error to: {out_path}")

# 8. Save heatmap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def create_relative_heatmap(table, output_path, task, llm_methods):
    """
    Create a heatmap for relative Q-error with LLM vs non-LLM color coding:
    - Non-LLM: Dark orange for lowest, light orange for second lowest (per column)
    - LLM: Shades of green based on ranking (per column)
    - Bold LLM names that beat lowest non-LLM in >=2 columns
    - *** prefix for LLM names that beat second lowest non-LLM in >=2 columns

    llm_methods: set of display names that are LLM-based
    """
    llm_cols = [col for col in table.columns if col in llm_methods]
    non_llm_cols = [col for col in table.columns if col not in llm_methods]

    ordered_cols = non_llm_cols + llm_cols
    table = table[ordered_cols]

    # Transpose: methods as rows, percentiles as columns
    table_T = table.T

    # Find lowest / second-lowest non-LLM per percentile
    lowest_non_llm = {}
    second_lowest_non_llm = {}
    for col in table_T.columns:
        non_llm_values = table_T.loc[non_llm_cols, col].sort_values()
        if len(non_llm_values) >= 1:
            lowest_non_llm[col] = non_llm_values.iloc[0]
        if len(non_llm_values) >= 2:
            second_lowest_non_llm[col] = non_llm_values.iloc[1]

    # Check LLM performance against non-LLM baselines
    llm_beats_lowest = {llm: 0 for llm in llm_cols}
    llm_beats_second = {llm: 0 for llm in llm_cols}
    for col in table_T.columns:
        for llm in llm_cols:
            llm_value = table_T.loc[llm, col]
            if col in lowest_non_llm and llm_value < lowest_non_llm[col]:
                llm_beats_lowest[llm] += 1
            if col in second_lowest_non_llm and llm_value < second_lowest_non_llm[col]:
                llm_beats_second[llm] += 1

    # Build y-axis labels with formatting
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
                    colors[i, j] = [1.0, 0.5, 0.0, 1.0]  # Dark orange
                elif len(non_llm_values) >= 2 and value == non_llm_values.iloc[1]:
                    colors[i, j] = [1.0, 0.8, 0.4, 1.0]  # Light orange
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
    ax.set_title(f'Averaged Relative Q-Error ({task})\n(Bold: beats best non-LLM in ≥2 cols, ***: beats 2nd-best in ≥2 cols)',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Heatmap saved to: {output_path}")

    # Print summary
    print("\n" + "="*80)
    print("LLM PERFORMANCE SUMMARY (Relative Q-Error)")
    print("="*80)
    for llm in llm_cols:
        print(f"{llm}:")
        print(f"  Beats best non-LLM: {llm_beats_lowest[llm]}/{len(table_T.columns)} columns")
        print(f"  Beats 2nd-best non-LLM: {llm_beats_second[llm]}/{len(table_T.columns)} columns")
    print("="*80)


if sum([args.sentbert_only, args.bert_only, args.bert2_only]) > 1:
    parser.error("--sentbert_only, --bert_only/--bert4_only, and --bert2_only are mutually exclusive")

# Filter LLM columns to one model family (plus non-LLM baselines) for heatmap.
# The unique on-disk substring for each model is used as the identifier:
#   sentBert-all  → sentence-transformers/all-MiniLM-L12-v2 (12-layer 384-dim)
#   L-4_H-768     → google/bert_uncased_L-4_H-768_A-12 (4-layer 768-dim)
#   L-2_H-256     → google/bert_uncased_L-2_H-256_A-4 (2-layer 256-dim)
if args.sentbert_only:
    _tag, suffix = 'sentBert-all', '_sentbert'
elif args.bert_only:
    _tag, suffix = 'L-4_H-768', '_bert4'
elif args.bert2_only:
    _tag, suffix = 'L-2_H-256', '_bert2'
else:
    _tag, suffix = None, ''
if _tag is not None:
    keep_cols = [col for col in avg_relative.columns
                 if col not in llm_display_names or _tag in col]
    heatmap_table = avg_relative[keep_cols]
    heatmap_llm = {m for m in llm_display_names if _tag in m}
else:
    heatmap_table = avg_relative
    heatmap_llm = llm_display_names

# Drop retrainMLP variants from the heatmap if requested (CSV table keeps them).
# Columns here are display names, so match on the _retrainMLP tag.
if args.exclude_retrain_mlp:
    if args.retrain_mlp_only:
        parser.error("--exclude_retrain_mlp and --retrain_mlp_only are mutually exclusive")
    keep_cols = [col for col in heatmap_table.columns if '_retrainMLP' not in col]
    heatmap_table = heatmap_table[keep_cols]
    heatmap_llm = {m for m in heatmap_llm if '_retrainMLP' not in m}
    suffix += '_noRetrainMLP'

# Drop _jointMLP variants from the heatmap if requested. Modes 7/7b/12/12w
# produce both a jointMLP (MLP head trained during joint LLM+PRICE finetune)
# and a retrainMLP (MLP retrained on cached embeddings post-finetune). The
# retrainMLP is usually the apples-to-apples comparison since modes 1/2 only
# have a retrainMLP-style variant. Mode 1 (no MLP at all) and mode 2
# (retrainMLP) keep all their columns.
if args.retrain_mlp_only:
    keep_cols = [col for col in heatmap_table.columns if '_jointMLP' not in col]
    heatmap_table = heatmap_table[keep_cols]
    heatmap_llm = {m for m in heatmap_llm if '_jointMLP' not in m}
    suffix += '_retrainMLPonly'

heatmap_path = os.path.join(out_dir, f'relative_qerror{db_tag}_{args.task}{anchor_tag}{suffix}_heatmap.png')
create_relative_heatmap(heatmap_table, heatmap_path, args.task, heatmap_llm)
