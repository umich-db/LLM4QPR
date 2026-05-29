#!/bin/bash
# duckdb / job_full eval on the CORRECTED query plans.  Script C (~baseline load).
# Two bert2 finetunes + all the cheap inference cells (skip-train / pretrained).
#
#   bert2 mode 12  : biCrossAttn FINETUNE  (no weights -> train)   ~medium
#   bert2 mode 12w : biCrossAttn FINETUNE  (no weights -> train)   ~medium
#   bert2 mode 1/2 : inference              (pretrained / base LoRA weights)  ~fast
#   sentbert 1,2,7,7b,12,12w : ALL inference (every imdb weight exists ->
#                    skip-train load, no finetune)                            ~fast-ish
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
export SEEDS=42
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(duckdb)
WORKLOADS_ARR=(job_full)

export MODEL="google/bert_uncased_L-2_H-256_A-4"
MODES_ARR=(1 2 12 12w)
run_ablation

export MODEL="sentence-transformers/all-MiniLM-L12-v2"
MODES_ARR=(1 2 7 7b 12 12w)
run_ablation
