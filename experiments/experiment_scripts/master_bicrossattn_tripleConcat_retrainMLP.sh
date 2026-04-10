#!/bin/bash
# BiCrossAttn with Triple Concatenation + RetrainMLP
# Concatenates: original LLM + refined LLM (256) + PRICE (512)
# Trains from scratch (randInit), then retrains MLP on frozen embeddings.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

COMMON=(
    --models "sentence-transformers/all-MiniLM-L6-v2"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --ft_batch_size "32"
    --ft_num_epoch "30"
    --removed_fields ""
    --seeds "42 43 44"
    --db "postgres"
    --price_s
    --price_random_init
    --retrain_mlp
    --triple_concat
    --n_cross_layers "4"
    --checkpoint_interval "5"
    --early_stop_patience "3"
    --early_stop_after_epoch "10"
)

WORKLOADS=("stats" "job" "jobm")

for wl in "${WORKLOADS[@]}"; do
    echo ""
    echo "============================================================"
    echo "  RetrainMLP | Workload: $wl | BiCrossAttn+TripleConcat cx4 | 30 epochs"
    echo "============================================================"

    bash "$RUN_SCRIPT" "${COMMON[@]}" \
        --workloads "$wl" \
        --finetune_mode "12" \
        --finetune_method "lora" \
        "$@"
done

echo ""
echo "All BiCrossAttn+TripleConcat retrainMLP experiments completed!"
