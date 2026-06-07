#!/bin/bash
# tpcds model-selection pool | Mode 12 inflatePRICE cx4 | e16 | GROUP B -> dbresearch2 (RTX 5080, 16 GB)
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
    "HuggingFaceTB/SmolLM2-135M-Instruct"
    "HuggingFaceTB/SmolLM-135M-Instruct"
    "google/electra-base-discriminator"
    "EleutherAI/pythia-160m-deduped"
    "facebook/opt-125m"
    "google-bert/bert-base-multilingual-cased"
    "google-bert/bert-base-uncased"
    "sentence-transformers/paraphrase-albert-base-v2"
    "google-bert/bert-base-multilingual-uncased"
    "sentence-transformers/multi-qa-mpnet-base-cos-v1"
    "google/bert_uncased_L-10_H-768_A-12"
    "distilbert/distilgpt2"
    "albert/albert-base-v1"
    "sentence-transformers/paraphrase-albert-small-v2"
    "distilbert/distilbert-base-cased"
    "sentence-transformers/multi-qa-distilbert-cos-v1"
    "distilbert/distilbert-base-uncased"
    "google/bert_uncased_L-4_H-768_A-12"
    "google/bert_uncased_L-12_H-512_A-8"
    "albert/albert-large-v1"
    "google/bert_uncased_L-2_H-768_A-12"
    "sentence-transformers/all-MiniLM-L12-v2"
    "google/electra-small-generator"
    "google/electra-base-generator"
    "sentence-transformers/paraphrase-MiniLM-L12-v2"
    "sentence-transformers/all-MiniLM-L6-v2"
    "google/bert_uncased_L-12_H-128_A-2"
    "google/bert_uncased_L-12_H-256_A-4"
    "google/bert_uncased_L-8_H-128_A-2"
    "google/bert_uncased_L-8_H-256_A-4"
    "sentence-transformers/paraphrase-MiniLM-L6-v2"
    "EleutherAI/pythia-14m-deduped"
    "google/bert_uncased_L-6_H-256_A-4"
    "google/bert_uncased_L-4_H-128_A-2"
    "google/bert_uncased_L-2_H-128_A-2"
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
echo "  tpcds pool | inflatePRICE cx4 e16 | GROUP B (dbresearch2 (RTX 5080, 16 GB))"
echo "  Models (35): ${MODELS[*]}"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "tpcds" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "tpcds pool GROUP B done!"
