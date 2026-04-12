#!/bin/bash
# Master experiment runner - Bidirectional Cross-Attention variant
# Mode 12 (BiCrossAttentionJoint) with PRICE_S and random init, 30 epochs, postgres
#
# Same setup as master_crossattn.sh (Mode 11) for direct comparison.
# Architecture: alternating single-direction layers
#   Layer 0: PRICE→LLM, Layer 1: LLM→PRICE, Layer 2: PRICE→LLM, Layer 3: LLM→PRICE
# Same params-per-layer as Mode 11, but LLM representations get refined too.

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
)

WORKLOADS=("stats" "job" "jobm")

MODES=(12)

for wl in "${WORKLOADS[@]}"; do
    for mode in "${MODES[@]}"; do
        echo ""
        echo "============================================================"
        echo "  Workload: $wl | Finetune mode: $mode (BiCrossAttentionJoint) | PRICE_S | Random Init | 30 epochs"
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
echo "All bidirectional cross-attention master experiments completed!"
