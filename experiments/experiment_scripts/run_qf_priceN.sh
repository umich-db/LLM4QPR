#!/usr/bin/env bash
# qf + priceN (mode-7-style PRICE concat) baseline: --baseline_price_concat with
# the PRICE_N flags (--price_n --price_n_or --price_random_init). Runs one engine
# (DB_ENGINE) over the given WORKLOADS, seed 42. Output cdfs get the _priceConcat
# tag automatically (train.py), so they never collide with the plain-qf cdfs.
#
# Usage: DB_ENGINE=postgres [WORKLOADS="stats tpch tpcds job syn job_full"] \
#        bash .../run_qf_priceN.sh
#   imdb-family cells (job/syn/job_full) train on imdb's 100k queries → a one-time
#   PRICE feature extraction (slow first run, then cached). Fast cells listed first.
# Output is tee'd so it shows live in the tmux pane AND lands in the log file.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

DB="${DB_ENGINE:?set DB_ENGINE=postgres|duckdb|spark}"
WORKLOADS="${WORKLOADS:-tpch tpcds stats job syn job_full}"
NUM_EPOCH="${NUM_EPOCH:-30}"
PRICE_FLAGS="--baseline_price_concat --price_n --price_n_or --price_random_init \
  --price_model_path price_statistics/model/model_params.pth --price_bin_size 40"

wl_dir() { case "$1" in syn|job|job_full|jobm) echo "../queryPlans/imdb/${DB}/";; *) echo "../queryPlans/$1/${DB}/";; esac; }

run() {  # <train_wl> <test_wl>
    local tr="$1" te="$2"
    local rd="results/${DB}/results_Train_${tr}_Test_${te}_ours"
    local ld="logs/${DB}/logs_Train_${tr}_Test_${te}_ours"
    mkdir -p "$rd" "$ld"
    local stem="time_qf_1.0_cdf_${DB}_0.001_b64_h256_seed42"
    echo ">>> qf+priceN db=${DB} train=${tr} test=${te}"
    [[ -n "${DRY_RUN:-}" ]] && return 0
    python -u train.py --dat_paths_train "$(wl_dir "$tr")" --dat_path_test "$(wl_dir "$te")" \
        --output_dir_qerror "${rd}/${stem}.csv" --output_dir_abs "${rd}/${stem}_abs.txt" \
        --log_file "${ld}/${stem}.log" \
        --db "${DB}" --workloads_train "$tr" --workload_test "$te" --algo qf \
        --num_epoch "${NUM_EPOCH}" --learning_rate 0.001 --batch_size 64 --train_ratio 1.0 --seed 42 \
        --early_stop_patience 5 --early_stop_after_epoch 20 \
        ${PRICE_FLAGS} || echo "FAILED: db=${DB} ${tr}->${te}"
}

for wl in $WORKLOADS; do
    case "$wl" in
        job)      run job job ;;
        syn)      run job syn ;;
        job_full) run job job_full ;;
        *)        run "$wl" "$wl" ;;
    esac
done
echo "Done (qf+priceN: ${DB} [${WORKLOADS}])."
