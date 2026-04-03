#!/bin/bash
# Batch 2: Only the 9 models still missing inference + val results.
set -u
cd "$(dirname "$0")"
source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export SKIP_HF_AUTH=1

LOG_DIR="logs/rank_stability"
RESULT_DIR="results/rank_stability"
CKPT_DIR="finetuned_models/postgres/checkpoints"
WEIGHT_DIR="finetuned_models/postgres"
mkdir -p "$LOG_DIR" "$RESULT_DIR" "$CKPT_DIR"

models=(
  "sentence-transformers/paraphrase-albert-base-v2"
  "albert/albert-base-v2"
  "google/bert_uncased_L-12_H-128_A-2"
  "albert/albert-large-v1"
  "albert/albert-large-v2"
  "google/electra-large-discriminator"
  "facebook/opt-350m"
  "albert/albert-xlarge-v1"
  "albert/albert-xlarge-v2"
)

total=${#models[@]}
echo "================================================================"
echo "  Batch 2: $total missing models"
echo "  Started: $(date)"
echo "================================================================"
echo ""

count=0
for model in "${models[@]}"; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')
    ft_log="$LOG_DIR/finetune_3ep_${model_safe}_seed42.log"
    weight_path="$WEIGHT_DIR/stats_time_lora_${model_safe}_b16_llm.pt"

    echo "===== [$count/$total] $model  ($(date '+%H:%M:%S')) ====="

    # ── Step 1: Finetune 3 epochs ──
    nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)
    if [ "$nval" -ge 3 ]; then
        echo "  Finetune: SKIP (already done, val=$nval)"
    else
        rm -f "$ft_log" 2>/dev/null
        rm -f "$CKPT_DIR/stats_time_lora_${model_safe}_b16_epoch"*.pt 2>/dev/null
        echo "  Finetune: running..."

        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test  ../queryPlans/stats/postgres/ \
            --log_file "$ft_log" \
            --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm_finetune \
            --learning_rate 0.0001 --batch_size 16 --hid_units 2048 \
            --model_name "$model" \
            --train_ratio 1.0 --llm_mode lora --num_epoch 3 --seed 42 \
            --quantification 4-bit --max_queries 10000 --embed_size 1000 \
            --checkpoint_interval 1

        nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)
        if [ "$nval" -ge 3 ]; then
            echo "  Finetune: OK (val=$nval)"
        else
            echo "  Finetune: FAIL (val=$nval), skipping inference"
            echo ""
            sleep 3
            continue
        fi
    fi

    # ── Step 2: Inference for epoch 1, 2, 3 ──
    for epoch in 1 2 3; do
        ckpt_file="$CKPT_DIR/stats_time_lora_${model_safe}_b16_epoch${epoch}.pt"
        resultfile="$RESULT_DIR/inference_ep${epoch}_${model_safe}_seed42.csv"

        if [ -f "$resultfile" ]; then
            echo "  Inference ep$epoch: SKIP (result exists)"
            continue
        fi
        if [ ! -f "$ckpt_file" ]; then
            echo "  Inference ep$epoch: SKIP (no checkpoint)"
            continue
        fi

        echo "  Inference ep$epoch: ($(date '+%H:%M:%S'))"

        python -c "
import torch
ckpt = torch.load('$ckpt_file', map_location='cpu')
sd = ckpt['model_state_dict']
llm_sd = {k.replace('0.model.', ''): v for k, v in sd.items() if k.startswith('0.')}
torch.save(llm_sd, '$weight_path')
" 2>/dev/null

        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test  ../queryPlans/stats/postgres/ \
            --log_file "$LOG_DIR/inference_ep${epoch}_${model_safe}_seed42.log" \
            --output_dir_qerror "$resultfile" \
            --output_dir_abs "$RESULT_DIR/inference_ep${epoch}_${model_safe}_seed42_abs.txt" \
            --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm \
            --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
            --model_name "$model" \
            --embed_size 1000 \
            --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
            --llm_pretrained lora --llm_pretrained_task time \
            --seed 42 --ft_batch_size 16 --ft_num_epoch $epoch \
            --quantification 4-bit \
            --max_queries 10000 \
            --verbose_info --llm_downstream mlp

        if [ $? -eq 0 ] && [ -f "$resultfile" ]; then
            echo "    OK"
        else
            echo "    FAIL"
        fi
    done

    rm -f "$weight_path" 2>/dev/null
    echo ""
    sleep 3
done

echo "================================================================"
echo "  Batch 2 ALL DONE: $(date)"
echo "================================================================"
