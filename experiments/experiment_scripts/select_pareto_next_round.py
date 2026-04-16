#!/usr/bin/env python3
"""
Successive-halving helper for Mode 12 inflatePRICE model selection.

Given:
  - a list of models that were finetuned in the current round
  - the epoch count at which those runs ended (to locate their logs)
  - a target group size for the next round
this script:
  1) Parses each model's finetune log to extract the FINAL val 90th-percentile Q-error.
  2) Computes (latency, val_p90) Pareto levels over the reachable models.
  3) Outputs the top `--group_size` models (ordered by Pareto level, ties broken
     by val_p90 then latency) to a text file you can feed into the next round.

It does not delete or touch any checkpoints/weights. The next round is driven
purely by the output models list; existing `_epoch{N}.pt` checkpoints will be
auto-resumed by train.py, so training continues from epoch N to the new num_epoch
without re-doing completed epochs.

Usage:
  python select_pareto_next_round.py \
      --models_file initial_32_models_seed42.txt \
      --current_epoch 4 \
      --group_size 16 \
      --output next_round_16.txt

Optional flags let you change the log-path pieces if you run with different
settings (e.g., different db/workload/ft_bs).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent
DEFAULT_CSV = SCRIPT_DIR / "model_profile_with_nonemb.csv"


def parse_models_file(path: str) -> List[str]:
    """Read models from a text file.
    Accepts either:
      - one model per line (anything non-comment)
      - tab-separated: 'rank<TAB>model<TAB>...'  (e.g. initial_32_models_seed42.txt)
    """
    models: List[str] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                # first field that looks like a model name (has '/' or is a known prefix)
                parts = line.split("\t")
                for p in parts:
                    if "/" in p:
                        models.append(p.strip())
                        break
            else:
                models.append(line)
    return models


def load_latency(csv_path: str) -> dict[str, float]:
    latency: dict[str, float] = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = row.get("model", "").strip()
            try:
                latency[m] = float(row["avg_ms"])
            except (KeyError, TypeError, ValueError):
                pass
    return latency


def log_path_for(
    model: str,
    db: str,
    train_wl: str,
    test_wl: str,
    ft_batch_size: int,
    num_epoch: int,
    lr: str,
    hid_units: int,
    quant: str,
    tag: str,  # e.g. "priceS_inflatePRICE_randInit_cx4"
) -> Path:
    model_hyphen = model.replace("/", "-")
    fname = (
        f"time_llm_price_finetune_lora_biCrossAttn_{db}_{lr}_b{ft_batch_size}_"
        f"h{hid_units}_{model_hyphen}_quant-{quant}_{tag}_e{num_epoch}.log"
    )
    return (
        EXPERIMENTS_DIR
        / "logs"
        / db
        / f"logs_Train_{train_wl}_Test_{test_wl}_ours"
        / fname
    )


_VAL_SECTION = re.compile(r"Data section:\s*val", re.IGNORECASE)
_P90 = re.compile(r"90th percentile:\s*([\d.eE+-]+)")


def extract_final_val_p90(log_path: Path) -> Tuple[float | None, int]:
    """Return (final val p90, number of val evaluations found)."""
    if not log_path.exists():
        return None, 0
    last_p90: float | None = None
    n_val = 0
    waiting_for_p90 = False
    with open(log_path, errors="ignore") as f:
        for line in f:
            if _VAL_SECTION.search(line):
                waiting_for_p90 = True
                continue
            if waiting_for_p90:
                m = _P90.search(line)
                if m:
                    try:
                        last_p90 = float(m.group(1))
                        n_val += 1
                    except ValueError:
                        pass
                    waiting_for_p90 = False
    return last_p90, n_val


def pareto_levels(points: List[Tuple[float, float]]) -> List[int]:
    """Assign Pareto level to each point (lower = better). Minimize both axes.

    Level 1 = Pareto frontier. Level 2 = frontier of remaining points. Etc.
    Points with the same (x, y) get the same level.
    """
    n = len(points)
    level = [0] * n
    remaining = list(range(n))
    lvl = 1
    while remaining:
        # Find Pareto-optimal set within remaining
        front: List[int] = []
        for i in remaining:
            dominated = False
            xi, yi = points[i]
            for j in remaining:
                if i == j:
                    continue
                xj, yj = points[j]
                if (xj <= xi and yj <= yi) and (xj < xi or yj < yi):
                    dominated = True
                    break
            if not dominated:
                front.append(i)
        if not front:
            break
        for idx in front:
            level[idx] = lvl
        remaining = [i for i in remaining if i not in front]
        lvl += 1
    return level


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models_file", required=True, help="File listing models finetuned this round.")
    ap.add_argument("--current_epoch", type=int, required=True, help="num_epoch used in the finished round.")
    ap.add_argument("--group_size", type=int, required=True, help="How many models to advance.")
    ap.add_argument("--output", default=None, help="Output file (one model per line). Default: stdout only.")
    ap.add_argument("--db", default="postgres")
    ap.add_argument("--train_wl", default="stats")
    ap.add_argument("--test_wl", default="stats")
    ap.add_argument("--ft_batch_size", type=int, default=24)
    ap.add_argument("--lr", default="0.0001")
    ap.add_argument("--hid_units", type=int, default=2048)
    ap.add_argument("--quant", default="4-bit")
    ap.add_argument("--tag", default="priceS_inflatePRICE_randInit_cx4",
                    help="Fixed suffix tying together the knobs you locked in this round.")
    ap.add_argument("--profile_csv", default=str(DEFAULT_CSV))
    args = ap.parse_args()

    models = parse_models_file(args.models_file)
    if not models:
        print(f"No models found in {args.models_file}", file=sys.stderr)
        return 1
    print(f"Loaded {len(models)} models from {args.models_file}")

    latency_map = load_latency(args.profile_csv)

    results: List[dict] = []
    missing: List[str] = []
    for model in models:
        log_path = log_path_for(
            model, args.db, args.train_wl, args.test_wl,
            args.ft_batch_size, args.current_epoch, args.lr, args.hid_units,
            args.quant, args.tag,
        )
        p90, n_val = extract_final_val_p90(log_path)
        lat = latency_map.get(model)
        results.append({
            "model": model,
            "log": str(log_path),
            "val_p90": p90,
            "n_val": n_val,
            "latency": lat,
        })
        if p90 is None or lat is None:
            missing.append(model)

    if missing:
        print(f"\nWARNING: {len(missing)} models missing val p90 or latency (will be excluded):")
        for m in missing:
            r = next(r for r in results if r["model"] == m)
            reason = []
            if r["val_p90"] is None:
                reason.append(f"no val in log (path={r['log']})")
            if r["latency"] is None:
                reason.append("no latency in CSV")
            print(f"  {m}: {', '.join(reason)}")

    usable = [r for r in results if r["val_p90"] is not None and r["latency"] is not None]
    if not usable:
        print("No usable models — aborting.", file=sys.stderr)
        return 1

    # Compute Pareto levels on (latency, val_p90) — both to minimize.
    points = [(r["latency"], r["val_p90"]) for r in usable]
    levels = pareto_levels(points)
    for r, lvl in zip(usable, levels):
        r["pareto_level"] = lvl

    # Sort by (pareto_level, val_p90, latency).
    usable.sort(key=lambda r: (r["pareto_level"], r["val_p90"], r["latency"]))

    # Print the full ranked table.
    print(f"\n{'rank':>4}  {'lvl':>3}  {'val_p90':>10}  {'lat_ms':>8}  model")
    print("-" * 80)
    for i, r in enumerate(usable, 1):
        print(f"{i:>4}  {r['pareto_level']:>3}  {r['val_p90']:>10.4f}  {r['latency']:>8.2f}  {r['model']}")

    # Select top group_size.
    selected = usable[: args.group_size]
    print(f"\nSelected {len(selected)} models for next round "
          f"(Pareto-level order, ties broken by val_p90 then latency).")

    if args.output:
        with open(args.output, "w") as f:
            f.write(f"# Selected {len(selected)} models from {args.models_file}\n")
            f.write(f"# Source round: epoch {args.current_epoch}, tag={args.tag}\n")
            f.write(f"# Selection: Pareto-level (latency, val_p90), then val_p90, then latency\n")
            f.write(f"# rank\tpareto_level\tval_p90\tlatency_ms\tmodel\n")
            for i, r in enumerate(selected, 1):
                f.write(f"{i}\t{r['pareto_level']}\t{r['val_p90']:.4f}\t{r['latency']:.2f}\t{r['model']}\n")
        print(f"\nWrote {args.output}")
        # Also write a simple model-list file for easy use with --models
        simple = Path(args.output).with_suffix(".models.txt")
        with open(simple, "w") as f:
            for r in selected:
                f.write(f"{r['model']}\n")
        print(f"Wrote {simple} (one model per line)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
