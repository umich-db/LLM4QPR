#!/bin/bash
# "Mode-7 + inflatePRICE" ablation on duckdb/syn — mode-7-like concat architecture
# (NO cross-attn) but with PRICE inflated to the LLM hidden dim (768 for bert4),
# matching what mode-12/cxdir use. Isolates whether inflatePRICE alone degrades vs
# the raw-512 PRICE of true mode-7.
#
# Why not just "--finetune_mode 7 --inflate_price": that's a silent no-op. In the
# JointPrice (mode-7) path, --inflate_price is gated on use_bi_cross_attention
# (train.py:789-792) and the JointPrice model hard-codes PRICE dim 512. The
# code-supported way is the PRICEEmbedder path with ZERO cross layers (train.py
# comment: n_cross_layers=0 is "byte-identical to mode 7") + --force_inflate, which
# sets _query_hidden_dim=embed_size (768) so PRICE is inflated while no cross-attn
# is added. No warmup/freeze/price_lr overrides -> PRICE lr = 2e-5 flat (pw=0),
# same schedule as normal mode 7.
#
# Env: MODEL (req), SEEDS (42), FT_NUM_EPOCH (30), FT_BATCH_SIZE (24),
#      CUDA_VISIBLE_DEVICES (0).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$SCRIPT_DIR/.."
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
export MODEL="${MODEL:?set MODEL=<hf name>}"
export SEEDS="${SEEDS:-42}"
export FT_NUM_EPOCH="${FT_NUM_EPOCH:-30}"
export FT_BATCH_SIZE="${FT_BATCH_SIZE:-24}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
source "$SCRIPT_DIR/_compare_modes_lib.sh"   # build_shared, RUN_SCRIPT, PRICE_N_FLAGS
export DB_ENGINE=duckdb
build_shared syn
echo "[mode7-inflate] host=$(hostname) MODEL=$MODEL seeds=[$SEEDS] mode7-concat + inflatePRICE (n_cross=0 force_inflate) e=$FT_NUM_EPOCH ftb=$FT_BATCH_SIZE dev=$CUDA_VISIBLE_DEVICES"
bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 "${PRICE_N_FLAGS[@]}" \
    --inflate_price --n_cross_layers 0 --force_inflate
echo "[mode7-inflate] DONE host=$(hostname) MODEL=$MODEL"
