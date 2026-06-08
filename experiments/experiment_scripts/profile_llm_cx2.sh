#!/bin/bash
# Profile mode-12 LLM (bert2 / bert4 / sentBert) training + inference time at
# n_cross_layers = 2 AND 4 on ONE system (default postgres), to get the real
# 2-block cost and a clean cx2/cx4 ratio.
#
# Why both cx2 and cx4 here (not reuse the old cx4 ablation): we want the ratio
# from the SAME harness/config (only block count differs), so it cleanly scales
# the OTHER engines' existing cx4 numbers:  cx2_other ~= cx4_other * (cx2/cx4)_pg.
#
# Methodology mirrors the cx4 ablation: tr0.1, 1 epoch (epoch-0, frozen-LLM
# warmup), no checkpoints. Per run the log carries:
#   training  : "Epoch: 0  Avg Loss: ..., Time: <sec>"   (per-epoch, on 10% data)
#   inference : "[Test] Total evaluation time — <ms>" + "[Test] Batch N"  (batch=1)
#
# Output -> logs/<db>/logs_Train_<wl>_Test_<wl>_ours/cx_profile/
#           filenames contain "_cx2_" / "_cx4_" so the two are distinguishable.
#
# Run on the H100:
#   DB=postgres CUDA_VISIBLE_DEVICES=0 \
#     bash experiment_scripts/profile_llm_cx2.sh 2>&1 | tee /tmp/cx2_profile.log
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
cd "$SCRIPT_DIR/.."   # -> experiments/
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

DB="${DB:-postgres}"
CX_LIST="${CX_LIST:-2 4}"
MODELS="google/bert_uncased_L-2_H-256_A-4,google/bert_uncased_L-4_H-768_A-12,sentence-transformers/all-MiniLM-L12-v2"
WORKLOADS="stats,tpch,tpcds,job,job_full,syn"   # comma-separated (run_different_llms splits on commas); train: stats/tpch/tpcds/job(imdb), test: all 6

for cx in $CX_LIST; do
    echo ""
    echo "############################################################"
    echo "  LLM time profile | DB=$DB | n_cross_layers=$cx | tr0.1 e1"
    echo "############################################################"
    TRAIN_RATIO=0.1 FT_BATCH_SIZE=16 FT_NUM_EPOCH=1 \
    bash experiment_scripts/run_different_llms.sh \
        --models "$MODELS" --task time --downstream mlp --quantification 4-bit \
        --bucketize None --embed_size 1000 --concat_true false \
        --ft_batch_size 16 --ft_num_epoch 1 --removed_fields "" --seeds 42 --db "$DB" \
        --price_s --price_random_init --inflate_price --n_cross_layers "$cx" \
        --checkpoint_interval 0 --freeze_llm_until_epoch 4 --price_warmup_epochs 4 \
        --subdir_tag cx_profile --workloads "$WORKLOADS" \
        --finetune_mode 12 --finetune_method lora
done

echo ""
echo "Done. Logs in:  logs/${DB}/logs_Train_*_Test_*_ours/cx_profile/"
echo "Send back that cx_profile/ tree (the *.log files) to regenerate the table."
