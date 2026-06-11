#!/bin/bash
# Mode-1 (pretrained inference) for meta-llama/Llama-3.1-8B on postgres,
# LLM embedding-generation batch size 1 (EMBED_BATCH_SIZE=1): tpcds plans run
# up to ~24.5k tokens and Llama takes a whole plan as ONE sequence, so larger
# batches pad every plan in the batch to the longest one.
#
# Requires the CausalLM base-model forward optimization (utilsLLM
# _causal_base_model): measured 13.8 GiB peak at 24.5k tokens / batch 1 — fits
# the db3 5090 (32 GiB) with room, and even a 16 GiB 5080. Without it the
# legacy path (double forward + fp32 128k-vocab logits) needs ~35 GiB at that
# length and OOMs everywhere.
#
# Phase 1 — cost estimation (time): tpcds, tpch, stats, job (small first).
#   Generates the embedding caches; every cache stores BOTH labels
#   (costs = Actual Total Time, cards = Actual Rows), and the filename has no
#   task component, so these caches serve cardinality estimation too.
# Phase 2 — cardinality estimation (card): job, stats. Train caches
#   (imdb / stats) are HITS from phase 1; only the small _sub test files
#   (~760 + ~2700 plans) need a fresh LLM pass.
#
# Usage (db3, 5090 = GPU 0):
#   CUDA_VISIBLE_DEVICES=0 bash experiment_scripts/run_mode1_llama8b_postgres.sh \
#       2>&1 | tee /tmp/mode1_llama8b.log
#
# Afterwards, copy the caches back for local PRICE training (mode 8):
#   experiments/embeddings/postgres/embeddings_meta-llama-Llama-3.1-8B_*pretrained-None*.csv
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export EMBED_BATCH_SIZE="${EMBED_BATCH_SIZE:-1}"

MODEL="meta-llama/Llama-3.1-8B"
SEEDS="${SEEDS:-42}"

SHARED=(
    --models          "$MODEL"
    --downstream      "mlp"
    --quantification  "4-bit"
    --bucketize       "None"
    --embed_size      "1000"
    --concat_true     "false"
    --ft_batch_size   "24"
    --ft_num_epoch    "30"
    --removed_fields  ""
    --seeds           "$SEEDS"
    --db              "postgres"
    --finetune_mode   "1"
)

echo "=== Phase 1: mode 1, task=time (cost), EMBED_BATCH_SIZE=$EMBED_BATCH_SIZE ==="
for wl in tpcds tpch stats job; do
    echo ""
    echo "----- [time] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task time --workloads "$wl"
done

echo ""
echo "=== Phase 2: mode 1, task=card (cardinality) — job, stats ==="
for wl in job stats; do
    echo ""
    echo "----- [card] workload=$wl -----"
    bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task card --workloads "$wl"
done

echo ""
echo "All done. Embedding caches in embeddings/postgres/ :"
ls -la embeddings/postgres/ | grep "Llama-3.1-8B" || true
