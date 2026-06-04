#!/usr/bin/env bash
# Profile per-epoch TRAINING time and INFERENCE time for the 5 ablation settings —
# modes 1, 2, 7, 7b, 12(frzEvenAll) — across 3 models × all systems × all workloads.
#
# Unlike the model-selection pool (mode-12 WITH a frozen-LLM warmup schedule), NONE
# of these 5 settings have a warmup phase: frzEvenAll trains the LLM throughout (the
# even cross-attn blocks are frozen PERMANENTLY, not per-epoch), and modes 1/2/7/7b
# have no freeze-warmup either. So there is a single training rate — no warmup vs
# post-warmup split — and 1 epoch suffices:
#   --num_epoch 1, --train_ratio 0.1  (10% data; multiply the measured epoch by 10
#   for a full-data epoch, and by the chunk's epoch count for a chunk — all chunks
#   share this one rate since there is no warmup).
# Parses:
#   train_epoch_ms = "[Train] Epoch 0 total — X ms"
#   infer_ms       = "[Test] Total evaluation time — X ms" (first pass)
# mode 1 (inference, no LoRA) has no training epoch -> train_epoch_ms = NA.
#
# Mode definitions match experiment_scripts/_compare_modes_lib.sh (train.py flags):
#   1   : pretrained LLM inference, no LoRA, no PRICE  (--algo llm --llm_mode inference)
#   2   : LoRA finetune, no PRICE                      (--algo llm_finetune --llm_mode lora)
#   7   : JointPrice PRICE_N                           (--price_n --price_n_or --price_random_init)
#   7b  : JointPrice PRICE_B (original)                (--price_b --price_random_init)
#   12  : biCrossAttn + inflatePRICE + cx4, frzEvenAll (--use_bi_cross_attention --inflate_price
#         --n_cross_layers 4 --freeze_even_blocks_until_epoch 999)  # even blocks frozen forever
#
# Usage:   bash profile_ablation_modes_e1.sh             # run everything
#          DRY_RUN=1 bash profile_ablation_modes_e1.sh   # print the train.py plan only (RECOMMENDED first)
# Env:     MODELS, DB_ENGINES, WORKLOADS, MODES, BIG_BATCH(16), TPCX_BATCH(4), SEED(42)
set -uo pipefail
SCRIPT_DIR_LOCAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR_LOCAL}/.."   # -> experiments/
if [ -f ~/venvs/tmpenv/bin/activate ]; then source ~/venvs/tmpenv/bin/activate; fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
REPO_ROOT="$(cd "${SCRIPT_DIR_LOCAL}/../.." && pwd)"

# ── the ablation grid ───────────────────────────────────────────────────────
MODELS="${MODELS:-google/bert_uncased_L-2_H-256_A-4 google/bert_uncased_L-4_H-768_A-12 sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES="${DB_ENGINES:-postgres duckdb spark}"
WORKLOADS="${WORKLOADS:-stats syn job job_full tpcds tpch}"
MODES="${MODES:-1 2 7 7b 12}"

# ── fixed pipeline params ───────────────────────────────────────────────────
LR="0.0001"; PRICE_LR="0.001"; HID_UNITS="2048"; QUANT="4-bit"; SEED="${SEED:-42}"
NUM_EPOCH="1"; TRAIN_RATIO="0.1"; N_CROSS_LAYERS="4"; PRICE_BIN_SIZE="40"; FRZ_EVEN="999"
PRICE_MODEL_PATH="${PRICE_MODEL_PATH:-${REPO_ROOT}/experiments/price_statistics/model/model_params.pth}"
SUBDIR="ablation_e1_profile"
BIG_BATCH="${BIG_BATCH:-16}"; TPCX_BATCH="${TPCX_BATCH:-4}"   # tpch/tpcds: smaller (deeper plans)
OUT_CSV="${REPO_ROOT}/experiments/analysis_scripts/profile_ablation_modes_e1.csv"
[ -f "$PRICE_MODEL_PATH" ] || { echo "ERROR: PRICE_MODEL_PATH not found: $PRICE_MODEL_PATH" >&2; exit 1; }

canon_train () { case "$1" in syn|job|job_full|jobm) echo "job" ;; *) echo "$1" ;; esac; }
canon_dir   () { case "$1" in syn|job|job_full|jobm) echo "imdb" ;; *) echo "$1" ;; esac; }

plans_exist () {
    local db="$1" wl="$2" canon; canon="$(canon_dir "$wl")"
    [ -d "../queryPlans/${canon}/${db}/" ] && {
        ls "../queryPlans/${canon}/${db}/"long_raw_${db}_${wl}*.csv >/dev/null 2>&1 ||
        ls "../queryPlans/${canon}/${db}/"long_raw_${db}_${canon}.csv >/dev/null 2>&1; }
}

