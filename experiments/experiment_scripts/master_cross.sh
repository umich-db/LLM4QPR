#!/bin/bash
# Master experiment runner — cross-workload with PRICE_S
# Runs job-light × time × finetune modes 1,2,3,4,7 with PRICE_S
# Mode 4 reuses mode 2's finetuned LLM weights (runs after mode 2)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_cross_workload_experiments.sh"

# Common flags shared by all runs
COMMON=(
    --models "sentence-transformers/all-MiniLM-L6-v2"
    --workloads "job-light"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --ft_batch_size "8"
    --grad_accum_steps "4"
    --ft_num_epoch "20"
    --removed_fields ""
    --seeds "42 43 44"
    --price_s
    --checkpoint_interval "5"
)

# Finetune modes:
#   1 = False           (no finetune / inference only)
#   2 = True            (LLM finetune, LoRA)
#   3 = PriceNoFT       (LLM+PRICE, no finetune)
#   4 = PriceLLMOnly    (LLM+PRICE, LLM finetuned only, LoRA — reuses mode 2 weights)
#   7 = JointPrice      (LLM+PRICE, both joint, LoRA)
MODES=(3 4)

for mode in "${MODES[@]}"; do
    echo ""
    echo "============================================================"
    echo "  Workload: job-light | Finetune mode: $mode | PRICE_S | cross-workload"
    echo "============================================================"

    MODE_ARGS=(--finetune_mode "$mode")

    # Add finetune_method for modes that finetune the LLM (2, 4, 7)
    if [[ "$mode" == 2 || "$mode" == 4 || "$mode" == 7 ]]; then
        MODE_ARGS+=(--finetune_method "lora")
    fi

    bash "$RUN_SCRIPT" "${COMMON[@]}" \
        "${MODE_ARGS[@]}"
done

echo ""
echo "All master (cross-workload) experiments completed!"
