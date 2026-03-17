#!/bin/bash
# Master experiment runner
# Mode 7 (JointPrice) with PRICE_M and random init

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
    --removed_fields ""
    --seeds "42 43 44"
    --db "postgres"
    --price_m
    --price_random_init
    --checkpoint_interval "5"
)

WORKLOADS=("stats" "job" "jobm")

MODES=(7)

for wl in "${WORKLOADS[@]}"; do
    for mode in "${MODES[@]}"; do
        echo ""
        echo "============================================================"
        echo "  Workload: $wl | Finetune mode: $mode | PRICE_M | Random Init"
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
echo "All master experiments completed!"
