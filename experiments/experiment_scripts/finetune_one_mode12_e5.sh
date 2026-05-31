#!/bin/bash
# Single-cell 5-epoch mode-12 (biCrossAttn frzLLM5/pwm5) finetune. Parameterized
# via env: MODEL (required), DB (default duckdb), WL (default syn). All 5 epochs
# are frozen (warmup), capturing mode-12's pre-overfit quality. Used to fan work
# out across machines (5080/5090). Prefers the py312 venv.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-5}"
export SEEDS="${SEEDS:-42}"
export MODEL="${MODEL:?set MODEL=...}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"
DB_ENGINES=("${DB:-duckdb}"); WORKLOADS_ARR=("${WL:-syn}"); MODES_ARR=(12)
echo "[runner] host=$(hostname) MODEL=$MODEL DB=${DB:-duckdb} WL=${WL:-syn} e=$FT_NUM_EPOCH b=$FT_BATCH_SIZE"
run_ablation
