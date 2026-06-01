#!/bin/bash
# NEW warmup schedule test (duckdb syn, mode 12, bert2):
#   - LLM is ALWAYS finetuned (no --freeze_llm_until_epoch; default 0).
#   - Warmup = first 5 epochs: FREEZE the ODD cross-attn blocks (LLM<-PRICE, i.e. the
#     direction where PRICE writes into the LLM token stream), so the LLM is untouched
#     by PRICE during warmup. The EVEN blocks (PRICE attends to LLM, LLM as K/V) stay
#     TRAINABLE the whole time.
#   - After epoch 5: odd blocks unfreeze (staged unfreeze in trainer.py).
#   - BOTH cross-attn directions are zero-initialised: odd is zero-init by default;
#     even via ZERO_INIT_EVEN_BLOCKS=1 (zero-inits even WITHOUT freezing it).
#   - PRICE lr is CONSTANT 2e-5 (price_warmup_epochs stays 0 -> no ramp).
#   - cx depth via N_CROSS_LAYERS: 4 (local) / 0 (db2; cx0 ~= mode 7 modulo inflate).
# Single workload: duckdb/syn. Set CUDA_VISIBLE_DEVICES / N_CROSS_LAYERS / SEEDS / FT_NUM_EPOCH in env.
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
export ZERO_INIT_EVEN_BLOCKS=1            # zero-init even (PRICE<-LLM) blocks, keep them trainable
NCX="${N_CROSS_LAYERS:-4}"
FRZ_ODD="${FREEZE_ODD_EPOCHS:-5}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS
echo "[m12-frzOdd-warmup] host=$(hostname) MODEL=$MODEL cx=$NCX frzOdd=$FRZ_ODD priceLR=2e-5(const) LLM=always-ft seed=$SEEDS e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES UNIFIED_WINDOW_POOL=1 ZERO_INIT_EVEN_BLOCKS=1"
build_shared "syn"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
    "${PRICE_N_FLAGS[@]}" --inflate_price --n_cross_layers "$NCX" \
    --freeze_odd_blocks_until_epoch "$FRZ_ODD" \
  || echo "[m12-frzOdd-warmup] WARN: exited non-zero"
echo "[m12-frzOdd-warmup] DONE host=$(hostname) cx=$NCX"
