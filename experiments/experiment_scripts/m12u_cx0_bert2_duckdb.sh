#!/bin/bash
# bert2 x duckdb — mode 12 CONTROL with cx=0 (NO cross-attn blocks; inflatePRICE
# kept) + unified per-window pooling, swept over [syn, job, job_full, tpch, tpcds,
# stats]. This is the cx0 counterpart to m12u_bert2_duckdb.sh (cx4) — same flags,
# only --n_cross_layers 0, so it isolates the cross-attn contribution. Both run
# under the new uniform duckdb ns latency scaling.
# Set CUDA_VISIBLE_DEVICES / SEEDS / FT_NUM_EPOCH in the env when launching.
export MODEL="google/bert_uncased_L-2_H-256_A-4"
export DB_ENGINE=duckdb
export N_CROSS_LAYERS=0
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mode12_unifpool_sweep.sh" "$@"
