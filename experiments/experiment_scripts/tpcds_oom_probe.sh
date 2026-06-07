#!/bin/bash
# Fast OOM batch-size probe for big tpcds-pool models (e.g. poolA on the 5090).
# For each model, runs a SKIP-WARMUP (LLM unfrozen from epoch 0 -> the memory peak
# happens immediately), tr0.1, 1-epoch, mode-12 inflatePRICE cx4 run at descending
# batch sizes; the largest batch whose epoch-0 completes without OOM is chosen.
# No checkpoints are written (checkpoint_interval 0) and outputs go to the
# 'oom_probe' subdir so the real model_selection pool is untouched.
#
# Usage:
#   MODELS_CSV="Qwen/Qwen2-0.5B,FacebookAI/roberta-large,..." \
#     [BATCHES="4 2 1"] [OUT=/tmp/poolA_oom_probe.tsv] \
#     bash .../tpcds_oom_probe.sh
# Output: OUT (TSV: model<TAB>chosen_batch), plus per-(model,batch) /tmp/probe_*.log
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
RUN="$SCRIPT_DIR/run_different_llms.sh"
cd "$SCRIPT_DIR/.."

: "${MODELS_CSV:?set MODELS_CSV (comma-separated)}"
: "${BATCHES:=4 2 1}"
OUT="${OUT:-/tmp/tpcds_oom_probe.tsv}"
: > "$OUT"

IFS=',' read -ra MODELS <<< "$MODELS_CSV"
for m in "${MODELS[@]}"; do
    chosen="NONE"
    for b in $BATCHES; do
        tag=$(echo "$m" | tr '/' '-')
        log="/tmp/probe_${tag}_b${b}.log"
        echo "[probe] $m  batch=$b ..."
        TRAIN_RATIO=0.1 FT_BATCH_SIZE="$b" FT_NUM_EPOCH=1 \
        bash "$RUN" \
            --models "$m" --task time --downstream mlp --quantification 4-bit \
            --bucketize None --embed_size 1000 --concat_true false \
            --ft_batch_size "$b" --ft_num_epoch 1 --removed_fields "" --seeds 42 --db postgres \
            --price_s --price_random_init --inflate_price --n_cross_layers 4 \
            --checkpoint_interval 0 --freeze_llm_until_epoch 0 --price_warmup_epochs 0 \
            --subdir_tag oom_probe --workloads tpcds --finetune_mode 12 --finetune_method lora \
            > "$log" 2>&1 || true
        if grep -qiE "out of memory|OutOfMemory|CUDA error" "$log"; then
            echo "    batch=$b -> OOM"
        elif grep -qE "Epoch: 0 +Avg Loss|\[Train\] Epoch 0 total" "$log"; then
            echo "    batch=$b -> OK (fits)"; chosen="$b"; break
        else
            echo "    batch=$b -> INCONCLUSIVE (check $log)"
        fi
    done
    accum=$([ "$chosen" = "NONE" ] && echo "-" || echo $(( 4 / chosen )))
    printf '%s\t%s\t%s\n' "$m" "$chosen" "$accum" | tee -a "$OUT"
done
echo ""
echo "[probe] done. model<TAB>batch<TAB>accum(=4/batch) -> $OUT"
cat "$OUT"
