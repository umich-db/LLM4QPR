#!/bin/bash
# Run poolA's big models (the Qwen-0.5B family + SmolLM-360M + electra-large +
# roberta-large) on an 80 GB H100. They OOM the 32 GB 5090 at cx4 even at batch 1
# (one long tpcds plan -> ~10 sliding windows -> ~30 GB unfrozen), so batch tuning
# can't fix it on the 5090 -- the 80 GB H100 can.
#
# Same recipe as the other pool groups: full e16, mode-12 inflatePRICE cx4,
# subdir_tag model_selection. Effective batch kept at 4 via gradient accumulation
# (master_tpcds_inflatePRICE_e16_retry.sh sets GRAD_ACCUM_STEPS = 4/FT_BATCH).
# Default FT_BATCH=2 (peak ~45 GB on 80 GB) -> accum 2. Bump FT_BATCH=4 (accum 1)
# if you want; drop to 1 (accum 4) only if 2 still OOMs.
#
# Usage (on the H100):
#   CUDA_VISIBLE_DEVICES=0 [FT_BATCH=2] \
#     bash experiment_scripts/master_tpcds_poolA_h100.sh 2>&1 | tee /tmp/poolA_h100.log
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

export FT_BATCH="${FT_BATCH:-2}"
# The 9 large-context DECODER models that OOM the 32 GB 5090 at cx4 even at batch 1
# (32k/8k context -> a ~5k-token tpcds plan is one long sequence). The other 4 poolA
# models (SmolLM-360M v1 = 2048-ctx -> chunked; electra-large + roberta-large =
# encoders) DO fit the 5090 at batch 4 and run there, so they're not in this list.
# (Qwen2.5-Coder-0.5B-Instruct already has a CDF; add it to re-run that one cleanly.)
export MODELS_CSV="Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-0.5B,Qwen/Qwen2-0.5B,Qwen/Qwen2.5-Coder-0.5B,Qwen/Qwen2-0.5B-Instruct,Qwen/Qwen1.5-0.5B-Chat,Qwen/Qwen1.5-0.5B,HuggingFaceTB/SmolLM2-360M-Instruct,HuggingFaceTB/SmolLM2-360M"

echo "=== poolA on H100 | ${MODELS_CSV//,/ } | FT_BATCH=$FT_BATCH ==="
bash "$SCRIPT_DIR/master_tpcds_inflatePRICE_e16_retry.sh"
echo "poolA H100 run done. Results in results/postgres/results_Train_tpcds_Test_tpcds_ours/model_selection/"
