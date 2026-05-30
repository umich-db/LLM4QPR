#!/bin/bash
# Collect warmup / after-warmup / inference time on H100 for the 87 pool models
# (all_models_full_e16.csv) on TPCH only.  Companion: profile_pool_tpcds_warmup_e2.sh.
# The two are independent (distinct OUT_CSV + log dirs) so they can run in
# parallel on separate machines/GPUs.
#
# Same pipeline/settings as profile_model_db_warmup_e2.sh (mode 12
# inflatePRICE+cx4 BiCross, 2 epochs, --train_ratio 0.1,
# --freeze_llm_until_epoch 1 --price_warmup_epochs 1), EXCEPT:
#   * workload = tpch
#   * batch size is PER-MODEL: 1 for "large" models, 16 for the rest.
#       large := total_params >= B1_PARAM_THRESHOLD (default 200M)  OR
#                an ALBERT xlarge/xxlarge (OOMs on activations, not params)  OR
#                listed in $B1_MODELS.
#
# Model list = the 87 pool models (model_profile_with_nonemb.csv rows whose
# dashed name appears in all_models_full_e16.csv).
# Output: analysis_scripts/profile_pool_tpch_warmup_e2.csv with columns
#   model,workload,batch_size,warmup_ms,after_warmup_ms,infer_ms,exit_code,log
# Knobs (env): B1_PARAM_THRESHOLD, SMALL_BATCH(=1), BIG_BATCH(=16),
#   B1_MODELS (extra space/comma list forced to b1), DRY_RUN=1 (print plan & exit).

set -uo pipefail
SCRIPT_DIR_LOCAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR_LOCAL}/.."   # -> repo's experiments/ dir (works on any host)
if [ -f ~/venvs/tmpenv/bin/activate ]; then
    source ~/venvs/tmpenv/bin/activate
fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

WORKLOAD="tpch"   # <-- this script's only workload

REPO_ROOT="$(cd "${SCRIPT_DIR_LOCAL}/../.." && pwd)"   # absolute, robust to how the script is invoked
POOL_CSV="${REPO_ROOT}/experiments/logs/postgres/logs_Train_stats_Test_stats_ours/all_models/all_models_full_e16.csv"
PROFILE_CSV="${REPO_ROOT}/experiments/experiment_scripts/model_profile_with_nonemb.csv"
OUT_CSV="${REPO_ROOT}/experiments/analysis_scripts/profile_pool_${WORKLOAD}_warmup_e2.csv"

# Batch-size policy (overridable).
export B1_PARAM_THRESHOLD="${B1_PARAM_THRESHOLD:-200000000}"
export SMALL_BATCH="${SMALL_BATCH:-1}"
export BIG_BATCH="${BIG_BATCH:-16}"
export B1_MODELS="${B1_MODELS:-}"

# Fixed pipeline params (mirroring profile_model_db_warmup_e2.sh).
DB="postgres"
DAT_PATH="../queryPlans/${WORKLOAD}/${DB}/"
LR="0.0001"
PRICE_LR="0.001"
HID_UNITS="2048"
QUANT="4-bit"
PRICE_MODEL_PATH="${PRICE_MODEL_PATH:-${REPO_ROOT}/experiments/price_statistics/model/model_params.pth}"
PRICE_BIN_SIZE="40"
N_CROSS_LAYERS="4"
SEED="42"
NUM_EPOCH="2"
TRAIN_RATIO="0.1"
FREEZE_LLM_UNTIL_EPOCH="1"
PRICE_WARMUP_EPOCHS="1"

[ -f "$PRICE_MODEL_PATH" ] || { echo "ERROR: PRICE_MODEL_PATH not found: $PRICE_MODEL_PATH" >&2; exit 1; }
[ -d "$DAT_PATH" ]        || { echo "ERROR: query plans dir not found: $DAT_PATH (cwd=$(pwd))" >&2; exit 1; }

# ---- Build the per-model batch plan: 87 pool models -> batch size ----
PLAN="$(python3 - "$POOL_CSV" "$PROFILE_CSV" <<'PY'
import csv, os, sys
pool = open(sys.argv[1]).read()
thr = float(os.environ.get("B1_PARAM_THRESHOLD", "200000000"))
small = os.environ.get("SMALL_BATCH", "1"); big = os.environ.get("BIG_BATCH", "16")
extra = {x for x in os.environ.get("B1_MODELS", "").replace(",", " ").split() if x}
in_pool = lambda m: f"_h2048_{m.replace('/', '-')}_quant" in pool
def f(x):
    try: return float(x)
    except: return 0.0
