#!/bin/bash
# bertSent x spark — mode 12 (biCrossAttn+cx4+inflatePRICE+priceN, pwm5/frzLLM5) +
# unified per-window pooling, swept over [syn, job, job_full, tpch, tpcds, stats].
# Set CUDA_VISIBLE_DEVICES / SEEDS / FT_NUM_EPOCH in the env when launching.
export MODEL="sentence-transformers/all-MiniLM-L12-v2"
export DB_ENGINE=spark
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mode12_unifpool_sweep.sh" "$@"
