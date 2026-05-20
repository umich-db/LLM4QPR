#!/bin/bash
# Script 1: {tpch, tpcds, stats} × modes {7b, 12w}
#   - 7b  = JointPrice + PRICE_B
#   - 12w = JointPrice + biCrossAttn + inflatePRICE + cx4 + NO warmup
# Paired with compare_modes_olap_7_12.sh (modes 7, 12) for the PRICE_N / warmup ablations.
#
# duckdb / spark only have stats here (no tpch/tpcds plans in queryPlans/);
# run_ablation prints "[skip] no plans for …" and moves on.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # → experiments/
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(tpch tpcds stats)
MODES_ARR=(7b 12w)

run_ablation
