#!/bin/bash
# Experiment: Improve JointPrice finetuning with frozen PRICE encoder
# Strategy: freeze PRICE encoder blocks, larger batch size, more epochs, higher PRICE lr
# Control: LLMOnly (mode 4) for apples-to-apples comparison
#
# Usage: bash run_joint_price_tuning.sh [round_num] [ft_batch_size] [num_epoch] [price_lr]
#   Defaults: round=1, ft_batch_size=16, num_epoch=5, price_lr=0.0001

set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

ROUND=${1:-1}
FT_BS=${2:-16}
NUM_EPOCH=${3:-5}
PRICE_LR=${4:-0.0001}

MODEL="sentence-transformers/all-MiniLM-L6-v2"
MODEL_SHORT="sentence-transformers-all-MiniLM-L6-v2"
DB="duckdb"
WL="job"
DAT_PATH="../queryPlans/imdb/${DB}/"
PRICE_MODEL="/root/PRICE/results/model_params.pth"
PRICE_BIN=40
SEEDS=(42 43 44)

# Output directories with round number for isolation (but finetuned models stay in standard location)
RESULTS_DIR="results_jointprice_tuning/round${ROUND}/${DB}"
LOGS_DIR="logs_jointprice_tuning/round${ROUND}/${DB}"

mkdir -p "$RESULTS_DIR/results_Train_${WL}_Test_${WL}_ours"
mkdir -p "$LOGS_DIR/logs_Train_${WL}_Test_${WL}_ours"
mkdir -p "finetuned_models/${DB}"

echo "============================================================"
echo "  JointPrice Tuning — Round $ROUND"
echo "  ft_batch_size=$FT_BS, num_epoch=$NUM_EPOCH, price_lr=$PRICE_LR"
echo "  freeze_price_encoder=YES"
echo "============================================================"
echo ""

# ── Phase 1: Control — LLMOnly ──
# Uses existing LoRA LLM weights (ft_batch_size=1) + pretrained PRICE (frozen)
echo "=== Phase 1: Control — LLMOnly ==="
CONTROL_RESULT="${RESULTS_DIR}/results_Train_${WL}_Test_${WL}_ours/time_llm_price_pretrained-lora_priceLLMOnly_1.0_cdf_${DB}_0.0001_b64_h2048_${MODEL_SHORT}_emb1000_quant-4-bit_priceS_ftb1_seed42.csv"
if [ -f "$CONTROL_RESULT" ]; then
    echo "Control (LLMOnly) results exist, skipping."
else
    for SEED in "${SEEDS[@]}"; do
        echo "--- LLMOnly seed=$SEED ---"
        python train.py --dat_paths_train "$DAT_PATH" --dat_path_test "$DAT_PATH" \
            --output_dir_qerror "${RESULTS_DIR}/results_Train_${WL}_Test_${WL}_ours/time_llm_price_pretrained-lora_priceLLMOnly_1.0_cdf_${DB}_0.0001_b64_h2048_${MODEL_SHORT}_emb1000_quant-4-bit_priceS_ftb1_seed${SEED}.csv" \
            --output_dir_abs "${RESULTS_DIR}/results_Train_${WL}_Test_${WL}_ours/time_llm_price_pretrained-lora_priceLLMOnly_1.0_abs_${DB}_priceS_ftb1_seed${SEED}.txt" \
            --log_file "${LOGS_DIR}/logs_Train_${WL}_Test_${WL}_ours/time_llm_price_priceLLMOnly_${DB}_seed${SEED}.log" \
            --db "$DB" \
            --workloads_train "$WL" --workload_test "$WL" \
            --algo llm_price \
            --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
            --model_name "$MODEL" --embed_size 1000 \
            --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
            --llm_pretrained lora --llm_pretrained_task time \
            --price_model_path "$PRICE_MODEL" --price_bin_size $PRICE_BIN \
            --price_pretrained --seed $SEED --ft_batch_size 1 \
            --quantification 4-bit --price_s
    done
fi

echo ""
echo "=== Phase 2: JointPrice Finetune (freeze_price_encoder) ==="
echo "  FT_BS=$FT_BS, NUM_EPOCH=$NUM_EPOCH, PRICE_LR=$PRICE_LR"

# Check if finetuned weights already exist (standard location)
JOINT_PREFIX="finetuned_models/${DB}/${WL}_time_lora_${MODEL_SHORT}_b${FT_BS}_priceS_llm_price"
if [ -f "${JOINT_PREFIX}_llm.pt" ] && [ -f "${JOINT_PREFIX}_price.pt" ]; then
    echo "Finetuned JointPrice weights already exist at ${JOINT_PREFIX}_*.pt, skipping finetune."
