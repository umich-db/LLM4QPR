#!/bin/bash
# Finish round: Mode 12 inflatePRICE cx4 — run each model through epoch 15.
# Auto-resume picks up the latest _e{N}_llm.pt fallback (train.py:988-1036):
#   - models with _e8_*.pt: resume from epoch 8 (post-R2 H100 checkpoint)
#   - models with only _e4_*.pt: resume from epoch 4 (post-R1 A100 warmup)
#   - models with no weights: start from epoch 0 (full 16 ep)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "FacebookAI/xlm-roberta-large"
    "EleutherAI/pythia-70m-deduped"
    "google/bert_uncased_L-8_H-128_A-2"
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
    --ft_num_epoch "16"
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
echo "  Finish Round Group B | inflatePRICE cx4 resume e8->e16 | stats"
echo "  Models: ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "stats" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "Finish Round Group B done!"
