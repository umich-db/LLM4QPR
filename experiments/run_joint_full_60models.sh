#!/bin/bash
# JointPrice mode 7 on full STATS workload, 2 epochs, 60 small models.
# Saves per-epoch checkpoints for future ep3 extension.
# Collects val metrics + test inference for epoch 1 and 2.
source ~/venvs/tmpenv/bin/activate
cd /root/LLM4QPR/experiments
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export SKIP_HF_AUTH=1
export WINDOW_BATCH_SIZE=32

LOG_DIR="logs/joint_full_experiment"
RESULT_DIR="results/joint_full_experiment"
CKPT_DIR="finetuned_models/postgres/checkpoints"
WEIGHT_DIR="finetuned_models/postgres"
mkdir -p "$LOG_DIR" "$RESULT_DIR"

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
)

total=${#models[@]}
echo "================================================================"
echo "  JointPrice full workload, 2 epochs, $total models"
echo "  Started: $(date)"
echo "================================================================"
echo ""

count=0
for model in "${models[@]}"; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')
    ft_log="$LOG_DIR/finetune_joint_full_${model_safe}_seed42.log"

    echo "===== [$count/$total] $model  ($(date '+%H:%M:%S')) ====="

    # ── Step 1: Finetune 2 epochs ──────────────────────────────────────
    ckpt2="$CKPT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_epoch2.pt"
    if [ -f "$ckpt2" ]; then
        echo "  Finetune: SKIP (epoch 2 checkpoint exists)"
    else
        rm -f "$ft_log" "$CKPT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_epoch"*.pt 2>/dev/null
        echo "  Finetune: b32, 2 epochs..."
        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test ../queryPlans/stats/postgres/ \
            --log_file "$ft_log" --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm_price_finetune \
            --learning_rate 0.0001 --price_lr 0.001 \
            --batch_size 32 --hid_units 2048 \
            --model_name "$model" \
            --train_ratio 1.0 --llm_mode lora --num_epoch 2 --seed 42 \
            --quantification 4-bit --price_s --checkpoint_interval 1

        ckpt1="$CKPT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_epoch1.pt"
        [ -f "$ckpt1" ] && echo "  epoch 1 ckpt: OK" || echo "  epoch 1 ckpt: MISSING"
        [ -f "$ckpt2" ] && echo "  epoch 2 ckpt: OK" || echo "  epoch 2 ckpt: MISSING"
    fi

    # ── Step 2: Extract weights and run inference ──────────────────────
    for epoch in 1 2; do
        ckpt="$CKPT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_epoch${epoch}.pt"
        resultfile="$RESULT_DIR/inference_joint_full_ep${epoch}_${model_safe}_seed42.csv"
        [ -f "$resultfile" ] && echo "  Inference ep$epoch: SKIP" && continue
        [ ! -f "$ckpt" ] && echo "  Inference ep$epoch: NO CKPT" && continue

        echo "  Inference ep$epoch: ($(date '+%H:%M:%S'))"

        # Extract LLM + PRICE + MLP weights
        base="$WEIGHT_DIR/stats_time_lora_${model_safe}_b32_priceS_llm_price_e${epoch}"
        python -c "
import torch
sd = torch.load('$ckpt', map_location='cpu')['model_state_dict']
torch.save({k.replace('llm.model.', ''): v for k, v in sd.items() if k.startswith('llm.')}, '${base}_llm.pt')
torch.save({k.replace('price.', ''): v for k, v in sd.items() if k.startswith('price.')}, '${base}_price.pt')
torch.save({k.replace('mlp.', ''): v for k, v in sd.items() if k.startswith('mlp.')}, '${base}_mlp.pt')
"
        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test ../queryPlans/stats/postgres/ \
            --log_file "$LOG_DIR/inference_joint_full_ep${epoch}_${model_safe}_seed42.log" \
            --output_dir_qerror "$resultfile" \
            --output_dir_abs "$RESULT_DIR/inference_joint_full_ep${epoch}_${model_safe}_seed42_abs.txt" \
            --db postgres --workloads_train stats --workload_test stats \
            --algo llm_price --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
            --model_name "$model" --embed_size 1000 \
            --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
            --llm_pretrained lora --llm_pretrained_task time \
            --seed 42 --ft_batch_size 32 --ft_num_epoch $epoch \
            --quantification 4-bit --price_s \
            --price_weights_source joint --verbose_info --llm_downstream mlp

        if [ $? -eq 0 ] && [ -f "$resultfile" ]; then
            echo "    OK"
        else
            echo "    FAIL"
        fi

        # Cleanup extracted weights (checkpoints stay for future ep3)
        rm -f "${base}_llm.pt" "${base}_price.pt" "${base}_mlp.pt" 2>/dev/null
    done

    echo ""
    sleep 3
done

echo "================================================================"
echo "  ALL DONE: $(date)"
echo "================================================================"
