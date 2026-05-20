#!/bin/bash
# {syn, job, job_full} × mode 12
#
# Same syn-first weight-reuse rationale as compare_modes_imdb_7.sh.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(syn job job_full)   # syn FIRST → weights reused by job/job_full
MODES_ARR=(12)

run_ablation
