#!/bin/bash
# RetrainMLP for Cross-Attention (Mode 11, 2 layers — default)
# Reuses finetuned weights, retrains only the MLP head.

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
)

WORKLOADS=("stats" "job" "jobm")

for wl in "${WORKLOADS[@]}"; do
    echo ""
    echo "============================================================"
    echo "  RetrainMLP | Workload: $wl | CrossAttn (Mode 11, 2 layers) | 30 epochs"
    echo "============================================================"

    bash "$RUN_SCRIPT" "${COMMON[@]}" \
        --workloads "$wl" \
        --finetune_mode "11" \
        --finetune_method "lora" \
        "$@"
done

echo ""
echo "All CrossAttn retrainMLP experiments completed!"
