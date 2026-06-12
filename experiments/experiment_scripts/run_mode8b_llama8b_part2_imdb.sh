#!/bin/bash
# Mode 8b (frozen LLM + priceB) for meta-llama/Llama-3.1-8B on postgres — PART 2.
# Cells: time on job, syn, job_full; card on job, syn (job_full card excluded
# by design). job runs FIRST in each phase: the three workloads share the
# canonical imdb training cache and hence the same frozen-joint PRICE+MLP
# weights — job's run trains them once, syn/job_full auto-skip to inference.
#
# Requires the syn/job_full TEST caches from run_mode1_llama8b_synjobfull.sh.
# Intended for db3 (where those caches are generated), but runs anywhere the
# caches exist.
#
# Usage (db3):
#   CUDA_VISIBLE_DEVICES=0 bash experiment_scripts/run_mode8b_llama8b_part2_imdb.sh \
#       2>&1 | tee /tmp/mode8b_part2.log
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export EMBED_BATCH_SIZE="${EMBED_BATCH_SIZE:-1}"   # safety net for any cache miss

MODEL="meta-llama/Llama-3.1-8B"
SEEDS="${SEEDS:-42}"
FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"

SHARED=(
    --models          "$MODEL"
    --downstream      "mlp"
    --quantification  "4-bit"
    --bucketize       "None"
    --embed_size      "1000"
    --concat_true     "false"
    --ft_batch_size   "$FT_BATCH_SIZE"
    --ft_num_epoch    "$FT_NUM_EPOCH"
    --removed_fields  ""
    --seeds           "$SEEDS"
    --db              "postgres"
    --finetune_mode   "8"
    --price_b
    --price_random_init
)

echo "=== Part 2, phase A: mode 8b, task=time (job, syn, job_full) ==="
for wl in job syn job_full; do
    echo ""
    echo "----- [time] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task time --workloads "$wl"
done

echo ""
echo "=== Part 2, phase B: mode 8b, task=card (job, syn — NO job_full) ==="
for wl in job syn; do
    echo ""
    echo "----- [card] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task card --workloads "$wl"
done

echo ""
echo "mode 8b PART 2 done."
