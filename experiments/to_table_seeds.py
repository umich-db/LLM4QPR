import pandas as pd
import glob
import os
import argparse
import re
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--dir", type=str)
parser.add_argument("--task", type=str)
parser.add_argument("--sentbert_only", action="store_true",
                    help="Only show sentBert-all_quant variants (plus non-LLM baselines) in .png")
args = parser.parse_args()

def strip_seed(filename):
    """Removes seed information to group files with same prefix"""
    return re.sub(r'_seed\d+', '', filename)

def extract_display_name(col_name):
    """Extract display name from column name"""
    # For LLM: extract model name
    if 'llm' in col_name:
        # Extract model name between h{number}_ and _emb or _quant
        match = re.search(r'h\d+_(.+?)(?:_emb|_quant)', col_name)
        if match:
            model = match.group(1)
            # Shorten common model names
            if 'sentence-transformers' in model:
                if 'paraphrase' in model:
                    model = 'sentBert-para'
                elif 'all-MiniLM' in model:
                    model = 'sentBert-all'
                else:
                    model = 'sentBert'
            # Also extract quantization
            quant_match = re.search(r'quant-([^_]+)', col_name)
            if quant_match:
                display_name = f"{model}_quant-{quant_match.group(1)}"
            else:
                display_name = model

            # Extract removed fields suffix if present
            rm_match = re.search(r'(_rm-[a-z\-]+)', col_name)
            if rm_match:
                display_name += rm_match.group(1)

            # Extract PRICE mode if this is an llm_price result
            if 'llm_price' in col_name:
                price_mode_match = re.search(r'(priceNoFT|priceLLMOnly|pricePRICEOnly|priceBothSep|priceFTwithLLM|priceFTthenJoint|priceGatedJoint)', col_name)
                if price_mode_match:
                    display_name = f"[{price_mode_match.group(1)}] {display_name}"
                else:
                    # Existing JointPrice (no explicit mode suffix)
                    display_name = f"[JointPrice] {display_name}"

            # Extract PRICE variant suffix (priceM or priceS)
            price_variant_match = re.search(r'_(priceM|priceS)', col_name)
            if price_variant_match:
                display_name += f"_{price_variant_match.group(1)}"

            # Extract pretrained status
            pretrained_match = re.search(r'pretrained-(\w+)', col_name)
            if pretrained_match:
                pt_status = pretrained_match.group(1)
                if pt_status != 'None':
                    display_name += f"_pt-{pt_status}"

            # Extract randInit flag
            if '_randInit' in col_name:
                display_name += '_randInit'

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

            return display_name
        return 'LLM'
    # For non-LLM: extract algorithm name
    else:
        # Extract algo name (e.g., aimai, qf, e2e_cost, bao)
        match = re.search(r'_(aimai|qf|e2e_cost|bao|postgres)_', col_name)
        if match:
            algo = match.group(1)
            # For aimai, also extract feature config if present
            feat_match = re.search(r'_f(\d+)', col_name)
            if feat_match and algo == 'aimai':
                return f"{algo}_f{feat_match.group(1)}"
            return algo
        return col_name

def is_llm_method(col_name):
    """Check if a method is LLM-based"""
    return 'llm' in col_name.lower()

def build_quantile_table(csv_folder, quantiles=[50, 75, 90, 99]):
    """
    Aggregates quantiles across seed files by averaging values with the same prefix.
    """
    # 1. Find all CSV files
    csv_paths = glob.glob(os.path.join(csv_folder, f'{args.task}*cdf*seed*.csv'))
    
    # Filter out files with "_rm-" and "downstream" (ablation studies and downstream tasks)
    filtered_paths = []
    for path in csv_paths:
        filename = os.path.basename(path)
        if "_rm-" in filename:
            continue
        if "downstream" in filename:
            continue
        if "trueEmb" in filename:
            continue
        filtered_paths.append(path)
    csv_paths = filtered_paths

    # 2. Group files by prefix
    grouped_paths = defaultdict(list)
    for path in csv_paths:
        base = os.path.splitext(os.path.basename(path))[0]
        prefix = strip_seed(base)
        grouped_paths[prefix].append(path)

    # 3. Initialize table
    idx = quantiles + ['max']
    table = pd.DataFrame(index=idx, columns=grouped_paths.keys(), dtype=float)

    # 4. Compute average quantiles per group
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

