#!/usr/bin/env bash
# Fill missing baseline cells (seed 42, task=time, train_ratio=1.0).
# Script B (~36 units): all of bao. See fill_baselines_A.sh for the weighting.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
RB="experiment_scripts/core_scripts/run_baseline.sh"

# Epoch budget + early stop for every baseline run here (honored by
# qf/aimai/e2e_cost/bao; postgres has no training and ignores them).
export NUM_EPOCH=30
export EARLY_STOP_PATIENCE=5
export EARLY_STOP_AFTER_EPOCH=20

run() {  # <db> <train_wls> <test_wl> <algo>
    echo ">>> db=$1 train=[$2] test=$3 algo=$4"
    [[ -n "${DRY_RUN:-}" ]] && return 0
    DB_ENGINE="$1" bash "$RB" "$2" "$3" 1.0 42 "$4" time \
        || echo "FAILED: db=$1 train=$2 test=$3 algo=$4"
}

ml_postgres() { run postgres "job" syn "$1"; run postgres "job" job "$1"; run postgres "job" job_full "$1"; run postgres "stats" stats "$1"; run postgres "tpch" tpch "$1"; }
ml_duckdb()   { run duckdb   "job" syn "$1"; run duckdb   "job" job_full "$1"; run duckdb "tpcds" tpcds "$1"; run duckdb "tpch" tpch "$1"; }
ml_spark()    { run spark    "job" syn "$1"; run spark    "job" job_full "$1"; run spark "tpcds" tpcds "$1"; run spark "tpch" tpch "$1"; }

echo "=== B: bao (all systems) ==="
ml_postgres bao
ml_duckdb   bao
ml_spark    bao

echo "Done (B)."
