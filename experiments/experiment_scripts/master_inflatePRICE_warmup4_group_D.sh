#!/bin/bash
# Mode 12 inflatePRICE cx4 — 4-epoch warmup only, 8 models (group D)
# Round-robin picks from initial_32_models_seed42.txt: ranks 4, 8, 12, 16, 20, 24, 28, 32
# All 4 epochs are warmup: LLM frozen, only even cross-attn layers + PRICE core train.
# Checkpoint at epoch 4.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "microsoft/deberta-v3-large"
    "albert/albert-xxlarge-v1"
    "distilbert/distilroberta-base"
    "EleutherAI/pythia-410m-deduped"
    "EleutherAI/pythia-31m"
    "sentence-transformers/multi-qa-distilbert-cos-v1"
    "HuggingFaceTB/SmolLM-360M-Instruct"
    "answerdotai/ModernBERT-base"
)

MODELS_CSV=$(IFS=','; echo "${MODELS[*]}")

COMMON=(
    --models "$MODELS_CSV"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --ft_batch_size "24"
    --ft_num_epoch "4"
    --removed_fields ""
    --seeds "42"
    --db "postgres"
    --price_s
    --price_random_init
    --inflate_price
    --n_cross_layers "4"
    --checkpoint_interval "4"
    --freeze_llm_until_epoch "4"
    --price_warmup_epochs "4"
)

echo "============================================================"
echo "  Group D | inflatePRICE cx4 warmup-only (4 epochs) | stats"
echo "  Models: ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "stats" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "Group D done!"
