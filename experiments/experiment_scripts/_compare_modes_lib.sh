#!/bin/bash
# Shared library for compare_modes_<...>.sh scripts. Sourced, not executed.
#
# Provides:
#   - PRICE_B_FLAGS / PRICE_N_FLAGS / CX4_FLAGS
#   - MODE12_SCHED / MODE12W_SCHED
#   - build_shared "$wl"  → fills the SHARED array (uses $DB_ENGINE)
#   - run_mode  "$m" "$wl" → dispatches one mode for one workload
#   - run_ablation         → iterates DB_ENGINES × WORKLOADS_ARR × MODES_ARR,
#                             skipping (db, wl) combos with no plan data.
#
# Callers set:
#   DB_ENGINES   array (e.g. (postgres duckdb spark))
#   WORKLOADS_ARR  array
#   MODES_ARR    array (subset of 1, 2, 7, 7b, 8, 12, 12w)
#   MODEL        e.g. "sentence-transformers/all-MiniLM-L12-v2"
#   SEEDS        e.g. "42"
#   FT_BATCH_SIZE, FT_NUM_EPOCH, ...  (or accept defaults)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_different_llms.sh"
source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
# Default to GPU 0 (every CUDA host has it; the old default of 1 hid the GPU
# on single-GPU machines like dbresearch3 → silent CPU fallback). Override
# with `CUDA_VISIBLE_DEVICES=N bash …` to target a different device.
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

: "${MODEL:=sentence-transformers/all-MiniLM-L12-v2}"
: "${SEEDS:=42}"
: "${FT_BATCH_SIZE:=24}"
: "${FT_NUM_EPOCH:=30}"

PRICE_B_FLAGS=(--price_b --price_random_init)
PRICE_N_FLAGS=(--price_n --price_n_or --price_random_init)
CX4_FLAGS=(--inflate_price --n_cross_layers "4")
# Mode 12: PRICE_N + cx4 + warmup (pwm5, frzLLM5).
MODE12_SCHED=(--price_warmup_epochs "5" --freeze_llm_until_epoch "5")
# Mode 12w: PRICE_N + cx4, no warmup (matches new defaults; emitted explicitly
# so future default changes don't silently flip behaviour).
MODE12W_SCHED=(--price_warmup_epochs "0" --freeze_llm_until_epoch "0")

build_shared () {
    local wl="$1"
    # tpch / tpcds plans are deeper than imdb/stats and OOM on a 16 GB GPU at
    # ft_batch_size=24. Drop the micro-batch to 4 and accumulate over 6 steps
    # so the effective per-step gradient is still computed over 24 plans.
    local ft_bs="$FT_BATCH_SIZE"
    # Default to 1 each call — do NOT inherit a previous workload's value via
    # ${GRAD_ACCUM_STEPS:-1} (the export below makes the variable sticky across
    # iterations, which would silently leave stats/imdb running at 6 after a
    # tpcds iteration in the same shell).
    local grad_accum="1"
    case "$wl" in
        tpch|tpcds)
            ft_bs="4"
            grad_accum="6"
            ;;
    esac
    export GRAD_ACCUM_STEPS="$grad_accum"
    SHARED=(
        --models                  "$MODEL"
        --task                    "time"
        --downstream              "mlp"
        --quantification          "4-bit"
        --bucketize               "None"
        --embed_size              "1000"
        --concat_true             "false"
        --ft_batch_size           "$ft_bs"
        --ft_num_epoch            "$FT_NUM_EPOCH"
        --removed_fields          "${REMOVED_FIELDS:-}"
        --seeds                   "$SEEDS"
        --db                      "$DB_ENGINE"
        --workloads               "$wl"
        --checkpoint_interval     "5"
        --early_stop_patience     "5"
        --early_stop_after_epoch  "20"
        --finetune_method         "lora"
    )
}

# Per-(db, wl) data-availability check. queryPlans dir must have at least one
# CSV matching the workload (or the canonical imdb dir for syn/job/job_full).
plans_exist () {
    local db="$1"; local wl="$2"
    local canon
    case "$wl" in
        syn|job|job_full|jobm) canon="imdb" ;;
        *)                      canon="$wl" ;;
    esac
    [ -d "../queryPlans/${canon}/${db}/" ] && \
      ls "../queryPlans/${canon}/${db}/"long_raw_${db}_${wl}*.csv >/dev/null 2>&1 || \
      ls "../queryPlans/${canon}/${db}/"long_raw_${db}_${canon}.csv >/dev/null 2>&1
}

run_mode () {
    local m="$1"; local wl="$2"
    build_shared "$wl"
    echo ""
    echo "=========================================================="
    echo "  Running mode $m  on $wl  (db=$DB_ENGINE, $MODEL, b=$FT_BATCH_SIZE, e=$FT_NUM_EPOCH, seeds=$SEEDS)"
    echo "=========================================================="
    case "$m" in
        1|2)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode "$m"
            ;;
        7b)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 "${PRICE_B_FLAGS[@]}"
            ;;
        7)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 7 "${PRICE_N_FLAGS[@]}"
            ;;
        8)
            # Frozen-LLM concat: mode 7's recipe but the LLM stays frozen
            # (pretrained) the whole run and is never forwarded per batch —
            # PRICE+MLP train on cached pooled embeddings (the mode-1
            # pretrained-None cache). Equivalent to mode 7 + frzLLM999, minus
            # the per-batch LLM forward.
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 8 "${PRICE_N_FLAGS[@]}"
            ;;
        12)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
                "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12_SCHED[@]}"
            ;;
        12w)
            bash "$RUN_SCRIPT" "${SHARED[@]}" --finetune_mode 12 \
                "${PRICE_N_FLAGS[@]}" "${CX4_FLAGS[@]}" "${MODE12W_SCHED[@]}"
            ;;
        *)
            echo "Unknown mode: $m   (expected 1, 2, 7, 7b, 8, 12, 12w)" >&2
            exit 1
            ;;
    esac
}

# WORKLOADS_ARR iteration order matters: when a canonical training set is
# shared (syn / job / job_full all canonicalise to 'imdb' via train.py's
# _CANONICAL_MAP), the FIRST workload's run produces the weight file, and
# subsequent workloads with the same canonical name re-use it via the
# --skip_train_load_finetuned_weights guard in run_llm_time.sh.
run_ablation () {
    local n_skipped=0; local n_run=0
    for db in "${DB_ENGINES[@]}"; do
        export DB_ENGINE="$db"
        for wl in "${WORKLOADS_ARR[@]}"; do
            if ! plans_exist "$db" "$wl"; then
                echo "[skip] no plans for db=$db workload=$wl"
                n_skipped=$((n_skipped+1))
                continue
            fi
            for m in "${MODES_ARR[@]}"; do
                run_mode "$m" "$wl"
                n_run=$((n_run+1))
            done
        done
    done
    echo ""
    echo "=========================================================="
    echo "  Done. Ran $n_run (db, workload, mode) combinations; skipped $n_skipped (db, workload) for missing plans."
    echo "=========================================================="
}
