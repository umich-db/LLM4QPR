#!/bin/bash
# Simple sequential finetune: one model at a time, no parallelism.
source ~/venvs/tmpenv/bin/activate
cd /root/LLM4QPR/experiments

total=$(wc -l < /tmp/remaining_models.txt)
count=0

while IFS= read -r model; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')
    logfile="logs/rank_stability/finetune_${model_safe}_seed42.log"

    rm -f "$logfile" 2>/dev/null

    echo "[$count/$total] $model  ($(date '+%H:%M:%S'))"

    SKIP_HF_AUTH=1 HF_HUB_OFFLINE=1 \
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    python -u train.py \
        --dat_paths_train ../queryPlans/stats/postgres/ \
        --dat_path_test  ../queryPlans/stats/postgres/ \
        --log_file "$logfile" \
        --db postgres \
        --workloads_train stats --workload_test stats \
        --algo llm_finetune \
        --learning_rate 0.0001 --batch_size 16 --hid_units 2048 \
        --model_name "$model" \
        --train_ratio 1.0 --llm_mode lora --num_epoch 2 --seed 42 \
        --quantification 4-bit --max_queries 10000 --embed_size 1000 \
        --checkpoint_interval 1 \
        >/dev/null 2>&1

    rc=$?
    nval=$(grep -c 'Data section: val' "$logfile" 2>/dev/null || echo 0)

    if [ "$rc" -eq 0 ] && [ "$nval" -ge 2 ]; then
        echo "  OK  (val=$nval)"
    else
        echo "  FAIL rc=$rc val=$nval"
    fi

    # Keep finetuned weights and checkpoints for future epoch extension
    sleep 3
done < /tmp/remaining_models.txt

echo "ALL DONE  $(date)"
