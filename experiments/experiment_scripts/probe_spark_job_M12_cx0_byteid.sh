#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 with
# n_cross_layers=0, NO --force_inflate, AND a flat schedule
# (--price_warmup_epochs 0 --freeze_llm_until_epoch 0).
#
# Goal: byte-identical to mode 7 — same architecture (see _cx0_sched probe
# for the arch-identity proof) AND same schedule (no LLM freeze, no PRICE
# LR warmup).
#
# This is a sanity check: if the byte-identical claim is real, results
# should match the existing mode 7 cell at
#   results/spark/results_Train_job_Test_job_full_ours/time_llm_price_finetune_lora_spark_..._priceN_priceNor_randInit_e30_cdf_seed42.csv
# (modulo init RNG; same seed=42 should produce the same trajectory).
#
# Discrepancy here would indicate hidden dispatch-time state we missed —
# different optimizer construction path, different scheduler, different
# init order for the empty cross_attn_blocks ModuleList, etc.
#
# Filename suffix tokens: `biCrossAttn_inflatePRICE_cx0` only — no
# `frzLLM`/`pwm` (both 0), no `finfl` (omitted), no `cx2`/`cx4`.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)
MODES_ARR=(12)

# cx=0 + no --force_inflate (architectural match to mode 7)
CX4_FLAGS=(--inflate_price --n_cross_layers "0")
# Flat schedule (mode 7 baseline has no warmup / no freeze)
MODE12_SCHED=(--price_warmup_epochs "0" --freeze_llm_until_epoch "0")

run_ablation