# train.py flags that DEFINE each mode (no freeze-warmup imposed — single rate).
mode_flags () {
    case "$1" in
        1)  echo "--algo llm --llm_mode inference" ;;
        2)  echo "--algo llm_finetune --llm_mode lora" ;;
        7)  echo "--algo llm_price_finetune --llm_mode lora --price_n --price_n_or --price_random_init \
                  --price_lr $PRICE_LR --price_model_path $PRICE_MODEL_PATH --price_bin_size $PRICE_BIN_SIZE" ;;
        7b) echo "--algo llm_price_finetune --llm_mode lora --price_b --price_random_init \
                  --price_lr $PRICE_LR --price_model_path $PRICE_MODEL_PATH --price_bin_size $PRICE_BIN_SIZE" ;;
        12) echo "--algo llm_price_finetune --llm_mode lora --price_n --price_n_or --price_random_init \
                  --use_bi_cross_attention --inflate_price --n_cross_layers $N_CROSS_LAYERS \
                  --freeze_even_blocks_until_epoch $FRZ_EVEN \
                  --price_lr $PRICE_LR --price_model_path $PRICE_MODEL_PATH --price_bin_size $PRICE_BIN_SIZE" ;;
        *)  echo "__BADMODE__" ;;
    esac
}

echo "============================================================"
echo "  Ablation 1-epoch profiling (no warmup; single training rate)"
echo "  models:    $MODELS"
echo "  systems:   $DB_ENGINES"
echo "  workloads: $WORKLOADS"
echo "  modes:     $MODES   (e1, tr0.1; mode 1 = inference only)"
echo "============================================================"

[ "${DRY_RUN:-0}" = "1" ] || echo "model,db,workload,mode,batch_size,train_epoch_ms,infer_ms,exit_code,log" > "$OUT_CSV"

i=0
for model in $MODELS; do
  model_dashed="${model//\//-}"
  for db in $DB_ENGINES; do
    for wl in $WORKLOADS; do
      if ! plans_exist "$db" "$wl"; then echo "[skip] no plans: $db/$wl"; continue; fi
      tr="$(canon_train "$wl")"; dir="$(canon_dir "$wl")"
      DAT_PATH="../queryPlans/${dir}/${db}/"
      case "$wl" in tpch|tpcds) bs="$TPCX_BATCH" ;; *) bs="$BIG_BATCH" ;; esac
      LOG_DIR="logs/${db}/logs_Train_${tr}_Test_${wl}_ours/${SUBDIR}"
      for m in $MODES; do
        mf="$(mode_flags "$m")"
        [ "$mf" = "__BADMODE__" ] && { echo "  [bad mode] $m"; continue; }
        i=$((i+1))
        log_file="${LOG_DIR}/time_ablation_mode${m}_${db}_${LR}_b${bs}_h${HID_UNITS}_${model_dashed}_quant-${QUANT}_e${NUM_EPOCH}_tr${TRAIN_RATIO}_seed${SEED}.log"
        cmd=(python train.py
             --dat_paths_train "$DAT_PATH" --dat_path_test "$DAT_PATH"
             --log_file "$log_file"
             --db "$db" --workloads_train "$tr" --workload_test "$wl"
             --learning_rate "$LR" --batch_size "$bs" --hid_units "$HID_UNITS"
             --model_name "$model" --quantification "$QUANT"
             --train_ratio "$TRAIN_RATIO" --num_epoch "$NUM_EPOCH" --seed "$SEED"
             --checkpoint_interval "$NUM_EPOCH" --subdir_tag "$SUBDIR"
             $mf)
        echo "[$i] ${model_dashed} ${db}/${wl} mode${m} (b${bs})"
        if [ "${DRY_RUN:-0}" = "1" ]; then printf '      %s\n' "${cmd[*]}"; continue; fi
        mkdir -p "$LOG_DIR"
        "${cmd[@]}" 2>&1 | tee "${log_file}.stdout"
        rc=${PIPESTATUS[0]}
        train_epoch_ms=$(grep -oE "\[Train\] Epoch 0 total — [0-9.]+ ms" "$log_file" 2>/dev/null | head -1 | grep -oE "[0-9.]+" | head -1)
        infer_ms=$(grep -oE "\[Test\] Total evaluation time — [0-9.]+ ms" "$log_file" 2>/dev/null | head -1 | grep -oE "[0-9.]+" | head -1)
        train_epoch_ms="${train_epoch_ms:-NA}"; infer_ms="${infer_ms:-NA}"
        echo "${model},${db},${wl},${m},${bs},${train_epoch_ms},${infer_ms},${rc},${log_file}" >> "$OUT_CSV"
        echo "  → train_epoch=${train_epoch_ms} infer=${infer_ms} rc=$rc"
      done
    done
  done
done

echo ""
[ "${DRY_RUN:-0}" = "1" ] && echo "(DRY_RUN=1 -> plan only; $i cells)" || echo "Done. Profile CSV: $OUT_CSV  ($i cells)"
