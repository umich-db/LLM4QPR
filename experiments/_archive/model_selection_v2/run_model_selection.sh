#!/bin/bash
# Latency-Aware Model Selection Pipeline
#
# Given a per-query latency budget (ms), automatically:
#   Phase 1: Binary search across models (sorted by size) to find largest feasible model
#   Phase 2: Evaluate nearby feasible models with inference-only accuracy test
#   Phase 3: Pick fastest model within epsilon of best accuracy
#   Phase 4: Run full JointPrice finetuning (mode 7) with selected model
#
# Usage:
#   cd experiments
#   bash experiment_scripts/run_model_selection.sh \
#       --latency_limit 50 --workloads "stats job" --task "time" \
#       --seeds "42 43 44" --db "postgres" --quantification "4-bit" \
#       --ft_batch_size "32" --ft_num_epoch "20" --price_s --checkpoint_interval "5"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Defaults ────────────────────────────────────────────────────────
LATENCY_LIMIT=""
WORKLOADS_STR=""
TASK="time"
SEEDS_STR="42 43 44"
DB="postgres"
QUANTIFICATION="4-bit"
FT_BATCH_SIZE="32"
FT_NUM_EPOCH="20"
EPSILON="0.1"
PRICE_S_FLAG=""
CHECKPOINT_INTERVAL="5"
NUM_PROBE_QUERIES="100"
MAX_EVAL_QUERIES="10000"
PRICE_RANDOM_INIT_FLAG=""
EMBED_SIZE="1000"
LOG_DIR=""

# ─── CLI argument parsing ────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --latency_limit)        LATENCY_LIMIT="$2";        shift 2 ;;
        --workloads)            WORKLOADS_STR="$2";         shift 2 ;;
        --task)                 TASK="$2";                  shift 2 ;;
        --seeds)                SEEDS_STR="$2";             shift 2 ;;
        --db)                   DB="$2";                    shift 2 ;;
        --quantification)       QUANTIFICATION="$2";        shift 2 ;;
        --ft_batch_size)        FT_BATCH_SIZE="$2";         shift 2 ;;
        --ft_num_epoch)         FT_NUM_EPOCH="$2";          shift 2 ;;
        --epsilon)              EPSILON="$2";               shift 2 ;;
        --price_s)              PRICE_S_FLAG="--price_s";   shift 1 ;;
        --price_random_init)    PRICE_RANDOM_INIT_FLAG="--price_random_init"; shift 1 ;;
        --checkpoint_interval)  CHECKPOINT_INTERVAL="$2";   shift 2 ;;
        --num_probe_queries)    NUM_PROBE_QUERIES="$2";     shift 2 ;;
        --max_eval_queries)     MAX_EVAL_QUERIES="$2";      shift 2 ;;
        --embed_size)           EMBED_SIZE="$2";            shift 2 ;;
        --log_dir)              LOG_DIR="$2";               shift 2 ;;
        *)
            echo "Unknown flag: $1"
            exit 1
            ;;
    esac
done

# ─── Validate required arguments ─────────────────────────────────────
if [[ -z "$LATENCY_LIMIT" ]]; then
    echo "Error: --latency_limit is required"
    exit 1
fi
if [[ -z "$WORKLOADS_STR" ]]; then
    echo "Error: --workloads is required"
    exit 1
fi

# Parse workloads into array
read -ra WORKLOADS <<< "$WORKLOADS_STR"
FIRST_WORKLOAD="${WORKLOADS[0]}"

# ─── Set up logging ──────────────────────────────────────────────────
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [[ -z "$LOG_DIR" ]]; then
    LOG_DIR="logs/model_selection"
fi
mkdir -p "$LOG_DIR"

