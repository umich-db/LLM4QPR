#!/usr/bin/env bash
# Rerun ALL bao cells for one engine after switching BaoRegression to the shared
# Normalizer (commit 55f70b8). bao's label transform changed (sklearn log1p+
# MinMax -> Normalizer log(x+0.001)+clamp), so every bao model must be RETRAINED,
# not re-evaluated — we delete the stale bao caches first.
#
# Usage: DB_ENGINE=duckdb bash .../rerun_baseline_bao_ns.sh
#   DB_ENGINE in {postgres, duckdb, spark}. Reruns the (train->test x seed) cells
#   that exist for that engine. The imdb-canonical 'job' training is done once per
#   seed and reused (cache) for the job_full/syn test variants.
#
# Output is tee'd so it shows live in the tmux pane AND lands in the log file.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

DB="${DB_ENGINE:?set DB_ENGINE=postgres|duckdb|spark}"
RB="experiment_scripts/core_scripts/run_baseline.sh"
export NUM_EPOCH=30
export EARLY_STOP_PATIENCE=5
export EARLY_STOP_AFTER_EPOCH=20

echo "=== Busting stale bao caches for ${DB} (label transform changed -> retrain) ==="
for f in finetuned_models/${DB}/*_time_bao_*model*; do
    [[ -e "$f" ]] && { echo "  rm $f"; rm -rf "$f"; }
done

run() {  # <train_wls> <test_wl> <seed>
    echo ">>> db=${DB} train=[$1] test=$2 seed=$3 algo=bao"
    [[ -n "${DRY_RUN:-}" ]] && return 0
    DB_ENGINE="${DB}" bash "$RB" "$1" "$2" 1.0 "$3" bao time \
        || echo "FAILED: db=${DB} train=$1 test=$2 seed=$3"
}

case "${DB}" in
  postgres)
    run job job 42; run job job_full 42; run job syn 42
    run stats stats 42; run tpch tpch 42; run tpcds tpcds 42
    ;;
  duckdb)
    # job/jobm/stats exist at seeds 42,43,44; train 'job' first each seed so the
    # job_full/syn (seed42) evals reuse the cache.
    for s in 42 43 44; do run job job "$s"; run jobm jobm "$s"; run stats stats "$s"; done
    run job job_full 42; run job syn 42
    run tpch tpch 42; run tpcds tpcds 42
    ;;
  spark)
    run job job 42; run job job_full 42; run job syn 42
    run jobm jobm 42
    run stats stats 42; run stats stats 43
    run tpch tpch 42; run tpcds tpcds 42
    ;;
  *) echo "unknown DB_ENGINE=${DB}"; exit 1 ;;
esac
echo "Done (bao ns rerun: ${DB})."
