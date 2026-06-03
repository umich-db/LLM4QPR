#!/usr/bin/env bash
# Re-collect warmup/after-warmup/inference timing for the POOL MODELS THAT ARE
# STILL MISSING (blank time_e1_4_ms) in a workload's all_models_full_e16.csv,
# using a SMALLER batch size so the post-warmup (unfrozen) epoch stops OOM-ing.
#
# Learns from profile_pool_{tpch,tpcds}_warmup_e2.sh: identical mode-12 pipeline
# (inflatePRICE + cx4 BiCross, 2 epochs, --train_ratio 0.1,
#  --freeze_llm_until_epoch 1 --price_warmup_epochs 1), EXCEPT batch size:
#   * original policy: b1 for "large" models (total_params >= B1_PARAM_THRESHOLD
#     or an ALBERT xlarge/xxlarge), b16 otherwise.
#   * here: models that were at b16 are re-run at REDUCED_BIG_BATCH (default 4).
#     Models ALREADY at b1 CANNOT be decreased further -> re-run at b1 with a loud
#     warning (skip them with SKIP_B1=1).
#
# Usage:   bash recollect_missing_pool_warmup_e2.sh <tpch|tpcds>
# Env:     REDUCED_BIG_BATCH=4  B1_PARAM_THRESHOLD=200000000  SKIP_B1=0  DRY_RUN=0
#
# New logs land in the same warmup_e2_profile/ dir under a b<new> filename (the
# old truncated b16 log is left in place; build_pool_time_from_warmup_logs.py
# prefers the COMPLETE log). A recollect CSV is written for convenience.
set -uo pipefail
SCRIPT_DIR_LOCAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR_LOCAL}/.."   # -> experiments/
if [ -f ~/venvs/tmpenv/bin/activate ]; then source ~/venvs/tmpenv/bin/activate; fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

WORKLOAD="${1:-}"
case "$WORKLOAD" in tpch|tpcds|stats) ;; *) echo "usage: $0 <tpch|tpcds|stats>" >&2; exit 1 ;; esac

REPO_ROOT="$(cd "${SCRIPT_DIR_LOCAL}/../.." && pwd)"
POOL_CSV="${REPO_ROOT}/experiments/logs/postgres/logs_Train_${WORKLOAD}_Test_${WORKLOAD}_ours/all_models/all_models_full_e16.csv"
PROFILE_CSV="${REPO_ROOT}/experiments/experiment_scripts/model_profile_with_nonemb.csv"
OUT_CSV="${REPO_ROOT}/experiments/analysis_scripts/profile_pool_${WORKLOAD}_warmup_e2_recollect.csv"
[ -f "$POOL_CSV" ] || { echo "ERROR: pool csv not found: $POOL_CSV" >&2; exit 1; }

export B1_PARAM_THRESHOLD="${B1_PARAM_THRESHOLD:-200000000}"
export REDUCED_BIG_BATCH="${REDUCED_BIG_BATCH:-4}"
export SKIP_B1="${SKIP_B1:-0}"

# Fixed pipeline params (mirror profile_pool_${WORKLOAD}_warmup_e2.sh).
DB="postgres"
DAT_PATH="../queryPlans/${WORKLOAD}/${DB}/"
LR="0.0001"; PRICE_LR="0.001"; HID_UNITS="2048"; QUANT="4-bit"
PRICE_MODEL_PATH="${PRICE_MODEL_PATH:-${REPO_ROOT}/experiments/price_statistics/model/model_params.pth}"
PRICE_BIN_SIZE="40"; N_CROSS_LAYERS="4"; SEED="42"; NUM_EPOCH="2"; TRAIN_RATIO="0.1"
FREEZE_LLM_UNTIL_EPOCH="1"; PRICE_WARMUP_EPOCHS="1"
[ -f "$PRICE_MODEL_PATH" ] || { echo "ERROR: PRICE_MODEL_PATH not found: $PRICE_MODEL_PATH" >&2; exit 1; }
[ -d "$DAT_PATH" ]        || { echo "ERROR: query plans dir not found: $DAT_PATH" >&2; exit 1; }

