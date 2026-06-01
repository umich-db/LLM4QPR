#!/bin/bash
# frzEven-warmup (duckdb syn, mode 12, cx4): the MIRROR/opposite of frzOdd-warmup.
#   - LLM is ALWAYS finetuned.
#   - Warmup = first 5 epochs: FREEZE the EVEN cross-attn blocks (PRICE<-LLM, i.e. PRICE
#     attends to LLM) -> during warmup the PRICE token is NOT refined by the LLM; the ODD
#     blocks (LLM<-PRICE, LLM attends to PRICE) stay TRAINABLE -> the LLM stream IS written
#     by PRICE during warmup. (frzOdd froze the opposite direction.)
#   - After epoch 5: even blocks unfreeze (staged unfreeze in trainer.py).
#   - --freeze_even_blocks_until_epoch 5 ALSO zero-inits the even output projection; odd is
#     zero-init by default -> BOTH directions are zero-initialised.
#   - PRICE lr constant 2e-5 (price_warmup_epochs=0); unified per-window pooling.
#   - cx via N_CROSS_LAYERS (4). Single workload: duckdb/syn.
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
NCX="${N_CROSS_LAYERS:-4}"
FRZ_EVEN="${FREEZE_EVEN_EPOCHS:-5}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS
echo "[m12-frzEven-warmup] host=$(hostname) MODEL=$MODEL cx=$NCX frzEven=$FRZ_EVEN priceLR=2e-5(const) LLM=always-ft seed=$SEEDS e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES UNIFIED_WINDOW_POOL=1"
build_shared "syn"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
    "${PRICE_N_FLAGS[@]}" --inflate_price --n_cross_layers "$NCX" \
    --freeze_even_blocks_until_epoch "$FRZ_EVEN" \
  || echo "[m12-frzEven-warmup] WARN: exited non-zero"
echo "[m12-frzEven-warmup] DONE host=$(hostname) cx=$NCX"
