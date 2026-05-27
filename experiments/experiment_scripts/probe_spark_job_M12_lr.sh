#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 with
# --price_warmup_lr 1e-4 (vs default 1e-3 for --price_random_init).
#
# Default schedule: PRICE LR 1e-3 (epochs 0..4) → 2e-5 (epochs 5+).  50× drop.
# This probe:       PRICE LR 1e-4 (epochs 0..4) → 2e-5 (epochs 5+).   5× drop.
#
# Hypothesis: high warmup LR pushes cross-attn into a noisy basin that the
# post-warmup 50× drop then locks in, manifesting as the test oscillation we
# see throughout M12 spark training. A smoother schedule (5× drop) should
# stabilise the trajectory.
#
# Target cell is the actual worst-case for TRUE mode 12 (the one with
# frzLLM5/pwm5 from MODE12_SCHED), not mode 12w. Per-cell M12/M7 p90 ratio:
#   L-4       spark train=job test=job_full: 2.061 (catastrophic on L-4)
#   sentBert  spark train=job test=job_full: 1.360 (still bad)
#   geomean across the two models: 1.675 (worst workload)
#
# Output CSV will carry a `_pLR0.0001_` token (train._price_path_suffix appends
# `pLR{plr:g}` when --price_warmup_lr differs from the 1e-3 default), so the
# aggregator sees this as a column distinct from the cx4 baseline.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"  # override to L-4 for the harder cell
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)        # canonical_map sends job_full to TRAIN_WL=job → train=job test=job_full
MODES_ARR=(12)

# Extend mode-12 dispatch with --price_warmup_lr 1e-4. The lib's run_mode for
# case 12 invokes:
#   "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12_SCHED[@]}"
# Appending to MODE12_SCHED is the cleanest insertion point.
MODE12_SCHED=(--price_warmup_epochs "5" --freeze_llm_until_epoch "5" --price_warmup_lr "1e-4")

run_ablation
