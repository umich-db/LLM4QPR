#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 cx=4 with
#   - Cross-attn frozen+zero-init in BOTH directions during warmup, unfrozen after
#   - LLM frozen for ALL epochs (never unfreezes)
#   - PRICE_core ramp 1e-3 → 2e-5 at epoch 5 (default MODE12 warmup)
#
# Identical to probe_spark_M12_cx0_inflate_warmup.sh except the LLM stays
# frozen permanently (the comparison probe unfreezes LLM at epoch 5).
#
# Implementation: --freeze_llm_until_epoch is set to a value > num_epoch so the
# unfreeze condition (epoch >= _freeze_llm_until) is never met during training.
# Stays on trainer.py's standard staged-unfreeze code path so cross-attn keeps
# its own param group at cross_attn_lr=1e-4 (vs the legacy --freeze_llm flag
# which routes through a custom optimizer that lumps cross-attn into the
# PRICE group at 1e-3 → 2e-5).
#
# What this isolates vs probe_spark_M12_cx0_inflate_warmup.sh:
#   Both have identical warmup phase (LLM frozen, cross-attn frozen+zero-init,
#   PRICE_core ramp). They differ only post-warmup:
#     - cx0_inflate_warmup: LLM unfreezes at epoch 5 alongside cross-attn
#     - this probe:         LLM stays frozen; only cross-attn + PRICE_core +
#                           MLP update post-warmup
#
# Tests whether keeping the LLM frozen lets cross-attn settle without competing
# against simultaneously-updating LLM tokens.
#
# Output CSV will carry `_frzLLM999_frzAll1_pwm1` token — distinct from
# `_frzLLM5_frzAll5_pwm5` (the warmup-only-freeze variant).

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)
MODES_ARR=(12)

# 999 > FT_NUM_EPOCH=30, so the LLM unfreeze condition never fires.
# Warmup phase shortened to 1 epoch: cross-attn frozen+zero for epoch 0, then
# unfreezes at epoch 1; PRICE_core drops from 1e-3 to 2e-5 at epoch 1.
MODE12_SCHED=(--price_warmup_epochs "1" --freeze_llm_until_epoch "999" --freeze_all_blocks_until_epoch "1")

run_ablation
