#!/bin/bash
# BiCrossAttn (Mode 12) + inflate_price: PRICE projected UP to LLM dim.
# 4 cross-attention layers (alternating PRICE→LLM / LLM→PRICE) at LLM dim.
# First 5 epochs: LLM frozen, odd layers skipped, PRICE lr=1e-3 warmup.
# After 5 epochs: joint finetuning LLM lr=1e-4, PRICE lr=2e-5.
# Output: concat(updated_LLM, updated_PRICE) at 2*LLM_dim.
# Checkpoint every 5 epochs.  30 epochs total.
# Then retrains MLP on the final converged embeddings.

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
    --ft_batch_size "24"
    --ft_num_epoch "30"
    --removed_fields ""
    --seeds "42 43 44"
    --db "postgres"
    --price_s
    --price_random_init
    --retrain_mlp
    --inflate_price
    --n_cross_layers "4"
    --checkpoint_interval "5"
    --freeze_llm_until_epoch "5"
    --price_warmup_epochs "5"
    --early_stop_patience "5"
    --early_stop_after_epoch "15"
)

WORKLOADS=("stats" "job" "jobm")

for wl in "${WORKLOADS[@]}"; do
    echo ""
    echo "============================================================"
    echo "  BiCrossAttn inflatePRICE cx4 | $wl | 30 ep | freeze_llm=5"
    echo "============================================================"

    bash "$RUN_SCRIPT" "${COMMON[@]}" \
        --workloads "$wl" \
        --finetune_mode "12" \
        --finetune_method "lora" \
        "$@"
done

echo ""
echo "All BiCrossAttn inflatePRICE cx4 experiments completed!"
