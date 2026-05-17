#!/bin/bash
# Profile train + inference latency for the 4 baseline algorithms
# (qf, aimai, e2e_cost, bao) across {tpch, tpcds, syn, job, job_full, stats}
# with --train_ratio 1.
#
# Per-algo hyperparams (hid_units, lr, batch_size) and the train.py invocation
# itself come from experiment_scripts/core_scripts/run_baseline.sh — this
# script wraps that runner instead of duplicating its argument matrix.
#
# Each run logs:
#   [Train] Training took <X> ms        → train_ms
#   [Test]  Total evaluation time — <X> ms  → infer_ms
# Both are grepped out of the per-run log and emitted as one row of
# analysis_scripts/profile_baselines_train_infer.csv with columns:
#   algo,workload,train_ms,infer_ms,exit_code,log

set -uo pipefail
SCRIPT_DIR_LOCAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR_LOCAL}/.."   # → repo's experiments/ dir (portable across hosts)
if [ -f ~/venvs/tmpenv/bin/activate ]; then
    source ~/venvs/tmpenv/bin/activate
fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

REPO_ROOT="$(cd "${SCRIPT_DIR_LOCAL}/../.." && pwd)"
OUT_CSV="${REPO_ROOT}/experiments/analysis_scripts/profile_baselines_train_infer.csv"
LOG_BASE="logs/postgres"
TASK="time"           # only time supported across all 6 workloads (card needs job/syn/stats)
TRAIN_RATIO="1.0"
SEED="42"
export DB_ENGINE="${DB_ENGINE:-postgres}"

ALGOS=(qf aimai e2e_cost bao)
WORKLOADS=(tpch tpcds syn job job_full stats)

# Optional caps to keep this script's runtime bounded. Override via env:
#   FAST_PROFILE=1                       → cap num_epoch via early stop
#   EARLY_STOP_PATIENCE=10               → stop after 10 epochs without improvement
#   EARLY_STOP_AFTER_EPOCH=20            → only start counting patience after epoch 20
if [[ -n "${EARLY_STOP_PATIENCE:-}" ]]; then
    export EARLY_STOP_PATIENCE
fi
if [[ -n "${EARLY_STOP_AFTER_EPOCH:-}" ]]; then
    export EARLY_STOP_AFTER_EPOCH
fi

echo "algo,workload,train_ms,infer_ms,exit_code,log" > "$OUT_CSV"

total=$(( ${#ALGOS[@]} * ${#WORKLOADS[@]} ))
i=0
for algo in "${ALGOS[@]}"; do
    for wl in "${WORKLOADS[@]}"; do
        i=$((i+1))
        # Recompute the per-run log path that run_baseline.sh will write to.
        # run_baseline.sh resolves base_name based on algo's hardcoded hyperparams;
        # we match its format exactly so the grep below finds the right file.
        case "$algo" in
          bao)      hid_units=256;      lr=0.001;  batch_size=16 ;;
          aimai)    hid_units=256;      lr=0.0001; batch_size=64 ;;
          qf)       hid_units=256;      lr=0.001;  batch_size=64 ;;
          e2e_cost) hid_units=256;      lr=0.001;  batch_size=64 ;;
        esac
        base="${TASK}_${algo}_${TRAIN_RATIO}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_seed${SEED}"
        log_dir="${LOG_BASE}/logs_Train_${wl}_Test_${wl}_ours"
        log_file="${log_dir}/${base}.log"
        mkdir -p "$log_dir"

        echo ""
        echo "[$i/$total] algo=${algo}  workload=${wl}  → ${log_file}"

        # run_baseline.sh signature:
        #   $1=TRAIN_WLS  $2=WORKLOAD_TEST  $3=train_ratio  $4=SEED  $5=ALGO  $6=TASK
        bash experiment_scripts/core_scripts/run_baseline.sh \
            "$wl" "$wl" "$TRAIN_RATIO" "$SEED" "$algo" "$TASK"
        rc=$?

        train_ms=$(grep -oE "\[Train\] Training took [0-9.]+ ms" "$log_file" 2>/dev/null \
                   | head -1 | grep -oE "[0-9.]+" | head -1)
        infer_ms=$(grep -oE "\[Test\] Total evaluation time — [0-9.]+ ms" "$log_file" 2>/dev/null \
                   | head -1 | grep -oE "[0-9.]+" | head -1)
        train_ms="${train_ms:-NA}"
        infer_ms="${infer_ms:-NA}"

        echo "${algo},${wl},${train_ms},${infer_ms},${rc},${log_file}" >> "$OUT_CSV"
        echo "  → train=${train_ms} ms, infer=${infer_ms} ms, rc=${rc}"
    done
done

echo ""
echo "Done. Profile CSV: $OUT_CSV"
