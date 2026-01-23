"""
Visualise geometry analysis tables as heatmaps with separate colouring for
non-LLM and LLM methods.

Usage:
    python plot_geometry_tables.py \
        --input_dir insights/geometry_results \
        --pattern geometry_table_*_card_seed42.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RESULT_DIRS = {
    "geometry": BASE_DIR / "geometry_results",
    "alignment": BASE_DIR / "metric_alignment_results",
}

GEOMETRY_METRICS = [
    "G1_mean_cosine",
    "G2_MCC",
    "G2_EVR1",
    "G2_effective_rank",
    "G4_hubness_gini",
    "CKA_metrics_embeddings",
    "CKA_embeddings_true_label",
    "CKA_embeddings_est_label",
]

LOWER_IS_BETTER = {
    "G1_mean_cosine",
    "G2_MCC",
    "G2_EVR1",
    "G4_hubness_gini",
}
HIGHER_IS_BETTER = {
    "G2_effective_rank",
    "CKA_metrics_embeddings",
    "CKA_embeddings_true_label",
    "CKA_embeddings_est_label",
}

NON_LLM_BASE = np.array([1.0, 0.45, 0.0])
LLM_BASE = np.array([0.0, 0.45, 0.0])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render heatmaps from geometry result tables."
    )
    parser.add_argument(
        "--result_type",
        choices=RESULT_DIRS.keys(),
        default="geometry",
        help="Which results to visualise: geometry or alignment (default: geometry).",
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        default=None,
        help="Directory containing result CSV files. Defaults to folder based on result_type.",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="geometry_table_*.csv",
        help="Glob pattern (relative to input_dir) for selecting CSV files.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=None,
        help="Optional output directory. Defaults to the CSV's directory.",
    )
    parser.add_argument(
        "--dpi", type=int, default=300, help="Figure DPI for saved heatmaps."
    )
    return parser.parse_args()


def is_llm_method(col_name: str) -> bool:
    return "llm" in col_name.lower()


def extract_display_name(col_name: str) -> str:
    if "llm" in col_name:
        # Extract model name between hXX_ and _emb/_quant/etc.
        import re

        match = re.search(r"h\d+_(.+?)(?:_emb|_quant)", col_name)
        if match:
            model = match.group(1)
        else:
            model = col_name
        quant_match = re.search(r"quant-([^_]+)", col_name)
        if quant_match:
            return f"{model}_quant-{quant_match.group(1)}"
        return model
    # For non-LLM methods, extract the algorithm name (second part after task)
    # Format: {task}_{algo}_...
    # Handle cases like "time_e2e_cost_..." -> "e2e_cost"
    parts = col_name.split("_")
    if len(parts) >= 2:
        # Check if it's a compound name like "e2e_cost"
        known_algos = ["e2e_cost", "aimai", "bao", "qf", "ALECE", "MSCN", "PRICE"]
        for algo in known_algos:
            if col_name.startswith(f"{parts[0]}_{algo}_"):
                return algo
        # Otherwise, just return the second part
        return parts[1]
    return col_name


def _metric_direction(metric: str, treat_missing_as_upper: bool = False) -> str:
    if metric in LOWER_IS_BETTER:
        return "lower"
    if metric in HIGHER_IS_BETTER:
        return "higher"
    return "higher" if treat_missing_as_upper else "lower"


def _rank_intensities(values: pd.Series, metric: str, treat_missing_as_upper: bool) -> pd.Series:
    values = values.astype(float)
    direction = _metric_direction(metric, treat_missing_as_upper=treat_missing_as_upper)
    ascending = direction == "lower"
    ranks = values.rank(method="min", ascending=ascending)
    max_rank = ranks.max()
    if max_rank <= 1:
        intensities = pd.Series(0.5, index=values.index)
    else:
        intensities = (ranks - 1) / (max_rank - 1)
    return intensities.clip(0.0, 1.0)


def _mix_with_white(base: np.ndarray, intensity: float) -> np.ndarray:
    intensity = float(np.clip(intensity, 0.0, 1.0))
    return base * (1 - intensity) + np.array([1.0, 1.0, 1.0]) * intensity


def _count_llm_wins(
    table: pd.DataFrame,
    llm_methods: List[str],
    non_llm_methods: List[str],
    treat_missing_as_upper: bool,
) -> dict[str, int]:
    wins = {method: 0 for method in llm_methods}
    for metric in table.columns:
        if not non_llm_methods:
            break
        non_llm_values = table.loc[non_llm_methods, metric]
        if non_llm_values.empty:
            continue
        direction = _metric_direction(metric, treat_missing_as_upper=treat_missing_as_upper)
        best = non_llm_values.min() if direction == "lower" else non_llm_values.max()
        for method in llm_methods:
            value = table.at[method, metric]
            if direction == "lower" and value < best:
                wins[method] += 1
            elif direction == "higher" and value > best:
                wins[method] += 1
    return wins


def _build_color_matrix(
    table: pd.DataFrame,
    llm_cols: List[str],
    treat_missing_as_upper: bool,
) -> np.ndarray:
    n_rows, n_cols = table.shape
    colors = np.ones((n_rows, n_cols, 4))
    colors[:, :, 3] = 1.0  # alpha

    for j, metric in enumerate(table.columns):
        intensities = _rank_intensities(table.iloc[:, j], metric, treat_missing_as_upper)
        for i, method in enumerate(table.index):
            base = LLM_BASE if method in llm_cols else NON_LLM_BASE
            colors[i, j, :3] = _mix_with_white(base, intensities.iloc[i])
    return colors


def _select_metrics(df: pd.DataFrame, desired_metrics: List[str], csv_path: Path) -> pd.DataFrame:
    if not desired_metrics:
        return df
    available = [metric for metric in desired_metrics if metric in df.index]
    if not available:
        print(
            f"Warning: none of the desired metrics {desired_metrics} were found in {csv_path.name}; "
            "using all available rows."
        )
        return df
    return df.loc[available]


def render_heatmap(
    csv_path: Path,
    output_dir: Path | None,
    dpi: int,
    desired_metrics: List[str],
    treat_missing_as_upper: bool,
) -> Path:
    df = pd.read_csv(csv_path, index_col=0)
    df = _select_metrics(df, desired_metrics, csv_path)
    df = df.T  # rows = methods, columns = metrics

    llm_methods = [idx for idx in df.index if is_llm_method(idx)]
    non_llm_methods = [idx for idx in df.index if idx not in llm_methods]
    ordered_methods = non_llm_methods + llm_methods
    df = df.loc[ordered_methods]

    display_names = {method: extract_display_name(method) for method in df.index}
    llm_win_counts = _count_llm_wins(df, llm_methods, non_llm_methods, treat_missing_as_upper)

    colors = _build_color_matrix(df, llm_methods, treat_missing_as_upper)

    fig_width = max(10, df.shape[1] * 1.8)
    fig_height = max(6, df.shape[0] * 0.6)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    ax.imshow(colors, aspect="auto")
    ax.set_xticks(np.arange(df.shape[1]))
    ax.set_yticks(np.arange(df.shape[0]))
    ax.set_xticklabels(df.columns, fontsize=12, rotation=30, ha="right")

    y_labels = [display_names[method] for method in df.index]
    ax.set_yticklabels(y_labels, fontsize=10)
    for tick, method in zip(ax.get_yticklabels(), df.index):
        if method in llm_methods and llm_win_counts.get(method, 0) >= 3:
            tick.set_fontweight("bold")

    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            value = df.iloc[i, j]
            text = f"{value:.4f}" if value < 1000 else f"{value:.2e}"
            ax.text(
                j,
                i,
                text,
                ha="center",
                va="center",
                color="black",
                fontsize=9,
            )

    if non_llm_methods and llm_methods:
        separator = len(non_llm_methods) - 0.5
        ax.axhline(separator, color="black", linewidth=2, linestyle="--")

    ax.set_xlabel("Geometry metrics", fontsize=14, fontweight="bold")
    ax.set_ylabel("Method", fontsize=14, fontweight="bold")
    ax.set_title(
        f"Embedding geometry comparison\n({csv_path.stem})",
        fontsize=15,
        fontweight="bold",
    )

    # Custom legend patches
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=_mix_with_white(NON_LLM_BASE, 0.1), label="Non-LLM (better)"),
        Patch(facecolor=_mix_with_white(NON_LLM_BASE, 0.8), label="Non-LLM (worse)"),
        Patch(facecolor=_mix_with_white(LLM_BASE, 0.1), label="LLM (better)"),
        Patch(facecolor=_mix_with_white(LLM_BASE, 0.8), label="LLM (worse)"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        fontsize=10,
    )

    plt.tight_layout()
    out_dir = output_dir or csv_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{csv_path.stem}.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved geometry heatmap: {out_path}")
    return out_path


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir or RESULT_DIRS[args.result_type]
    # Search recursively in dataset subdirectories (e.g., geometry_results/job_full/, geometry_results/tpch/, etc.)
    # Pattern like "geometry_table_*.csv" will match in any subdirectory
    recursive_pattern = f"**/{args.pattern}"
    csv_files = sorted(input_dir.glob(recursive_pattern))
    if not csv_files:
        raise FileNotFoundError(
            f"No files matched pattern '{args.pattern}' in {input_dir} or its subdirectories"
        )

    desired_metrics = GEOMETRY_METRICS if args.result_type == "geometry" else []
    treat_missing_as_upper = args.result_type == "alignment"

    for csv_path in csv_files:
        render_heatmap(
            csv_path,
            args.output_dir,
            args.dpi,
            desired_metrics,
            treat_missing_as_upper,
        )


if __name__ == "__main__":
    main()

