#!/bin/bash
# Mode 8b (frozen LLM + priceB) for meta-llama/Llama-3.1-8B on postgres — PART 1.
# Cells: time on tpch, tpcds, stats; card on stats.
# (tpch/tpcds have no cardinality task in this codebase: utilsTrain only
#  supports card for syn/job/job_full/stats, and no card plan files exist.)
# All embedding caches for these cells are already local — runs on the 5080.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=1 bash experiment_scripts/run_mode8b_llama8b_part1_tpc_stats.sh \
#       2>&1 | tee /tmp/mode8b_part1.log
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source ~/venvs/tmpenv/bin/activate 2>/dev/null || source ~/venvs/py312/bin/activate 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
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

echo "=== Part 1, phase A: mode 8b, task=time (tpch, tpcds, stats) ==="
for wl in tpch tpcds stats; do
    echo ""
    echo "----- [time] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task time --workloads "$wl"
done

echo ""
echo "=== Part 1, phase B: mode 8b, task=card (stats) ==="
echo "----- [card] workload=stats -----"
bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task card --workloads stats

echo ""
echo "mode 8b PART 1 done."
