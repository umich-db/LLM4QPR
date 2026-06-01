#!/bin/bash
# bert4 x postgres — mode 12 (biCrossAttn+cx4+inflatePRICE+priceN, pwm5/frzLLM5) +
# unified per-window pooling, swept over [syn, job, job_full, tpch, tpcds, stats].
# Set CUDA_VISIBLE_DEVICES / SEEDS / FT_NUM_EPOCH in the env when launching.
export MODEL="google/bert_uncased_L-4_H-768_A-12"
export DB_ENGINE=postgres
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mode12_unifpool_sweep.sh" "$@"
