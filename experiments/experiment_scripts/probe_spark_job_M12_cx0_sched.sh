#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 with
# n_cross_layers=0 (no cross-attn) AND no --force_inflate, keeping
# MODE12_SCHED's frzLLM5/pwm5 warmup intact.
#
# Architecturally byte-identical to mode 7:
#   - _query_hidden_dim falls into the else branch (=512) since both
#     n_cross_layers > 0 and force_inflate are False (train.py:778)
#   - PRICEEmbedder.cross_attn_blocks is empty, no inflate layer
#   - LLMPriceJointModel(LLM, price_embedder, embed_size, 512, hid_units)
#   - PRICEEmbedder.forward returns (emb, None, None) — same as mode 7
#
# But the SCHEDULE differs: --price_warmup_epochs 5 + --freeze_llm_until_epoch 5
# still apply, so the LoRA LLM is frozen for the first 5 epochs and PRICE LR
# follows the 1e-3→2e-5 ramp.
#
# What this tests: does the frzLLM5/pwm5 schedule ALONE shift results vs mode
# 7, when there's no cross-attn to actually warm up?
#   - If result ≈ mode 7: the schedule is a no-op without cross-attn
#   - If result ≠ mode 7: the schedule has independent effect (LoRA freeze
#     pause + PRICE LR ramp), and mode 12's gap vs mode 7 isn't all about
#     cross-attn
#
# Filename suffix tokens: `biCrossAttn_inflatePRICE_frzLLM5_cx0_pwm5`
# (no `finfl` because --force_inflate is omitted; no `cx2`/`cx4`).

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)        # canonical_map sends job_full to TRAIN_WL=job → train=job test=job_full
MODES_ARR=(12)

# cx=0 + NO --force_inflate. Otherwise leave MODE12_SCHED untouched.
CX4_FLAGS=(--inflate_price --n_cross_layers "0")

run_ablation
