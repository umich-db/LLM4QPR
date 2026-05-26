#!/bin/bash
# Fill all missing L-4_H-768 ablation cells for modes 1, 2 (= jointMLP), 2r (= retrainMLP)
# across (postgres, duckdb, spark) × (stats, syn, job, job_full).
#
# --finetune_mode 2 triggers run_llm_time.sh's full "finetune=True" branch,
# which runs ALL THREE of {M2 LoRA train, M1 pretrained-None inference,
# M2r pretrained-lora retrain-MLP inference} per call. So a single MODES_ARR=(2)
# pass covers all three modes simultaneously.
#
# Workload ordering exploits canonical reuse: syn/job/job_full all canonicalise
# to "imdb", so the FIRST imdb-family workload trains the LoRA LLM weights and
# the next two reuse them via --skip_train_load_finetuned_weights. We place syn
# first because syn cells already have a (weightless) CSV — the others currently
# don't, and we want them populated. tpch/tpcds are skipped (already 100% covered
# in the existing ablation).
#
# stats is independent (canonical=stats), so each db retrains stats from scratch.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="google/bert_uncased_L-4_H-768_A-12"
DB_ENGINES=(postgres duckdb spark)
# stats first (independent canonical) then imdb family in canonical-reuse order
WORKLOADS_ARR=(stats syn job job_full)
MODES_ARR=(2)

run_ablation
