#!/bin/bash
# Experiment: Compare pretrained vs 1-epoch JointPrice (mode 7) for 10 models.
# JointPrice = LLM + PRICE concatenation, no cross-attention.
source ~/venvs/tmpenv/bin/activate
cd /root/LLM4QPR/experiments
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export SKIP_HF_AUTH=1

models=(
  "google/bert_uncased_L-2_H-256_A-4"
  "distilbert/distilbert-base-multilingual-cased"
  "EleutherAI/pythia-70m"
  "sentence-transformers/paraphrase-albert-small-v2"
  "google/bert_uncased_L-6_H-768_A-12"
  "google/bert_uncased_L-8_H-128_A-2"
  "google/bert_uncased_L-10_H-768_A-12"
  "albert/albert-base-v1"
  "google/bert_uncased_L-12_H-128_A-2"
  "sentence-transformers/all-MiniLM-L12-v2"
)

LOG_DIR="logs/price_joint_experiment"
RESULT_DIR="results/price_joint_experiment"
mkdir -p "$LOG_DIR" "$RESULT_DIR"

total=${#models[@]}
echo "================================================================"
echo "  JointPrice (mode 7) experiment: $total models"
echo "  Started: $(date)"
echo "================================================================"
echo ""

count=0
for model in "${models[@]}"; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')

    echo "===== [$count/$total] $model  ($(date '+%H:%M:%S')) ====="

    # ── Step 1: JointPrice finetune (1 epoch) ──────────────────────────
    ft_log="$LOG_DIR/finetune_joint_${model_safe}_seed42.log"
    nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)

    if [ "$nval" -ge 1 ]; then
        echo "  Finetune: SKIP (val=$nval)"
    else
        rm -f "$ft_log" 2>/dev/null
        echo "  Finetune: JointPrice 1 epoch..."

        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test ../queryPlans/stats/postgres/ \
            --log_file "$ft_log" \
            --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm_price_finetune \
            --learning_rate 0.0001 \
            --price_lr 0.001 \
            --batch_size 16 --hid_units 2048 \
            --model_name "$model" \
            --train_ratio 1.0 --llm_mode lora --num_epoch 1 --seed 42 \
            --quantification 4-bit --max_queries 10000 \
            --price_s \
            --checkpoint_interval 1

        nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)
        if [ "$nval" -ge 1 ]; then
            echo "  Finetune: OK (val=$nval)"
        else
            echo "  Finetune: FAIL (val=$nval)"
            continue
        fi
    fi

    # ── Step 2: Inference with finetuned JointPrice weights ────────────
    resultfile="$RESULT_DIR/inference_joint_ep1_${model_safe}_seed42.csv"
    if [ -f "$resultfile" ]; then
        echo "  Inference: SKIP (result exists)"
    else
        echo "  Inference: running..."

        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test ../queryPlans/stats/postgres/ \
            --log_file "$LOG_DIR/inference_joint_${model_safe}_seed42.log" \
            --output_dir_qerror "$resultfile" \
            --output_dir_abs "$RESULT_DIR/inference_joint_ep1_${model_safe}_seed42_abs.txt" \
            --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm_price \
            --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
            --model_name "$model" \
            --embed_size 1000 \
            --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
            --llm_pretrained lora --llm_pretrained_task time \
            --seed 42 --ft_batch_size 16 --ft_num_epoch 1 \
            --quantification 4-bit \
            --max_queries 10000 \
            --price_s \
            --price_weights_source joint \
            --verbose_info --llm_downstream mlp

        if [ $? -eq 0 ] && [ -f "$resultfile" ]; then
            echo "  Inference: OK"
        else
            echo "  Inference: FAIL"
        fi
    fi

    echo ""
    sleep 3
done

echo "================================================================"
echo "  ALL DONE: $(date)"
echo "================================================================"
