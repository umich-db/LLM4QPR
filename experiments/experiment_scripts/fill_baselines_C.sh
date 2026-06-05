#!/usr/bin/env bash
# Fill missing baseline cells (seed 42, task=time, train_ratio=1.0).
# Script C (~39 units): all of aimai + e2e_cost on {duckdb,spark} + the postgres
# native baseline (postgres system only, all 6 workloads). See fill_baselines_A.sh.
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

# Targeted fill: GAP_ONLY=1 runs ONLY the lone outstanding cell
# (e2e_cost on duckdb/job_full) and exits — avoids re-running all of C just to
# fill one cell. This same cell is also covered by C2's `ml_duckdb e2e_cost`
# below (train=job/imdb reuses the cached duckdb e2e_cost model, test=job_full).
if [[ -n "${GAP_ONLY:-}" ]]; then
    echo "=== GAP_ONLY: e2e_cost @ duckdb/job_full ==="
    run duckdb "job" job_full e2e_cost
    echo "Done (gap)."
    exit 0
fi

ml_postgres() { run postgres "job" syn "$1"; run postgres "job" job "$1"; run postgres "job" job_full "$1"; run postgres "stats" stats "$1"; run postgres "tpch" tpch "$1"; }
ml_duckdb()   { run duckdb   "job" syn "$1"; run duckdb   "job" job_full "$1"; run duckdb "tpcds" tpcds "$1"; run duckdb "tpch" tpch "$1"; }
ml_spark()    { run spark    "job" syn "$1"; run spark    "job" job_full "$1"; run spark "tpcds" tpcds "$1"; run spark "tpch" tpch "$1"; }

echo "=== C1: aimai (all systems) ==="
ml_postgres aimai
ml_duckdb   aimai
ml_spark    aimai

echo "=== C2: e2e_cost @ duckdb + spark ==="
ml_duckdb e2e_cost
ml_spark  e2e_cost

echo "=== C3: postgres native baseline (postgres only, all 6 workloads) ==="
run postgres "job"   syn      postgres
run postgres "job"   job      postgres
run postgres "job"   job_full postgres
run postgres "stats" stats    postgres
run postgres "tpcds" tpcds    postgres
run postgres "tpch"  tpch     postgres

echo "Done (C)."