def create_heatmap_with_comparison(table, output_path):
    """
    Create a heatmap comparing LLM and non-LLM algorithms with special color coding:
    - Non-LLM: Dark orange for lowest, light orange for second lowest (per column)
    - LLM: Different shades of green based on ranking (per column)
    - Bold LLM names that beat lowest non-LLM in ≥2 columns
    - Add *** prefix for LLM names that beat second lowest non-LLM in ≥2 columns
    """
    # Separate LLM and non-LLM columns
    llm_cols = [col for col in table.columns if is_llm_method(col)]
    non_llm_cols = [col for col in table.columns if not is_llm_method(col)]
    
    # Reorder: non-LLM first, then LLM
    ordered_cols = non_llm_cols + llm_cols
    table = table[ordered_cols]
    
    # Create display names for y-axis
    display_names = {col: extract_display_name(col) for col in table.columns}
    
    # Transpose for visualization (methods as rows, percentiles as columns)
    table_T = table.T
    
    # Calculate statistics for each percentile (column)
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
    
    # Create custom y-axis labels with formatting
    y_labels = []
    for method in table_T.index:
        label = display_names[method]
        if method in llm_cols:
            # Bold if beats lowest in ≥2 columns
            if llm_beats_lowest[method] >= 2:
                # Escape underscores for LaTeX math mode
                label_escaped = label.replace('_', '\\_')
                label = f"$\\mathbf{{{label_escaped}}}$"
            # Add *** prefix if beats second lowest in ≥2 columns
            if llm_beats_second[method] >= 2:
                label = f"***{label}"
        y_labels.append(label)
    
    # Create figure with adjusted width for longer LLM names
    # Calculate max label length to adjust left margin
    max_label_length = max(len(str(label)) for label in y_labels)
    # Base width + extra for longer labels
    fig_width = max(12, len(table_T.columns) * 1.5 + max_label_length * 0.1)
    fig_height = max(8, len(table_T.index) * 0.5)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Create a custom colormap array
    n_rows, n_cols = table_T.shape
    colors = np.zeros((n_rows, n_cols, 4))  # RGBA
    
    # Color each cell based on rules
    for i, method in enumerate(table_T.index):
        for j, percentile in enumerate(table_T.columns):
            value = table_T.iloc[i, j]
            
            if method in non_llm_cols:
                # Non-LLM: mark lowest and second lowest
                non_llm_values = table_T.loc[non_llm_cols, percentile].sort_values()
                if len(non_llm_values) >= 1 and value == non_llm_values.iloc[0]:
                    # Dark orange for lowest
                    colors[i, j] = [1.0, 0.5, 0.0, 1.0]  # Dark orange
                elif len(non_llm_values) >= 2 and value == non_llm_values.iloc[1]:
                    # Light orange for second lowest
                    colors[i, j] = [1.0, 0.8, 0.4, 1.0]  # Light orange
                else:
                    # White for others
                    colors[i, j] = [1.0, 1.0, 1.0, 1.0]
            else:
                # LLM: shade of green based on ranking among LLM methods only
                # Smaller values (better performance) → darker green
                llm_values = table_T.loc[llm_cols, percentile].sort_values()
                # Find rank: 0 for smallest (best), n-1 for largest (worst)
                rank = list(llm_values.values).index(value)
                
                if len(llm_values) > 1:
                    # Map rank to intensity
                    # Rank 0 (best/smallest) → intensity = 0.3 (darkest)
                    # Rank n-1 (worst/largest) → intensity = 1.0 (brightest)
                    intensity = 0.3 + (rank / (len(llm_values) - 1)) * 0.7
                else:
                    # Single LLM method
                    intensity = 0.65
                
                colors[i, j] = [0.0, intensity, 0.0, 1.0]
    
    # Create the heatmap without color mapping (we'll use custom colors)
    im = ax.imshow(colors, aspect='auto')
    
    # Set ticks and labels
    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(table_T.columns, fontsize=12)
    ax.set_yticklabels(y_labels, fontsize=10)
    
    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add text annotations with values
    for i in range(n_rows):
        for j in range(n_cols):
            value = table_T.iloc[i, j]
            # Use scientific notation for values >= 1000
            if value >= 1000:
                text_str = f'{value:.2e}'
            else:
                text_str = f'{value:.2f}'
            text = ax.text(j, i, text_str,
                          ha="center", va="center", color="black", fontsize=8)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=[1.0, 0.5, 0.0, 1.0], label='Non-LLM: Lowest'),
        mpatches.Patch(facecolor=[1.0, 0.8, 0.4, 1.0], label='Non-LLM: 2nd Lowest'),
        mpatches.Patch(facecolor=[0.0, 0.3, 0.0, 1.0], label='LLM: Best (Smallest)'),
        mpatches.Patch(facecolor=[0.0, 0.65, 0.0, 1.0], label='LLM: Middle'),
        mpatches.Patch(facecolor=[0.0, 1.0, 0.0, 1.0], label='LLM: Worst (Largest)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
    
    # Add separator line between non-LLM and LLM
    if len(non_llm_cols) > 0 and len(llm_cols) > 0:
        separator_y = len(non_llm_cols) - 0.5
        ax.axhline(y=separator_y, color='black', linewidth=2, linestyle='--')
    
    # Labels
    ax.set_xlabel('Percentile', fontsize=14, fontweight='bold')
    ax.set_ylabel('Method', fontsize=14, fontweight='bold')
    ax.set_title(f'Q-Error Comparison: LLM vs Non-LLM Algorithms\n(Bold: beats best non-LLM in ≥2 cols, ***: beats 2nd-best in ≥2 cols)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Heatmap saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("LLM PERFORMANCE SUMMARY")
    print("="*80)
    for llm in llm_cols:
        print(f"{display_names[llm]}:")
        print(f"  Beats best non-LLM: {llm_beats_lowest[llm]}/{len(table_T.columns)} columns")
        print(f"  Beats 2nd-best non-LLM: {llm_beats_second[llm]}/{len(table_T.columns)} columns")
    print("="*80)

csv_folder = args.dir
quant_table = build_quantile_table(csv_folder, [50, 90, 95])
quant_table = quant_table.reindex(sorted(quant_table.columns), axis=1)

# Save CSV
csv_path = csv_folder + f'/quantile_table_{args.dir.replace("/", "_")}_{args.task}.csv'
quant_table.to_csv(csv_path)

# Filter to sentBert-all variants only (plus non-LLM baselines) for heatmap
if args.sentbert_only:
    display_map = {col: extract_display_name(col) for col in quant_table.columns}
    keep_cols = [col for col in quant_table.columns
                 if not is_llm_method(col) or 'sentBert-all' in display_map[col]]
    heatmap_table = quant_table[keep_cols]
    suffix = '_sentbert'
else:
    heatmap_table = quant_table
    suffix = ''

# Create heatmap
heatmap_path = csv_folder + f'/quantile_table_{args.dir.replace("/", "_")}_{args.task}{suffix}_heatmap.png'
create_heatmap_with_comparison(heatmap_table, heatmap_path)

print(csv_folder, "\n", quant_table.to_markdown())
