#!/bin/bash
# Compare modes 1, 2, 7, 7s, 7b, 7q, 12, 12q, 12w on TPC-DS and STATS (postgres backend, MiniLM-L6).
#
#   Mode 1  — LLM inference only          (no finetune,  no PRICE)
#   Mode 2  — LLM LoRA finetune           (LoRA finetune, no PRICE)
#   Mode 7  — JointPrice + PRICE_N        (LoRA finetune, LLM ⊕ PRICE → MLP)
#             PRICE_N: 75-dim filter w/ IN/NULL/OR/date/pairwise/outer-join
#             side flags + DNF expansion via --price_n_or. Partial outer-
#             encoding for non-simple CTE / scalar-subq-in-projection /
#             UNION-ALL-derived-table queries.
#   Mode 7s — JointPrice + PRICE_S        (LoRA finetune, LLM ⊕ PRICE → MLP)
#             PRICE_S: 43-dim filter (histogram + bounding-box range + sel),
#             IN/LIKE via bounding-box. Partial encoding on missing cols.
#   Mode 7b — JointPrice + PRICE_B        (LoRA finetune, LLM ⊕ PRICE → MLP)
#             PRICE_B (original PRICE design): 43-dim filter, ONLY equi-join
#             and col-op-literal predicates are kept. BETWEEN/IN/LIKE/NULL/
#             NOT/OR/subqueries are dropped without decomposition. Never
#             rejects a query — zero placeholder when nothing survives.
#   Mode 7q — Mode 7 + Stat-core ↔ QRT cross-attn
#             (--use_qrt_cross_attn enables a single self-attn layer over
#              [stat-core CLS || residual-SQL tokens] before LLM⊕PRICE concat.
#              Residual SQL = LIKE/EXISTS/IN-subq/scalar-subq/opaque fragments
#              that Sql2FeatureN can't encode. Path-suffix _qrt.)
#   Mode 12 — BiCrossAttentionJoint, cx=4 (LoRA finetune, bidirectional
#             cross-attention between LLM tokens and PRICE_N summary)
#             PRICE & cross_attn LR: 1e-3, no warmup → 2e-5 from epoch 0.
#   Mode 12q — Mode 12 + Stat-core ↔ QRT cross-attn
#             (QRT block refines stat-core CLS before biCross; biCross input
#              shape is unchanged. Path-suffix _qrt_biCrossAttn_…)
#   Mode 12w — same as mode 12 but with PRICE & cross_attn warmup:
#             5 epochs at lr=1e-4, then 2e-5. (Tests if a gentler ramp helps.)
#             Path-suffix differs (_pwm5_pLR0.0001) so it doesn't collide.
#
# All runs share: 4-bit quantization, batch size 4, 30 finetune epochs, seed 42.
# PRICE-using modes (7, 7q, 12, 12q, 12w) employ PRICE_N; 7s uses PRICE_S;
# 7b uses PRICE_B (original PRICE design). All use --price_random_init.
#
# By default the script runs ALL modes on TPC-DS first, then on STATS.
#
# Usage:
#   bash experiment_scripts/compare_modes_tpcds.sh                # all modes, both workloads
#   MODES="7 12" bash experiment_scripts/compare_modes_tpcds.sh   # mode subset
#   WORKLOADS="stats" bash experiment_scripts/compare_modes_tpcds.sh   # workload subset
#   MODES="12w" WORKLOADS="tpcds" bash compare_modes_tpcds.sh     # both subsets
#   SEEDS="42 43 44" bash experiment_scripts/compare_modes_tpcds.sh   # multi-seed
#
# Seeds: with joint-finetune weights now saved seedless (commit e92a317),
# the first seed pays the full LLM+PRICE+MLP finetune cost; subsequent
# seeds detect the existing seedless artifact, skip retrain, and only
# pay the cheap inference-time MLP retrain + per-seed result CSV write.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

source ~/venvs/tmpenv/bin/activate
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export GRAD_ACCUM_STEPS=${GRAD_ACCUM_STEPS:-4}

