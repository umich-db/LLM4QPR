#!/bin/bash
# duckdb / job_full eval on the CORRECTED query plans.  Script A (HEAVIEST, ~50%
# larger than B and C) — carries the three heaviest cells: bert4 price-mode
# FINETUNES (no saved imdb weights -> trained from scratch on imdb).
#
#   bert4 mode 1  : pretrained-None inference   (no weights needed)        ~fast
#   bert4 mode 2  : LoRA, skip-train load        (base weights exist)      ~fast
#   bert4 mode 7  : priceN  FINETUNE             (no weights -> train)     ~heavy
#   bert4 mode 7b : priceB  FINETUNE             (no weights -> train)     ~heavy
#   bert4 mode 12 : biCrossAttn FINETUNE         (no weights -> train)     ~heavy
#
# bert4 mode 12w is in Script B to keep the load balanced.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
export SEEDS=42
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(duckdb)
WORKLOADS_ARR=(job_full)

export MODEL="google/bert_uncased_L-4_H-768_A-12"
MODES_ARR=(1 2 7 7b 12)
run_ablation