# Build descriptive log filename:
#   model_selection_lat{LIMIT}_{DB}_{WL}_{TASK}_s{SEEDS}_e{EPOCHS}_{FLAGS}_{TIMESTAMP}
LOG_SEEDS_SHORT=$(echo "$SEEDS_STR" | tr ' ' '-')
LOG_WL_SHORT=$(echo "$WORKLOADS_STR" | tr ' ' '-')
LOG_FLAGS=""
[[ -n "$PRICE_S_FLAG" ]] && LOG_FLAGS="${LOG_FLAGS}_priceS"
[[ -n "$PRICE_RANDOM_INIT_FLAG" ]] && LOG_FLAGS="${LOG_FLAGS}_randInit"
LOG_QUANT_SHORT=$(echo "$QUANTIFICATION" | tr -d '-')  # "4-bit" → "4bit"
LOG_BASENAME="model_selection_lat${LATENCY_LIMIT}_${DB}_${LOG_WL_SHORT}_${TASK}_s${LOG_SEEDS_SHORT}_e${FT_NUM_EPOCH}_q${LOG_QUANT_SHORT}${LOG_FLAGS}_${TIMESTAMP}"
LOG_FILE="${LOG_DIR}/${LOG_BASENAME}.log"
JSON_FILE="${LOG_DIR}/${LOG_BASENAME}.json"

# log: write to both stdout and the log file (with timestamp prefix in log)
# Supports -n flag for no-trailing-newline on stdout (log file always gets newline)
log() {
    local echo_flag=""
    if [[ "${1:-}" == "-n" ]]; then
        echo_flag="-n"
        shift
    fi
    local msg="$*"
    echo $echo_flag "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" >> "$LOG_FILE"
}

# log_only: write only to the log file (for verbose details)
log_only() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Initialize log
{
    echo "# Model Selection Log"
    echo "# Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Command: $0 $*" 2>/dev/null || echo "# Command: $0"
    echo ""
} > "$LOG_FILE"

log "============================================================"
log " Latency-Aware Model Selection Pipeline"
log "============================================================"
log "Latency limit:     ${LATENCY_LIMIT} ms/query"
log "Workloads:         ${WORKLOADS_STR}"
log "Task:              ${TASK}"
log "Seeds:             ${SEEDS_STR}"
log "DB:                ${DB}"
log "Quantification:    ${QUANTIFICATION}"
log "Epsilon:           ${EPSILON}"
log "Probe queries:     ${NUM_PROBE_QUERIES}"
log "Max eval queries:  ${MAX_EVAL_QUERIES}"
log "Log file:          ${LOG_FILE}"
log "JSON summary:      ${JSON_FILE}"
log "============================================================"
log ""

