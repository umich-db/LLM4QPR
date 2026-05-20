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
                    help="Only show sentBert-all_quant variants (plus non-LLM baselines) in .png")
parser.add_argument("--exclude_retrain_mlp", action="store_true",
                    help="Drop _retrainMLP (inference-phase pretrained-lora) variants from the .png heatmap.")
parser.add_argument("--special_set1", action="store_true",
                    help="Special set 1: only the 4 setups from master_cross_engine_comparison.sh spark section "
                         "(Mode 1 pretrained, Mode 2 LoRA, Mode 7 JointPrice priceS, Mode 12 inflatePRICE cx4) "
                         "plus non-LLM baselines.")
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

            pretrained_match = re.search(r'pretrained-(\w+)', col_name)
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
            pwm_match = re.search(r'_pwm(\d+)', col_name)
            if pwm_match:
                display_name += f"_pwm{pwm_match.group(1)}"

            # Extract PRICE n_layers (e.g., _pL3, _pL12)
            pl_match = re.search(r'_pL(\d+)', col_name)
            if pl_match:
                display_name += f"_pL{pl_match.group(1)}"

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

            return display_name
        return 'LLM'
    else:
        match = re.search(r'_(aimai|qf|e2e_cost|bao|postgres)_', col_name)
        if match:
            algo = match.group(1)
            feat_match = re.search(r'_f(\d+)', col_name)
            if feat_match and algo == 'aimai':
                return f"{algo}_f{feat_match.group(1)}"
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


def compute_relative_qerror(tables_by_dataset):
    """
    Given {dataset_name: quantile_table}, compute relative Q-error:
    For each dataset, divide ALL values by a single scalar — the minimum
    value in the median (p50) row. Using one divisor per dataset preserves
    monotonicity across percentiles (p50 <= p90 <= p95 <= max).

    Returns {dataset_name: relative_table} with same structure.
    """
    relative_tables = {}
    for ds_name, table in tables_by_dataset.items():
        # Use the best method's median Q-error as the single reference scalar
        median_row = table.index[0]  # first row is the lowest quantile (p50)
        ref_scalar = table.loc[median_row].min()
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

# 2. Rename columns to display names (resolve collisions by keeping prefix)
#    First check for display name collisions
dn_to_prefixes = defaultdict(list)
for prefix, dn in display_name_map.items():
    dn_to_prefixes[dn].append(prefix)

# If collision, keep prefix as display name
final_name_map = {}
for prefix, dn in display_name_map.items():
    if len(dn_to_prefixes[dn]) > 1:
        final_name_map[prefix] = prefix  # keep full prefix
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
relative_tables = compute_relative_qerror(tables_by_dataset)

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
out_path = os.path.join(out_dir, f'relative_qerror_{args.task}.csv')
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


# Filter to sentBert-all variants only (plus non-LLM baselines) for heatmap
if args.sentbert_only:
    keep_cols = [col for col in avg_relative.columns
                 if col not in llm_display_names or 'sentBert-all' in col]
    heatmap_table = avg_relative[keep_cols]
    heatmap_llm = {m for m in llm_display_names if 'sentBert-all' in m}
    suffix = '_sentbert'
else:
    heatmap_table = avg_relative
    heatmap_llm = llm_display_names
    suffix = ''

# Drop retrainMLP variants from the heatmap if requested (CSV table keeps them).
# Columns here are display names, so match on the _retrainMLP tag.
if args.exclude_retrain_mlp:
    keep_cols = [col for col in heatmap_table.columns if '_retrainMLP' not in col]
    heatmap_table = heatmap_table[keep_cols]
    heatmap_llm = {m for m in heatmap_llm if '_retrainMLP' not in m}
    suffix += '_noRetrainMLP'

heatmap_path = os.path.join(out_dir, f'relative_qerror_{args.task}{suffix}_heatmap.png')
create_relative_heatmap(heatmap_table, heatmap_path, args.task, heatmap_llm)
