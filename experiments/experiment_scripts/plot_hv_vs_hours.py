#!/usr/bin/env python3
"""Plot HV vs training hours for multi-fidelity elimination configs + baselines.

Each curve traces (mean total_min/60, mean hv_ours) over a sweep of init_K.
Shaded band is ±1 standard error across seeds (~30 seeds per point).

Multi-fidelity elimination methods (all use filter [12]@0.85):
    A — kmeans+latency init + topval keep   (full recipe)
    B — kmeans+latency init + random keep   (ablate keep ranking)
    C — latency init + topval keep          (ablate kmeans)
    D — random init + topval keep           (ablate latency-stratification)
    G — latency init + random keep          (ablate keep ranking, w/ latency init)

Baselines (no filter):
    E — kmeans+latency init, train all to e16  (isolates filter contribution)
    F — random init, train all to e16          (pure random model selection)
    H — latency init, train all to e16          (isolates filter w/ latency init)

Usage:
    python experiment_scripts/plot_hv_vs_hours.py
    python experiment_scripts/plot_hv_vs_hours.py --output /tmp/my.png \\
        --seeds 0 1 2 3 4 5 6 7 8 9 --init_Ks 6 12 18 24 30 43
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parent / "compare_round_pareto.py"

# (label, color, marker, args, rounds_override)  — rounds_override forces --rounds 1.
CONFIGS = [
    # Multi-fidelity elimination methods (filter at e12 with kr=0.85).
    ("A: kmeans+latency + topval keep (multi-fidelity, full)", "#1f77b4", "o",
        ["--init_strategy", "stratified_kmeans_round",
         "--keep_strategy", "topval"], None),
    ("B: kmeans+latency + random keep (multi-fidelity)",       "#ff7f0e", "s",
        ["--init_strategy", "stratified_kmeans_round",
         "--keep_strategy", "random"], None),
    ("C: latency + topval keep (multi-fidelity)",              "#2ca02c", "^",
        ["--init_strategy", "stratified",
         "--keep_strategy", "topval"], None),
    ("D: random + topval keep (multi-fidelity)",               "#d62728", "v",
        ["--init_strategy", "random",
         "--keep_strategy", "topval"], None),
    # E: same init as the multi-fidelity methods but no filter.
    # Isolates the value of the filter step itself (compare A vs E at same init).
    ("E: kmeans+latency (no filter)",                          "#9467bd", "D",
        ["--init_strategy", "stratified_kmeans_round"], 1),
    # F: random init, no filter. Pure "random model selection" baseline.
    ("F: random (random baseline)",                            "#7f7f7f", "x",
        ["--init_strategy", "random"], 1),
    # G: latency init + random keep. Pairs with C to isolate the keep step
    # under latency-stratified (not kmeans) init.
    ("G: latency + random keep (multi-fidelity)",              "#8c564b", "P",
        ["--init_strategy", "stratified",
         "--keep_strategy", "random"], None),
    # H: latency init, no filter. Pairs with C/G to isolate the filter step
    # under latency-stratified init (compare A↔E and C↔H side-by-side).
    ("H: latency (no filter)",                                 "#e377c2", "*",
        ["--init_strategy", "stratified"], 1),
]


def _setting_letter(label: str) -> str:
    """Extract the leading 'A:' / 'B:' / … letter from a CONFIGS label."""
    return label.split(":", 1)[0].strip().upper()


def run_and_load(label, args, rounds_override, seeds, init_Ks,
                  decision_epochs, keep_ratio, out_csv):
    """Run compare_round_pareto.py, return DataFrame aggregated per init_K."""
    cmd = [
        sys.executable, str(SCRIPT),
        "--keep_ratio", str(keep_ratio),
        "--seeds", *map(str, seeds),
        "--init_Ks", *map(str, init_Ks),
        "--per_seed_output", str(out_csv),
        *args,
    ]
    if rounds_override is not None:
        cmd += ["--rounds", str(rounds_override)]
    elif decision_epochs:
        cmd += ["--decision_epochs", *map(str, decision_epochs)]
    print(f"  $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, capture_output=True, text=True, check=True)

    df = pd.read_csv(out_csv)
    agg = df.groupby("init_K").agg(
        hv_mean=("hv_ours", "mean"),
        hv_sem=("hv_ours", lambda s: s.std() / np.sqrt(len(s))),
        hours_mean=("total_min", lambda s: s.mean() / 60.0),
        hours_sem=("total_min", lambda s: (s.std() / np.sqrt(len(s))) / 60.0),
        n=("hv_ours", "size"),
    ).reset_index()
    return agg


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(30)))
    ap.add_argument("--init_Ks", type=int, nargs="+",
                     default=[6, 8, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30,
                               32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78])
    ap.add_argument("--decision_epochs", type=int, nargs="*", default=[12])
    ap.add_argument("--keep_ratio", type=float, default=0.85)
    ap.add_argument("--tmpdir", type=str, default="/tmp/hv_vs_hours")
    ap.add_argument("--output", type=str, default="/tmp/hv_vs_hours.png")
    ap.add_argument("--title", type=str, default=None,
                     help="Plot title (default: auto-generated).")
    ap.add_argument("--no_band", action="store_true",
                     help="Skip the ±1 SEM error bars on each point.")
    ap.add_argument("--settings", type=str, nargs="+", default=None,
                     metavar="LETTER",
                     help="Subset of CONFIGS to plot, by leading letter "
                          "(e.g. --settings C D F G H). Default: all.")
    args = ap.parse_args()

    configs = CONFIGS
    if args.settings:
        wanted = {s.strip().upper() for s in args.settings}
        configs = [c for c in CONFIGS if _setting_letter(c[0]) in wanted]
        missing = wanted - {_setting_letter(c[0]) for c in CONFIGS}
        if missing:
            print(f"WARNING: --settings asked for {sorted(missing)} which are not in CONFIGS")
        if not configs:
            ap.error(f"No CONFIGS matched --settings {sorted(wanted)}")
        print(f"Plotting {len(configs)} settings: "
              f"{[_setting_letter(c[0]) for c in configs]}")

    tmpdir = Path(args.tmpdir)
    tmpdir.mkdir(parents=True, exist_ok=True)

    # Run all configs, collect per-init_K aggregates.
    records = []
    for label, color, marker, extra, rounds_override in configs:
        print(f"\n=== {label} ===")
        out_csv = tmpdir / f"per_seed_{label.split(':')[0].strip()}.csv"
        agg = run_and_load(label, extra, rounds_override, args.seeds, args.init_Ks,
                            args.decision_epochs, args.keep_ratio, out_csv)
        agg["label"] = label
        agg["color"] = color
        agg["marker"] = marker
        records.append(agg)

    # ─── Plot ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fits = {}   # setting letter → (x_grid, y_fit) sampled densely from the line
    for df in records:
        color = df["color"].iloc[0]
        marker = df["marker"].iloc[0]
        label = df["label"].iloc[0]
        x = df["hours_mean"].to_numpy()
        y = df["hv_mean"].to_numpy()
        y_sem = df["hv_sem"].to_numpy()
        # Sort by x.
        order = np.argsort(x)
        x, y, y_sem = x[order], y[order], y_sem[order]
        is_baseline = "baseline" in label

        # Scatter the actual data points (with or without error bars).
        ax.errorbar(x, y, yerr=(None if args.no_band else y_sem),
                     fmt=marker, color=color,
                     markersize=8 if is_baseline else 6,
                     elinewidth=1.0, capsize=3, alpha=0.85,
                     zorder=4 if is_baseline else 3,
                     linestyle="None")

        # Fit a smooth curve through the points: 2nd-degree polynomial on
        # log-x. Captures the saturating "diminishing returns" shape without
        # the wiggle that connecting raw points produces.
        x_fit_grid = np.linspace(x.min(), x.max(), 200)
        if len(x) >= 3:
            coeffs = np.polyfit(np.log(x), y, deg=min(2, len(x) - 1))
            y_fit = np.polyval(coeffs, np.log(x_fit_grid))
        else:
            y_fit = np.interp(x_fit_grid, x, y)
        ax.plot(x_fit_grid, y_fit, color=color, label=label,
                 linewidth=2.5 if is_baseline else 1.8,
                 linestyle="--" if is_baseline else "-",
                 zorder=3 if is_baseline else 2,
                 alpha=0.85)
        fits[_setting_letter(label)] = (x_fit_grid, y_fit)

    ax.set_xlabel("Training time (H100-equivalent hours)", fontsize=12)
    ax.set_ylabel("Hypervolume (hv_ours)", fontsize=12)
    if args.title is None:
        title = ("Model-selection HV vs training time   "
                 f"(schedule=[{','.join(map(str, args.decision_epochs))}], "
                 f"kr={args.keep_ratio}, "
                 f"{len(args.seeds)} seeds × {len(args.init_Ks)} init_K)")
    else:
        title = args.title
    ax.set_title(title, fontsize=12)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output, dpi=140, bbox_inches="tight")
    print(f"\nSaved: {args.output}")

    # ─── C vs F time-at-HV table (uses the fitted lines) ───────────────────
    if "C" in fits and "F" in fits:
        xC, yC = fits["C"]
        xF, yF = fits["F"]
        # Inverse-interp on the fitted, cumulative-max curves.
        yC_mono = np.maximum.accumulate(yC)
        yF_mono = np.maximum.accumulate(yF)
        hv_lo = max(yC_mono.min(), yF_mono.min())
        hv_hi = min(yC_mono.max(), yF_mono.max())
        targets = np.linspace(hv_lo, hv_hi, 12)

        def hours_at_hv(x_grid, y_mono, hv_t):
            if hv_t < y_mono[0] or hv_t > y_mono[-1]:
                return None
            j = int(np.searchsorted(y_mono, hv_t, side="left"))
            if j == 0:
                return float(x_grid[0])
            y0, y1 = y_mono[j - 1], y_mono[j]
            x0, x1 = x_grid[j - 1], x_grid[j]
            if y1 == y0:
                return float(x1)
            return float(x0 + (x1 - x0) * (hv_t - y0) / (y1 - y0))

        print("\n=== Time-at-HV from fitted lines: F vs C ===")
        print(f"HV overlap on fits: [{hv_lo:.3f}, {hv_hi:.3f}]")
        print(f"{'HV target':>10}  {'hours_C':>9}  {'hours_F':>9}  "
              f"{'F - C (h)':>11}  {'F / C':>7}")
        for t in targets:
            hC = hours_at_hv(xC, yC_mono, t)
            hF = hours_at_hv(xF, yF_mono, t)
            if hC is None or hF is None:
                print(f"{t:>10.3f}  {'N/A':>9}  {'N/A':>9}  "
                      f"{'N/A':>11}  {'N/A':>7}")
                continue
            print(f"{t:>10.3f}  {hC:>9.2f}  {hF:>9.2f}  "
                  f"{hF - hC:>+11.2f}  {hF / hC:>7.2f}×")


if __name__ == "__main__":
    main()
