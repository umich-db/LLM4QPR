#!/bin/bash
# Master experiment runner - PRICE n_layers=3 ablation
# Mode 7 (JointPrice) with PRICE_S, random init, 30 epochs, postgres
# Compares half-depth PRICE (3 layers per encoder = 6 total) vs default (6 layers = 12 total)

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
    --db "postgres"
    --price_s
    --price_random_init
    --price_n_layers "3"
    --checkpoint_interval "5"
)

WORKLOADS=("job")

MODES=(7)

for wl in "${WORKLOADS[@]}"; do
    for mode in "${MODES[@]}"; do
        echo ""
        echo "============================================================"
        echo "  Workload: $wl | Finetune mode: $mode | PRICE_S | Random Init | 30 epochs | n_layers=3"
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
echo "All PRICE n_layers=3 experiments completed!"
