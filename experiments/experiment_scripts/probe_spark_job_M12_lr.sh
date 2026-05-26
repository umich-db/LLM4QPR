#!/bin/bash
# Single-cell probe: spark × train=job × test=job × mode 12 with
# --price_warmup_lr 1e-4 (vs default 1e-3 for --price_random_init).
#
# Default schedule: PRICE LR 1e-3 (epochs 0..4) → 2e-5 (epochs 5+).  50× drop.
# This probe:       PRICE LR 1e-4 (epochs 0..4) → 2e-5 (epochs 5+).   5× drop.
#
# Hypothesis: high warmup LR pushes cross-attn into a noisy basin that the
# post-warmup 50× drop then locks in, manifesting as the test oscillation
# we see throughout M12 spark training. A smoother schedule (5× drop) should
# stabilise the trajectory.
#
# Baseline (warmup_lr=1e-3, the bad cell):       p90 = 4.998  (sentBert)
# Goal: get p90 under ~2.7 (= M7's p90 × 1.2).
#
# Output CSV will have a distinct token "_pwlr1e-4" in the filename (the
# train.py CSV path includes the price-warmup-LR when non-default), so the
# aggregator sees this as a separate column from the cx4 baseline.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="sentence-transformers/all-MiniLM-L12-v2"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job)
MODES_ARR=(12)

# Extend the mode-12 dispatch with --price_warmup_lr 1e-4.
# The lib's run_mode for case 12 invokes:
#   "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12_SCHED[@]}"
# Appending the flag to MODE12_SCHED is the cleanest insertion point.
# Use --price_lr (alias for --price_warmup_lr; the shell layer
# run_different_llms.sh only forwards --price_lr to train.py).
MODE12_SCHED=(--price_warmup_epochs "5" --freeze_llm_until_epoch "5" --price_lr "1e-4")

run_ablation