for r in csv.DictReader(open(sys.argv[2])):
    m = r["model"]
    if not in_pool(m):
        continue
    is_albert_big = ("albert" in m.lower() and "xlarge" in m.lower())  # xlarge + xxlarge
    b1 = (f(r.get("total_params", 0)) >= thr) or is_albert_big or (m in extra)
    print(f"{m}\t{small if b1 else big}")
PY
)"

n_total=$(printf '%s\n' "$PLAN" | grep -c .)
n_b1=$(printf '%s\n' "$PLAN" | awk -F'\t' -v s="$SMALL_BATCH" '$2==s' | wc -l)
echo "[${WORKLOAD}] Plan: ${n_total} pool models  (b${SMALL_BATCH}: ${n_b1}, b${BIG_BATCH}: $((n_total-n_b1)))"
echo "----- models at batch ${SMALL_BATCH} -----"
printf '%s\n' "$PLAN" | awk -F'\t' -v s="$SMALL_BATCH" '$2==s {print "  "$1}'
if [ "${DRY_RUN:-0}" = "1" ]; then echo "(DRY_RUN=1 -> plan only, exiting)"; exit 0; fi

LOG_DIR="logs/postgres/logs_Train_${WORKLOAD}_Test_${WORKLOAD}_ours/warmup_e2_profile"
mkdir -p "$LOG_DIR"
echo "model,workload,batch_size,warmup_ms,after_warmup_ms,infer_ms,exit_code,log" > "$OUT_CSV"

i=0
while IFS=$'\t' read -r model bs; do
    [ -z "$model" ] && continue
    i=$((i+1))
    model_dashed="${model//\//-}"
    log_file="${LOG_DIR}/time_llm_price_finetune_lora_biCrossAttn_${DB}_${LR}_b${bs}_h${HID_UNITS}_${model_dashed}_quant-${QUANT}_priceS_inflatePRICE_randInit_cx4_pwm${PRICE_WARMUP_EPOCHS}_frzLLM${FREEZE_LLM_UNTIL_EPOCH}_e${NUM_EPOCH}_tr${TRAIN_RATIO}_seed${SEED}.log"
    echo "[$i/${n_total}] ${model}  ${WORKLOAD}  (b${bs})"

    python train.py \
        --dat_paths_train "$DAT_PATH" --dat_path_test "$DAT_PATH" \
        --log_file "$log_file" \
        --db "$DB" \
        --workloads_train "$WORKLOAD" --workload_test "$WORKLOAD" \
        --algo llm_price_finetune \
        --learning_rate "$LR" --price_lr "$PRICE_LR" \
        --batch_size "$bs" --hid_units "$HID_UNITS" \
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

    warmup_ms=$(grep -oE "\[Train\] Epoch 0 total — [0-9.]+ ms" "$log_file" 2>/dev/null | head -1 | grep -oE "[0-9.]+" | head -1)
    after_warmup_ms=$(grep -oE "\[Train\] Epoch 1 total — [0-9.]+ ms" "$log_file" 2>/dev/null | head -1 | grep -oE "[0-9.]+" | head -1)
    infer_ms=$(grep -oE "\[Test\] Total evaluation time — [0-9.]+ ms" "$log_file" 2>/dev/null | head -1 | grep -oE "[0-9.]+" | head -1)
    warmup_ms="${warmup_ms:-NA}"; after_warmup_ms="${after_warmup_ms:-NA}"; infer_ms="${infer_ms:-NA}"

    echo "${model},${WORKLOAD},${bs},${warmup_ms},${after_warmup_ms},${infer_ms},${rc},${log_file}" >> "$OUT_CSV"
    echo "  → ${WORKLOAD}: warmup=${warmup_ms} ms, after_warmup=${after_warmup_ms} ms, infer=${infer_ms} ms, rc=$rc"
done <<< "$PLAN"

echo ""
echo "Done. Profile CSV: $OUT_CSV"