# ─── Model list (sorted by parameter count ascending) ────────────────
MODELS=(
    "NeuML/bert-hash-femto-embeddings"              #   244K
    "NeuML/bert-hash-pico-embeddings"               #   448K
    "NeuML/bert-hash-nano-embeddings"               #   970K
    # NeuML/pubmedbert-base-embeddings-1M uses model2vec arch, unsupported by transformers
    "prajjwal1/bert-tiny"                           #   4.4M
    "google/bert_uncased_L-2_H-128_A-2"             #   4.2M
    "google/bert_uncased_L-4_H-128_A-2"             #   4.5M
    "google/bert_uncased_L-6_H-128_A-2"             #   4.8M
    "google/bert_uncased_L-8_H-128_A-2"             #   5.1M
    "google/bert_uncased_L-10_H-128_A-2"            #   5.4M
    "google/bert_uncased_L-12_H-128_A-2"            #   5.7M
    "EleutherAI/pythia-14m"                         #   7.1M
    "EleutherAI/pythia-14m-deduped"                 #   7.1M
    "google/bert_uncased_L-2_H-256_A-4"             #   8.8M
    "google/electra-small-generator"                #   8.8M
    "google/bert_uncased_L-4_H-256_A-4"             #  10.2M
    "albert/albert-base-v1"                         #  11.7M
    "albert/albert-base-v2"                         #  11.7M
    "google/bert_uncased_L-6_H-256_A-4"             #  11.5M
    "sentence-transformers/paraphrase-albert-small-v2" #  11M
    "google/bert_uncased_L-8_H-256_A-4"             #  12.9M
    "google/electra-small-discriminator"            #  13.5M
    "google/bert_uncased_L-10_H-256_A-4"            #  14.2M
    "google/bert_uncased_L-12_H-256_A-4"            #  15.5M
    "sentence-transformers/paraphrase-MiniLM-L3-v2" #  17.4M
    "albert/albert-large-v1"                        #  17.7M
    "albert/albert-large-v2"                        #  17.7M
    "sentence-transformers/paraphrase-MiniLM-L6-v2" #  22.7M
    "sentence-transformers/all-MiniLM-L6-v2"        #  22.7M
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1" #  22.7M
    "sentence-transformers/multi-qa-MiniLM-L6-dot-v1" #  22.7M
    "nreimers/MiniLM-L6-H384-uncased"              #  22.7M
    "microsoft/MiniLM-L12-H384-uncased"             #  22.9M
    "google/mobilebert-uncased"                     #  25.3M
    "EleutherAI/pythia-31m"                         #  24.8M
    "EleutherAI/pythia-31m-deduped"                 #  24.8M
    "google/bert_uncased_L-2_H-512_A-8"             #  24.1M
    "google/bert_uncased_L-4_H-512_A-8"             #  27.9M
    "google/bert_uncased_L-6_H-512_A-8"             #  31.7M
    "intfloat/e5-small-v2"                          #    33M
    "sentence-transformers/all-MiniLM-L12-v2"       #  33.4M
    "sentence-transformers/paraphrase-MiniLM-L12-v2" #  33.4M
    "google/bert_uncased_L-8_H-512_A-8"             #  35.4M
    "google/bert_uncased_L-10_H-512_A-8"            #  39.2M
    "sentence-transformers/paraphrase-albert-base-v2" #  11.8M
    "google/bert_uncased_L-12_H-512_A-8"            #  43.0M
    "microsoft/deberta-v3-xsmall"                   #  22M
    "microsoft/deberta-v3-small"                    #  44M
    "google/electra-base-generator"                 #  33.6M
    "google/bert_uncased_L-2_H-768_A-12"            #  46.5M
    "google/bert_uncased_L-4_H-768_A-12"            #  52.7M
    "google/bert_uncased_L-6_H-768_A-12"            #  58.8M
    "albert/albert-xlarge-v1"                       #  58.7M
    "albert/albert-xlarge-v2"                       #  58.7M
    "distilbert/distilbert-base-uncased"            #  66.4M
    "distilbert/distilbert-base-cased"              #  66.4M
    "distilbert/distilroberta-base"                 #  82.1M
    "distilbert/distilbert-base-multilingual-cased" #  135M
    "distilbert/distilgpt2"                         #  82M
    "EleutherAI/pythia-70m"                         #  52.7M
    "EleutherAI/pythia-70m-deduped"                 #  52.7M
    "google/bert_uncased_L-8_H-768_A-12"            #  65.0M
    "google/bert_uncased_L-10_H-768_A-12"           #  71.2M
    "google/bert_uncased_L-12_H-768_A-12"           #  77.3M  (≈ BERT-base)
    "facebook/opt-125m"                             #  83.1M
    "HuggingFaceTB/SmolLM-135M"                     #  81.9M
    "HuggingFaceTB/SmolLM-135M-Instruct"            #  81.9M
    "HuggingFaceTB/SmolLM2-135M"                    #  81.9M
    "HuggingFaceTB/SmolLM2-135M-Instruct"           #  81.9M
    "google-bert/bert-base-uncased"                 # 110M
    "google-bert/bert-base-cased"                   # 110M
    "google-bert/bert-base-multilingual-cased"      # 179M
    "google-bert/bert-base-multilingual-uncased"    # 168M
    "google/electra-base-discriminator"             # 110M
    "sentence-transformers/all-mpnet-base-v2"       # 110M
    "sentence-transformers/paraphrase-mpnet-base-v2" # 110M
    "sentence-transformers/multi-qa-mpnet-base-cos-v1" # 110M
    "sentence-transformers/paraphrase-TinyBERT-L6-v2" #  66M
    "sentence-transformers/multi-qa-distilbert-cos-v1" #  66M
    "sentence-transformers/multi-qa-distilbert-dot-v1" #  66M
    "EleutherAI/gpt-neo-125m"                      # 125M
    "FacebookAI/roberta-base"                       # 125M
    "FacebookAI/xlm-roberta-base"                   # 278M
    "microsoft/deberta-v3-base"                     # 184M
    "microsoft/mdeberta-v3-base"                    # 279M
    "nomic-ai/nomic-embed-text-v1.5"                #   137M
    "Alibaba-NLP/gte-modernbert-base"               #   149M
    "nomic-ai/modernbert-embed-base"                #   149M
    "answerdotai/ModernBERT-base"                   # 149M
    "EleutherAI/pythia-160m"                        # 162M
    "EleutherAI/pythia-160m-deduped"                # 162M
    "albert/albert-xxlarge-v1"                      # 223M
    "albert/albert-xxlarge-v2"                      # 223M
    "google/gemma-3-270m"                           #   270M
    "google/embeddinggemma-300m"                    #   300M
    "facebook/opt-350m"                             # 331M
    "google/electra-large-generator"                # 335M
    "google/electra-large-discriminator"            # 335M
    "microsoft/deberta-v3-large"                    # 304M
    "HuggingFaceTB/SmolLM-360M"                     # 360M
    "HuggingFaceTB/SmolLM-360M-Instruct"            # 360M
    "HuggingFaceTB/SmolLM2-360M"                    # 360M
    "HuggingFaceTB/SmolLM2-360M-Instruct"           # 360M
    "FacebookAI/roberta-large"                      # 355M
    "FacebookAI/xlm-roberta-large"                  # 559M
    "answerdotai/ModernBERT-large"                  # 395M
    "EleutherAI/pythia-410m"                        # 405M
    "EleutherAI/pythia-410m-deduped"                # 405M
    "Qwen/Qwen1.5-0.5B"                            #   0.5B
    "Qwen/Qwen1.5-0.5B-Chat"                       #   0.5B
    "Qwen/Qwen2-0.5B"                              #   0.5B
    "Qwen/Qwen2-0.5B-Instruct"                     #   0.5B
    "Qwen/Qwen2.5-0.5B"                            #   0.5B
    "Qwen/Qwen2.5-0.5B-Instruct"                   #   0.5B
    "Qwen/Qwen2.5-Coder-0.5B"                      #   0.5B
    "Qwen/Qwen2.5-Coder-0.5B-Instruct"             #   0.5B
    "Qwen/Qwen3-Embedding-0.6B"                    #   0.6B
    "Qwen/Qwen3-0.6B"                              #   0.6B
)
NUM_MODELS=${#MODELS[@]}

# ─── GPU selection ────────────────────────────────────────────────────
# If CUDA_VISIBLE_DEVICES is not already set, auto-detect the most capable GPU
# (highest compute capability) to avoid FlashAttention errors on older GPUs.
# We use PCI_BUS_ID ordering so nvidia-smi indices match CUDA indices.
export CUDA_DEVICE_ORDER=PCI_BUS_ID
if [[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]; then
    BEST_GPU=$(nvidia-smi --query-gpu=index,compute_cap --format=csv,noheader 2>/dev/null \
        | sort -t, -k2 -rn | head -1 | cut -d, -f1 | tr -d ' ')
    if [[ -n "$BEST_GPU" ]]; then
        export CUDA_VISIBLE_DEVICES="$BEST_GPU"
        log "Auto-selected GPU ${BEST_GPU} (highest compute capability)"
        log_only "  $(nvidia-smi --query-gpu=index,name,compute_cap,memory.total --format=csv,noheader -i "$BEST_GPU")"
    fi
fi

# ─── Helper: run latency probe ───────────────────────────────────────
# Returns the full JSON on stdout; model-loading noise goes to the log file.
probe_latency() {
    local model="$1"
    python "$SCRIPT_DIR/latency_probe.py" \
        --model_name "$model" \
        --workload "$FIRST_WORKLOAD" \
        --db "$DB" \
        --num_queries "$NUM_PROBE_QUERIES" \
        --quantification "$QUANTIFICATION" \
        2>>"$LOG_FILE"
}

# ─── Helper: extract avg_ms from probe JSON ──────────────────────────
extract_avg_ms() {
    python3 -c "import sys,json; print(json.load(sys.stdin)['avg_ms'])"
}

# ─── Helper: extract full probe stats from JSON ──────────────────────
extract_probe_stats() {
    python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d:
    print('ERROR: ' + d['error'], file=sys.stderr)
    sys.exit(1)
print(f\"avg={d['avg_ms']}ms  p50={d['p50_ms']}ms  p95={d['p95_ms']}ms  n={d['num_queries']}\")
"
}

# =====================================================================
# Phase 1: Binary Search for Latency Feasibility
# =====================================================================
log "[Phase 1] Binary search: testing up to ${NUM_MODELS} models with latency limit ${LATENCY_LIMIT} ms/query"
log ""

lo=0
hi=$((NUM_MODELS - 1))
best_feasible=-1

# Cache: associative arrays for latency results and full probe JSON
declare -A LATENCY_CACHE
declare -A PROBE_JSON_CACHE

while [ $lo -le $hi ]; do
    mid=$(( (lo + hi) / 2 ))
    model="${MODELS[$mid]}"
    short_name=$(basename "$model")

    log -n "[Phase 1] Testing ${model} (idx=${mid})... "
    log_only "  Binary search state: lo=${lo} hi=${hi} mid=${mid}"

    result=$(probe_latency "$model" || true)
    avg_ms=$(echo "$result" | extract_avg_ms 2>/dev/null || true)

    # Check if probe returned an error
    if [[ -z "$avg_ms" || "$avg_ms" == "null" ]]; then
        log "FAILED (probe error), skipping"
        log_only "  Probe raw output: ${result}"
        hi=$((mid - 1))
        continue
    fi

    # Log the full probe result
    probe_detail=$(echo "$result" | extract_probe_stats 2>/dev/null || true)
    log_only "  Probe detail: ${probe_detail}"
    log_only "  Probe raw JSON: ${result}"

    LATENCY_CACHE["$mid"]="$avg_ms"
    PROBE_JSON_CACHE["$mid"]="$result"

    feasible=$(echo "$avg_ms <= $LATENCY_LIMIT" | bc -l)
    if [[ "$feasible" == "1" ]]; then
        log "${avg_ms} ms ✓ (within ${LATENCY_LIMIT} ms budget)"
        best_feasible=$mid
        lo=$((mid + 1))  # Try larger models
    else
        log "${avg_ms} ms ✗ (exceeds ${LATENCY_LIMIT} ms budget)"
        hi=$((mid - 1))  # Try smaller models
    fi
done

if [[ $best_feasible -lt 0 ]]; then
    log ""
    log "[Phase 1] ERROR: No model fits within the ${LATENCY_LIMIT} ms latency budget."
    log "Consider increasing --latency_limit or reducing --quantification."
    exit 1
fi

log ""
log "[Phase 1] Largest feasible model: ${MODELS[$best_feasible]} (idx=${best_feasible})"
log ""

# Log Phase 1 summary table
log_only ""
log_only "=== Phase 1 Summary ==="
log_only "Models probed during binary search:"
for idx in $(echo "${!LATENCY_CACHE[@]}" | tr ' ' '\n' | sort -n); do
    ms="${LATENCY_CACHE[$idx]}"
    f=$(echo "$ms <= $LATENCY_LIMIT" | bc -l)
    status="✗"
    [[ "$f" == "1" ]] && status="✓"
    log_only "  [${idx}] ${MODELS[$idx]}  —  ${ms} ms  ${status}"
done
log_only "Best feasible index: ${best_feasible} (${MODELS[$best_feasible]})"
log_only ""

# =====================================================================
# Phase 2: Explore Nearby Models (inference-only accuracy test)
# =====================================================================
# Window: best_feasible-2 .. best_feasible (inclusive)
window_lo=$((best_feasible > 2 ? best_feasible - 2 : 0))
window_hi=$best_feasible
window_size=$((window_hi - window_lo + 1))

log "[Phase 2] Evaluating ${window_size} nearby models (inference mode, ≤${MAX_EVAL_QUERIES} queries):"
log "  Window: indices ${window_lo}..${window_hi}"
log ""

# Arrays to collect results
declare -a EVAL_MODELS=()
declare -a EVAL_LATENCIES=()
declare -a EVAL_P90S=()
declare -a EVAL_QERROR_JSONS=()
declare -a EVAL_CDF_FILES=()

for idx in $(seq $window_lo $window_hi); do
    model="${MODELS[$idx]}"
    short_name=$(basename "$model")
    model_safe="${model//\//-}"

    log_only "--- Phase 2: evaluating model idx=${idx}: ${model} ---"

    # Check/measure latency
    if [[ -n "${LATENCY_CACHE[$idx]+x}" ]]; then
        avg_ms="${LATENCY_CACHE[$idx]}"
        log_only "  Latency from cache: ${avg_ms} ms"
    else
        log "  [Phase 2] Probing latency for ${model}..."
        result=$(probe_latency "$model" || true)
        avg_ms=$(echo "$result" | extract_avg_ms 2>/dev/null || true)
        if [[ -z "$avg_ms" || "$avg_ms" == "null" ]]; then
            log "  ${model}: FAILED (probe error), skipping"
            log_only "  Probe raw output: ${result}"
            continue
        fi
        LATENCY_CACHE["$idx"]="$avg_ms"
        PROBE_JSON_CACHE["$idx"]="$result"
        log_only "  Probe raw JSON: ${result}"
    fi

    # Verify still within budget
    feasible=$(echo "$avg_ms <= $LATENCY_LIMIT" | bc -l)
    if [[ "$feasible" != "1" ]]; then
        log "  ${short_name}: ${avg_ms} ms — exceeds budget, skipping"
        continue
    fi

    log "  [Phase 2] Running inference mode (mode 1) for ${model} (max_queries=${MAX_EVAL_QUERIES})..."
    log_only "  Invoking run_different_llms.sh --models ${model} --workloads ${FIRST_WORKLOAD} --finetune_mode 1 --seeds 42"

    # Run inference-only evaluation via run_different_llms.sh
    # Pass all defaulting flags to skip every interactive prompt
    # Export MAX_QUERIES to limit embedding generation to MAX_EVAL_QUERIES
    MAX_QUERIES="$MAX_EVAL_QUERIES" \
    bash "$SCRIPT_DIR/run_different_llms.sh" \
        --models "$model" \
        --workloads "$FIRST_WORKLOAD" \
        --task "$TASK" \
        --finetune_mode 1 \
        --seeds "42" \
        --db "$DB" \
        --quantification "$QUANTIFICATION" \
        --embed_size "$EMBED_SIZE" \
        --downstream "mlp" \
        --bucketize "None" \
        --concat_true "false" \
        --removed_fields "" \
        $PRICE_S_FLAG \
        2>>"$LOG_FILE" \
        || { log "  WARNING: Inference run failed for ${model}, skipping"; continue; }

    # Find the output CDF CSV
    # Mode 1 = inference (finetune=False), output pattern:
    #   results/{DB}/results_Train_{WL}_Test_{WL}_ours/time_llm_pretrained-None_1.0_cdf_{DB}_*_{model_safe}_emb*_seed42.csv
    # Map workload to training workload (same logic as run_different_llms.sh)
    TRAIN_WL="$FIRST_WORKLOAD"
    case "$FIRST_WORKLOAD" in
        syn|job_full) TRAIN_WL="job" ;;
    esac

    RESULTS_BASE="results/${DB}/results_Train_${TRAIN_WL}_Test_${FIRST_WORKLOAD}_ours"
    cdf_pattern="${RESULTS_BASE}/time_llm_pretrained-None_1.0_cdf_${DB}_*_${model_safe}_emb${EMBED_SIZE}*_seed42.csv"

    # Find the most recently created matching file
    cdf_file=$(ls -t $cdf_pattern 2>/dev/null | head -1) || true

    if [[ -z "$cdf_file" || ! -f "$cdf_file" ]]; then
        log "  WARNING: Could not find CDF file for ${model} (pattern: ${cdf_pattern})"
        log_only "  Glob pattern tried: ${cdf_pattern}"
        continue
    fi

    log_only "  CDF file: ${cdf_file}"

    # Parse Q-error
    qerror_json=$(python "$SCRIPT_DIR/parse_qerror.py" "$cdf_file")
    p90=$(echo "$qerror_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['p90'])")

    log "  ${short_name}: latency=${avg_ms} ms, p90=${p90}"
    log_only "  Full Q-error: ${qerror_json}"

    EVAL_MODELS+=("$model")
    EVAL_LATENCIES+=("$avg_ms")
    EVAL_P90S+=("$p90")
    EVAL_QERROR_JSONS+=("$qerror_json")
    EVAL_CDF_FILES+=("$cdf_file")
done

log ""

# Log Phase 2 summary table
log_only "=== Phase 2 Summary ==="
for i in "${!EVAL_MODELS[@]}"; do
    log_only "  ${EVAL_MODELS[$i]}  latency=${EVAL_LATENCIES[$i]}ms  p90=${EVAL_P90S[$i]}  qerror=${EVAL_QERROR_JSONS[$i]}"
done
log_only ""

if [[ ${#EVAL_MODELS[@]} -eq 0 ]]; then
    log "[Phase 2] ERROR: No models were successfully evaluated."
    exit 1
fi

# =====================================================================
# Phase 3: Select Best Model
# =====================================================================
log "[Phase 3] Selecting best model (epsilon=${EPSILON}):"

# Find best p90 and compute threshold; also write the JSON summary
SELECTION=$(python3 -c "
import json, sys

models = $(printf '%s\n' "${EVAL_MODELS[@]}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin]))")
latencies = [$(IFS=,; echo "${EVAL_LATENCIES[*]}")]
p90s = [$(IFS=,; echo "${EVAL_P90S[*]}")]
epsilon = ${EPSILON}

best_p90 = min(p90s)
threshold = best_p90 * (1 + epsilon)

print(f'Best p90: {best_p90:.4f}, threshold ({epsilon*100:.0f}%): {threshold:.4f}', file=sys.stderr)

# Among models with p90 <= threshold, pick fastest (lowest latency)
candidates = [(m, lat, p) for m, lat, p in zip(models, latencies, p90s) if p <= threshold]

if not candidates:
    # Fallback: pick model with best p90
    idx = p90s.index(best_p90)
    candidates = [(models[idx], latencies[idx], p90s[idx])]

# Sort by latency ascending
candidates.sort(key=lambda x: x[1])

for m, lat, p in candidates:
    short = m.split('/')[-1]
    print(f'  Candidate: {short} — latency={lat} ms, p90={p:.4f}', file=sys.stderr)

selected = candidates[0]
print(selected[0])  # stdout: selected model name

# Write JSON summary to a temp file (will be moved to JSON_FILE by shell)
summary = {
    'selected_model': selected[0],
    'selected_latency_ms': selected[1],
    'selected_p90': selected[2],
    'best_p90': best_p90,
    'threshold': threshold,
    'epsilon': epsilon,
    'candidates': [
        {'model': m, 'latency_ms': lat, 'p90': p}
        for m, lat, p in candidates
    ],
    'all_evaluated': [
        {'model': m, 'latency_ms': lat, 'p90': p}
        for m, lat, p in zip(models, latencies, p90s)
    ],
}
with open('${JSON_FILE}', 'w') as f:
    json.dump(summary, f, indent=2)
")

SELECTED_MODEL="$SELECTION"

log ""
log "[Phase 3] Selected: ${SELECTED_MODEL}"
log_only "Phase 3 JSON summary written to: ${JSON_FILE}"
log ""

# =====================================================================
# Phase 4: Run Full JointPrice Finetuning (mode 7)
# =====================================================================
log "[Phase 4] Running JointPrice finetuning with ${SELECTED_MODEL}..."
log "  Workloads:     ${WORKLOADS_STR}"
log "  Seeds:         ${SEEDS_STR}"
log "  Batch size:    ${FT_BATCH_SIZE}"
log "  Epochs:        ${FT_NUM_EPOCH}"
log "  Checkpoint:    ${CHECKPOINT_INTERVAL}"
log ""

# Convert workloads array to comma-separated for run_different_llms.sh
WORKLOADS_CSV=$(IFS=,; echo "${WORKLOADS[*]}")

PHASE4_EXIT=0
bash "$SCRIPT_DIR/run_different_llms.sh" \
    --models "$SELECTED_MODEL" \
    --workloads "$WORKLOADS_CSV" \
    --task "$TASK" \
    --finetune_mode 7 \
    --finetune_method "lora" \
    --seeds "$SEEDS_STR" \
    --db "$DB" \
    --quantification "$QUANTIFICATION" \
    --embed_size "$EMBED_SIZE" \
    --ft_batch_size "$FT_BATCH_SIZE" \
    --ft_num_epoch "$FT_NUM_EPOCH" \
    --checkpoint_interval "$CHECKPOINT_INTERVAL" \
    --downstream "mlp" \
    --bucketize "None" \
    --concat_true "false" \
    --removed_fields "" \
    $PRICE_S_FLAG \
    $PRICE_RANDOM_INIT_FLAG \
    2>>"$LOG_FILE" \
    || PHASE4_EXIT=$?

if [[ $PHASE4_EXIT -ne 0 ]]; then
    log ""
    log "[Phase 4] ERROR: Finetuning failed (exit code ${PHASE4_EXIT})."
    log "  This often happens when the selected model is too large to finetune"
    log "  on the available GPU (CUDA OOM during backward pass)."
    log "  Suggestions:"
    log "    - Lower --latency_limit to select a smaller model"
    log "    - Reduce --ft_batch_size (currently ${FT_BATCH_SIZE})"
    log "    - Use a GPU with more VRAM"
    log ""
fi

# ─── Final summary ───────────────────────────────────────────────────
# Append final config + timing to JSON
python3 -c "
import json
with open('${JSON_FILE}') as f:
    summary = json.load(f)
summary['config'] = {
    'latency_limit_ms': ${LATENCY_LIMIT},
    'workloads': '${WORKLOADS_STR}',
    'task': '${TASK}',
    'seeds': '${SEEDS_STR}',
    'db': '${DB}',
    'quantification': '${QUANTIFICATION}',
    'epsilon': ${EPSILON},
    'ft_batch_size': ${FT_BATCH_SIZE},
    'ft_num_epoch': ${FT_NUM_EPOCH},
    'num_probe_queries': ${NUM_PROBE_QUERIES},
    'embed_size': ${EMBED_SIZE},
    'phase4_exit_code': ${PHASE4_EXIT},
}
with open('${JSON_FILE}', 'w') as f:
    json.dump(summary, f, indent=2)
"

log ""
log "============================================================"
log " Model Selection Pipeline Complete"
log "============================================================"
log "Selected model: ${SELECTED_MODEL}"
if [[ $PHASE4_EXIT -eq 0 ]]; then
    log "Phase 4 (JointPrice finetuning) finished successfully for workloads: ${WORKLOADS_STR}"
else
    log "Phase 4 (JointPrice finetuning) FAILED for workloads: ${WORKLOADS_STR}"
fi
log ""
log "Artifacts:"
log "  Log file:     ${LOG_FILE}"
log "  JSON summary: ${JSON_FILE}"
log "============================================================"
