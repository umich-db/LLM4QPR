#!/bin/bash
# {tpch, tpcds, stats} × mode 7
#   7 = JointPrice + PRICE_N
# Paired with compare_modes_olap_7b.sh, compare_modes_olap_12.sh, compare_modes_olap_12w.sh.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(tpch tpcds stats)
MODES_ARR=(7)

run_ablation
