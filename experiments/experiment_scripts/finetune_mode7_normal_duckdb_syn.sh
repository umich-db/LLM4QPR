#!/bin/bash
# Normal mode-7 (JointPrice, priceN random-init) on duckdb/syn — the canonical
# mode-7 baseline. Run alongside the cross-attn-direction variants for comparison
# (esp. against cxdir_all = freeze_all = "no cross-attn ≈ mode 7").
#
# "Normal setting" = the _compare_modes_lib mode-7 invocation: --finetune_mode 7
# + PRICE_N_FLAGS (--price_n --price_n_or --price_random_init), NO cross-attn,
# NO warmup/freeze/price_lr overrides.
#
# Env: MODEL (required, HF name); SEEDS (42); FT_NUM_EPOCH (30);
#      FT_BATCH_SIZE (24); CUDA_VISIBLE_DEVICES (0).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:?set MODEL=<hf name>}"
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS
export DB_ENGINE=duckdb
build_shared syn
echo "[mode7-normal] host=$(hostname) MODEL=$MODEL seeds=[$SEEDS] normal mode7 (priceN randInit) e=$FT_NUM_EPOCH ftb=$FT_BATCH_SIZE dev=$CUDA_VISIBLE_DEVICES"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 "${PRICE_N_FLAGS[@]}"
echo "[mode7-normal] DONE host=$(hostname) MODEL=$MODEL"
