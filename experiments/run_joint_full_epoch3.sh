#!/bin/bash
# Extend JointPrice 2-epoch models to 3 epochs.
# Resumes from epoch 2 checkpoints, trains 1 more epoch,
# then runs inference for epoch 3.
# Only processes models that have ep1+ep2 results but no ep3.
source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
cd "$(dirname "$0")"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export SKIP_HF_AUTH=1
export WINDOW_BATCH_SIZE=32

LOG_DIR="logs/joint_full_experiment"
RESULT_DIR="results/joint_full_experiment"
CKPT_DIR="finetuned_models/postgres/checkpoints"
WEIGHT_DIR="finetuned_models/postgres"
mkdir -p "$LOG_DIR" "$RESULT_DIR"

# All models from the 60+40 model experiments
models=(
  "google/bert_uncased_L-2_H-512_A-8"
  "sentence-transformers/multi-qa-distilbert-cos-v1"
  "distilbert/distilbert-base-cased"
  "distilbert/distilbert-base-multilingual-cased"
  "google/bert_uncased_L-4_H-768_A-12"
  "sentence-transformers/multi-qa-distilbert-dot-v1"
  "distilbert/distilroberta-base"
  "EleutherAI/pythia-70m"
  "EleutherAI/pythia-31m-deduped"
  "EleutherAI/pythia-14m"
  "EleutherAI/pythia-31m"
  "EleutherAI/pythia-14m-deduped"
  "EleutherAI/pythia-70m-deduped"
  "sentence-transformers/paraphrase-albert-small-v2"
  "google/bert_uncased_L-4_H-512_A-8"
  "google/bert_uncased_L-4_H-256_A-4"
  "distilbert/distilgpt2"
  "google/bert_uncased_L-6_H-256_A-4"
  "google/bert_uncased_L-6_H-768_A-12"
  "sentence-transformers/multi-qa-MiniLM-L6-dot-v1"
  "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
  "sentence-transformers/paraphrase-MiniLM-L6-v2"
  "sentence-transformers/paraphrase-TinyBERT-L6-v2"
  "google/bert_uncased_L-8_H-128_A-2"
  "google/bert_uncased_L-8_H-512_A-8"
  "google/bert_uncased_L-8_H-256_A-4"
  "nreimers/MiniLM-L6-H384-uncased"
  "google/bert_uncased_L-8_H-768_A-12"
  "google/bert_uncased_L-10_H-128_A-2"
  "google/bert_uncased_L-10_H-768_A-12"
  "google/bert_uncased_L-10_H-256_A-4"
  "google/bert_uncased_L-10_H-512_A-8"
  "FacebookAI/xlm-roberta-base"
  "FacebookAI/roberta-base"
  "facebook/opt-125m"
  "albert/albert-base-v1"
  "google/bert_uncased_L-12_H-256_A-4"
  "google-bert/bert-base-cased"
  "google/bert_uncased_L-12_H-512_A-8"
  "google/bert_uncased_L-12_H-768_A-12"
  "google-bert/bert-base-multilingual-cased"
  "google/bert_uncased_L-12_H-128_A-2"
  "EleutherAI/pythia-160m-deduped"
  "EleutherAI/pythia-160m"
  "google/electra-small-discriminator"
  "microsoft/MiniLM-L12-H384-uncased"
  "google/electra-small-generator"
  "google/electra-base-discriminator"
  "sentence-transformers/paraphrase-albert-base-v2"
  "albert/albert-base-v2"
  "google/electra-base-generator"
  "sentence-transformers/paraphrase-mpnet-base-v2"
  "sentence-transformers/all-mpnet-base-v2"
  "sentence-transformers/multi-qa-mpnet-base-cos-v1"
  "google-bert/bert-base-multilingual-uncased"
  "sentence-transformers/paraphrase-MiniLM-L12-v2"
  "google-bert/bert-base-uncased"
  "microsoft/deberta-v3-small"
  "microsoft/deberta-v3-xsmall"
  "google/electra-large-generator"
  "EleutherAI/pythia-410m"
  "sentence-transformers/all-MiniLM-L6-v2"
  "google/bert_uncased_L-2_H-128_A-2"
  "google/bert_uncased_L-2_H-256_A-4"
  "google/bert_uncased_L-2_H-768_A-12"
  "google/bert_uncased_L-4_H-128_A-2"
  "google/bert_uncased_L-6_H-128_A-2"
  "google/bert_uncased_L-6_H-512_A-8"
  "prajjwal1/bert-tiny"
  "prajjwal1/bert-mini"
  "prajjwal1/bert-small"
  "prajjwal1/bert-medium"
  "google/electra-large-discriminator"
  "google-bert/bert-large-uncased"
  "facebook/opt-350m"
  "albert/albert-large-v2"
  "sentence-transformers/all-MiniLM-L12-v2"
)

