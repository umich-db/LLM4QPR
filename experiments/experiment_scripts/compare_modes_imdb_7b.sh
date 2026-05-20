#!/bin/bash
# {syn, job, job_full} × mode 7b
#
# All three workloads canonicalise to 'imdb' (utilsTrain._CANONICAL_MAP), so the
# saved joint-finetune weight file has the same path. WORKLOADS_ARR places 'syn'
# FIRST — its run trains LLM+PRICE+MLP from scratch on syn's training split (the
# largest of the three), saves _seed{N} weights, and the subsequent job /
# job_full runs hit run_llm_time.sh's existence guard and pass
# --skip_train_load_finetuned_weights to train.py.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

DB_ENGINES=(postgres duckdb spark)
WORKLOADS_ARR=(syn job job_full)   # syn FIRST → weights reused by job/job_full
MODES_ARR=(7b)

run_ablation
