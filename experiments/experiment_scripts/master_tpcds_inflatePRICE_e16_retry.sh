#!/bin/bash
# Retry tpcds pool models that OOM'd at ft_batch_size 4 (16 GB 5080s), with a
# smaller batch. Same mode-12 inflatePRICE cx4 recipe as the group_{A,B,C} scripts.
#
# Usage (in tmux, per machine):
#   MODELS_CSV="modelA,modelB,..." FT_BATCH=2 \
#     bash .../master_tpcds_inflatePRICE_e16_retry.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"
cd "$SCRIPT_DIR/.."   # run_different_llms.sh calls core_scripts/ via a relative path

: "${MODELS_CSV:?set MODELS_CSV to a comma-separated model list}"
: "${FT_BATCH:=2}"
# Keep the EFFECTIVE batch at 4 via gradient accumulation: batch*accum = 4
# (batch 4 -> accum 1, batch 2 -> accum 2, batch 1 -> accum 4). Override by
# exporting GRAD_ACCUM_STEPS yourself. run_llm_time.sh forwards it to train.py.
: "${GRAD_ACCUM_STEPS:=$(( 4 / FT_BATCH ))}"
export GRAD_ACCUM_STEPS
echo "[retry] effective batch = ${FT_BATCH} x ${GRAD_ACCUM_STEPS} = $(( FT_BATCH * GRAD_ACCUM_STEPS ))"

COMMON=(
    --models "$MODELS_CSV"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --ft_batch_size "$FT_BATCH"
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
echo "  tpcds pool RETRY | inflatePRICE cx4 e16 | ft_batch_size=$FT_BATCH"
echo "  Models: $MODELS_CSV"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "tpcds" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "tpcds pool RETRY (ft_batch_size=$FT_BATCH) done!"
