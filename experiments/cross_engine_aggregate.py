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
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

DBS = ['postgres', 'duckdb', 'spark']
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
    args = parser.parse_args()

    anchor_tag = "" if args.anchor == "50" else f"_anchor{args.anchor}"
    anchor_key = args.anchor if args.anchor == "max" else int(args.anchor)

    tables = {}
    for db in DBS:
        path = os.path.join(args.results_dir, db,
                            f"relative_qerror_{db}_{args.task}{anchor_tag}.csv")
        if not os.path.isfile(path):
            raise SystemExit(f"missing per-DB CSV: {path}")
        df = pd.read_csv(path, index_col=0)
        # CSV round-trip turns the index into strings; coerce 50/90/95 back to int
        # so the anchor lookup matches to_table_relative.py's index labels.
        df.index = [r if r == "max" else int(r) for r in df.index.astype(str)]
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

        base = f"relative_qerror_{model_label}_{args.task}{anchor_tag}"
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