else
    echo "--- Joint LLM+PRICE finetune ---"
    python train.py --dat_paths_train "$DAT_PATH" --dat_path_test "$DAT_PATH" \
        --log_file "${LOGS_DIR}/logs_Train_${WL}_Test_${WL}_ours/time_llm_price_finetune_lora_${DB}_0.0001_b${FT_BS}_priceS_freezeEnc.log" \
        --db "$DB" \
        --workloads_train "$WL" --workload_test "$WL" \
        --algo llm_price_finetune \
        --learning_rate 0.0001 --price_lr "$PRICE_LR" \
        --batch_size "$FT_BS" --hid_units 2048 \
        --model_name "$MODEL" \
        --train_ratio 1.0 --llm_mode lora \
        --num_epoch "$NUM_EPOCH" --seed 42 \
        --price_model_path "$PRICE_MODEL" --price_bin_size $PRICE_BIN \
        --quantification 4-bit --price_s \
        --freeze_price_encoder
fi

echo ""
echo "=== Phase 3: JointPrice Inference (using finetuned weights) ==="
for SEED in "${SEEDS[@]}"; do
    echo "--- JointPrice inference seed=$SEED ---"
    python train.py --dat_paths_train "$DAT_PATH" --dat_path_test "$DAT_PATH" \
        --output_dir_qerror "${RESULTS_DIR}/results_Train_${WL}_Test_${WL}_ours/time_llm_price_pretrained-lora_1.0_cdf_${DB}_0.0001_b64_h2048_${MODEL_SHORT}_emb1000_quant-4-bit_priceS_ftb${FT_BS}_seed${SEED}.csv" \
        --output_dir_abs "${RESULTS_DIR}/results_Train_${WL}_Test_${WL}_ours/time_llm_price_pretrained-lora_1.0_abs_${DB}_priceS_ftb${FT_BS}_seed${SEED}.txt" \
        --log_file "${LOGS_DIR}/logs_Train_${WL}_Test_${WL}_ours/time_llm_price_inference_${DB}_ftb${FT_BS}_seed${SEED}.log" \
        --db "$DB" \
        --workloads_train "$WL" --workload_test "$WL" \
        --algo llm_price \
        --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
        --model_name "$MODEL" --embed_size 1000 \
        --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
        --llm_pretrained lora --llm_pretrained_task time \
        --price_model_path "$PRICE_MODEL" --price_bin_size $PRICE_BIN \
        --price_pretrained --seed $SEED --ft_batch_size "$FT_BS" \
        --quantification 4-bit --price_s
done

echo ""
echo "=== Phase 4: Compare Results ==="
python3 -c "
import glob, csv, numpy as np, os, sys

results_dir = '${RESULTS_DIR}/results_Train_${WL}_Test_${WL}_ours'

def read_cdf(path):
    \"\"\"Read CDF CSV and return dict of percentile -> qerror.\"\"\"
    pcts, qerrs = [], []
    with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                pcts.append(float(row[0]))
                qerrs.append(float(row[1]))
            except (ValueError, IndexError):
                continue
    pcts, qerrs = np.array(pcts), np.array(qerrs)
    result = {}
    for target in [50, 90, 95, 99]:
        idx = np.searchsorted(pcts, target/100.0)
        if idx < len(qerrs):
            result[f'p{target}'] = qerrs[idx]
    result['mean'] = np.trapz(qerrs, pcts) if len(pcts) > 1 else 0
    result['max'] = qerrs[-1] if len(qerrs) > 0 else 0
    return result

def avg_seeds(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    all_results = [read_cdf(f) for f in files]
    keys = all_results[0].keys()
    return {k: np.mean([r[k] for r in all_results]) for k in keys}

# Control: LLMOnly
ctrl = avg_seeds(f'{results_dir}/time_llm_price_pretrained-lora_priceLLMOnly_*_seed*.csv')
# Experiment: JointPrice with freeze encoder
exp = avg_seeds(f'{results_dir}/time_llm_price_pretrained-lora_1.0_cdf_*_ftb${FT_BS}_seed*.csv')

print(f'{'Config':<45} {'Median':>8} {'P90':>8} {'P95':>8} {'P99':>8} {'Mean':>8} {'Max':>8}')
print('-' * 100)
if ctrl:
    print(f'{\"LLMOnly (control)\":<45} {ctrl[\"p50\"]:8.2f} {ctrl[\"p90\"]:8.2f} {ctrl[\"p95\"]:8.2f} {ctrl[\"p99\"]:8.2f} {ctrl[\"mean\"]:8.2f} {ctrl[\"max\"]:8.2f}')
else:
    print('LLMOnly: no results found')
if exp:
    print(f'{\"JointPrice (freezeEnc,bs=${FT_BS},ep=${NUM_EPOCH})\":<45} {exp[\"p50\"]:8.2f} {exp[\"p90\"]:8.2f} {exp[\"p95\"]:8.2f} {exp[\"p99\"]:8.2f} {exp[\"mean\"]:8.2f} {exp[\"max\"]:8.2f}')
else:
    print('JointPrice: no results found')

if ctrl and exp:
    print()
    better = sum(1 for k in ['p50','p90','p95','p99','mean','max'] if exp[k] < ctrl[k])
    print(f'JointPrice better on {better}/6 metrics')
"

echo ""
echo "============================================================"
echo "  Round $ROUND complete!"
echo "============================================================"
