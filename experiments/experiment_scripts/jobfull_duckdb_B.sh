#!/bin/bash
# duckdb / job_full eval on the CORRECTED query plans.  Script B (~baseline load).
# One bert4 finetune + two bert2 finetunes.
#
#   bert4 mode 12w : biCrossAttn FINETUNE  (no weights -> train)   ~heavy
#   bert2 mode 7   : priceN  FINETUNE      (no weights -> train)   ~medium
#   bert2 mode 7b  : priceB  FINETUNE      (no weights -> train)   ~medium
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
export SEEDS=42
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(duckdb)
WORKLOADS_ARR=(job_full)

export MODEL="google/bert_uncased_L-4_H-768_A-12"
MODES_ARR=(12w)
run_ablation

export MODEL="google/bert_uncased_L-2_H-256_A-4"
MODES_ARR=(7 7b)
run_ablation
