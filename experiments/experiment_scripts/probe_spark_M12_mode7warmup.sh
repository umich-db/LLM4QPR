#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 cx=4 with
# a MODE-7-LIKE warmup phase:
#   - All cross-attn blocks (both even=PRICE←LLM and odd=LLM←PRICE) are
#     zero-initialised on output projection + last FF.
#   - All cross-attn blocks frozen for first 5 epochs.
#   - PRICE warmup LR = post-warmup LR = 2e-5 (no LR ramp).
#   - LLM is NOT frozen (LoRA adapters train normally).
#
# During warmup (epochs 0..4), the forward pass is:
#   PRICE core → linear (→embed_size) → length-1 token → cross_attn_blocks
#     (computed but contribute 0 due to zero-init+frozen) → token unchanged
#     → MLP(concat(LLM_tokens, PRICE_token))
# Loss flows back to: LLM (LoRA), PRICE core, MLP. Cross-attn params have
# requires_grad=False so they don't update.
#
# This approximates mode 7's training mechanics: LLM and PRICE+MLP train
# together, no cross-attn signal. BUT it is NOT byte-identical to mode 7:
#   - The PRICE linear projects to embed_size (because cx>0), not 512.
#     → MLP input width is LLM + embed_size, not LLM + 512.
#   - The cross-attn forward IS computed (wasted compute but zero contribution).
#   - The cross-attn param group exists in the optimizer (with grads None).
#
# After warmup (epoch 5+): cross-attn unfreezes, both directions grow from
# exactly zero residual. PRICE_core stays at 2e-5 (no LR drop since
# --price_lr 2e-5 makes warmup_lr == finetune_lr).
#
# Implementation: --freeze_all_blocks_until_epoch 5 (triggers zero-init on
# even blocks too via PRICEEmbedder's zero_init_all_blocks=True path),
# --price_lr 2e-5, --freeze_llm_until_epoch 0.
#
# Output CSV will carry `_frzAll5_pwm5` token.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)
MODES_ARR=(12)

# Drop --freeze_llm_until_epoch, add --freeze_all_blocks_until_epoch 5 and
# --price_warmup_lr 2e-5 (canonical alias; shell layer also accepts --price_lr).
MODE12_SCHED=(--price_warmup_epochs "5" --price_warmup_lr "2e-5" --freeze_all_blocks_until_epoch "5")

run_ablation
