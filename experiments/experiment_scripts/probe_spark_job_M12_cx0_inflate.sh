#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 with
# n_cross_layers=0 + force_inflate (PRICE output projected to embed_size,
# no cross-attention blocks).
#
# Why this configuration:
#   - cx=4 (default mode 12): 4 cross-attn blocks; spark mode-12 test loss
#     oscillates badly + worst-case L-4 ratio M12/M7 = 2.06× at p90 on job→job_full.
#   - cx=0 WITHOUT force_inflate: byte-identical to mode 7 (RegressionModel built
#     with query_hidden_dim=512, no inflate).
#   - cx=0 WITH force_inflate: PRICE side outputs LLM-hidden-dim (e.g. 384 for
#     sentBert), MLP input dim = embed_size + embed_size, but NO cross-attn
#     blocks are constructed and PRICEEmbedder.forward early-returns at
#     `if self.n_cross_layers == 0: return query_output, None, None`.
#     This isolates the effect of the projection dim (mode 7's 512 vs mode 12's
#     embed_size on PRICE) from the effect of cross-attention itself.
#
# Hypothesis: if cx=0 + force_inflate ≈ mode 7 at p90, then cross-attn capacity
# is causing the instability; if it stays close to cx=4, the issue is the
# projection / MLP-input-dim choice rather than cross-attn.
#
# Target cell (worst-case for true mode 12 with frzLLM5/pwm5):
#   spark train=job test=job_full, sentBert + L-4. We probe sentBert here;
#   override MODEL to retest with L-4 if helpful.
#
# Output CSV will have `_cx0_` in place of `_cx4_` (the n_cross_layers token
# gets baked into the price-path suffix via train._price_path_suffix).

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)        # train→test = job→job_full (canonical_map sends job_full to TRAIN_WL=job)
MODES_ARR=(12)

# Override mode-12 dispatch: cx=0 + force_inflate so PRICE outputs embed_size
# instead of 512, but no cross-attn blocks are built.
CX4_FLAGS=(--inflate_price --n_cross_layers "0" --force_inflate)

run_ablation
