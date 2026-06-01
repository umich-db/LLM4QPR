#!/bin/bash
# VERIFICATION of --mlp_before_cross_attn: same as isolate_cx4frozen (cx4 frozen
# zero-init blocks + m7+inflate schedule) but WITH --mlp_before_cross_attn.
# Expectation if the fix works:
#   - MLP init row0_sum == -0.951133 (the cx0 / m7+inflate value), NOT cx4's -0.627773
#     -> the MLP is now built before the blocks, so its init is block-count-independent.
#   - ep0 p90 ~= 2.37 (m7+inflate), since the frozen blocks are forward-identity AND
#     the MLP init now matches -> cx4-frozen+mlpFirst should track m7+inflate (cx0) at
#     every epoch, confirming the init-shift confound is removed.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:?set MODEL=<hf name>}"
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"
export DB_ENGINE=duckdb
build_shared syn
echo "[mlpFirst-cx4frozen] host=$(hostname) MODEL=$MODEL seeds=[$SEEDS] cx4 frozen + --mlp_before_cross_attn e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 "${PRICE_N_FLAGS[@]}" \
    --inflate_price --n_cross_layers 4 --force_inflate --freeze_all_blocks_until_epoch 999 \
    --mlp_before_cross_attn
echo "[mlpFirst-cx4frozen] DONE host=$(hostname) MODEL=$MODEL"
