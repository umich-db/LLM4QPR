#!/bin/bash
# Cross-attn DIRECTION ablation on duckdb/syn — "normal mode 12 but LLM is updated
# during warmup, PRICE lr = 2e-5", with ONE cross-attn direction kept active.
#
# Normal mode 12 = biCrossAttn + cx4 + inflatePRICE + priceN (random init). The
# bidirectional cross-attn has two interleaved directions (models/llm_price_model.py):
#   EVEN blocks (i%2==0) = PRICE(Q) attends to LLM(K/V)   ["PRICE attends to LLM"]
#   ODD  blocks (i%2==1) = LLM(Q)   attends to PRICE(K/V) ["LLM attends to PRICE"]
# A direction is DISABLED by zero-initialising its blocks and freezing them for the
# whole run (until_epoch 999 >> total epochs), so they contribute exactly 0.
#
# FREEZE_DIR selects which direction to disable:
#   odd  -> freeze ODD  => only EVEN active => "PRICE attends to LLM"   (variant 1, local)
#   even -> freeze EVEN => only ODD  active => "LLM attends to PRICE"   (variant 2, db3)
#   all  -> freeze BOTH => no cross-attn   => ~ mode 7 (concat->MLP)    (variant 3, db2)
#
# Differences vs the canonical mode-12 schedule (MODE12_SCHED = pwm5/frzLLM5):
#   - LLM is UPDATED during warmup:        --freeze_llm_until_epoch 0  (not 5)
#   - PRICE lr fixed at 2e-5:              --price_lr 0.00002          (warmup lr too)
#   - keep the 5-epoch PRICE warmup window: --price_warmup_epochs 5
#
# Env: MODEL (required, HF name); FREEZE_DIR (odd|even|all, required);
#      SEEDS (42); FT_NUM_EPOCH (30); FT_BATCH_SIZE (24); CUDA_VISIBLE_DEVICES (0).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:?set MODEL=<hf name>}"
FREEZE_DIR="${FREEZE_DIR:?set FREEZE_DIR=odd|even|all}"
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS, CX4_FLAGS
export DB_ENGINE=duckdb
build_shared syn

case "$FREEZE_DIR" in
  odd)  FREEZE_FLAG=(--freeze_odd_blocks_until_epoch  999); DESC="freeze ODD  -> only EVEN active (PRICE attends to LLM)";;
  even) FREEZE_FLAG=(--freeze_even_blocks_until_epoch 999); DESC="freeze EVEN -> only ODD  active (LLM attends to PRICE)";;
  all)  FREEZE_FLAG=(--freeze_all_blocks_until_epoch  999); DESC="freeze BOTH -> no cross-attn (~ mode 7)";;
  *) echo "FREEZE_DIR must be odd|even|all (got '$FREEZE_DIR')"; exit 2;;
esac

# Warmup but LLM updatable (frzLLM 0); PRICE lr 2e-5; keep 5-epoch PRICE warmup window.
DIR_SCHED=(--price_warmup_epochs "5" --freeze_llm_until_epoch "0" --price_lr "0.00002")

echo "[cross-attn-dir] host=$(hostname) MODEL=$MODEL FREEZE_DIR=$FREEZE_DIR ($DESC)"
echo "[cross-attn-dir] seeds=[$SEEDS] e=$FT_NUM_EPOCH ftb=$FT_BATCH_SIZE dev=$CUDA_VISIBLE_DEVICES price_lr=2e-5 frzLLM=0 pwm=5"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
    "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${DIR_SCHED[@]}" "${FREEZE_FLAG[@]}"
echo "[cross-attn-dir] DONE host=$(hostname) MODEL=$MODEL FREEZE_DIR=$FREEZE_DIR"
