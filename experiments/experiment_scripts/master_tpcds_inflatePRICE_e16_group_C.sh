#!/bin/bash
# tpcds model-selection pool | Mode 12 inflatePRICE cx4 | e16 | GROUP C -> local, RTX 5080 16 GB -> CUDA_VISIBLE_DEVICES=1
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
cd "$SCRIPT_DIR/.."   # run_different_llms.sh calls core_scripts/ via a relative path

MODELS=(
    "HuggingFaceTB/SmolLM2-135M"
    "HuggingFaceTB/SmolLM-135M"
    "microsoft/deberta-v3-small"
    "EleutherAI/pythia-160m"
    "google-bert/bert-base-cased"
    "google/bert_uncased_L-12_H-768_A-12"
    "albert/albert-base-v2"
    "FacebookAI/xlm-roberta-base"
    "sentence-transformers/all-mpnet-base-v2"
    "sentence-transformers/paraphrase-mpnet-base-v2"
    "google/electra-large-generator"
    "google/bert_uncased_L-8_H-768_A-12"
    "FacebookAI/roberta-base"
    "distilbert/distilbert-base-multilingual-cased"
    "sentence-transformers/multi-qa-distilbert-dot-v1"
    "google/mobilebert-uncased"
    "sentence-transformers/paraphrase-TinyBERT-L6-v2"
    "albert/albert-large-v2"
    "google/electra-small-discriminator"
    "distilbert/distilroberta-base"
    "google/bert_uncased_L-8_H-512_A-8"
    "microsoft/MiniLM-L12-H384-uncased"
    "google/bert_uncased_L-10_H-512_A-8"
    "google/bert_uncased_L-4_H-512_A-8"
    "EleutherAI/pythia-70m-deduped"
    "google/bert_uncased_L-6_H-512_A-8"
    "google/bert_uncased_L-10_H-128_A-2"
    "google/bert_uncased_L-10_H-256_A-4"
    "sentence-transformers/multi-qa-MiniLM-L6-dot-v1"
    "EleutherAI/pythia-31m"
    "nreimers/MiniLM-L6-H384-uncased"
    "google/bert_uncased_L-2_H-256_A-4"
    "google/bert_uncased_L-6_H-128_A-2"
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    "EleutherAI/pythia-14m"
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
echo "  tpcds pool | inflatePRICE cx4 e16 | GROUP C (local, RTX 5080 16 GB -> CUDA_VISIBLE_DEVICES=1)"
echo "  Models (35): ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "tpcds" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "tpcds pool GROUP C done!"
