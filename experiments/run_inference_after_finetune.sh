#!/bin/bash
# Evaluate all models on the test set at 4 fidelity levels:
#   - Pretrained (0-epoch): --algo llm (no LoRA) — already in model_ground_truth.csv
#   - 1-epoch LoRA: load epoch1 checkpoint, inference + MLP
#   - 2-epoch LoRA: load epoch2 checkpoint, inference + MLP
#   - 3-epoch LoRA: load epoch3 checkpoint, inference + MLP
#
# For each epoch checkpoint, we:
#   1. Copy the checkpoint to the expected LoRA weight path
#   2. Run --algo llm --llm_pretrained lora (generates embeddings + trains MLP 100 epochs)
#   3. Evaluate on test set, save results
source ~/venvs/tmpenv/bin/activate
cd /root/LLM4QPR/experiments

CKPT_DIR="finetuned_models/postgres/checkpoints"
WEIGHT_DIR="finetuned_models/postgres"
RESULT_DIR="results/rank_stability"
LOG_DIR="logs/rank_stability"
mkdir -p "$RESULT_DIR"

# Get models with epoch3 checkpoints
models=$(python -c "
import glob, os, re
orgs = ['google', 'distilbert', 'EleutherAI', 'albert', 'nreimers',
        'sentence-transformers', 'FacebookAI', 'facebook', 'google-bert',
        'HuggingFaceTB', 'Qwen', 'microsoft', 'prajjwal1', 'Alibaba-NLP',
        'answerdotai', 'NousResearch', 'NeuML']
def to_model_name(model_safe):
    for org in sorted(orgs, key=len, reverse=True):
        prefix = org.replace('/', '-')
        if model_safe.startswith(prefix + '-'):
            return org + '/' + model_safe[len(prefix) + 1:]
    return model_safe.replace('-', '/', 1)

seen = set()
for f in sorted(glob.glob('$CKPT_DIR/stats_time_lora_*_epoch3.pt')):
    base = os.path.basename(f)
    # Extract model_safe from: stats_time_lora_{model_safe}_b16_epoch3.pt
    m = re.match(r'stats_time_lora_(.+?)_b\d+_epoch\d+\.pt', base)
    if m:
        model_safe = m.group(1)
        model = to_model_name(model_safe)
        if model not in seen:
            seen.add(model)
            print(model)
")

total=$(echo "$models" | grep -c .)
echo "Evaluating $total models x 3 epochs on test set at $(date)"
echo ""

count=0
for model in $models; do
    count=$((count + 1))
    model_safe=$(echo "$model" | tr '/' '-')
    weight_path="$WEIGHT_DIR/stats_time_lora_${model_safe}_b16_llm.pt"

    echo "===== [$count/$total] $model ====="

    for epoch in 1 2 3; do
        ckpt_file="$CKPT_DIR/stats_time_lora_${model_safe}_b16_epoch${epoch}.pt"

        if [ ! -f "$ckpt_file" ]; then
            echo "  epoch $epoch: SKIP (no checkpoint)"
            continue
        fi

        logfile="$LOG_DIR/inference_ep${epoch}_${model_safe}_seed42.log"
        resultfile="$RESULT_DIR/inference_ep${epoch}_${model_safe}_seed42.csv"

        echo "  epoch $epoch: ($(date '+%H:%M:%S'))"

        # Extract LLM state_dict from checkpoint and save as the LoRA weight file
        python -c "
import torch
ckpt = torch.load('$ckpt_file', map_location='cpu')
# The checkpoint has 'model_state_dict' which is the full Sequential(LLM, MLP)
# We need just the LLM part (keys starting with '0.')
sd = ckpt['model_state_dict']
llm_sd = {k.replace('0.model.', ''): v for k, v in sd.items() if k.startswith('0.')}
torch.save(llm_sd, '$weight_path')
" 2>/dev/null

        SKIP_HF_AUTH=1 \
        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test  ../queryPlans/stats/postgres/ \
            --log_file "$logfile" \
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

        rc=$?
        if [ $rc -eq 0 ] && [ -f "$resultfile" ]; then
            test_p90=$(python -c "
import pandas as pd
df = pd.read_csv('$resultfile')
row = df[df['percentage']==90.0]
if not row.empty: print(f'{row.iloc[0][\"Qerror\"]:.2f}')
else: print('N/A')
" 2>/dev/null)
            echo "    OK  test_p90=$test_p90"
        else
            echo "    FAIL rc=$rc"
        fi
    done

    # Clean up temp weight file
    rm -f "$weight_path" 2>/dev/null
    echo ""
    sleep 3
done

echo "ALL DONE  $(date)"
