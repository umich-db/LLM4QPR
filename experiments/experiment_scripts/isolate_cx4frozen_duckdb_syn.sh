#!/bin/bash
# ISOLATION run: m7+inflate (concat, no ACTIVE cross-attn) but with 4 zero-init
# FROZEN cross-attn blocks added (cx4 + freeze_all_999), keeping m7+inflate's
# schedule (pw0, no --price_lr, force_inflate). Everything else == m7+inflate.
#
# Purpose: m7+inflate (cx0) gave ep0 p90=2.37; cxdir_all (cx4 frozen + pw5 + pLR)
# gave 4.58. This isolates ONLY the cx4-frozen-blocks effect (holding the schedule
# == m7+inflate). If this ~= 4.58 -> the 4 frozen blocks (RNG-init shift +/- forward
# perturbation) are the cause; if ~= 2.37 -> the cause is the pw5/pLR schedule diffs.
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
echo "[isolate-cx4frozen] host=$(hostname) MODEL=$MODEL seeds=[$SEEDS] m7+inflate schedule + cx4 frozen blocks e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 "${PRICE_N_FLAGS[@]}" \
    --inflate_price --n_cross_layers 4 --force_inflate --freeze_all_blocks_until_epoch 999
echo "[isolate-cx4frozen] DONE host=$(hostname) MODEL=$MODEL"
