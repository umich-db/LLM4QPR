#!/usr/bin/env bash
# Fill missing baseline cells (seed 42, task=time, train_ratio=1.0).
# Script A (HEAVY ~1.5x the others): all of qf + e2e_cost on postgres.
# Weighting (per-training cost): qf=5, bao=4, e2e_cost=3, aimai=2, postgres~=0.
#   A = qf(9 trainings x5=45) + e2e_cost@postgres(3x3=9)        = 54  (1.5x)
#   B = bao(9x4)                                                = 36   (fill_baselines_B.sh)
#   C = aimai(9x2=18) + e2e_cost@{duckdb,spark}(6x3=18) + postgres(0) = 36 (fill_baselines_C.sh)
# => A is exactly 50% heavier than B and C, which are equal.
# Scripts touch disjoint per-(algo,db) caches, so they can run in parallel.
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

# All-systems missing cells for one ML algo. The imdb family (syn/job/job_full)
# trains once on 'job' and the rest reuse the cache; stats/tpcds/tpch each train.
ml_postgres() { run postgres "job" syn "$1"; run postgres "job" job "$1"; run postgres "job" job_full "$1"; run postgres "stats" stats "$1"; run postgres "tpch" tpch "$1"; }
ml_duckdb()   { run duckdb   "job" syn "$1"; run duckdb   "job" job_full "$1"; run duckdb "tpcds" tpcds "$1"; run duckdb "tpch" tpch "$1"; }
ml_spark()    { run spark    "job" syn "$1"; run spark    "job" job_full "$1"; run spark "tpcds" tpcds "$1"; run spark "tpch" tpch "$1"; }

echo "=== A1: qf (all systems) ==="
ml_postgres qf
ml_duckdb   qf
ml_spark    qf

echo "=== A2: e2e_cost @ postgres ==="
ml_postgres e2e_cost

echo "Done (A)."
