#!/bin/bash
# Script A — heaviest (~12-13h)
#
# Spark × bert4: the only bert4 atoms in the missing-cell set.
#   mode 1: job_full, syn       (light inference, ~5 min total)
#   mode 2: syn / job / job_full (one LoRA train on imdb + 2 reload-evals, ~7h)
#   mode 2: stats               (fresh LoRA train, ~6h)

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="google/bert_uncased_L-4_H-768_A-12"
DB_ENGINES=(spark)

# Mode 1 (LLM inference only): job_full + syn missing on spark for bert4.
WORKLOADS_ARR=(syn job_full)
MODES_ARR=(1)
run_ablation

# Mode 2 (LoRA finetune): all four imdb-family + stats missing on spark for bert4.
# Workload order matters: syn trains imdb-canonical LoRA, job/job_full reload via
# --skip_train_load_finetuned_weights; stats then trains its own LoRA.
WORKLOADS_ARR=(syn job job_full stats)
MODES_ARR=(2)
run_ablation
