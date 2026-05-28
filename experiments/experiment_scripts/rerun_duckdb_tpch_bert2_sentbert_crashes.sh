#!/bin/bash
# One-off rerun for the duckdb-tpch crashes that survived the latency-to-ns fix:
#   bert2    × mode 7b
#   sentbert × mode 7b
#   sentbert × mode 12w
#
# bert4 was already rerun earlier (rerun_duckdb_tpch_L4_12_12w_7b.sh); these
# three cells still held pre-fix CSVs (p90 in the 1e5 - 1e6 range). All
# matching results / logs / finetuned weights / stale sentbert tpch lora
# embeddings have been deleted before this script runs.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(duckdb)
WORKLOADS_ARR=(tpch)

# bert2 only needs mode 7b.
export MODEL="google/bert_uncased_L-2_H-256_A-4"
MODES_ARR=(7b)
run_ablation

# sentbert needs both 7b and 12w.
export MODEL="sentence-transformers/all-MiniLM-L12-v2"
MODES_ARR=(7b 12w)
run_ablation
