#!/bin/bash
# {tpch, tpcds, stats} × mode 7b
#   7b = JointPrice + PRICE_B
# Paired with compare_modes_olap_7.sh, compare_modes_olap_12.sh, compare_modes_olap_12w.sh.
#
# duckdb / spark only have stats here (no tpch/tpcds plans in queryPlans/);
# run_ablation prints "[skip] no plans for …" and moves on.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # → experiments/
# Default model: google/bert_uncased_L-2_H-256_A-4 (the current 2-layer BERT target).
# Override with `MODEL='sentence-transformers/all-MiniLM-L12-v2' bash …` or any
# other HF model string. Must be set BEFORE sourcing the lib so the lib's
#   : "${MODEL:=...}"   default doesn't override.
export MODEL="${MODEL:-google/bert_uncased_L-2_H-256_A-4}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(tpch tpcds stats)
MODES_ARR=(7b)

run_ablation
