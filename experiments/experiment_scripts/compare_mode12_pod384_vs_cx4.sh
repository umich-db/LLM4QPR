#!/bin/bash
# Compare three Mode 12 (BiCrossAttentionJoint + inflate_price) variants on TPC-DS:
#
#   Mode 12 cx=0 / pod=384:
#       --inflate_price --n_cross_layers 0 --price_output_dim 384
#       PRICE encoder produces a 384-d summary directly (regression_model.linear
#       built at 272 -> 384). No cross-attn layers exist. LLM concats with the
#       384-d PRICE summary -> MLP. Mirrors mode 7's structure but with PRICE
#       output sized to LLM hidden dim instead of 512.
#
#   Mode 12 cx=4 / noop:
#       --inflate_price --n_cross_layers 4 --cross_attn_noop
#       4 cross-attn blocks ARE constructed (their parameters live in the
#       model, get saved, get loaded at inference) but their forward is
#       SKIPPED. Functionally equivalent to cx=0/pod=384 in output, but:
#         - the cross-attn parameters consume RNG at init (shifts MLP init)
#         - they're carried along in the saved checkpoint
#         - they're loaded at inference (model has the same architecture)
#       Useful to test whether the mere presence of cross-attn parameters
#       in the optimization (with zero gradient, unused) affects the result.
#
#   Mode 12 cx=4:
#       --inflate_price --n_cross_layers 4
#       Standard mode 12: PRICE summary attends to LLM tokens through 4 cross
#       attention layers. PRICE output is 384-d automatically (cx>0 sets
#       query_hidden_dim=embed_size).
#
# All runs share TPC-DS template-split, MiniLM-L6, 4-bit, b=4, e=30, seed=42,
# and PRICE_N + price_n_or (multi-clause OR-Transformer wired in).
#
# Usage:
#   bash experiment_scripts/compare_mode12_pod384_vs_cx4.sh                # all three
#   bash experiment_scripts/compare_mode12_pod384_vs_cx4.sh cx0            # only cx=0/pod=384
#   bash experiment_scripts/compare_mode12_pod384_vs_cx4.sh cx4_noop       # only cx=4/noop
#   bash experiment_scripts/compare_mode12_pod384_vs_cx4.sh cx4            # only cx=4
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"

source ~/venvs/tmpenv/bin/activate
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export GRAD_ACCUM_STEPS=${GRAD_ACCUM_STEPS:-4}

VARIANTS=("$@")
if [[ ${#VARIANTS[@]} -eq 0 ]]; then
    VARIANTS=(cx0 cx4_noop cx4)
fi

SHARED=(
    --models                  "sentence-transformers/all-MiniLM-L6-v2"
    --task                    "time"
    --downstream              "mlp"
    --quantification          "4-bit"
    --bucketize               "None"
    --embed_size              "1000"
    --concat_true             "false"
    --ft_batch_size           "4"
    --ft_num_epoch            "30"
    --removed_fields          ""
    --seeds                   "42"
    --db                      "postgres"
    --workloads               "tpcds"
    --checkpoint_interval     "5"
    --early_stop_patience     "10"
    --early_stop_after_epoch  "20"
    --finetune_method         "lora"
    --freeze_llm_until_epoch  "0"
    --deterministic_algorithms
    --finetune_mode           "12"
    --inflate_price
    --price_n
    --price_n_or
    --price_random_init
    --price_warmup_epochs     "0"
)

run_variant () {
    local v="$1"
    echo ""
    echo "=========================================================="
    echo " Mode 12 / variant=$v  (TPC-DS, MiniLM-L6, b=4, e=30)"
    echo "=========================================================="
    case "$v" in
        cx0)
            bash "$RUN_SCRIPT" "${SHARED[@]}" \
                --n_cross_layers 0 \
                # --price_output_dim 384
            ;;
        cx4_noop)
            # cross_attn_blocks constructed but forward is no-op'd.
            # Path suffix gets `_noop` so weights don't collide with cx4.
            bash "$RUN_SCRIPT" "${SHARED[@]}" \
                --n_cross_layers 4 \
                --cross_attn_noop
            ;;
        cx4)
            bash "$RUN_SCRIPT" "${SHARED[@]}" \
                --n_cross_layers 4
            ;;
        *)
            echo "Unknown variant: $v   (expected cx0, cx4_noop, or cx4)"
            exit 1
            ;;
    esac
}

for v in "${VARIANTS[@]}"; do
    run_variant "$v"
done

echo ""
echo "=========================================================="
echo " All requested variants complete."
echo "=========================================================="
echo "Result CSVs in results/postgres/results_Train_tpcds_Test_tpcds_ours/"
echo "  cx=0/pod=384:  *priceBiCrossAttnJoint*inflatePRICE*_cx0_*pod384_*_seed42.csv"
echo "  cx=4/noop:     *priceBiCrossAttnJoint*inflatePRICE*_cx4_noop_*_seed42.csv"
echo "  cx=4:          *priceBiCrossAttnJoint*inflatePRICE*_cx4_*_seed42.csv"
