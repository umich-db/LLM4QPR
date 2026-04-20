#!/bin/bash
# Round 2: Mode 12 inflatePRICE cx4 — resume from epoch 4 to epoch 8.
# Epochs 1-4 are warmup (done); epochs 5-8 are normal inflatePRICE finetuning.
# Auto-resume picks up _epoch4.pt; warmup_mode off since start_epoch (4) == freeze_llm_until_epoch (4).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "answerdotai/ModernBERT-base"
    "EleutherAI/pythia-31m"
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
    --ft_num_epoch "8"
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
    --subdir_tag "model_selection"
)

echo "============================================================"
echo "  Round 2 Group D | inflatePRICE cx4 resume e4->e8 | stats"
echo "  Models: ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "stats" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "Round 2 Group D done!"
