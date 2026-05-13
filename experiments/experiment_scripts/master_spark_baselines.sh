#!/bin/bash
# Run the 4 baseline algorithms (qf, bao, aimai, e2e_cost) on Spark.
# Workloads: stats, job, jobm. Task: time.
# Uses 3 seeds (42, 43, 44).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export DB_ENGINE="spark"
export VERBOSE_INFO="false"
# Early stop: stop if val p90 hasn't improved for 5 epochs, active after epoch 10.
export EARLY_STOP_PATIENCE="5"
export EARLY_STOP_AFTER_EPOCH="10"

ALGORITHMS=("qf")
# ALGORITHMS=("qf" "bao" "aimai" "e2e_cost")
WORKLOADS=("stats" "job" "jobm")
SEEDS=(42 43 44)

cd "$EXPERIMENTS_DIR"

for SEED in "${SEEDS[@]}"; do
    for WL in "${WORKLOADS[@]}"; do
        for ALGO in "${ALGORITHMS[@]}"; do
            echo ""
            echo "============================================================"
            echo "  $ALGO | spark | $WL | seed $SEED | time"
            echo "============================================================"
            bash experiment_scripts/core_scripts/run_baseline.sh "$WL" "$WL" 1.0 "$SEED" "$ALGO" "time"
        done
    done
done

echo ""
echo "All Spark baseline experiments completed!"
