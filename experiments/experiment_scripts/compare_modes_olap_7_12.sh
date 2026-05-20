#!/bin/bash
# Script 2: {tpch, tpcds, stats} × modes {7, 12}
#   - 7   = JointPrice + PRICE_N
#   - 12  = JointPrice + biCrossAttn + inflatePRICE + cx4 + warmup (pwm5, frzLLM5)
# Paired with compare_modes_olap_7b_12w.sh (modes 7b, 12w) for the PRICE_N / warmup ablations.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(tpch tpcds stats)
MODES_ARR=(7 12)

run_ablation
