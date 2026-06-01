#!/bin/bash
# bert2 x postgres — mode 12 frzEven-ALWAYS: the EVEN cross-attn blocks (PRICE<-LLM, PRICE attends
# to LLM) are FROZEN for the whole run (zero-init); the ODD blocks (LLM<-PRICE) stay trainable;
# LLM is always finetuned; PRICE lr constant 2e-5; cx4 + unified per-window pooling. Swept over
# [syn, job, job_full, tpch, tpcds, stats]. Set CUDA_VISIBLE_DEVICES / SEEDS / FT_NUM_EPOCH in env.
export MODEL="google/bert_uncased_L-2_H-256_A-4"
export DB_ENGINE=postgres
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mode12_frzEvenAlways_sweep.sh" "$@"
