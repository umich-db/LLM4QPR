#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 with
# n_cross_layers=2.
#
# Target cell is the actual worst-case for TRUE mode 12 (the one with
# frzLLM5/pwm5 from MODE12_SCHED), not mode 12w. Per-cell M12/M7 p90 ratio:
#   L-4       spark train=job test=job_full: 2.061 (catastrophic on L-4)
#   sentBert  spark train=job test=job_full: 1.360 (still bad)
#   geomean across the two models: 1.675 (worst workload)
#
# Goal: cx=2 dampens the cross-attn capacity to half; if instability is what's
# hurting mode 12, this should pull the ratio below ~1.3.
#
# Hold every other knob from MODE12_SCHED constant so we can compare directly
# to the existing cx=4 cell in results/spark/results_Train_job_Test_job_full_ours/.
#
# Output CSV will have `_cx2_` in place of `_cx4_` (the n_cross_layers token
# is baked into the price-path suffix by train._price_path_suffix).

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"  # override to L-4 for the harder cell
export CX_LAYERS=2
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)        # canonical_map sends job_full to TRAIN_WL=job → train=job test=job_full
MODES_ARR=(12)

# Override the CX4_FLAGS the lib hard-codes (--n_cross_layers 4 → 2).
CX4_FLAGS=(--inflate_price --n_cross_layers "$CX_LAYERS")

run_ablation
