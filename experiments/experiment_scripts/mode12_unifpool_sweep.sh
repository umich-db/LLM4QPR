#!/bin/bash
# Mode-12 (biCrossAttn + cx4 + inflatePRICE + priceN random-init, MODE12_SCHED:
# --price_warmup_epochs 5 --freeze_llm_until_epoch 5) WITH the unified per-window
# LLM pooling (--unified_window_pool, via env UNIFIED_WINDOW_POOL=1), swept over
# [syn, job, job_full, tpch, tpcds, stats] IN ORDER for one MODEL + DB_ENGINE.
#
# Shared core for the 9 m12u_<model>_<engine>.sh wrappers (3 models x 3 engines).
#
# UNIFIED_WINDOW_POOL=1 reaches train.py via the environment (train.py reads it
# directly; run_llm_time adds the _unifPool filename suffix). This fixes the long-
# plan truncation (cross-attn path was using only the first sliding window's CLS).
#
# Env: MODEL (req, HF name), DB_ENGINE (req: duckdb|spark|postgres),
#      SEEDS (42), FT_NUM_EPOCH (30), FT_BATCH_SIZE (24; build_shared drops to 4 for
#      tpch/tpcds), CUDA_VISIBLE_DEVICES (0).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:?set MODEL=<hf name>}"
export DB_ENGINE="${DB_ENGINE:?set DB_ENGINE=duckdb|spark|postgres}"
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export UNIFIED_WINDOW_POOL=1   # the per-window cross-attn pooling fix
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS, CX4_FLAGS, MODE12_SCHED

# Cross-attn depth: default 4 (cx4). Set N_CROSS_LAYERS=0 for the cx0 control
# (no cross-attn blocks; inflatePRICE kept on so cx0 isolates ONLY the cross-attn
# contribution vs cx4). run_llm_time tags filenames with the cx value, so cx0 and
# cx4 outputs never collide.
N_CROSS_LAYERS="${N_CROSS_LAYERS:-4}"
CX_FLAGS=(--inflate_price --n_cross_layers "$N_CROSS_LAYERS")

WORKLOADS=(syn job job_full tpch tpcds stats)
echo "[m12-unifpool] host=$(hostname) MODEL=$MODEL DB_ENGINE=$DB_ENGINE seeds=[$SEEDS] e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES UNIFIED_WINDOW_POOL=1 cx=$N_CROSS_LAYERS"
for WL in "${WORKLOADS[@]}"; do
  echo "================ [m12-unifpool] $DB_ENGINE / $WL ($MODEL) ================"
  build_shared "$WL"
  bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
      "${PRICE_N_FLAGS[@]}" "${CX_FLAGS[@]}" "${MODE12_SCHED[@]}" \
    || echo "[m12-unifpool] WARN: $DB_ENGINE/$WL exited non-zero (missing data for this engine?) — continuing"
done
echo "[m12-unifpool] DONE host=$(hostname) MODEL=$MODEL DB_ENGINE=$DB_ENGINE"
