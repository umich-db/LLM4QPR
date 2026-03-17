#!/bin/bash
# Master experiment runner - 30 epoch variant
# Mode 7 (JointPrice) with PRICE_M and random init, 30 epochs
# Auto-resumes from 20-epoch checkpoints

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

# Common flags shared by all runs
COMMON=(
    --models "sentence-transformers/all-MiniLM-L6-v2"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --ft_batch_size "32"
    --ft_num_epoch "30"
    --removed_fields ""
    --seeds "42 43 44"
    --db "duckdb"
    --price_s
    --price_random_init
    --checkpoint_interval "5"
)

WORKLOADS=("stats" "job" "jobm")

MODES=(7)

for wl in "${WORKLOADS[@]}"; do
    for mode in "${MODES[@]}"; do
        echo ""
        echo "============================================================"
        echo "  Workload: $wl | Finetune mode: $mode | PRICE_M | Random Init | 30 epochs"
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
echo "All 30-epoch master experiments completed!"