# Modes can be supplied as positional args (legacy) or via $MODES env var.
if [[ $# -gt 0 ]]; then
    MODES=("$@")
elif [[ -n "${MODES:-}" ]]; then
    read -ra MODES <<< "$MODES"
else
    MODES=(7b 7)
    # MODES=(1 2 7 12 12w)
fi

# Workloads via $WORKLOADS env var (space-separated), default both.
if [[ -n "${WORKLOADS:-}" ]]; then
    read -ra WORKLOADS_ARR <<< "$WORKLOADS"
else
    WORKLOADS_ARR=(tpcds tpch)
    # WORKLOADS_ARR=(tpcds stats)
fi

# Seeds via $SEEDS env var (space-separated), default 42.
# Multiple seeds reuse the same joint-finetune weights and only retrain
# the inference-time MLP head per seed.
SEEDS="${SEEDS:-42}"

# ─── Shared training arguments (workload set per-run via build_shared) ───
build_shared () {
    local wl="$1"
    SHARED=(
        --models                  "sentence-transformers/all-MiniLM-L6-v2"
        --task                    "time"
        --downstream              "mlp"
        --quantification          "4-bit"
        --bucketize               "None"
        --embed_size              "1000"
        --concat_true             "false"
        # NOTE: under --price_n_or each batch item expands to max_n_clauses rows
        # in the PRICE encoder, so the effective per-step batch is
        # ft_batch_size * max_n_clauses. With cx=4 cross-attn over LLM tokens, that
        # OOMs on a 16 GiB GPU at b=24 (max_clauses ≈ 9 for tpcds q13). Keep
        # ft_batch_size small under --price_n_or and use GRAD_ACCUM_STEPS to
        # control the effective optimization batch.
        --ft_batch_size           "4"
        --ft_num_epoch            "30"
        --removed_fields          ""
        --seeds                   "$SEEDS"
        --db                      "postgres"
        --workloads               "$wl"
        --checkpoint_interval     "5"
        --early_stop_patience     "15"
        --early_stop_after_epoch  "20"
        --finetune_method         "lora"
        --deterministic_algorithms
    )
}

PRICE_S_FLAGS=(
    --price_s
    --price_random_init
)

PRICE_B_FLAGS=(
    --price_b
    --price_random_init
)

# PRICE flags applied to modes 7 & 12 only.
# --price_n_or expands mixed-column OR into per-clause DNF so the OR-Transformer
# sees the disjunctive structure of queries like TPC-DS q13 instead of dropping
# the OR blocks as residual.
PRICE_N_FLAGS=(
    --price_n
    --price_n_or
    --price_random_init
)

# Cross-attn flags applied to modes 12 and 12w
CX4_FLAGS=(
    --inflate_price
    --n_cross_layers          "4"
)

# Stat-core ↔ QRT cross-attn flag (modes 7q and 12q).
QRT_FLAGS=(
    --use_qrt_cross_attn
)

# Mode 12 schedule: PRICE & cross_attn at base 1e-3, no warmup → 2e-5 from epoch 0.
MODE12_SCHED=(
    --price_warmup_epochs     "5"
    --freeze_llm_until_epoch  "5"
)

# Mode 12w schedule: 5 epochs warmup at 1e-4 → 2e-5 thereafter.
# (Path suffix gets _pwm5_pLR0.0001 so files don't overwrite mode 12's.)
MODE12W_SCHED=(
    --price_warmup_lr         "1e-4"
    --price_warmup_epochs     "5"
    --freeze_llm_until_epoch  "5"
)

run_mode () {
    local m="$1"
    local wl="$2"
    build_shared "$wl"
    echo ""
    echo "=========================================================="
    echo " Running mode $m  on $wl  (MiniLM-L6, b=4, e=30, seed=42)"
    echo "=========================================================="
    case "$m" in
        1|2)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode "$m"
            ;;
        7)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 "${PRICE_N_FLAGS[@]}"
            ;;
        7q)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 \
                "${PRICE_N_FLAGS[@]}" "${QRT_FLAGS[@]}"
            ;;
        7s)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 "${PRICE_S_FLAGS[@]}"
            ;;
        7b)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 "${PRICE_B_FLAGS[@]}"
            ;;
        12)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
                "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12_SCHED[@]}"
            ;;
        12q)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
                "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12_SCHED[@]}" \
                "${QRT_FLAGS[@]}"
            ;;
        12w)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
                "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12W_SCHED[@]}"
            ;;
        *)
            echo "Unknown mode: $m   (expected 1, 2, 7, 7s, 7b, 7q, 12, 12q, or 12w)"
            exit 1
            ;;
    esac
}

for wl in "${WORKLOADS_ARR[@]}"; do
    for m in "${MODES[@]}"; do
        run_mode "$m" "$wl"
    done
done

echo ""
echo "=========================================================="
echo " All requested runs complete."
echo "=========================================================="
echo "Result CSVs (test q_errors) per workload <wl>:"
echo "  results/postgres/results_Train_<wl>_Test_<wl>_ours/"
echo "  Mode 1 :  time_llm_*pretrained-None_*_seed42.csv"
echo "  Mode 2 :  time_llm_pretrained-lora_*_seed42.csv"
echo "  Mode 7 :  time_llm_price_pretrained-lora_price-joint_*priceN*_seed42.csv"
echo "  Mode 7s:  time_llm_price_pretrained-lora_price-joint_*priceS*_seed42.csv"
echo "  Mode 7b:  time_llm_price_pretrained-lora_price-joint_*priceB*_seed42.csv"
echo "  Mode 7q:  time_llm_price_pretrained-lora_price-joint_*priceN*_qrt_*_seed42.csv"
echo "  Mode 12:  time_llm_price_pretrained-lora_priceBiCrossAttnJoint_*_inflatePRICE*_cx4_*_seed42.csv"
echo "  Mode 12q: time_llm_price_pretrained-lora_priceBiCrossAttnJoint_*_inflatePRICE*_qrt*_cx4_*_seed42.csv"
echo "  Mode 12w: time_llm_price_pretrained-lora_priceBiCrossAttnJoint_*_inflatePRICE*_cx4*_pwm5_pLR0.0001_*_seed42.csv"
