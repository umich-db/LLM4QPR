#!/bin/bash
# tpcds model-selection pool | Mode 12 inflatePRICE cx4 | e16 | GROUP A -> dbresearch3 (RTX 5090, 32 GB)
# Same recipe as master_finish_inflatePRICE_e16_group_*.sh but:
#   - workload = tpcds (not stats)
#   - ft_batch_size = 4 (tpcds plans are longer than stats; 16 GB-safe, mirrors
#     build_shared's tpch/tpcds OOM guard) instead of 24
# Fresh run from epoch 0 (no prior _e* checkpoints for tpcds) -> full 16 epochs.
# Excluded from the 87-model pool (OOM even on the 32 GB 5090 with the 805M
# inflated cross-attn): albert/albert-xlarge-v1, albert/albert-xlarge-v2,
# albert/albert-xxlarge-v2.  -> 84 models run, split A(14, 5090)/B(35)/C(35).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "Qwen/Qwen2.5-0.5B-Instruct"
    "Qwen/Qwen2.5-0.5B"
    "Qwen/Qwen2-0.5B"
    "Qwen/Qwen2.5-Coder-0.5B"
    "Qwen/Qwen2.5-Coder-0.5B-Instruct"
    "Qwen/Qwen2-0.5B-Instruct"
    "Qwen/Qwen1.5-0.5B-Chat"
    "Qwen/Qwen1.5-0.5B"
    "HuggingFaceTB/SmolLM2-360M-Instruct"
    "HuggingFaceTB/SmolLM2-360M"
    "HuggingFaceTB/SmolLM-360M"
    "HuggingFaceTB/SmolLM-360M-Instruct"
    "google/electra-large-discriminator"
    "FacebookAI/roberta-large"
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
    --ft_batch_size "4"
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
echo "  tpcds pool | inflatePRICE cx4 e16 | GROUP A (dbresearch3 (RTX 5090, 32 GB))"
echo "  Models (14): ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "tpcds" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "tpcds pool GROUP A done!"
