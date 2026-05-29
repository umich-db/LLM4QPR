#!/usr/bin/env python3
"""
4-panel visualization of the surrogate-based model selection search process.

Produces a 2x2 figure:
  A (top-left):  Latency-Accuracy Landscape
  B (top-right): Convergence / Search Progress
  C (bottom-left): Surrogate Uncertainty Contraction
  D (bottom-right): Feature Importance
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def visualize_search(
    result,
    candidates: pd.DataFrame,
    config,
    oracle_data: Optional[Dict] = None,
    output_path: str = "model_selection_v2_search.png",
    all_feasible_results: Optional[pd.DataFrame] = None,
) -> None:
    """Generate the 4-panel search visualization.

    Args:
        all_feasible_results: DataFrame with columns [model, latency_ms, p90]
            for ALL feasible models (from exhaustive evaluation). If provided,
            Panel A shows every feasible model with real accuracy.
    """
    plt.style.use("seaborn-v0_8-ticks")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Surrogate Model Selection — Search Visualization", fontsize=16, y=0.98)

    _panel_landscape(axes[0, 0], result, candidates, config, oracle_data,
                     all_feasible_results=all_feasible_results)
    _panel_convergence(axes[0, 1], result, config, oracle_data)
    _panel_uncertainty(axes[1, 0], result)
    _panel_feature_importance(axes[1, 1], result)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ============================================================
# Panel A: Latency–Accuracy Landscape
# ============================================================

def _panel_landscape(ax, result, candidates, config, oracle_data,
                     all_feasible_results=None):
    ax.set_title("A. Latency–Accuracy Landscape", fontsize=14, fontweight="bold")
    ax.set_xlabel("Latency (ms)", fontsize=12)
    ax.set_ylabel("Accuracy (neg. p90 Q-error)", fontsize=12)

    latencies = candidates["avg_ms"].to_numpy()

    # Latency limit shading
    ax.axvline(config.latency_limit, color="red", linestyle="--", alpha=0.7, linewidth=1.5, label="Latency limit")
    xlim_max = max(latencies.max() * 1.05, config.latency_limit * 1.3)
    ax.axvspan(config.latency_limit, xlim_max, alpha=0.08, color="red")

    # Build lookup of real accuracy for all feasible models
    real_acc = {}  # model_name -> -p90
    if all_feasible_results is not None:
        for _, r in all_feasible_results.iterrows():
            real_acc[r["model"]] = -r["p90"]

    # Set of evaluated model names
    eval_models = set()
    if not result.evaluated.empty and "model" in result.evaluated.columns:
        eval_models = set(result.evaluated["model"].tolist())
    eval_order = {h["candidate_id"]: i for i, h in enumerate(result.history)}

    if all_feasible_results is not None:
        # --- Mode: show ALL feasible models with real accuracy ---
        feasible_set = set(all_feasible_results["model"].tolist())

        # Infeasible models (latency > limit): gray, small, in the red zone
        infeasible_mask = candidates["avg_ms"] > config.latency_limit
        if infeasible_mask.any():
            ax.scatter(
                latencies[infeasible_mask],
                [real_acc.get(m, np.nan) for m in candidates.loc[infeasible_mask, "model"]],
                c="lightgray", alpha=0.25, s=15, zorder=1,
            )

        # Feasible + NOT evaluated by the search: gray circles
        unevaluated_feasible = []
        for _, r in all_feasible_results.iterrows():
            if r["model"] not in eval_models:
                unevaluated_feasible.append(r)
        if unevaluated_feasible:
            uf = pd.DataFrame(unevaluated_feasible)
            ax.scatter(
                uf["latency_ms"], -uf["p90"],
                c="silver", alpha=0.5, s=35, zorder=2, edgecolors="gray",
                linewidths=0.3, label="Feasible (not evaluated)",
            )

        # Feasible + evaluated by the search: colored by eval order
        evaluated_feasible = []
        eval_orders = []
        for _, r in all_feasible_results.iterrows():
            if r["model"] in eval_models:
                evaluated_feasible.append(r)
                eval_orders.append(eval_order.get(r["model"], 0))
        if evaluated_feasible:
            ef = pd.DataFrame(evaluated_feasible)
            sc = ax.scatter(
                ef["latency_ms"], -ef["p90"],
                c=eval_orders, cmap="viridis", alpha=0.85, s=55, zorder=3,
                edgecolors="k", linewidths=0.5, label="Evaluated by search",
            )
            cbar = plt.colorbar(sc, ax=ax, pad=0.02, fraction=0.04)
            cbar.set_label("Eval order", fontsize=10)

        # Evaluated infeasible models (latency > limit, evaluated by search)
        eval_infeasible = []
        eval_inf_orders = []
        for h in result.history:
            model_name = h["candidate_id"]
            if model_name not in feasible_set and model_name in real_acc:
                continue  # skip if no real data
            if h.get("feasible") is False or h["latency"] > config.latency_limit:
                acc = h["accuracy"]
                if np.isfinite(acc):
                    eval_infeasible.append((h["latency"], acc))
                    eval_inf_orders.append(eval_order.get(model_name, 0))
        if eval_infeasible:
            inf_lats, inf_accs = zip(*eval_infeasible)
            ax.scatter(inf_lats, inf_accs, c=eval_inf_orders, cmap="viridis",
                       alpha=0.6, s=40, zorder=3, edgecolors="red",
                       linewidths=1.0, marker="^")

    else:
        # --- Fallback: original behavior (dry run / no exhaustive data) ---
        evaluated_mask = candidates.index.isin(result.evaluated.index)
        noiseless_acc = {}
        if oracle_data and "oracle_best_accuracy" in oracle_data:
            try:
                from model_selection_v2 import synthetic_accuracy_noiseless
                for _, row in candidates.iterrows():
                    noiseless_acc[row["model"]] = synthetic_accuracy_noiseless(row)
            except ImportError:
                pass

        all_acc = np.array([
            noiseless_acc.get(row["model"], np.nan) for _, row in candidates.iterrows()
        ])

        uneval_mask = ~evaluated_mask
        if uneval_mask.any() and not np.all(np.isnan(all_acc[uneval_mask])):
            ax.scatter(
                latencies[uneval_mask], all_acc[uneval_mask],
                c="gray", alpha=0.35, s=30, zorder=2, label="Unevaluated",
            )

        eval_order_idx = {h["row_index"]: i for i, h in enumerate(result.history)}
        eval_indices = [idx for idx in candidates.index if idx in eval_order_idx]
        if eval_indices:
            orders = np.array([eval_order_idx[idx] for idx in eval_indices])
            lats = latencies[eval_indices]
            accs = np.array([
                noiseless_acc.get(candidates.loc[idx, "model"], result.evaluated.loc[idx, "_accuracy"])
                if idx in result.evaluated.index else all_acc[idx]
                for idx in eval_indices
            ])
            sc = ax.scatter(
                lats, accs, c=orders, cmap="viridis", alpha=0.8, s=50, zorder=3,
                edgecolors="k", linewidths=0.5, label="Evaluated",
            )
            cbar = plt.colorbar(sc, ax=ax, pad=0.02, fraction=0.04)
            cbar.set_label("Eval order", fontsize=10)

    # Oracle best
    if oracle_data and oracle_data.get("oracle_best_model"):
        oracle_model = oracle_data["oracle_best_model"]
        oracle_lat = oracle_data.get("oracle_best_latency")
        oracle_acc = oracle_data.get("oracle_best_accuracy")
        # Use real accuracy if available
        if oracle_model in real_acc:
            oracle_acc = real_acc[oracle_model]
        if oracle_lat is None:
            oracle_row = candidates[candidates["model"] == oracle_model]
            if not oracle_row.empty:
                oracle_lat = oracle_row["avg_ms"].values[0]
        if oracle_lat is not None and oracle_acc is not None:
            ax.scatter(
                oracle_lat, oracle_acc,
                marker="D", s=140, c="gold", edgecolors="k", linewidths=1.5,
                zorder=7, label="Oracle best",
            )

    # Selected model
    if result.best_feasible_row is not None:
        sel = result.best_feasible_row
        sel_model = sel["model"]
        sel_acc = real_acc.get(sel_model, sel["_accuracy"])
        sel_lat = sel.get("_latency", candidates[candidates["model"] == sel_model]["avg_ms"].values[0])
        ax.scatter(
            sel_lat, sel_acc,
            marker="*", s=280, c="limegreen", edgecolors="k", linewidths=1.5,
            zorder=8, label="Selected",
        )

    ax.legend(fontsize=9, loc="lower right")
    ax.set_xlim(left=0, right=xlim_max)


# ============================================================
# Panel B: Convergence / Search Progress
# ============================================================

def _panel_convergence(ax, result, config, oracle_data):
    ax.set_title("B. Convergence / Search Progress", fontsize=14, fontweight="bold")
    ax.set_xlabel("Evaluation #", fontsize=12)
    ax.set_ylabel("Best feasible accuracy", fontsize=12)

    history = result.history
    if not history:
        ax.text(0.5, 0.5, "No evaluations", ha="center", va="center", transform=ax.transAxes)
        return

    eval_nums = list(range(1, len(history) + 1))
    feasible_flags = [h["feasible"] for h in history]
    accuracies = [h["accuracy"] for h in history]

    # Scatter each evaluation
    for i, (en, feas, acc) in enumerate(zip(eval_nums, feasible_flags, accuracies)):
        color = "green" if feas else "red"
        ax.scatter(en, acc, c=color, s=25, alpha=0.7, zorder=3,
                   edgecolors="k", linewidths=0.3)

    # Cumulative best feasible line
    cum_best = []
    current_best = None
    for h in history:
        if h["feasible"]:
            if current_best is None or h["accuracy"] > current_best:
                current_best = h["accuracy"]
        cum_best.append(current_best)

    valid_evals = [(i + 1, cb) for i, cb in enumerate(cum_best) if cb is not None]
    if valid_evals:
        xs, ys = zip(*valid_evals)
        ax.step(xs, ys, where="post", color="royalblue", linewidth=2, label="Best feasible", zorder=4)

    # Oracle line
    if oracle_data and oracle_data.get("oracle_best_accuracy") is not None:
        ax.axhline(oracle_data["oracle_best_accuracy"], color="gold", linestyle="--",
                   linewidth=1.5, alpha=0.8, label="Oracle best")

    # Init budget boundary
    ax.axvline(config.init_budget, color="gray", linestyle="--", alpha=0.5, linewidth=1,
               label=f"Init budget ({config.init_budget})")

    # Legend with proxy artists for feasible/infeasible
    from matplotlib.lines import Line2D
    handles, labels = ax.get_legend_handles_labels()
    handles.extend([
        Line2D([0], [0], marker="o", color="w", markerfacecolor="green", markersize=7, label="Feasible"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="red", markersize=7, label="Infeasible"),
    ])
    ax.legend(handles=handles, fontsize=9, loc="lower right")
    ax.set_xlim(left=0)


# ============================================================
# Panel C: Surrogate Uncertainty Contraction
# ============================================================

def _panel_uncertainty(ax, result):
    ax.set_title("C. Surrogate Uncertainty Contraction", fontsize=14, fontweight="bold")
    ax.set_xlabel("Round", fontsize=12)
    ax.set_ylabel("Mean surrogate σ (unevaluated)", fontsize=12)

    snapshots = result.round_snapshots
    if not snapshots:
        ax.text(0.5, 0.5, "No round snapshots", ha="center", va="center", transform=ax.transAxes)
        return

    rounds = []
    mean_stds = []
    std_of_stds = []
    feature_change_rounds = []

    prev_features = None
    for snap in snapshots:
        r = snap["round"]
        rounds.append(r)

        # Std across ALL candidates (whole pool, not just unevaluated)
        all_std = snap["all_std_accuracy"]
        mean_stds.append(np.mean(all_std))
        std_of_stds.append(np.std(all_std))

        # Detect feature filtering events
        cur_features = snap["selected_feature_cols"]
        if prev_features is not None and cur_features != prev_features:
            feature_change_rounds.append(r)
        prev_features = cur_features

    rounds = np.array(rounds)
    mean_stds = np.array(mean_stds)
    std_of_stds = np.array(std_of_stds)

    ax.plot(rounds, mean_stds, color="steelblue", linewidth=2, marker="o", markersize=4, zorder=3)
    ax.fill_between(
        rounds,
        mean_stds - std_of_stds,
        mean_stds + std_of_stds,
        alpha=0.2, color="steelblue",
    )

    # Mark feature filtering events
    for fr in feature_change_rounds:
        ax.axvline(fr, color="orange", linestyle=":", linewidth=1.5, alpha=0.8)
        ypos = mean_stds.max() + std_of_stds.max() * 0.3
        ax.annotate("feature\nfilter", xy=(fr, ypos),
                     fontsize=8, color="orange", ha="center", va="bottom",
                     xytext=(0, 5), textcoords="offset points")

    ax.set_xlim(left=0.5)
    if len(rounds) > 0:
        ax.set_xlim(right=rounds.max() + 0.5)


# ============================================================
# Panel D: Feature Importance
# ============================================================

def _panel_feature_importance(ax, result):
    ax.set_title("D. Feature Importance (Final Surrogate)", fontsize=14, fontweight="bold")

    snapshots = result.round_snapshots
    selected_features = result.selected_feature_names

    if not selected_features:
        ax.text(0.5, 0.5, "No features", ha="center", va="center", transform=ax.transAxes)
        return

    # Use the last snapshot's std as a proxy for feature diversity
    # Better: compute permutation importance from the final accuracy surrogate
    # We'll use the evaluated data + a simple RF importance approach
    evaluated = result.evaluated
    if evaluated.empty or len(selected_features) == 0:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center", transform=ax.transAxes)
        return

    # Check which features are available in the evaluated dataframe
    available = [f for f in selected_features if f in evaluated.columns]
    if not available:
        ax.text(0.5, 0.5, "Features not in evaluated data", ha="center", va="center", transform=ax.transAxes)
        return

    # Try to get importances from permutation importance on a quick RF
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler, OneHotEncoder
        from sklearn.compose import ColumnTransformer

        from model_selection_v2 import CONTINUOUS_COLS, CATEGORICAL_COLS

        X = evaluated[available].copy()
        y = evaluated["_accuracy"].to_numpy()

        cont_feats = [c for c in available if c in CONTINUOUS_COLS or c == "log_non_embedding_params"]
        cat_feats = [c for c in available if c in CATEGORICAL_COLS]

        cont_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
        cat_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                             ("onehot", OneHotEncoder(handle_unknown="ignore"))])
        prep = ColumnTransformer([
            ("cont", cont_pipe, cont_feats),
            ("cat", cat_pipe, cat_feats),
        ], remainder="drop")

        rf = Pipeline([("prep", prep), ("model", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))])
        rf.fit(X, y)

        pi = permutation_importance(rf, X, y, n_repeats=10, random_state=42, n_jobs=-1)
        importances = pd.Series(pi.importances_mean, index=available).sort_values(ascending=True)
    except Exception:
        # Fallback: just show feature names with no importance
        importances = pd.Series(np.ones(len(available)), index=available).sort_values(ascending=True)

    # Color by type
    colors = []
    for feat in importances.index:
        if feat in CATEGORICAL_COLS:
            colors.append("tab:orange")
        else:
            colors.append("tab:blue")

    ax.barh(range(len(importances)), importances.values, color=colors, edgecolor="k", linewidth=0.3)
    ax.set_yticks(range(len(importances)))
    ax.set_yticklabels(importances.index, fontsize=9)
    ax.set_xlabel("Permutation importance", fontsize=12)

    # Legend for color meaning
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="tab:blue", edgecolor="k", label="Continuous"),
        Patch(facecolor="tab:orange", edgecolor="k", label="Categorical"),
    ]
    ax.legend(handles=legend_elements, fontsize=9, loc="lower right")


if __name__ == "__main__":
    print("This module is imported by model_selection_v2.py. Run that script instead.")
