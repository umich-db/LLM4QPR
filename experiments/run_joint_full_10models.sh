#!/bin/bash
# JointPrice (mode 7) on full training set, 2 epochs, 10 models.
# Collects val metrics at each epoch + test inference for epoch 1 and 2.
source ~/venvs/tmpenv/bin/activate
cd /root/LLM4QPR/experiments
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export SKIP_HF_AUTH=1

models=(
  "google/bert_uncased_L-2_H-128_A-2"
  "distilbert/distilbert-base-uncased"
  "google/bert_uncased_L-6_H-512_A-8"
  "sentence-transformers/all-MiniLM-L12-v2"
  "answerdotai/ModernBERT-base"
  "EleutherAI/pythia-410m"
  "HuggingFaceTB/SmolLM2-360M"
  "Qwen/Qwen1.5-0.5B"
  "Qwen/Qwen2.5-0.5B-Instruct"
  "Qwen/Qwen2-0.5B-Instruct"
)

LOG_DIR="logs/joint_full_experiment"
RESULT_DIR="results/joint_full_experiment"
CKPT_DIR="finetuned_models/postgres/checkpoints"
WEIGHT_DIR="finetuned_models/postgres"
mkdir -p "$LOG_DIR" "$RESULT_DIR"

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

    # ── Step 1: JointPrice finetune 2 epochs ───────────────────────────
    nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)
    if [ "$nval" -ge 2 ]; then
        echo "  Finetune: SKIP (val=$nval)"
    else
        rm -f "$ft_log" 2>/dev/null
        echo "  Finetune: JointPrice 2 epochs (full workload)..."

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
            --train_ratio 1.0 --llm_mode lora --num_epoch 2 --seed 42 \
            --quantification 4-bit \
            --price_s \
            --checkpoint_interval 1

        nval=$(grep -c 'Data section: val' "$ft_log" 2>/dev/null || echo 0)
        if [ "$nval" -ge 2 ]; then
            echo "  Finetune: OK (val=$nval)"
        else
            echo "  Finetune: FAIL (val=$nval)"
            continue
        fi
    fi

    # ── Step 2: Inference for epoch 1 and 2 ────────────────────────────
    for epoch in 1 2; do
        # Find checkpoint (could be b16 prefix)
        ckpt_file="$CKPT_DIR/stats_time_lora_${model_safe}_b16_priceS_llm_price_epoch${epoch}.pt"
        resultfile="$RESULT_DIR/inference_joint_full_ep${epoch}_${model_safe}_seed42.csv"

        if [ -f "$resultfile" ]; then
            echo "  Inference ep$epoch: SKIP (result exists)"
            continue
        fi
        if [ ! -f "$ckpt_file" ]; then
            echo "  Inference ep$epoch: NO CKPT ($ckpt_file)"
            continue
        fi

        echo "  Inference ep$epoch: ($(date '+%H:%M:%S'))"

        # Extract LLM weights from checkpoint
        weight_path="$WEIGHT_DIR/stats_time_lora_${model_safe}_b16_priceS_llm_price_e${epoch}_llm.pt"
        python -c "
import torch
ckpt = torch.load('$ckpt_file', map_location='cpu')
sd = ckpt['model_state_dict']
# LLM keys start with '0.model.' in the Sequential
llm_sd = {k.replace('0.model.', ''): v for k, v in sd.items() if k.startswith('0.')}
torch.save(llm_sd, '$weight_path')
print(f'Extracted {len(llm_sd)} LLM keys')
" 2>/dev/null

        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \
        python -u train.py \
            --dat_paths_train ../queryPlans/stats/postgres/ \
            --dat_path_test ../queryPlans/stats/postgres/ \
            --log_file "$LOG_DIR/inference_joint_full_ep${epoch}_${model_safe}_seed42.log" \
            --output_dir_qerror "$resultfile" \
            --output_dir_abs "$RESULT_DIR/inference_joint_full_ep${epoch}_${model_safe}_seed42_abs.txt" \
            --db postgres \
            --workloads_train stats --workload_test stats \
            --algo llm_price \
            --learning_rate 0.0001 --batch_size 64 --hid_units 2048 \
            --model_name "$model" \
            --embed_size 1000 \
            --train_ratio 1.0 --llm_mode inference --num_epoch 100 \
            --llm_pretrained lora --llm_pretrained_task time \
            --seed 42 --ft_batch_size 16 --ft_num_epoch $epoch \
            --quantification 4-bit \
            --price_s \
            --price_weights_source joint \
            --verbose_info --llm_downstream mlp

        if [ $? -eq 0 ] && [ -f "$resultfile" ]; then
            echo "    OK"
        else
            echo "    FAIL"
        fi
    done

    echo ""
    sleep 3
