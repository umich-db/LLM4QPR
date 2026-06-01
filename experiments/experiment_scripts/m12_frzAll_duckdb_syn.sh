#!/bin/bash
# CONTROL baseline (duckdb syn, mode 12): cross-attn ALWAYS FROZEN for the whole run.
#   - FREEZE_ALL_BLOCKS_UNTIL_EPOCH=999 (>> e30): freeze BOTH cross-attn directions for
#     every epoch (never unfreezes) AND zero-init the even-block output projection. Odd is
#     zero-init by default -> with both directions zero-init + frozen forever, the cross-attn
#     output projection stays exactly 0, i.e. the cross-attn is an exact identity that
#     contributes nothing. The model reduces to LLM-pooled + raw PRICE token -> MLP, which
#     is the cx=0 / mode-7 computation (the unifpool path makes the LLM pooling the exact
#     cx=0 limit). This is the architecture-matched inert baseline for the cx4 frzOdd-warmup
#     run: both are cx4, so the 4-block construction-RNG offset cancels in the comparison.
#   - LLM always finetuned; PRICE lr constant 2e-5 (price_warmup_epochs=0); unified pooling.
#   - cx via N_CROSS_LAYERS (4 by default). Driven by ENV (run_llm_time.sh reads
#     FREEZE_ALL_BLOCKS_UNTIL_EPOCH; the CLI export in run_different_llms.sh is guarded, so
#     the env value is not clobbered when no --freeze_all CLI flag is passed).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:-google/bert_uncased_L-2_H-256_A-4}"
export DB_ENGINE=duckdb
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export UNIFIED_WINDOW_POOL=1
export FREEZE_ALL_BLOCKS_UNTIL_EPOCH="${FREEZE_ALL_EPOCHS:-999}"   # >> e30 -> always frozen
NCX="${N_CROSS_LAYERS:-4}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS
echo "[m12-frzAll] host=$(hostname) MODEL=$MODEL cx=$NCX frzAll=$FREEZE_ALL_BLOCKS_UNTIL_EPOCH(always) priceLR=2e-5(const) LLM=always-ft seed=$SEEDS e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES UNIFIED_WINDOW_POOL=1"
build_shared "syn"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
    "${PRICE_N_FLAGS[@]}" --inflate_price --n_cross_layers "$NCX" \
  || echo "[m12-frzAll] WARN: exited non-zero"
echo "[m12-frzAll] DONE host=$(hostname) cx=$NCX"
