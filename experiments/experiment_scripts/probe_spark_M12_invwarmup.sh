#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 cx=4 with the
# INVERSE warmup schedule — LLM updates during warmup, but odd cross-attn
# blocks (LLM←PRICE direction) are FROZEN at their zero-init for the warmup
# window, then unfreeze and grow from exactly 0.
#
# Compared to the default MODE12_SCHED:
#                            DEFAULT mode 12          THIS PROBE
#   LLM (LoRA) during 0..4:  frozen                   trainable
#   Odd cross-attn blocks:   trainable (soft warmup,  FROZEN at zero-init
#                            residual learns from 0)  (no LLM-token update)
#   PRICE LR schedule:       1e-3 → 2e-5 at epoch 5   1e-3 → 2e-5 at epoch 5
#
# What this isolates: the question is whether the warmup-phase friction comes
# from (a) the LLM updating while PRICE was still nascent or (b) the LLM-side
# update from PRICE happening prematurely. The default design gates (a) but
# leaves (b) soft. This probe gates (b) hard and leaves (a) free.
#
# Hypothesis: letting LLM adapt to query plans freely while keeping the LLM
# token stream untouched by PRICE produces a cleaner handoff at epoch 5.
#
# Implementation: --freeze_odd_blocks_until_epoch 5 + --freeze_llm_until_epoch 0.
# The new flag is wired through trainer.py:_freeze_odd_until and the unified
# PRICEEmbedder's odd_layer_parameters() method (only odd-indexed blocks).
#
# Output CSV will carry `_frzOdd5_pwm5` instead of `_frzLLM5_pwm5` —
# distinct from the default mode 12 cell so the aggregator sees a new column.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)
MODES_ARR=(12)

# Replace MODE12_SCHED: drop --freeze_llm_until_epoch, add --freeze_odd_blocks_until_epoch.
# Keep --price_warmup_epochs 5 so the PRICE LR ramp is identical between the two designs.
MODE12_SCHED=(--price_warmup_epochs "5" --freeze_odd_blocks_until_epoch "5")

run_ablation
