#!/bin/bash
# Mode-12 frzEven-ALWAYS sweep — shared core for the 9 m12fea_<model>_<engine>.sh wrappers
# (3 models x 3 engines). Counterpart of mode12_unifpool_sweep.sh.
#
# Setting ("frzEven-always" warmup ablation, applied to the FULL workload sweep):
#   - cx4 biCrossAttn + inflatePRICE + priceN random-init + unified per-window pooling.
#   - The EVEN cross-attn blocks (PRICE<-LLM, i.e. PRICE attends to LLM) are FROZEN for the
#     ENTIRE run (--freeze_even_blocks_until_epoch 999, >> e30) and zero-initialised, so PRICE
#     is never refined by the LLM. The ODD blocks (LLM<-PRICE, LLM attends to PRICE) stay
#     TRAINABLE (zero-init by default) -> only the LLM<-PRICE direction is ever active.
#   - LLM is ALWAYS finetuned (no --freeze_llm_until_epoch; default 0).
#   - PRICE lr is CONSTANT 2e-5 (price_warmup_epochs stays 0 -> no ramp).
#   Swept over [syn, job, job_full, tpch, tpcds, stats] IN ORDER for one MODEL + DB_ENGINE.
#
# Env: MODEL (req, HF name), DB_ENGINE (req: duckdb|spark|postgres), SEEDS (42),
#      FT_NUM_EPOCH (30), FT_BATCH_SIZE (24; build_shared drops to 4 for tpch/tpcds),
#      CUDA_VISIBLE_DEVICES (0), N_CROSS_LAYERS (4), FREEZE_EVEN_EPOCHS (999).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:?set MODEL=<hf name>}"
export DB_ENGINE="${DB_ENGINE:?set DB_ENGINE=duckdb|spark|postgres}"
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export UNIFIED_WINDOW_POOL=1   # unified per-window cross-attn pooling (long-plan fix)
N_CROSS_LAYERS="${N_CROSS_LAYERS:-4}"
CX_FLAGS=(--inflate_price --n_cross_layers "$N_CROSS_LAYERS")
FRZ_EVEN_FLAGS=(--freeze_even_blocks_until_epoch "${FREEZE_EVEN_EPOCHS:-999}")  # even frozen forever
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS

WORKLOADS=(syn job job_full tpch tpcds stats)
echo "[m12-frzEvenAlways] host=$(hostname) MODEL=$MODEL DB_ENGINE=$DB_ENGINE cx=$N_CROSS_LAYERS frzEven=${FREEZE_EVEN_EPOCHS:-999}(always) priceLR=2e-5(const) LLM=always-ft seeds=[$SEEDS] e=$FT_NUM_EPOCH dev=$CUDA_VISIBLE_DEVICES UNIFIED_WINDOW_POOL=1"
for WL in "${WORKLOADS[@]}"; do
  echo "================ [m12-frzEvenAlways] $DB_ENGINE / $WL ($MODEL) ================"
  build_shared "$WL"
  bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
      "${PRICE_N_FLAGS[@]}" "${CX_FLAGS[@]}" "${FRZ_EVEN_FLAGS[@]}" \
    || echo "[m12-frzEvenAlways] WARN: $DB_ENGINE/$WL exited non-zero (missing data for this engine?) — continuing"
done
echo "[m12-frzEvenAlways] DONE host=$(hostname) MODEL=$MODEL DB_ENGINE=$DB_ENGINE"
