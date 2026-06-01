#!/bin/bash
# CONTROL for the inflatePRICE ablation: same path as mode7_inflate (mode-7 concat
# via finetune_mode 12, n_cross_layers 0, force_inflate) but PRICE dim PINNED to 512
# via --price_output_dim 512 (the _pod branch overrides force_inflate's embed_size).
#
# Purpose: if this reproduces true mode-7 (~p90 1.53), the force_inflate/PRICEEmbedder
# path is correct and the m7+inflate degradation (2.37) is purely the 512->768 dim.
# If it does NOT, the path itself has a confound (e.g. RNG-init shift from building
# the cross-attn module, or a projection force_inflate adds), not the dim.
#
# Env: MODEL (req), SEEDS (42), FT_NUM_EPOCH (30), FT_BATCH_SIZE (24),
#      CUDA_VISIBLE_DEVICES (0).
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
echo "[mode7-finfl-dim512] host=$(hostname) MODEL=$MODEL seeds=[$SEEDS] mode7-concat + force_inflate but PRICE dim PINNED 512 (control) e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 "${PRICE_N_FLAGS[@]}" \
    --inflate_price --n_cross_layers 0 --force_inflate --price_output_dim 512
echo "[mode7-finfl-dim512] DONE host=$(hostname) MODEL=$MODEL"
