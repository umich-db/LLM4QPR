#!/bin/bash
# Script C (~10h)
#
# duckdb × bert4: mode 2 job_full (reload + eval, ~30 min — bert4 imdb LoRA exists)
# duckdb × bert2: full mode 1 + mode 2 (imdb-canonical + stats)
# spark  × bert2: mode 2 stats only (paired here to balance hours vs Script B)

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source "$SCRIPT_DIR/_compare_modes_lib.sh"

# -- duckdb × bert4: mode 2 job_full (reload-and-eval on existing imdb LoRA) --
export MODEL="google/bert_uncased_L-4_H-768_A-12"
DB_ENGINES=(duckdb)
WORKLOADS_ARR=(job_full)
MODES_ARR=(2)
run_ablation

# -- duckdb × bert2: modes 1 and 2 on all four workloads --
export MODEL="google/bert_uncased_L-2_H-256_A-4"
DB_ENGINES=(duckdb)
WORKLOADS_ARR=(syn job job_full stats)
MODES_ARR=(1 2)
run_ablation

# -- spark × bert2: mode 2 stats (fresh LoRA finetune, ~3h) --
DB_ENGINES=(spark)
WORKLOADS_ARR=(stats)
MODES_ARR=(2)
run_ablation