# ---- Plan: missing pool models -> reduced batch size ----
# missing := row in POOL_CSV whose time_e1_4_ms is blank.
PLAN="$(python3 - "$POOL_CSV" "$PROFILE_CSV" <<'PY'
import csv, os, re, sys
pool = list(csv.DictReader(open(sys.argv[1])))
missing = set()
for r in pool:
    if not (r.get("time_e1_4_ms") or "").strip():
        m = re.search(r"_h2048_(.+?)_quant-4-bit", r["key"])
        if m: missing.add(m.group(1))           # dashed model name
thr = float(os.environ["B1_PARAM_THRESHOLD"]); red = os.environ["REDUCED_BIG_BATCH"]
def f(x):
    try: return float(x)
    except: return 0.0
seen = set()
for r in csv.DictReader(open(sys.argv[2])):
    model = r["model"]; dashed = model.replace("/", "-")
    if dashed not in missing or dashed in seen: continue
    seen.add(dashed)
    is_albert_big = ("albert" in model.lower() and "xlarge" in model.lower())
    orig_b1 = (f(r.get("total_params", 0)) >= thr) or is_albert_big
    if orig_b1:
        print(f"{model}\t1\tB1")          # already b1 -> cannot decrease
    else:
        print(f"{model}\t{red}\tREDUCED")  # was b16 -> reduced
# report any missing model not found in the profile csv
for d in sorted(missing - seen):
    print(f"#NOTFOUND\t{d}\tNA")
PY
)"

echo "[${WORKLOAD}] missing-model re-collection plan (reduced_big_batch=${REDUCED_BIG_BATCH}):"
printf '%s\n' "$PLAN" | awk -F'\t' '{printf "    %-48s b%-3s %s\n",$1,$2,$3}'
n_total=$(printf '%s\n' "$PLAN" | grep -vc '^#NOTFOUND')
[ "${DRY_RUN:-0}" = "1" ] && { echo "(DRY_RUN=1 -> plan only)"; exit 0; }

LOG_DIR="logs/postgres/logs_Train_${WORKLOAD}_Test_${WORKLOAD}_ours/warmup_e2_profile"
mkdir -p "$LOG_DIR"
echo "model,workload,batch_size,reduce_kind,warmup_ms,after_warmup_ms,infer_ms,exit_code,log" > "$OUT_CSV"

i=0
while IFS=$'\t' read -r model bs kind; do
    [ -z "$model" ] && continue
    [ "$model" = "#NOTFOUND" ] && { echo "  [warn] not in profile csv: $bs"; continue; }
    if [ "$kind" = "B1" ] && [ "$SKIP_B1" = "1" ]; then
        echo "  [skip] $model already b1 (cannot decrease; SKIP_B1=1)"; continue
    fi
    [ "$kind" = "B1" ] && echo "  [warn] $model already at b1 — cannot decrease; may OOM again."
    i=$((i+1)); model_dashed="${model//\//-}"
    log_file="${LOG_DIR}/time_llm_price_finetune_lora_biCrossAttn_${DB}_${LR}_b${bs}_h${HID_UNITS}_${model_dashed}_quant-${QUANT}_priceS_inflatePRICE_randInit_cx4_pwm${PRICE_WARMUP_EPOCHS}_frzLLM${FREEZE_LLM_UNTIL_EPOCH}_e${NUM_EPOCH}_tr${TRAIN_RATIO}_seed${SEED}.log"
    echo "[$i/${n_total}] ${model}  ${WORKLOAD}  (b${bs}, ${kind})"

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
    echo "${model},${WORKLOAD},${bs},${kind},${warmup_ms},${after_warmup_ms},${infer_ms},${rc},${log_file}" >> "$OUT_CSV"
    echo "  → warmup=${warmup_ms} after_warmup=${after_warmup_ms} infer=${infer_ms} rc=$rc"
done <<< "$PLAN"

echo ""
echo "Done. Recollect CSV: $OUT_CSV"
echo "Next: re-run build_pool_time_from_warmup_logs.py for ${WORKLOAD} to fold the new"
echo "      complete logs into all_models_full_e16.csv (it auto-prefers complete logs)."
