#!/bin/bash
# CrossAttn (Mode 11) with moderate PRICE reduction: 3 layers, FFN ratio 2.
# 4 cross-attention layers.
# First 5 epochs: LLM frozen, PRICE lr=1e-3 (random init warmup).
# After 5 epochs: joint finetuning LLM lr=1e-4, PRICE lr=2e-5.
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
    --n_cross_layers "4"
    --price_n_layers "3"
    --price_ffn_ratio "2"
    --checkpoint_interval "5"
    --freeze_llm_until_epoch "5"
    --price_warmup_epochs "5"
    --early_stop_patience "5"
    --early_stop_after_epoch "5"
)

WORKLOADS=("stats" "job" "jobm")

for wl in "${WORKLOADS[@]}"; do
    echo ""
    echo "============================================================"
    echo "  CrossAttn cx4 pL3 ffn2 | $wl | 30 epochs | freeze_llm=5"
    echo "============================================================"

    bash "$RUN_SCRIPT" "${COMMON[@]}" \
        --workloads "$wl" \
        --finetune_mode "11" \
        --finetune_method "lora" \
        "$@"
done

echo ""
echo "All CrossAttn cx4 pL3 ffn2 experiments completed!"
