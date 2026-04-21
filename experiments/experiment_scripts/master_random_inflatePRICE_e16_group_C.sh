#!/bin/bash
# Random baseline: 9 models sampled by random_model_selection.py (seed 42),
# trained from scratch for 16 epochs. Same Mode 12 inflatePRICE cx4 settings
# as our model selection algorithm. Outputs go into subdir_tag=random_selection
# so they don't mix with model_selection outputs.
#
# Group C: albert/albert-xlarge-v2 (73.00 ms, alone — caps the 4-way split).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "google/electra-large-discriminator"
    "google/electra-base-generator"
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
    --subdir_tag "random_selection"
)

echo "============================================================"
echo "  Random Group C | inflatePRICE cx4 e16 from scratch | stats"
echo "  Models: ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "stats" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "Random Group C done!"
