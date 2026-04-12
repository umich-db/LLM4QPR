#!/usr/bin/env bash
#
# Surrogate-based model selection v2 — shell wrapper.
#
# Phase 1: Runs model_selection_v2.py (surrogate search → selects best model)
# Phase 2 (optional): Runs JointPrice finetuning (mode 7) on the selected model
#
# Usage:
#   bash run_model_selection_v2.sh --latency_limit 50 --workload stats --dry_run
#   bash run_model_selection_v2.sh --latency_limit 50 --workload stats --finetune
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # experiments/

# Defaults
LATENCY_LIMIT=""
WORKLOAD="stats"
TASK="time"
DB="postgres"
QUANTIFICATION="4-bit"
EMBED_SIZE=1000
INIT_BUDGET=24
BATCH_SIZE=4
MAX_EVALS=80
MAX_EVAL_QUERIES=500
RANDOM_STATE=42
DRY_RUN=""
FINETUNE=""
PRICE_S=""
CSV=""
OUTPUT=""
NO_VISUALIZE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --latency_limit)    LATENCY_LIMIT="$2";     shift 2 ;;
        --workload)         WORKLOAD="$2";           shift 2 ;;
        --task)             TASK="$2";               shift 2 ;;
        --db)               DB="$2";                 shift 2 ;;
        --quantification)   QUANTIFICATION="$2";     shift 2 ;;
        --embed_size)       EMBED_SIZE="$2";         shift 2 ;;
        --init_budget)      INIT_BUDGET="$2";        shift 2 ;;
        --batch_size)       BATCH_SIZE="$2";         shift 2 ;;
        --max_evals)        MAX_EVALS="$2";          shift 2 ;;
        --max_eval_queries) MAX_EVAL_QUERIES="$2";   shift 2 ;;
        --random_state)     RANDOM_STATE="$2";       shift 2 ;;
        --dry_run)          DRY_RUN="--dry_run";     shift 1 ;;
        --finetune)         FINETUNE="1";            shift 1 ;;
        --price_s)          PRICE_S="--price_s";     shift 1 ;;
        --csv)              CSV="$2";                shift 2 ;;
        --output)           OUTPUT="$2";             shift 2 ;;
        --no_visualize)     NO_VISUALIZE="--no_visualize"; shift 1 ;;
        --visualize)        NO_VISUALIZE="--visualize";    shift 1 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

if [[ -z "$LATENCY_LIMIT" ]]; then
    echo "ERROR: --latency_limit is required"
    exit 1
fi

# Build output path
if [[ -z "$OUTPUT" ]]; then
    OUTPUT="model_selection_v2_result_${WORKLOAD}_${LATENCY_LIMIT%.*}ms.json"
fi

echo "===== Model Selection v2 (Surrogate-Based) ====="
echo "Latency limit: ${LATENCY_LIMIT} ms"
echo "Workload: ${WORKLOAD}, Task: ${TASK}, DB: ${DB}"
echo "Budget: init=${INIT_BUDGET}, batch=${BATCH_SIZE}, max=${MAX_EVALS}"
echo ""

# Phase 1: Surrogate search
CSV_FLAG=""
[[ -n "$CSV" ]] && CSV_FLAG="--csv $CSV"

python "$SCRIPT_DIR/model_selection_v2.py" \
    --latency_limit "$LATENCY_LIMIT" \
    --workload "$WORKLOAD" \
    --task "$TASK" \
    --db "$DB" \
    --quantification "$QUANTIFICATION" \
    --embed_size "$EMBED_SIZE" \
    --init_budget "$INIT_BUDGET" \
    --batch_size "$BATCH_SIZE" \
    --max_evals "$MAX_EVALS" \
    --max_eval_queries "$MAX_EVAL_QUERIES" \
    --random_state "$RANDOM_STATE" \
    --output "$OUTPUT" \
    $DRY_RUN \
    $PRICE_S \
    $NO_VISUALIZE \
    $CSV_FLAG

# Read selected model from JSON
SELECTED_MODEL=$(python3 -c "import json; d=json.load(open('$OUTPUT')); print(d.get('selected_model') or '')")

if [[ -z "$SELECTED_MODEL" ]]; then
    echo ""
    echo "No feasible model selected. Exiting."
    exit 0
fi

echo ""
echo "===== Selected model: ${SELECTED_MODEL} ====="

# Phase 2 (optional): JointPrice finetuning on the selected model
if [[ -n "$FINETUNE" && -z "$DRY_RUN" ]]; then
    echo ""
    echo "===== Phase 2: JointPrice Finetuning (mode 7) ====="
    PRICE_S_FLAG=""
    [[ -n "$PRICE_S" ]] && PRICE_S_FLAG="--price_s"

    bash "$SCRIPT_DIR/run_different_llms.sh" \
        --models "$SELECTED_MODEL" \
        --workloads "$WORKLOAD" \
        --task "$TASK" \
        --finetune_mode 7 \
        --seeds "42" \
        --db "$DB" \
        --quantification "$QUANTIFICATION" \
        --embed_size "$EMBED_SIZE" \
        --downstream "mlp" \
        --bucketize "None" \
        --concat_true "false" \
        --removed_fields "" \
        $PRICE_S_FLAG

    echo "Finetuning complete for ${SELECTED_MODEL}"
fi

echo ""
echo "Done. Results: ${OUTPUT}"
