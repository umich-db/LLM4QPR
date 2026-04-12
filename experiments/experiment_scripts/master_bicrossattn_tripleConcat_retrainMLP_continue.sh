#!/bin/bash
# Continue tripleConcat training from epoch 30 to 60.
# Auto-resumes from existing epoch 30 checkpoints.
# Uses early stopping (patience 5, after epoch 10) to avoid waste.
# Retrains MLP on the final converged embeddings.

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
    --ft_num_epoch "60"
    --removed_fields ""
    --seeds "42 43 44"
    --db "postgres"
    --price_s
    --price_random_init
    --retrain_mlp
    --triple_concat
    --n_cross_layers "4"
    --checkpoint_interval "5"
    --early_stop_patience "5"
    --early_stop_after_epoch "30"
)

WORKLOADS=("stats" "job" "jobm")

for wl in "${WORKLOADS[@]}"; do
    echo ""
    echo "============================================================"
    echo "  Continue tripleConcat | $wl | epoch 30→60 | early_stop=5"
    echo "============================================================"

    bash "$RUN_SCRIPT" "${COMMON[@]}" \
        --workloads "$wl" \
        --finetune_mode "12" \
        --finetune_method "lora" \
        "$@"
done

echo ""
echo "All tripleConcat continuation experiments completed!"
