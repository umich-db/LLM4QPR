#!/usr/bin/env python3
"""
Random-baseline model selection. Samples N models uniformly at random from the
same candidate pool used by model_selection_v2.py's first round.

Matches model_selection_v2.py behavior:
  - Reads `model_profile_with_nonemb.csv` (same default).
  - Pre-filters to feasible candidates with `avg_ms <= --latency_limit`.
  - Uses numpy's default_rng seeded by --seed for reproducibility.

Usage:
  python random_model_selection.py --n 32 --latency_limit 200 --seed 42 \
      --output random_32_seed42.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / "model_profile_with_nonemb.csv"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", type=str, default=str(DEFAULT_CSV),
                   help="Model profile CSV (same pool as model_selection_v2.py).")
    p.add_argument("--n", type=int, required=True, help="Number of models to sample.")
    p.add_argument("--latency_limit", type=float, default=float("inf"),
                   help="Keep only candidates with avg_ms <= this value. Default: no limit.")
    p.add_argument("--seed", type=int, default=42, help="Random seed.")
    p.add_argument("--output", default=None,
                   help="Output file (one model per line). Default: stdout only.")
    p.add_argument("--id_col", default="model",
                   help="Column in the CSV holding the model identifier.")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    if args.id_col not in df.columns:
        print(f"Missing column '{args.id_col}' in {args.csv}", file=sys.stderr)
        return 1
    if "avg_ms" not in df.columns:
        print(f"Missing column 'avg_ms' in {args.csv}", file=sys.stderr)
        return 1

    total = len(df)
    feasible = df[df["avg_ms"] <= args.latency_limit].reset_index(drop=True)
    print(f"Candidate pool: {len(feasible)}/{total} feasible "
          f"(avg_ms <= {args.latency_limit}).", file=sys.stderr)

    if args.n > len(feasible):
        print(f"ERROR: requested --n={args.n} but only {len(feasible)} feasible.",
              file=sys.stderr)
        return 1

    rng = np.random.default_rng(args.seed)
    # Nested sampling: permute once per seed, take a prefix. For the same seed,
    # larger --n contains the picks of any smaller --n.
    idx = rng.permutation(len(feasible))[: args.n]
    picks = feasible.iloc[idx].reset_index(drop=True)

    # Print + optional file output
    header = f"# Random sample of {args.n} models from {args.csv}\n" \
             f"# latency_limit={args.latency_limit}  seed={args.seed}\n" \
             f"# rank\tmodel\tavg_ms"
    print(header)
    for i, row in enumerate(picks.itertuples(index=False), 1):
        print(f"{i}\t{getattr(row, args.id_col)}\t{getattr(row, 'avg_ms'):.2f}")

    if args.output:
        out = Path(args.output)
        with open(out, "w") as f:
            f.write(header + "\n")
            for i, row in enumerate(picks.itertuples(index=False), 1):
                f.write(f"{i}\t{getattr(row, args.id_col)}\t{getattr(row, 'avg_ms'):.2f}\n")
        # Also write a simple one-model-per-line file for easy use with --models.
        simple = out.with_suffix(".models.txt")
        with open(simple, "w") as f:
            for row in picks.itertuples(index=False):
                f.write(f"{getattr(row, args.id_col)}\n")
        print(f"\nWrote {out}", file=sys.stderr)
        print(f"Wrote {simple} (one model per line)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
