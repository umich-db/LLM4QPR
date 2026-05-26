#!/bin/bash
# Single-cell probe: spark × train=job × test=job × mode 12 with n_cross_layers=2.
# Holds every other knob constant from the existing M12 recipe so we can
# directly compare to the spark_job_M12 cell in
# results/spark/results_Train_job_Test_job_ours/.
#
# Baseline (cx4, current bad cell):                p90 = 4.998  (sentBert)
# Goal: get p90 under ~2.7 (= M7's p90 × 1.2).
#
# Output CSV will have a distinct token "cx2" in the filename so the
# aggregator picks it up as a separate column from cx4.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="sentence-transformers/all-MiniLM-L12-v2"  # match the worst-cell model
export CX_LAYERS=2                                       # override default of 4
DB_ENGINES=(spark)
WORKLOADS_ARR=(job)            # train workload (test workload = "job" is set per-workload in run_ablation)
MODES_ARR=(12)

# Override the CX4_FLAGS used inside run_mode for mode 12.
# (The lib hard-codes --n_cross_layers 4 in CX4_FLAGS; we shadow it.)
CX4_FLAGS=(--inflate_price --n_cross_layers "$CX_LAYERS")

run_ablation
