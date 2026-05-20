#!/bin/bash
# {tpch, tpcds, stats} × mode 12
#   12 = JointPrice + biCrossAttn + inflatePRICE + cx4 + warmup (pwm5, frzLLM5)
# Paired with compare_modes_olap_7.sh, compare_modes_olap_7b.sh, compare_modes_olap_12w.sh.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(tpch tpcds stats)
MODES_ARR=(12)

run_ablation
