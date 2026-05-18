"""Plot the test-side Pareto frontier on (inference latency, test_p90) and
emit (a) a PNG showing all models with the frontier highlighted and (b) a
terminal table listing the frontier models in ascending latency.

Pool source:  all_models/all_models_full_e16.csv (test_p90_e16, key→model).
Latency src:  all_models_full_e16.csv:test_total_eval_ms — H100 per-query
              LLM+PRICE+MLP+cross-attn forward (the deployed-inference latency,
              not the LLM-only avg_ms from model_profile_with_nonemb.csv).
              The override happens inside join_pool_with_profile.

Pareto sense: minimise BOTH avg_ms (= deployed latency) and test_p90_e16.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path("/root/LLM4QPR/experiments")
ALL_MODELS_CSV = ROOT / "logs/postgres/logs_Train_stats_Test_stats_ours/all_models/all_models_full_e16.csv"
PROFILE_CSV = ROOT / "experiment_scripts/model_profile_with_nonemb.csv"

# Reuse the existing join helper so the model-name resolution stays in sync
# with compare_round_pareto.py / plot_hv_vs_hours.
sys.path.insert(0, str(ROOT / "experiment_scripts"))
from compare_round_pareto import (  # noqa: E402
    join_pool_with_profile, pareto_frontier_indices,
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=str, default="/tmp/true_pareto_frontier.png")
    ap.add_argument("--title", type=str, default=None)
    ap.add_argument("--logy", action="store_true",
                     help="Log-scale the test_p90 axis (helpful when the "
                          "frontier spans a wide qerror range).")
    ap.add_argument("--annotate", action="store_true",
                     help="Annotate each frontier point with its model name.")
    ap.add_argument("--max_qerror", type=float, default=float("inf"),
                     help="Hide models with test_p90_e16 > this from the FIGURE "
                          "only (frontier computation + terminal table still use "
                          "the full pool).")
    ap.add_argument("--max_latency", type=float, default=float("inf"),
                     help="Hide models with avg_ms > this from the FIGURE only.")
    args = ap.parse_args()

    all_df = pd.read_csv(ALL_MODELS_CSV)
    prof = pd.read_csv(PROFILE_CSV)
    pool = join_pool_with_profile(all_df, prof).reset_index(drop=True)

    lat = pool["avg_ms"].to_numpy(dtype=float)
    qerr = pool["test_p90_e16"].to_numpy(dtype=float)
    pts = np.column_stack([lat, qerr])

    frontier_ix = pareto_frontier_indices(pts)
    frontier_ix = sorted(frontier_ix, key=lambda i: lat[i])  # sort by latency
    n_total = len(pool)
    n_frontier = len(frontier_ix)

    # ─── Terminal table ─────────────────────────────────────────────────────
    print(f"Pool: {n_total} models. Frontier: {n_frontier} models on "
          f"(avg_ms ↓, test_p90_e16 ↓).\n")
    print(f"  {'#':>2}  {'avg_ms':>8}  {'test_p90':>9}  model")
    for rank, i in enumerate(frontier_ix, 1):
        print(f"  {rank:>2}  {lat[i]:>8.2f}  {qerr[i]:>9.4f}  {pool.at[i, 'model']}")

    # ─── PNG ────────────────────────────────────────────────────────────────
    # Figure-only filter: don't change frontier/table, just hide off-grid points.
    def visible(i):
        return lat[i] <= args.max_latency and qerr[i] <= args.max_qerror

    fig, ax = plt.subplots(figsize=(10, 6.5))
    front_set = set(frontier_ix)
    # Non-frontier points: light gray, filtered.
    non_front = [i for i in range(n_total) if i not in front_set and visible(i)]
    ax.scatter(lat[non_front], qerr[non_front],
                s=24, color="#bbbbbb", alpha=0.7,
                label=f"non-frontier ({len(non_front)} shown)", zorder=2)
    # Frontier points (visible subset), preserving sorted-by-latency order.
    vis_frontier = [i for i in frontier_ix if visible(i)]
    fx = lat[vis_frontier]
    fy = qerr[vis_frontier]
    n_hidden_front = n_frontier - len(vis_frontier)
    front_label = f"Pareto frontier ({len(vis_frontier)} shown)"
    if n_hidden_front:
        front_label += f", {n_hidden_front} hidden by filter"
    ax.scatter(fx, fy, s=70, color="#d62728", marker="o",
                edgecolor="black", linewidth=1.0,
                label=front_label, zorder=4)
    # Staircase line between visible frontier points.
    if len(fx) >= 2:
        step_x, step_y = [fx[0]], [fy[0]]
        for j in range(1, len(fx)):
            step_x += [fx[j], fx[j]]
            step_y += [step_y[-1], fy[j]]
        ax.plot(step_x, step_y, color="#d62728", linewidth=1.5, alpha=0.75,
                 zorder=3)

    if args.annotate:
        for i in vis_frontier:
            ax.annotate(pool.at[i, "model"], (lat[i], qerr[i]),
                         xytext=(4, 4), textcoords="offset points",
                         fontsize=7, alpha=0.8)

    ax.set_xlabel("Inference latency  avg_ms (lower = better)", fontsize=12)
    ax.set_ylabel("Test Q-error p90 (e16)  (lower = better)", fontsize=12)
    if args.logy:
        ax.set_yscale("log")
    title = args.title or (f"Pool Pareto frontier (avg_ms × test_p90_e16)   "
                            f"{n_frontier}/{n_total} models")
    ax.set_title(title, fontsize=12)
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output, dpi=140, bbox_inches="tight")
    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
