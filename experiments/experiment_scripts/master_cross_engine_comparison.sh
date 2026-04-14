#!/bin/bash
# Cross-engine comparison: modes 1, 2, 7, 12 on duckdb and spark.
# Mode 1: pretrained (no finetune)
# Mode 2: LLM LoRA finetune
# Mode 7: JointPrice with pretrained PRICE
# Mode 12: BiCrossAttn inflatePRICE cx4 randInit
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

COMMON=(
    --models "sentence-transformers/all-MiniLM-L6-v2"
    --task "time"
    --downstream "mlp"
    --quantification "4-bit"
    --bucketize "None"
    --embed_size "1000"
    --concat_true "false"
    --removed_fields ""
    --seeds "42 43 44"
)

WORKLOADS=("stats" "job" "jobm")

run() {
    local desc="$1"; shift
    echo ""
    echo "============================================================"
    echo "  $desc"
    echo "============================================================"
    bash "$RUN_SCRIPT" "${COMMON[@]}" "$@"
}

# ═══════════════════════════════════════════════════════════════════════
#  DuckDB — only Mode 12 inflatePRICE needed (modes 1, 2, 7 exist)
# ═══════════════════════════════════════════════════════════════════════

for wl in "${WORKLOADS[@]}"; do
    run "Mode 12 inflatePRICE cx4 | duckdb | $wl" \
        --db "duckdb" \
        --ft_batch_size "24" --ft_num_epoch "30" \
        --price_s --price_random_init --inflate_price \
        --n_cross_layers "4" --checkpoint_interval "5" \
        --freeze_llm_until_epoch "5" --price_warmup_epochs "5" \
        --early_stop_patience "5" --early_stop_after_epoch "15" \
        --workloads "$wl" --finetune_mode "12" --finetune_method "lora"
done

# ═══════════════════════════════════════════════════════════════════════
#  Spark — all 4 modes needed
# ═══════════════════════════════════════════════════════════════════════

for wl in "${WORKLOADS[@]}"; do
    # Mode 1: pretrained (no finetune)
    run "Mode 1 pretrained | spark | $wl" \
        --db "spark" \
        --ft_batch_size "32" \
        --workloads "$wl" --finetune_mode "1" --finetune_method "lora"

    # Mode 2: LLM LoRA finetune
    run "Mode 2 LoRA finetune | spark | $wl" \
        --db "spark" \
        --ft_batch_size "32" --ft_num_epoch "30" \
        --workloads "$wl" --finetune_mode "2" --finetune_method "lora"

    # Mode 7: JointPrice with pretrained PRICE
    run "Mode 7 JointPrice priceS | spark | $wl" \
        --db "spark" \
        --ft_batch_size "32" --ft_num_epoch "30" \
        --price_s \
        --workloads "$wl" --finetune_mode "7" --finetune_method "lora"

    # Mode 12: BiCrossAttn inflatePRICE cx4 randInit
    run "Mode 12 inflatePRICE cx4 | spark | $wl" \
        --db "spark" \
        --ft_batch_size "24" --ft_num_epoch "30" \
        --price_s --price_random_init --inflate_price \
        --n_cross_layers "4" --checkpoint_interval "5" \
        --freeze_llm_until_epoch "5" --price_warmup_epochs "5" \
        --early_stop_patience "5" --early_stop_after_epoch "15" \
        --workloads "$wl" --finetune_mode "12" --finetune_method "lora"
done

echo ""
echo "All cross-engine comparison experiments completed!"
