#!/bin/bash
# Script B (~10-11h)
#
# postgres × bert2: full mode 1 + mode 2 (imdb-canonical + stats)
# postgres × bert4: mode 1 syn (light inference)
# duckdb   × bert4: mode 1 syn (light inference)
# spark    × bert2: mode 1 (imdb-canonical only) + mode 2 (imdb-canonical only)
#                   — spark stats lands in Script C to balance hours.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source "$SCRIPT_DIR/_compare_modes_lib.sh"

# -- bert4 mode 1 syn light-cells, postgres + duckdb --
export MODEL="google/bert_uncased_L-4_H-768_A-12"
MODES_ARR=(1)
WORKLOADS_ARR=(syn)
DB_ENGINES=(postgres)
run_ablation
DB_ENGINES=(duckdb)
run_ablation

# -- postgres × bert2: modes 1 and 2 on all four workloads --
export MODEL="google/bert_uncased_L-2_H-256_A-4"
DB_ENGINES=(postgres)
WORKLOADS_ARR=(syn job job_full stats)
MODES_ARR=(1 2)
run_ablation

# -- spark × bert2: mode 1 + mode 2 on imdb-canonical workloads only --
# (spark bert2 stats goes to Script C.)
DB_ENGINES=(spark)
WORKLOADS_ARR=(syn job job_full)
MODES_ARR=(1 2)
run_ablation
# Spark bert2 mode 1 on stats is still missing — it's cheap, include here:
WORKLOADS_ARR=(stats)
MODES_ARR=(1)
run_ablation
