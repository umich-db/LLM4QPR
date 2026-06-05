#!/usr/bin/env bash
# Rerun the duckdb/tpcds LEARNED baselines (qf/aimai/bao/e2e_cost) under the new
# NANOSECOND label scaling (evaluation/dataset_utils.py get_costs: duckdb
# tpch/tpcds now ×1e9 instead of ×1000→ms). The old caches were trained on ms
# labels, which collapsed onto the Normalizer epsilon → catastrophic Q-errors
# (aimai/e2e_cost ~1e15, bao max=inf). A model trained under one scaling MUST be
# RETRAINED under the other, so we delete the stale caches first.
#
# tpcds is the HEAVIEST cell (9900 plans) → run this on dbresearch3 (RTX 5090).
# Output is tee'd so it shows live in the tmux pane AND lands in the log file.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

RB="experiment_scripts/core_scripts/run_baseline.sh"
DB=duckdb
WL=tpcds
ALGOS=(qf aimai bao e2e_cost)

export NUM_EPOCH=30
export EARLY_STOP_PATIENCE=5
export EARLY_STOP_AFTER_EPOCH=20

echo "=== Busting stale ms-trained ${DB}/${WL} baseline caches (force ns retrain) ==="
for algo in "${ALGOS[@]}"; do
    for f in finetuned_models/${DB}/${WL}_time_${algo}_*model*; do
        [[ -e "$f" ]] && { echo "  rm $f"; rm -rf "$f"; }
    done
done

for algo in "${ALGOS[@]}"; do
    echo ">>> db=${DB} train=[${WL}] test=${WL} algo=${algo}  (ns labels)"
    [[ -n "${DRY_RUN:-}" ]] && continue
    DB_ENGINE="${DB}" bash "$RB" "${WL}" "${WL}" 1.0 42 "${algo}" time \
        || echo "FAILED: db=${DB} test=${WL} algo=${algo}"
done
echo "Done (duckdb tpcds ns baselines)."