total=${#models[@]}
echo "================================================================"
echo "  JointPrice epoch 3 extension, up to $total models"
echo "  Started: $(date)"
echo "================================================================"
echo ""

count=0
skipped=0
done_count=0
failed=0

for model in "${models[@]}"; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')

    resultfile_ep3="$RESULT_DIR/inference_joint_full_ep3_${model_safe}_seed42.csv"
    ckpt2="$CKPT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_epoch2.pt"

    # Skip if ep3 result already exists
    if [ -f "$resultfile_ep3" ]; then
        echo "[$count/$total] $model — ep3 result exists, SKIP"
        skipped=$((skipped + 1))
        continue
    fi

    # Skip if no epoch 2 checkpoint
    if [ ! -f "$ckpt2" ]; then
        echo "[$count/$total] $model — no epoch 2 checkpoint, SKIP"
        skipped=$((skipped + 1))
        continue
    fi

    echo ""
    echo "===== [$count/$total] $model  ($(date '+%H:%M:%S')) ====="

    # ── Step 1: Resume from epoch 2, train 1 more epoch ───────────────
    ckpt3="$CKPT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_epoch3.pt"
    ft_log="$LOG_DIR/finetune_joint_full_ep3_${model_safe}_seed42.log"

    if [ -f "$ckpt3" ]; then
        echo "  Finetune: SKIP (epoch 3 checkpoint exists)"
    else
        echo "  Finetune: resuming from epoch 2 → epoch 3..."
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test ../queryPlans/stats/postgres/ \
            --log_file "$ft_log" --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm_price_finetune \
            --learning_rate 0.0001 --price_lr 0.001 \
            --batch_size 32 --hid_units 2048 \
            --model_name "$model" \
            --train_ratio 1.0 --llm_mode lora --num_epoch 3 --seed 42 \
            --quantification 4-bit --price_s --checkpoint_interval 1

        if [ -f "$ckpt3" ]; then
            echo "  epoch 3 ckpt: OK"
        else
            echo "  epoch 3 ckpt: MISSING — FAILED"
            failed=$((failed + 1))
            continue
        fi
    fi

    # ── Step 2: Extract weights and run inference for epoch 3 ─────────
    echo "  Inference ep3: ($(date '+%H:%M:%S'))"

    base="$WEIGHT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_e3"
    python -c "
import torch
sd = torch.load('$ckpt3', map_location='cpu')['model_state_dict']
torch.save({k.replace('llm.model.', ''): v for k, v in sd.items() if k.startswith('llm.')}, '${base}_llm.pt')
torch.save({k.replace('price.', ''): v for k, v in sd.items() if k.startswith('price.')}, '${base}_price.pt')
torch.save({k.replace('mlp.', ''): v for k, v in sd.items() if k.startswith('mlp.')}, '${base}_mlp.pt')
"

    python -u train.py \
        --dat_paths_train ../queryPlans/stats/postgres/ \
        --dat_path_test ../queryPlans/stats/postgres/ \
        --log_file "$LOG_DIR/inference_joint_full_ep3_${model_safe}_seed42.log" \
        --output_dir_qerror "$resultfile_ep3" \
        --output_dir_abs "$RESULT_DIR/inference_joint_full_ep3_${model_safe}_seed42_abs.txt" \
        --db postgres --workloads_train stats --workload_test stats \
        --algo llm_price --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
        --model_name "$model" --embed_size 1000 \
        --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
        --llm_pretrained lora --llm_pretrained_task time \
        --seed 42 --ft_batch_size 32 --ft_num_epoch 3 \
        --quantification 4-bit --price_s \
        --price_weights_source joint --verbose_info --llm_downstream mlp

    if [ $? -eq 0 ] && [ -f "$resultfile_ep3" ]; then
        echo "    OK"
        done_count=$((done_count + 1))
    else
        echo "    FAIL"
        failed=$((failed + 1))
    fi

    # Cleanup extracted weights (checkpoints stay)
    rm -f "${base}_llm.pt" "${base}_price.pt" "${base}_mlp.pt" 2>/dev/null

    sleep 3
done

echo ""
echo "================================================================"
echo "  DONE: $done_count succeeded, $skipped skipped, $failed failed"
echo "  Finished: $(date)"
echo "================================================================"
