#!/usr/bin/env bash
# Rerun the spark/{tpch,tpcds} qf baseline cells. Their cdfs are currently
# header-only (empty) — qf produced NaN predictions that were filtered out, so qf
# is dropped from the cross_engine table. This is NOT a scaling issue (spark is
# already in ms, epsilon-safe); it's a plain rerun of the two failed cells.
# We delete any stale qf cache first so it retrains cleanly.
#
# Lightest job → run LOCALLY. GPU 0 here is a 2 GB card; default to GPU 1 (16 GB).
# Output is tee'd so it shows live in the tmux pane AND lands in the log file.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-1}"

RB="experiment_scripts/core_scripts/run_baseline.sh"
DB=spark
ALGO=qf
WLS=(tpch tpcds)

export NUM_EPOCH=30
export EARLY_STOP_PATIENCE=5
export EARLY_STOP_AFTER_EPOCH=20

echo "=== Busting stale ${DB} ${ALGO} tpch/tpcds caches (clean retrain) ==="
for wl in "${WLS[@]}"; do
    for f in finetuned_models/${DB}/${wl}_time_${ALGO}_*model*; do
        [[ -e "$f" ]] && { echo "  rm $f"; rm -rf "$f"; }
    done
done

for wl in "${WLS[@]}"; do
    echo ">>> db=${DB} train=[${wl}] test=${wl} algo=${ALGO}  (CVD=${CUDA_VISIBLE_DEVICES})"
    [[ -n "${DRY_RUN:-}" ]] && continue
    DB_ENGINE="${DB}" bash "$RB" "${wl}" "${wl}" 1.0 42 "${ALGO}" time \
        || echo "FAILED: db=${DB} test=${wl} algo=${ALGO}"
done
echo "Done (spark qf tpch/tpcds)."
