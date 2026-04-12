#!/bin/bash
# Master experiment runner - Bidirectional Cross-Attention with Refined LLM Pooling
# Mode 12 (BiCrossAttentionJoint) with PRICE_S, random init, refined_pool, 30 epochs, postgres
#
# Same as master_bicrossattn.sh but with --refined_pool:
# Instead of using the original pooled LLM embedding, mean-pools the
# cross-attention-refined LLM tokens and projects 256→1000.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

# Common flags shared by all runs
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
    --checkpoint_interval "5"
    --n_cross_layers "4"
    --refined_pool
)

WORKLOADS=("stats" "job" "jobm")

MODES=(12)

for wl in "${WORKLOADS[@]}"; do
    for mode in "${MODES[@]}"; do
        echo ""
        echo "============================================================"
        echo "  Workload: $wl | Finetune mode: $mode (BiCrossAttn+RefinedPool) | PRICE_S | Random Init | 30 epochs"
        echo "============================================================"

        MODE_ARGS=(--finetune_mode "$mode")

        # Mode 12 finetunes the LLM
        MODE_ARGS+=(--finetune_method "lora")

        bash "$RUN_SCRIPT" "${COMMON[@]}" \
            --workloads "$wl" \
            "${MODE_ARGS[@]}" \
            "$@"
    done
done

echo ""
echo "All BiCrossAttn+RefinedPool master experiments completed!"
