#!/bin/bash
# Extend finetuning to 3 epochs for models that already have 2-epoch results.
# - If a 2-epoch checkpoint exists: resumes and trains 1 more epoch
# - If no checkpoint exists: trains from scratch for 3 epochs
# Saves checkpoints at every epoch so future extensions are possible.
source ~/venvs/tmpenv/bin/activate
cd /root/LLM4QPR/experiments

# Get models that have completed 2 epochs (2 val sections in their logs)
models=$(python -c "
import glob, os, re
orgs = ['google', 'distilbert', 'EleutherAI', 'albert', 'nreimers',
        'sentence-transformers', 'FacebookAI', 'facebook', 'google-bert',
        'HuggingFaceTB', 'Qwen', 'microsoft', 'prajjwal1', 'Alibaba-NLP',
        'answerdotai', 'NousResearch', 'NeuML']
def extract_model_name(logpath):
    base = os.path.basename(logpath)
    m = re.match(r'finetune_(.+?)_seed\d+\.log', base)
    if not m: return None
    raw = m.group(1)
    for org in sorted(orgs, key=len, reverse=True):
        prefix = org.replace('/', '-')
        if raw.startswith(prefix + '-'):
            return org + '/' + raw[len(prefix) + 1:]
    return raw.replace('-', '/', 1)
for f in sorted(glob.glob('/root/LLM4QPR/experiments/logs/rank_stability/finetune_*_seed42.log')):
    with open(f) as fh: content = fh.read()
    if content.count('Data section: val') >= 2:
        model = extract_model_name(f)
        if model: print(model)
")

total=$(echo "$models" | wc -l)
echo "Running $total models for epoch 3 at $(date)"

count=0
for model in $models; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')
    logfile="logs/rank_stability/finetune_3ep_${model_safe}_seed42.log"

    echo "[$count/$total] $model  ($(date '+%H:%M:%S'))"

    SKIP_HF_AUTH=1 \
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
        --train_ratio 1.0 --llm_mode lora --num_epoch 3 --seed 42 \
        --quantification 4-bit --max_queries 10000 --embed_size 1000 \
        --checkpoint_interval 1

    rc=$?
    nval=$(grep -c 'Data section: val' "$logfile" 2>/dev/null || echo 0)

    if [ "$rc" -eq 0 ] && [ "$nval" -ge 3 ]; then
        echo "  OK  (val=$nval)"
    else
        echo "  FAIL rc=$rc val=$nval"
    fi

    # Keep checkpoints for future use, only delete the final merged weights
    rm -f "finetuned_models/postgres/stats_time_lora_${model_safe}_b16_llm.pt" 2>/dev/null
    sleep 3
done

echo "ALL DONE  $(date)"
