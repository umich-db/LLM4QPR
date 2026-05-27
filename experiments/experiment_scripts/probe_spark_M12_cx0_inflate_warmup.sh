#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 cx=4 with
# cross-attn frozen+zero-initialised in BOTH directions during warmup, but
# keeping the EXACT MODE12_SCHED schedule used by probe_spark_job_M12_cx0_inflate.sh:
#   - LLM (LoRA) frozen for epochs 0..4
#   - PRICE_core LR follows the 1e-3 → 2e-5 warmup ramp
#
# What this isolates: during the first 5 epochs, the model is architecturally
# equivalent to probe_spark_job_M12_cx0_inflate.sh — cross-attn contributes 0
# in both directions, MLP input width is LLM + embed_size, LLM frozen,
# PRICE_core ramping at 1e-3. The DIFFERENCE only kicks in at epoch 5:
#   - cx0_inflate: stays cx=0 (no cross-attn blocks exist), LLM unfreezes.
#   - this probe: 4 cross-attn blocks unfreeze and grow from 0 alongside LLM.
#
# So the comparison cx0_inflate ↔ this probe isolates the post-warmup
# contribution of cross-attn from a zero start, with everything else
# (warmup schedule, projection dim, MLP width) held constant.
#
# Implementation:
#   --freeze_all_blocks_until_epoch 5  → both directions zero-init+frozen
#   --freeze_llm_until_epoch 5         → LLM frozen during warmup (same as cx0_inflate)
#   --price_warmup_epochs 5            → PRICE_core 1e-3 ramp for first 5 epochs
#   (no --price_lr override → uses default 1e-3 warmup)
#
# Output CSV will carry `_frzLLM5_frzAll5_pwm5` token — distinct from
# `_frzLLM5_pwm5` (default M12), `_frzAll5_pwm5` (mode7warmup probe), and
# `_frzLLM5_cx0_pwm5_finfl` (cx0_inflate probe).

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)
MODES_ARR=(12)

# Keep MODE12_SCHED's LLM freeze + price warmup, add the all-blocks freeze.
MODE12_SCHED=(--price_warmup_epochs "5" --freeze_llm_until_epoch "5" --freeze_all_blocks_until_epoch "5")

run_ablation
