#!/bin/bash
# Backfill the syn / job_full embedding caches for meta-llama/Llama-3.1-8B on
# postgres (both tasks), batch 1. The imdb TRAINING cache already exists from
# run_mode1_llama8b_postgres.sh — these runs only embed the four missing TEST
# files (imdb_syn 5k, imdb_job_full 113, imdb_syn_sub 15.7k,
# imdb_job_full_sub_selected 10k ≈ 31k queries total) and emit the mode-1
# results for the four cells.
#
# Usage (db3):
#   CUDA_VISIBLE_DEVICES=0 bash experiment_scripts/run_mode1_llama8b_synjobfull.sh \
#       2>&1 | tee /tmp/mode1_llama8b_sjf.log
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

for task in time card; do
    for wl in syn job_full; do
        echo ""
        echo "----- [$task] workload=$wl -----"
        bash "$SCRIPT_DIR/run_different_llms.sh" "${SHARED[@]}" --task "$task" --workloads "$wl"
    done
done

echo ""
echo "Backfill done. syn/job_full caches:"
ls -la embeddings/postgres/ | grep "Llama-3.1-8B" | grep -E "syn|job_full" || true
