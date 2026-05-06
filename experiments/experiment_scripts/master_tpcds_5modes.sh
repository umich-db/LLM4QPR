#!/bin/bash
# TPC-DS five-mode comparison runner.
#
# Modes:
#   1) Pretrained LLM only           (--finetune_mode 1)
#   2) Finetuned LLM only            (--finetune_mode 2, LoRA)
#   3) LLM + pretrained PRICE        (--finetune_mode 7, JointPrice)
#   4) LLM + PRICE_N inflated        (--finetune_mode 12, BiCrossAttn + inflate + price_n)
#   5) PRICE_N inflated, no LLM      (--finetune_mode 12 + --no_llm_residual)
#
# Filename suffixes encode every flag, so all five runs land in distinct
# weight / checkpoint / log / result paths.
#
# TPC-DS uses the template-based split (81 train templates + 9 test templates,
# 10% of train+val held for val). This is automatic when --workload_test tpcds.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

# ─── Flags shared by every run ────────────────────────────────────────────
COMMON=(
    --models           "distilbert/distilbert-base-uncased"
    --task             "time"
    --downstream       "mlp"
    --quantification   "4-bit"
    --bucketize        "None"
    --embed_size       "1000"
    --concat_true      "false"
    --ft_batch_size    "16"
    --ft_num_epoch     "16"
    --removed_fields   ""
    --seeds            "42"
    --db               "postgres"
    --workloads        "tpcds"
    --checkpoint_interval "4"
)

run() {
    local label="$1"; shift
    echo ""
    echo "============================================================"
    echo "  TPC-DS | $label"
    echo "============================================================"
    bash "$RUN_SCRIPT" "${COMMON[@]}" "$@"
}

# ─── Run 1: Pretrained LLM only ────────────────────────────────────────────
run "mode 1 — pretrained LLM" \
    --finetune_mode "1"

# ─── Run 2: Finetuned LLM only (LoRA) ──────────────────────────────────────
run "mode 2 — finetune LLM (LoRA)" \
    --finetune_mode "2" \
    --finetune_method "lora"

# ─── Run 3: LLM + pretrained PRICE (JointPrice) ────────────────────────────
# Note: no --price_random_init → pretrained PRICE weights are loaded.
run "mode 7 — LLM + pretrained PRICE" \
    --finetune_mode "7" \
    --finetune_method "lora"

# ─── Run 4: LLM + inflated bidirectional cross-attn + PRICE_N ──────────────
# --price_n enables all four PRICE_N flags (parsing/filter/fanout/pairwise).
# --inflate_price uses the inflated bi-cross-attention fusion.
# --price_random_init: PRICE_N's filter dim (75) doesn't match pretrained
# PRICE (43), so we start the PRICE encoder from random init.
# --n_cross_layers 4 matches the prior expanded_pool runs.
# --price_warmup_epochs / --freeze_llm_until_epoch keep PRICE training stable.
run "mode 12 — inflatePRICE + PRICE_N" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    --inflate_price \
    --price_n \
    --price_random_init \
    --n_cross_layers       "4" \
    --price_warmup_epochs  "4" \
    --freeze_llm_until_epoch "4"

# ─── Run 5: Same as Run 4 + --no_llm_residual ──────────────────────────────
# Disables the LLM-residual fusion path; PRICE statistics-core embedding
# goes directly to the prediction head. Filename gets the `noLLMres` tag.
run "mode 12 — inflatePRICE + PRICE_N + no_llm_residual" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    --inflate_price \
    --price_n \
    --price_random_init \
    --no_llm_residual \
    --n_cross_layers       "4" \
    --price_warmup_epochs  "4" \
    --freeze_llm_until_epoch "4"

echo ""
echo "============================================================"
echo "  All five TPC-DS runs done."
echo "============================================================"
