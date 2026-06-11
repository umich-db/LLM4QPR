#!/bin/bash
# Smoke test for mode 8 (PriceFTwithLLM): frozen-LLM concat finetune on cached
# pretrained embeddings (mode-1 cache), PRICE_N recipe, 2 epochs only.
#   CUDA_VISIBLE_DEVICES=1 bash experiment_scripts/smoke_mode8_frozen.sh
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-2}"
DB_ENGINES=(postgres)
WORKLOADS_ARR=(${WORKLOADS:-stats})
MODES_ARR=(8)

source "$SCRIPT_DIR/_compare_modes_lib.sh"
run_ablation
