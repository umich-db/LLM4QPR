#!/bin/bash
# Master experiment runner (DuckDB)
# Runs experiments for stats/job/jobm × time × finetune modes 1,2,3,4,7 with PRICE_S
# Mode 2 & 7 use R4 settings: StepLR, bs=32, ep=20, price_lr=2e-5
# Mode 4 reuses mode 2's finetuned LLM weights (runs after mode 2)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

# Common flags shared by all runs
COMMON=(
    # --models "sentence-transformers/all-MiniLM-L6-v2"
    --models "prajjwal1/bert-tiny"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --ft_batch_size "32"
    --ft_num_epoch "20"
    --price_lr "0.00002"
    --removed_fields ""
    --seeds "42 43 44"
    --db "duckdb"
    --price_s
)

WORKLOADS=("stats" "job" "jobm")

# Finetune modes:
#   1 = False           (no finetune / inference only)
#   2 = True            (LLM finetune, LoRA)
#   3 = PriceNoFT       (LLM+PRICE, no finetune)
#   4 = PriceLLMOnly    (LLM+PRICE, LLM finetuned only, LoRA — reuses mode 2 weights)
#   7 = JointPrice      (LLM+PRICE, both joint, LoRA)
MODES=(1 2 3 4 7)

for wl in "${WORKLOADS[@]}"; do
    for mode in "${MODES[@]}"; do
        echo ""
        echo "============================================================"
        echo "  Workload: $wl | Finetune mode: $mode | PRICE_S | duckdb"
        echo "============================================================"

        MODE_ARGS=(--finetune_mode "$mode")

        # Add finetune_method for modes that finetune the LLM (2, 4, 7)
        if [[ "$mode" == 2 || "$mode" == 4 || "$mode" == 7 ]]; then
            MODE_ARGS+=(--finetune_method "lora")
        fi

        bash "$RUN_SCRIPT" "${COMMON[@]}" \
            --workloads "$wl" \
            "${MODE_ARGS[@]}"
    done
done

echo ""
echo "All master (duckdb) experiments completed!"
