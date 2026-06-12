#!/bin/bash
# Mode 8b for meta-llama/Llama-3.1-8B on postgres: frozen-LLM concat finetune
# with the original PRICE_B encoding (--price_b --price_random_init) — the
# frozen analog of mode 7b. The LLM is never forwarded: PRICE+MLP train on the
# pooled-embedding caches generated on db3 (mode-1 pretrained-None caches,
# already present locally for every cell below; both labels stored per cache).
#
# Cells (= every cell with an existing embedding cache):
#   Phase 1 — cost (time): tpcds, tpch, stats, job, syn, job_full
#   Phase 2 — cardinality (card): job, stats, syn, job_full
# job runs BEFORE syn/job_full in each phase: the three share the canonical
# imdb training cache and hence the same frozen-joint PRICE+MLP weights —
# job's run trains them once, syn/job_full auto-skip to inference.
# Requires the syn/job_full TEST caches (run_mode1_llama8b_synjobfull.sh on db3).
#
# Training is PRICE+MLP only (no LLM in memory) — runs fine on the local 5080.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=1 bash experiment_scripts/run_mode8b_llama8b_postgres.sh \
#       2>&1 | tee /tmp/mode8b_llama8b.log
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source ~/venvs/tmpenv/bin/activate 2>/dev/null || source ~/venvs/py312/bin/activate 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

MODEL="meta-llama/Llama-3.1-8B"
SEEDS="${SEEDS:-42}"
FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"   # no LLM in the model => no OOM guard needed for tpch/tpcds

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

echo "=== Phase 1: mode 8b (frozen LLM + priceB), task=time ==="
for wl in tpcds tpch stats job syn job_full; do
    echo ""
    echo "----- [time] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task time --workloads "$wl"
done

echo ""
echo "=== Phase 2: mode 8b (frozen LLM + priceB), task=card ==="
for wl in job stats syn job_full; do
    echo ""
    echo "----- [card] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task card --workloads "$wl"
done

echo ""
echo "mode 8b done. Results:"
ls results/postgres/results_Train_*_ours/*priceFTwithLLM*Llama-3.1-8B*priceB* 2>/dev/null || true
ls results/postgres/results_Train_*_ours/card_*priceFTwithLLM*Llama-3.1-8B*priceB* 2>/dev/null || true
