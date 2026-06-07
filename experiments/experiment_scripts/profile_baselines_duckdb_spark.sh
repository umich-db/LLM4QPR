#!/bin/bash
# Collect baseline (qf / aimai / e2e_cost / bao) train + per-query inference time
# on duckdb and spark — the cross-engine companion to the postgres-only
# profile_baselines_train_infer.sh (which the original h100_profile_runs used).
#
# bao inference is now logged too: evaluation/trainer.py::train_and_test_bao
# emits the canonical "[Test] Total evaluation time — <X> ms" line the harness
# greps (previously only "[Test] Testing took", so bao infer was NA).
#
# Outputs (one row per algo x workload):
#   experiments/analysis_scripts/profile_baselines_train_infer_duckdb.csv
#   experiments/analysis_scripts/profile_baselines_train_infer_spark.csv
# Per-run logs land in logs/<db>/logs_Train_<wl>_Test_<wl>_ours/.
#
# Run locally (baselines are light) in tmux, pinning a GPU, e.g.:
#   tmux new-session -d -s base_dt \
#     "CUDA_VISIBLE_DEVICES=1 bash experiments/experiment_scripts/profile_baselines_duckdb_spark.sh \
#        2>&1 | tee /tmp/base_dt.log"
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

DBS="${DBS:-duckdb spark}"
for db in $DBS; do
    echo ""
    echo "############################################################"
    echo "  baseline time profile  |  DB_ENGINE=${db}"
    echo "############################################################"
    DB_ENGINE="$db" bash "$SCRIPT_DIR/profile_baselines_train_infer.sh"
done

echo ""
echo "Done. CSVs: experiments/analysis_scripts/profile_baselines_train_infer_{${DBS// /,}}.csv"
