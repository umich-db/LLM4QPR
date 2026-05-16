#!/bin/bash
# Profile warmup-vs-after-warmup-vs-inference time for every model in
# analysis_scripts/model_db.csv at minimal cost.
#
# Per model: run mode 12 (inflatePRICE+cx4 BiCross) for exactly 2 epochs at
# --train_ratio 0.1 with --freeze_llm_until_epoch 1 --price_warmup_epochs 1.
# That gives one "warmup" epoch (epoch 0: LLM frozen + PRICE high-LR) and one
# "after-warmup" epoch (epoch 1: LLM unfrozen + PRICE drop LR).
#
# Each per-epoch wall time is logged by trainer as
#   "[Train] Epoch <N> total — <X> ms"
# Inference wall time is logged as
#   "[Test] Total evaluation time — <X> ms"
# A post-processor at the end of this script greps both from the per-model
# log file and emits a single profile_model_db_warmup_e2.csv with three
# numeric columns: warmup_ms (epoch 0), after_warmup_ms (epoch 1), infer_ms.
#
# All other parameters mirror master_finish_inflatePRICE_e16_group_A.sh, so the
# extrapolation from this 2-epoch profile to a full 16-epoch run is just a
# per-phase multiplication.

set -uo pipefail
SCRIPT_DIR_LOCAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR_LOCAL}/.."   # → repo's experiments/ dir (works on any host)
if [ -f ~/venvs/tmpenv/bin/activate ]; then
    source ~/venvs/tmpenv/bin/activate
fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODEL_DB="${REPO_ROOT}/experiments/analysis_scripts/model_db.csv"
OUT_CSV="${REPO_ROOT}/experiments/analysis_scripts/profile_model_db_warmup_e2.csv"
LOG_DIR="logs/postgres/logs_Train_stats_Test_stats_ours/warmup_e2_profile"
mkdir -p "$LOG_DIR"

# Fixed pipeline params (mirroring master_finish_inflatePRICE_e16_group_A.sh).
DB="postgres"
WORKLOAD="stats"
DAT_PATH="../queryPlans/${WORKLOAD}/${DB}/"
LR="0.0001"
PRICE_LR="0.001"
FT_BATCH_SIZE="24"
HID_UNITS="2048"
QUANT="4-bit"
PRICE_MODEL_PATH="${PRICE_MODEL_PATH:-${REPO_ROOT}/experiments/price_statistics/model/model_params.pth}"
PRICE_BIN_SIZE="40"
N_CROSS_LAYERS="4"
SEED="42"

if [ ! -f "$PRICE_MODEL_PATH" ]; then
    echo "ERROR: PRICE_MODEL_PATH not found: $PRICE_MODEL_PATH" >&2
    echo "Set PRICE_MODEL_PATH=/path/to/model_params.pth and rerun." >&2
    exit 1
fi
if [ ! -d "$DAT_PATH" ]; then
    echo "ERROR: query plans dir not found: $DAT_PATH (cwd=$(pwd))" >&2
    exit 1
fi
echo "Using PRICE_MODEL_PATH=$PRICE_MODEL_PATH"
echo "Using DAT_PATH=$DAT_PATH"

# Minimal-cost overrides (the whole point of this script).
NUM_EPOCH="2"
TRAIN_RATIO="0.1"
FREEZE_LLM_UNTIL_EPOCH="1"
PRICE_WARMUP_EPOCHS="1"

# Header.
echo "model,warmup_ms,after_warmup_ms,infer_ms,exit_code,log" > "$OUT_CSV"

# Iterate models from model_db.csv (skip header).
N=$(tail -n +2 "$MODEL_DB" | wc -l)
i=0
while IFS=, read -r model rest; do
    i=$((i+1))
    model_dashed="${model//\//-}"
    log_file="${LOG_DIR}/time_llm_price_finetune_lora_biCrossAttn_${DB}_${LR}_b${FT_BATCH_SIZE}_h${HID_UNITS}_${model_dashed}_quant-${QUANT}_priceS_inflatePRICE_randInit_cx4_pwm${PRICE_WARMUP_EPOCHS}_frzLLM${FREEZE_LLM_UNTIL_EPOCH}_e${NUM_EPOCH}_tr${TRAIN_RATIO}_seed${SEED}.log"
    echo "[$i/$N] $model"

    # Tee train.py output to ${log_file}.stdout AND the terminal so progress
    # / errors are visible. PIPESTATUS captures train.py's rc (not tee's).
    python train.py \
        --dat_paths_train "$DAT_PATH" --dat_path_test "$DAT_PATH" \
        --log_file "$log_file" \
        --db "$DB" \
        --workloads_train "$WORKLOAD" --workload_test "$WORKLOAD" \
        --algo llm_price_finetune \
        --learning_rate "$LR" --price_lr "$PRICE_LR" \
        --batch_size "$FT_BATCH_SIZE" --hid_units "$HID_UNITS" \
        --model_name "$model" \
        --train_ratio "$TRAIN_RATIO" \
        --llm_mode lora --use_bi_cross_attention \
        --num_epoch "$NUM_EPOCH" --seed "$SEED" \
        --price_model_path "$PRICE_MODEL_PATH" \
        --price_bin_size "$PRICE_BIN_SIZE" \
        --quantification "$QUANT" \
        --price_s --price_random_init \
        --checkpoint_interval "$NUM_EPOCH" \
        --n_cross_layers "$N_CROSS_LAYERS" --inflate_price \
        --freeze_llm_until_epoch "$FREEZE_LLM_UNTIL_EPOCH" \
        --price_warmup_epochs "$PRICE_WARMUP_EPOCHS" \
        --subdir_tag warmup_e2_profile \
        2>&1 | tee "${log_file}.stdout"
    rc=${PIPESTATUS[0]}

    # Extract per-epoch totals + inference time from the trainer log.
    warmup_ms=$(grep -oE "\[Train\] Epoch 0 total — [0-9.]+ ms" "$log_file" 2>/dev/null \
                | head -1 | grep -oE "[0-9.]+" | head -1)
    after_warmup_ms=$(grep -oE "\[Train\] Epoch 1 total — [0-9.]+ ms" "$log_file" 2>/dev/null \
                     | head -1 | grep -oE "[0-9.]+" | head -1)
    infer_ms=$(grep -oE "\[Test\] Total evaluation time — [0-9.]+ ms" "$log_file" 2>/dev/null \
              | head -1 | grep -oE "[0-9.]+" | head -1)
    warmup_ms="${warmup_ms:-NA}"
    after_warmup_ms="${after_warmup_ms:-NA}"
    infer_ms="${infer_ms:-NA}"

    echo "${model},${warmup_ms},${after_warmup_ms},${infer_ms},${rc},${log_file}" >> "$OUT_CSV"
    echo "  → warmup=${warmup_ms} ms, after_warmup=${after_warmup_ms} ms, infer=${infer_ms} ms, rc=$rc"
done < <(tail -n +2 "$MODEL_DB")

echo ""
echo "Done. Profile CSV: $OUT_CSV"
