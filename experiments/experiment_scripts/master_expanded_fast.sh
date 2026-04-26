#!/bin/bash
# Expanded pool — 20 fast (<20 ms) unknown models from the 103-candidate HF pool.
# Same Mode 12 inflatePRICE cx4 settings as model_selection. Outputs go under
# --subdir_tag "expanded_pool" to keep them separate from model_selection results.
#
# Total inference latency: 299 ms. Estimated 16-epoch training: ~124 h on H100.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "google/bert_uncased_L-2_H-256_A-4"
    "google/bert_uncased_L-2_H-768_A-12"
    "distilbert/distilbert-base-cased"
    "distilbert/distilbert-base-uncased"
    "EleutherAI/pythia-70m"
    "EleutherAI/pythia-31m-deduped"
    "distilbert/distilgpt2"
    "sentence-transformers/multi-qa-MiniLM-L6-dot-v1"
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    "sentence-transformers/paraphrase-TinyBERT-L6-v2"
    "FacebookAI/xlm-roberta-base"
    "FacebookAI/roberta-base"
    "albert/albert-base-v1"
    "google-bert/bert-base-cased"
    "google/electra-small-discriminator"
    "google/electra-small-generator"
    "sentence-transformers/paraphrase-albert-base-v2"
    "sentence-transformers/paraphrase-mpnet-base-v2"
    "sentence-transformers/all-mpnet-base-v2"
    "google-bert/bert-base-multilingual-uncased"
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
    --subdir_tag "expanded_pool"
)

echo "============================================================"
echo "  Expanded pool (FAST <20ms) | inflatePRICE cx4 e16 | stats"
echo "  Models: ${#MODELS[@]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "stats" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "Expanded fast batch done!"
