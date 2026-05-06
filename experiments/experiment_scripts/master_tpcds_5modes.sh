#!/bin/bash
# TPC-DS five-mode comparison runner.
# Settings aligned with master_bicrossattn_inflatePRICE.sh:
#   - model:      sentence-transformers/all-MiniLM-L6-v2
#   - batch:      24
#   - epochs:     30
#   - seeds:      42 43 44
#   - 4 cross-attention layers, freeze LLM 5 epochs, PRICE warmup 5 epochs
#   - early stop patience 5 (after epoch 15)
#   - retrain MLP on converged embeddings
#
# Modes:
#   1) Pretrained LLM only           (--finetune_mode 1)
#   2) Finetuned LLM only            (--finetune_mode 2, LoRA)
#   3) LLM + pretrained PRICE        (--finetune_mode 7, JointPrice; no random init)
#   4) LLM + PRICE_N inflated        (--finetune_mode 12, BiCrossAttn + inflate + price_n)
#   5) PRICE_N inflated, no LLM res. (--finetune_mode 12 + --no_llm_residual)
#
# Filename suffixes encode every flag, so all five runs land in distinct
# weight / checkpoint / log / result paths.
#
# TPC-DS uses the template-based split: 81 train templates + 9 test templates,
# 10% of train+val held for val. Automatic when --workload_test tpcds.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

# ─── Flags shared by every run ────────────────────────────────────────────
COMMON=(
    --models                  "sentence-transformers/all-MiniLM-L6-v2"
    --task                    "time"
    --downstream              "mlp"
    --quantification          "4-bit"
    --bucketize               "None"
    --embed_size              "1000"
    --concat_true             "false"
    --ft_batch_size           "24"
    --ft_num_epoch            "30"
    --removed_fields          ""
    --seeds                   "42 43 44"
    --db                      "postgres"
    --workloads               "tpcds"
    --checkpoint_interval     "5"
    --early_stop_patience     "5"
    --early_stop_after_epoch  "15"
)

# ─── Joint-finetune flags (modes 7 and 12 only) ───────────────────────────
JOINT=(
    --freeze_llm_until_epoch  "5"
    --price_warmup_epochs     "5"
)

# ─── BiCrossAttn + inflatePRICE flags (mode 12 only) ──────────────────────
BICROSS_INFLATE=(
    --inflate_price
    --n_cross_layers          "4"
    --retrain_mlp
)

run() {
    local label="$1"; shift
    echo ""
    echo "============================================================"
    echo "  TPC-DS | $label"
    echo "============================================================"
    bash "$RUN_SCRIPT" "${COMMON[@]}" "$@"
}

# ─── Run 1: Pretrained LLM only ───────────────────────────────────────────
run "mode 1 — pretrained LLM" \
    --finetune_mode "1"

# ─── Run 2: Finetuned LLM only (LoRA) ─────────────────────────────────────
run "mode 2 — finetune LLM (LoRA)" \
    --finetune_mode "2" \
    --finetune_method "lora"

# ─── Run 3: LLM + pretrained PRICE (JointPrice) ───────────────────────────
# No --price_random_init → pretrained PRICE weights (filter_dim=43) are loaded.
# No PRICE_S/M/N flag → base PRICE shape, matching the pretrained checkpoint.
run "mode 7 — LLM + pretrained PRICE (joint)" \
    --finetune_mode "7" \
    --finetune_method "lora" \
    "${JOINT[@]}"

# ─── Run 4: LLM + inflated bidirectional cross-attn + PRICE_N ─────────────
# --price_n: enables all four PRICE_N sub-flags (parsing/filter/fanout/pairwise).
# --price_random_init: PRICE_N filter_dim=75 ≠ pretrained's 43, so random-init.
# BICROSS_INFLATE: inflated bi-cross-attention with 4 cross-attn layers,
# retrain_mlp on converged embeddings.
run "mode 12 — inflatePRICE + PRICE_N" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    --price_n \
    --price_random_init \
    "${JOINT[@]}" \
    "${BICROSS_INFLATE[@]}"

# ─── Run 5: Same as Run 4 + --no_llm_residual ─────────────────────────────
# Disables the LLM-residual fusion path; PRICE statistics-core embedding
# goes directly to the prediction head. Filename gets the `noLLMres` tag.
run "mode 12 — inflatePRICE + PRICE_N + no_llm_residual" \
    --finetune_mode "12" \
    --finetune_method "lora" \
    --price_n \
    --price_random_init \
    --no_llm_residual \
    "${JOINT[@]}" \
    "${BICROSS_INFLATE[@]}"

echo ""
echo "============================================================"
echo "  All five TPC-DS runs done."
echo "============================================================"
