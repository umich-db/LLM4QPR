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

echo "algo,workload,train_ms,infer_ms,exit_code,log" > "$OUT_CSV"

NUM_EPOCH="1"
RESULTS_DIR="results/${DB_ENGINE}"

# Map workload → query-plan dir (matches run_baseline.sh's resolution).
plans_dir() {
    case "$1" in
        syn|job|job_full|jobm) echo "../queryPlans/imdb/${DB_ENGINE}/" ;;
        *)                     echo "../queryPlans/$1/${DB_ENGINE}/" ;;
    esac
}

total=$(( ${#ALGOS[@]} * ${#WORKLOADS[@]} ))
i=0
for algo in "${ALGOS[@]}"; do
    case "$algo" in
        bao)      hid_units=256;      lr=0.001;  batch_size=16 ;;
        aimai)    hid_units=256;      lr=0.0001; batch_size=64 ;;
        qf)       hid_units=256;      lr=0.001;  batch_size=64 ;;
        e2e_cost) hid_units=256;      lr=0.001;  batch_size=64 ;;
    esac
    for wl in "${WORKLOADS[@]}"; do
        i=$((i+1))
        dat_path=$(plans_dir "$wl")
        base="${TASK}_${algo}_${TRAIN_RATIO}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_seed${SEED}"
        log_dir="${LOG_BASE}/logs_Train_${wl}_Test_${wl}_ours"
        res_dir="${RESULTS_DIR}/results_Train_${wl}_Test_${wl}_ours"
        log_file="${log_dir}/${base}.log"
        mkdir -p "$log_dir" "$res_dir"

        echo ""
        echo "[$i/$total] algo=${algo}  workload=${wl}  num_epoch=${NUM_EPOCH}"
        echo "  log:  ${log_file}"

        # Bypass run_baseline.sh so we can override num_epoch=1 (it hardcodes 100).
        # All other args mirror run_baseline.sh:114-128 (time task path).
        python train.py \
            --dat_paths_train "$dat_path" --dat_path_test "$dat_path" \
            --output_dir_qerror "${res_dir}/${base}.csv" \
            --output_dir_abs    "${res_dir}/${base}_abs.txt" \
            --log_file          "$log_file" \
            --db                "$DB_ENGINE" \
            --workloads_train   "$wl" \
            --workload_test     "$wl" \
            --algo              "$algo" \
            --num_epoch         "$NUM_EPOCH" \
            --learning_rate     "$lr" \
            --batch_size        "$batch_size" \
            --train_ratio       "$TRAIN_RATIO" \
            --seed              "$SEED" \
            2>&1 | tee "${log_file}.stdout"
        rc=${PIPESTATUS[0]}

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
