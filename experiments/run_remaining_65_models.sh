#!/bin/bash
# =============================================================================
# Run finetuning (3 epochs) + inference (epoch 1,2,3) for 65 remaining models.
# Designed to run on a multi-GPU machine.
#
# Usage:
#   bash run_remaining_65_models.sh              # uses GPU 0
#   CUDA_VISIBLE_DEVICES=1 bash run_remaining_65_models.sh  # uses GPU 1
#
# Prerequisites:
#   - Same conda/venv environment as the main machine
#   - Copy the full LLM4QPR repo to the target machine
#   - HuggingFace models cached or HF_TOKEN set
#
# Output files to copy back:
#   1. experiments/logs/rank_stability/finetune_3ep_*_seed42.log  (val metrics)
#   2. experiments/results/rank_stability/inference_ep*_seed42.csv (test results)
#   3. experiments/finetuned_models/postgres/checkpoints/stats_time_lora_*_epoch*.pt (optional)
# =============================================================================

set -u
cd "$(dirname "$0")"
source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

SKIP_HF_AUTH="${SKIP_HF_AUTH:-0}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

LOG_DIR="logs/rank_stability"
RESULT_DIR="results/rank_stability"
CKPT_DIR="finetuned_models/postgres/checkpoints"
WEIGHT_DIR="finetuned_models/postgres"
mkdir -p "$LOG_DIR" "$RESULT_DIR" "$CKPT_DIR"

# 65 remaining models (sorted by latency)
models=(
#   "sentence-transformers/paraphrase-albert-small-v2"
#   "sentence-transformers/multi-qa-MiniLM-L6-dot-v1"
#   "FacebookAI/xlm-roberta-base"
#   "FacebookAI/roberta-base"
#   "facebook/opt-125m"
#   "albert/albert-base-v1"
#   "google/bert_uncased_L-12_H-256_A-4"
#   "google-bert/bert-base-cased"
#   "google/bert_uncased_L-12_H-512_A-8"
#   "google/bert_uncased_L-12_H-768_A-12"
#   "google-bert/bert-base-multilingual-cased"
#   "google/bert_uncased_L-12_H-128_A-2"
#   "EleutherAI/pythia-160m-deduped"
#   "EleutherAI/pythia-160m"
#   "google/electra-small-discriminator"
#   "microsoft/MiniLM-L12-H384-uncased"
#   "sentence-transformers/all-MiniLM-L12-v2"
  "google/electra-small-generator"
  "google/electra-base-discriminator"
  "sentence-transformers/paraphrase-albert-base-v2"
  "albert/albert-base-v2"
  "google/electra-base-generator"
  "sentence-transformers/paraphrase-mpnet-base-v2"
  "sentence-transformers/multi-qa-mpnet-base-cos-v1"
  "sentence-transformers/all-mpnet-base-v2"
  "google-bert/bert-base-multilingual-uncased"
  "sentence-transformers/paraphrase-MiniLM-L12-v2"
  "google-bert/bert-base-uncased"
#   "microsoft/deberta-v3-small"
#   "microsoft/deberta-v3-xsmall"
#   "google/electra-large-generator"
#   "FacebookAI/xlm-roberta-large"
#   "FacebookAI/roberta-large"
#   "EleutherAI/gpt-neo-125m"
#   "albert/albert-large-v1"
#   "albert/albert-large-v2"
#   "google/electra-large-discriminator"
#   "facebook/opt-350m"
#   "HuggingFaceTB/SmolLM2-135M"
#   "EleutherAI/pythia-410m"
#   "HuggingFaceTB/SmolLM-135M"
#   "EleutherAI/pythia-410m-deduped"
#   "HuggingFaceTB/SmolLM-135M-Instruct"
#   "microsoft/deberta-v3-base"
#   "microsoft/mdeberta-v3-base"
#   "HuggingFaceTB/SmolLM2-135M-Instruct"
#   "HuggingFaceTB/SmolLM2-360M"
#   "HuggingFaceTB/SmolLM-360M-Instruct"
#   "HuggingFaceTB/SmolLM-360M"
#   "HuggingFaceTB/SmolLM2-360M-Instruct"
#   "answerdotai/ModernBERT-large"
#   "google/mobilebert-uncased"
#   "albert/albert-xlarge-v1"
#   "albert/albert-xlarge-v2"
#   "Qwen/Qwen1.5-0.5B"
#   "Qwen/Qwen1.5-0.5B-Chat"
#   "microsoft/deberta-v3-large"
#   "Qwen/Qwen2.5-Coder-0.5B"
#   "Qwen/Qwen2.5-0.5B-Instruct"
#   "Qwen/Qwen2.5-Coder-0.5B-Instruct"
#   "Qwen/Qwen2.5-0.5B"
#   "Qwen/Qwen2-0.5B-Instruct"
#   "Qwen/Qwen2-0.5B"
#   "albert/albert-xxlarge-v1"
#   "albert/albert-xxlarge-v2"
)

total=${#models[@]}
echo "================================================================"
echo "  Running $total models: 3-epoch finetune + epoch 1,2,3 inference"
echo "  Started: $(date)"
echo "================================================================"
echo ""

count=0
for model in "${models[@]}"; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')
    ft_log="$LOG_DIR/finetune_3ep_${model_safe}_seed42.log"

    echo "===== [$count/$total] $model  ($(date '+%H:%M:%S')) ====="

    # ── Step 1: Finetune 3 epochs ──────────────────────────────────────
    # Skip if already done (3 val sections in log)
    nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)
    if [ "$nval" -ge 3 ]; then
        echo "  Finetune: SKIP (already done, val=$nval)"
    else
        rm -f "$ft_log" 2>/dev/null
        echo "  Finetune: running..."

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

    # ── Step 2: Inference for epoch 1, 2, 3 ───────────────────────────
    weight_path="$WEIGHT_DIR/stats_time_lora_${model_safe}_b16_llm.pt"

    for epoch in 1 2 3; do
        ckpt_file="$CKPT_DIR/stats_time_lora_${model_safe}_b16_epoch${epoch}.pt"
        inf_log="$LOG_DIR/inference_ep${epoch}_${model_safe}_seed42.log"
        resultfile="$RESULT_DIR/inference_ep${epoch}_${model_safe}_seed42.csv"

        # Skip if result already exists
        if [ -f "$resultfile" ]; then
            echo "  Inference ep$epoch: SKIP (result exists)"
            continue
        fi

        if [ ! -f "$ckpt_file" ]; then
            echo "  Inference ep$epoch: SKIP (no checkpoint)"
            continue
        fi

        echo "  Inference ep$epoch: ($(date '+%H:%M:%S'))"

        # Extract LLM weights from checkpoint
        python -c "
import torch
ckpt = torch.load('$ckpt_file', map_location='cpu')
sd = ckpt['model_state_dict']
llm_sd = {k.replace('0.model.', ''): v for k, v in sd.items() if k.startswith('0.')}
torch.save(llm_sd, '$weight_path')
" 2>/dev/null

        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test  ../queryPlans/stats/postgres/ \
            --log_file "$inf_log" \
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

    # Clean up weight file (checkpoints are kept)
    rm -f "$weight_path" 2>/dev/null
    echo ""
    sleep 3
done

echo "================================================================"
echo "  ALL DONE: $(date)"
echo "================================================================"