done

echo "================================================================"
echo "  ALL DONE: $(date)"
echo "================================================================"

# ── Comparison ─────────────────────────────────────────────────────────
python -c "
import pandas as pd, numpy as np, os, re, glob
from scipy.stats import spearmanr

gt = pd.read_csv('/root/LLM4QPR/model_selection/model_ground_truth.csv')
gt_lookup = dict(zip(gt['model'], gt['p90_qerror']))

models = [
    'google/bert_uncased_L-2_H-128_A-2',
    'distilbert/distilbert-base-uncased',
    'google/bert_uncased_L-6_H-512_A-8',
    'sentence-transformers/all-MiniLM-L12-v2',
    'answerdotai/ModernBERT-base',
    'EleutherAI/pythia-410m',
    'HuggingFaceTB/SmolLM2-360M',
    'Qwen/Qwen1.5-0.5B',
    'Qwen/Qwen2.5-0.5B-Instruct',
    'Qwen/Qwen2-0.5B-Instruct',
]

def read_p90(filepath):
    if not os.path.exists(filepath): return np.nan
    df = pd.read_csv(filepath)
    if 'q_error' in df.columns: return np.percentile(df['q_error'], 90)
    if 'percentage' in df.columns:
        row = df[(df['percentage'] - 90.0).abs() < 0.1]
        return row['Qerror'].values[0] if len(row) > 0 else np.nan
    return np.percentile(df.iloc[:,1], 90)

def parse_val_p90(logpath):
    current_epoch = 0; current_section = None; val_p90s = {}
    if not os.path.exists(logpath): return val_p90s
    with open(logpath) as f:
        for line in f:
            em = re.search(r'Epoch (\d+) Batch', line)
            if em: current_epoch = int(em.group(1))
            if 'Data section: train' in line: current_section = 'train'
            elif 'Data section: val' in line: current_section = 'val'
            pm = re.search(r'90th percentile:\s*([\d.]+)', line)
            if pm and current_section == 'val':
                val_p90s[current_epoch] = float(pm.group(1))
    return val_p90s

rows = []
for m in models:
    ms = m.replace('/', '-')
    val_p90s = parse_val_p90(f'$LOG_DIR/finetune_joint_full_{ms}_seed42.log')
    rows.append({
        'model': m.split('/')[-1],
        'pretrained': round(gt_lookup.get(m, np.nan), 1),
        'val_ep1': round(val_p90s.get(0, np.nan), 2),
        'val_ep2': round(val_p90s.get(1, np.nan), 2),
        'test_ep1': round(read_p90(f'$RESULT_DIR/inference_joint_full_ep1_{ms}_seed42.csv'), 1),
        'test_ep2': round(read_p90(f'$RESULT_DIR/inference_joint_full_ep2_{ms}_seed42.csv'), 1),
    })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
print()

valid = df.dropna()
if len(valid) >= 3:
    for c1, c2, label in [
        ('pretrained', 'test_ep1', 'Pre vs Test ep1'),
        ('pretrained', 'test_ep2', 'Pre vs Test ep2'),
        ('val_ep1', 'test_ep2', 'Val ep1 vs Test ep2'),
        ('val_ep1', 'val_ep2', 'Val ep1 vs Val ep2'),
        ('test_ep1', 'test_ep2', 'Test ep1 vs Test ep2'),
    ]:
        v = valid.dropna(subset=[c1, c2])
        if len(v) >= 3:
            rho, p = spearmanr(v[c1], v[c2])
            sig = '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else ''
            print(f'  {label:25s}: rho={rho:+.3f} p={p:.4f} {sig}  n={len(v)}')
"
