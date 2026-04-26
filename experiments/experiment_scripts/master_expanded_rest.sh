#!/bin/bash
# Expanded pool — all 56 unknown models from the 103-candidate HF pool that are
# NOT in master_expanded_fast.sh and NOT already in the model_db (i.e. not yet
# evaluated to e16). Sorted by non-embedding parameter count (ascending).
# Same Mode 12 inflatePRICE cx4 settings as model_selection.
# Outputs go under --subdir_tag "expanded_pool".
#
# Total inference latency: 2209 ms. Estimated 16-epoch training: ~914 h on a
# single H100 (~38 days). You will almost certainly want to split this across
# multiple GPUs / sub-scripts in practice.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

MODELS=(
    "google/bert_uncased_L-4_H-128_A-2"
    "google/bert_uncased_L-6_H-128_A-2"
    "EleutherAI/pythia-14m"
    "google/bert_uncased_L-10_H-128_A-2"
    "google/bert_uncased_L-12_H-128_A-2"
    "google/bert_uncased_L-4_H-256_A-4"
    "google/bert_uncased_L-6_H-256_A-4"
    "google/bert_uncased_L-8_H-256_A-4"
    "google/bert_uncased_L-10_H-256_A-4"
    "albert/albert-base-v2"
    "google/bert_uncased_L-12_H-256_A-4"
    "nreimers/MiniLM-L6-H384-uncased"
    "google/bert_uncased_L-4_H-512_A-8"
    "albert/albert-large-v2"
    "albert/albert-large-v1"
    "google/electra-large-generator"
    "google/mobilebert-uncased"
    "microsoft/deberta-v3-xsmall"
    "sentence-transformers/paraphrase-MiniLM-L12-v2"
    "sentence-transformers/all-MiniLM-L12-v2"
    "microsoft/MiniLM-L12-H384-uncased"
    "google/bert_uncased_L-8_H-512_A-8"
    "google/bert_uncased_L-4_H-768_A-12"
    "google/bert_uncased_L-12_H-512_A-8"
    "google/bert_uncased_L-6_H-768_A-12"
    "google/bert_uncased_L-8_H-768_A-12"
    "albert/albert-xlarge-v2"
    "albert/albert-xlarge-v1"
    "google/electra-base-discriminator"
    "microsoft/deberta-v3-base"
    "microsoft/mdeberta-v3-base"
    "google/bert_uncased_L-12_H-768_A-12"
    "EleutherAI/pythia-160m"
    "EleutherAI/pythia-160m-deduped"
    "EleutherAI/gpt-neo-125m"
    "answerdotai/ModernBERT-base"
    "HuggingFaceTB/SmolLM2-135M-Instruct"
    "albert/albert-xxlarge-v1"
    "albert/albert-xxlarge-v2"
    "facebook/opt-350m"
    "microsoft/deberta-v3-large"
    "FacebookAI/roberta-large"
    "EleutherAI/pythia-410m-deduped"
    "EleutherAI/pythia-410m"
    "Qwen/Qwen1.5-0.5B-Chat"
    "Qwen/Qwen1.5-0.5B"
    "HuggingFaceTB/SmolLM-360M"
    "HuggingFaceTB/SmolLM2-360M"
    "HuggingFaceTB/SmolLM2-360M-Instruct"
    "answerdotai/ModernBERT-large"
    "Qwen/Qwen2.5-Coder-0.5B"
    "Qwen/Qwen2-0.5B-Instruct"
    "Qwen/Qwen2-0.5B"
    "Qwen/Qwen2.5-0.5B-Instruct"
    "Qwen/Qwen2.5-0.5B"
    "Qwen/Qwen2.5-Coder-0.5B-Instruct"
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
echo "  Expanded pool (REST, sorted by size) | inflatePRICE cx4 e16 | stats"
echo "  Models: ${#MODELS[@]} (sorted ascending by non-embedding parameter count)"
echo "============================================================"

bash "$RUN_SCRIPT" "${COMMON[@]}" \
    --workloads "stats" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    "$@"

echo ""
echo "Expanded rest batch done!"
