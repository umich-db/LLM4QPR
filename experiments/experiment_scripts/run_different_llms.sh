#!/bin/bash
# Different LLMs Comparison Experiments
# Interactive script to run experiments with different models and workloads
# Supports CLI flags for non-interactive/automated usage.
# If a flag is provided, the corresponding interactive prompt is skipped.

# ─── CLI argument parsing ───────────────────────────────────────────────
CLI_MODELS=""
CLI_WORKLOADS=""
CLI_DOWNSTREAM=""
CLI_BUCKETIZE=""
CLI_QUANTIFICATION=""
CLI_CONCAT_TRUE=""
CLI_QUERIES_TRUE_DIR=""
CLI_SEEDS=""
CLI_EMBED_SIZE=""
CLI_TASK=""
CLI_FINETUNE_MODE=""
CLI_FINETUNE_METHOD=""
CLI_FT_BATCH_SIZE=""
CLI_REMOVED_FIELDS="__unset__"
CLI_DB=""
CLI_PRICE_M=""
CLI_PRICE_S=""
CLI_PRICE_RANDOM_INIT=""
CLI_FT_NUM_EPOCH=""
CLI_CHECKPOINT_INTERVAL=""
CLI_PRICE_LR=""
CLI_PRICE_N_LAYERS=""
CLI_N_CROSS_LAYERS=""
CLI_CROSS_ATTN_LR=""
CLI_RETRAIN_MLP=""
CLI_REFINED_POOL=""
CLI_TRIPLE_CONCAT=""
CLI_EARLY_STOP_PATIENCE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --models)           CLI_MODELS="$2";           shift 2 ;;
        --workloads)        CLI_WORKLOADS="$2";        shift 2 ;;
        --downstream)       CLI_DOWNSTREAM="$2";       shift 2 ;;
        --bucketize)        CLI_BUCKETIZE="$2";        shift 2 ;;
        --quantification)   CLI_QUANTIFICATION="$2";   shift 2 ;;
        --concat_true)      CLI_CONCAT_TRUE="$2";      shift 2 ;;
        --queries_true_dir) CLI_QUERIES_TRUE_DIR="$2";  shift 2 ;;
        --seeds)            CLI_SEEDS="$2";            shift 2 ;;
        --embed_size)       CLI_EMBED_SIZE="$2";       shift 2 ;;
        --task)             CLI_TASK="$2";             shift 2 ;;
        --finetune_mode)    CLI_FINETUNE_MODE="$2";    shift 2 ;;
        --finetune_method)  CLI_FINETUNE_METHOD="$2";  shift 2 ;;
        --ft_batch_size)    CLI_FT_BATCH_SIZE="$2";    shift 2 ;;
        --ft_num_epoch)     CLI_FT_NUM_EPOCH="$2";     shift 2 ;;
        --checkpoint_interval) CLI_CHECKPOINT_INTERVAL="$2"; shift 2 ;;
        --price_lr)         CLI_PRICE_LR="$2";         shift 2 ;;
        --removed_fields)   CLI_REMOVED_FIELDS="$2";   shift 2 ;;
        --db)               CLI_DB="$2";               shift 2 ;;
        --price_m)          CLI_PRICE_M="true";        shift 1 ;;
        --price_s)          CLI_PRICE_S="true";        shift 1 ;;
        --price_random_init) CLI_PRICE_RANDOM_INIT="true"; shift 1 ;;
        --price_n_layers)   CLI_PRICE_N_LAYERS="$2";     shift 2 ;;
        --n_cross_layers)   CLI_N_CROSS_LAYERS="$2";     shift 2 ;;
        --cross_attn_lr)    CLI_CROSS_ATTN_LR="$2";     shift 2 ;;
        --retrain_mlp)      CLI_RETRAIN_MLP="true";     shift 1 ;;
        --refined_pool)     CLI_REFINED_POOL="true";    shift 1 ;;
        --triple_concat)   CLI_TRIPLE_CONCAT="true";   shift 1 ;;
        --early_stop_patience) CLI_EARLY_STOP_PATIENCE="$2"; shift 2 ;;
        *)
            echo "Unknown flag: $1"
            exit 1
            ;;
    esac
done

# ─── Detect non-interactive (CLI) mode ─────────────────────────────────
# If any CLI flag was provided, skip all interactive prompts and use defaults.
CLI_MODE=false
if [[ -n "$CLI_MODELS" || -n "$CLI_WORKLOADS" || -n "$CLI_TASK" || -n "$CLI_FINETUNE_MODE" ]]; then
    CLI_MODE=true
fi

# ─── Begin setup ────────────────────────────────────────────────────────

echo "Running Different LLMs Comparison Experiments..."

export VERBOSE_INFO="true"

# Define available models
models=(
    "bert-base-uncased"
    "answerdotai/ModernBERT-base"
    "sentence-transformers/all-MiniLM-L6-v2"
    "openai/gpt-oss-20b"
    "google/embeddinggemma-300m"
    "google/gemma-3-270m"
    "google/gemma-3-1b-pt"
    "google/gemma-3-4b-pt"
    "google/gemma-3-12b-pt"
    "google/gemma-3-27b-pt"
    "Qwen/Qwen3-Embedding-0.6B"
    "Qwen/Qwen3-Embedding-4B"
    "Qwen/Qwen3-Embedding-8B"
    "Qwen/Qwen3-0.6B"
    "Qwen/Qwen3-1.7B"
    "Qwen/Qwen3-4B"
    "Qwen/Qwen3-8B"
    "Qwen/Qwen3-14B"
    "Qwen/Qwen3-32B"
    "meta-llama/Llama-3.2-1B"
    "meta-llama/Llama-3.2-3B"
    "meta-llama/Llama-3.1-8B"
    "meta-llama/Llama-3.1-70B"
)

# Define available workloads
workloads=(
    "tpch"
    "tpcds"
    "syn"
    "job"
    "job_full"
    "jobm"
    "stats"
)

# ─── Model selection ────────────────────────────────────────────────────
if [[ -n "$CLI_MODELS" ]]; then
    IFS=',' read -ra selected_models <<< "$CLI_MODELS"
else
    echo "=== Model Selection ==="
    echo "Choose model(s):"
    for i in "${!models[@]}"; do
        echo "$((i+1)). ${models[i]}"
    done
    echo "Enter numbers separated by spaces (e.g., 1 3 5) or 'all' for all options:"
    read -r model_selection

    selected_models=()
    if [[ "$model_selection" == "all" ]]; then
        selected_models=("${models[@]}")
    else
        for num in $model_selection; do
            if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#models[@]}" ]]; then
                selected_models+=("${models[$((num-1))]}")
            else
                echo "Invalid selection: $num"
                exit 1
            fi
        done
    fi
fi

echo "Selected models: ${selected_models[*]}"

# ─── Workload selection ─────────────────────────────────────────────────
if [[ -n "$CLI_WORKLOADS" ]]; then
    IFS=',' read -ra selected_workloads <<< "$CLI_WORKLOADS"
else
    echo ""
    echo "=== Workload Selection ==="
    echo "Choose workload(s):"
    for i in "${!workloads[@]}"; do
        echo "$((i+1)). ${workloads[i]}"
    done
    echo "Enter numbers separated by spaces (e.g., 1 3 5) or 'all' for all options:"
    read -r workload_selection

    selected_workloads=()
    if [[ "$workload_selection" == "all" ]]; then
        selected_workloads=("${workloads[@]}")
    else
        for num in $workload_selection; do
            if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#workloads[@]}" ]]; then
                selected_workloads+=("${workloads[$((num-1))]}")
            else
                echo "Invalid selection: $num"
                exit 1
            fi
        done
    fi
fi

echo "Selected workloads: ${selected_workloads[*]}"

# ─── Downstream learner ─────────────────────────────────────────────────
if [[ -n "$CLI_DOWNSTREAM" ]]; then
    LLM_DOWNSTREAM="$CLI_DOWNSTREAM"
else
    echo ""
    echo "=== Downstream Learner for LLM embeddings ==="
    echo "1. mlp (default)"
    echo "2. autogluon"
    echo "Enter choice (1 or 2):"
    read -r downstream_choice
    if [[ "$downstream_choice" == "2" ]]; then
        LLM_DOWNSTREAM="autogluon"
    else
        LLM_DOWNSTREAM="mlp"
    fi
fi
echo "Using downstream: $LLM_DOWNSTREAM"

# ─── Bucketize option ───────────────────────────────────────────────────
if [[ -n "$CLI_BUCKETIZE" ]]; then
    BUCKETIZE="$CLI_BUCKETIZE"
else
    echo ""
    echo "=== Bucketize Option ==="
    echo "1. separate"
    echo "2. unified"
    echo "3. None"
    echo "Enter choice (1, 2, or 3):"
    read -r bucketize_choice

    if [[ "$bucketize_choice" == "1" ]]; then
        BUCKETIZE="separate"
    elif [[ "$bucketize_choice" == "2" ]]; then
        BUCKETIZE="unified"
    elif [[ "$bucketize_choice" == "3" ]]; then
        BUCKETIZE="None"
    else
        echo "Invalid choice, defaulting to unified"
        BUCKETIZE="unified"
    fi
fi

# ─── Quantification option ──────────────────────────────────────────────
if [[ -n "$CLI_QUANTIFICATION" ]]; then
    QUANTIFICATION="$CLI_QUANTIFICATION"
else
    echo ""
    echo "=== Quantification Option ==="
    echo "1. 4-bit"
    echo "2. 8-bit"
    echo "3. None"
    echo "Enter choice (1, 2, or 3):"
    read -r quantification_choice

    if [[ "$quantification_choice" == "1" ]]; then
        QUANTIFICATION="4-bit"
    elif [[ "$quantification_choice" == "2" ]]; then
        QUANTIFICATION="8-bit"
    elif [[ "$quantification_choice" == "3" ]]; then
        QUANTIFICATION="None"
    else
        echo "Invalid choice, defaulting to 4-bit"
        QUANTIFICATION="4-bit"
    fi
fi

# ─── queries_true concatenation ─────────────────────────────────────────
if [[ -n "$CLI_CONCAT_TRUE" ]]; then
    CONCAT_TRUE_EMBEDDINGS="$CLI_CONCAT_TRUE"
    if [[ "$CONCAT_TRUE_EMBEDDINGS" == "true" ]]; then
        QUERIES_TRUE_DIR="${CLI_QUERIES_TRUE_DIR:-../queries_true}"
    else
        QUERIES_TRUE_DIR=""
    fi
else
    echo ""
    echo "=== queries_true Embeddings ==="
    echo "Concatenate queries_true embeddings to LLM embeddings?"
    echo "1. No (default)"
    echo "2. Yes"
    echo "Enter choice (1 or 2):"
    read -r concat_choice
    if [[ "$concat_choice" == "2" ]]; then
        CONCAT_TRUE_EMBEDDINGS="true"
        echo "Enter queries_true directory (default: ../queries_true):"
        read -r queries_true_input
        if [[ -z "$queries_true_input" ]]; then
            QUERIES_TRUE_DIR="../queries_true"
        else
            QUERIES_TRUE_DIR="$queries_true_input"
        fi
    else
        CONCAT_TRUE_EMBEDDINGS="false"
        QUERIES_TRUE_DIR=""
    fi
fi

# ─── Seeds ──────────────────────────────────────────────────────────────
if [[ -n "$CLI_SEEDS" ]]; then
    seeds=($CLI_SEEDS)
else
    echo ""
    echo "=== Seeds ==="
    echo "Enter seed numbers separated by spaces (e.g., 42 43 44):"
    read -r seeds_input

    if [[ -z "$seeds_input" ]]; then
        echo "No seeds provided, using default: 42 43 44"
        seeds=(42 43 44)
    else
        seeds=($seeds_input)
    fi
fi

# ─── Embedding size ─────────────────────────────────────────────────────
if [[ -n "$CLI_EMBED_SIZE" ]]; then
    EMBED_SIZE="$CLI_EMBED_SIZE"
else
    echo ""
    echo "=== Embedding Size ==="
    echo "Enter embedding size (default: 1000, or 9999999 for full):"
    read -r embed_size_input

    if [[ -z "$embed_size_input" ]]; then
        echo "No embed_size provided, using default: 1000"
        EMBED_SIZE=1000
    else
        EMBED_SIZE=$embed_size_input
    fi
fi

# ─── Task selection ─────────────────────────────────────────────────────
RUN_TIME=false
RUN_CARD=false

if [[ -n "$CLI_TASK" ]]; then
    case "$CLI_TASK" in
        time) RUN_TIME=true ;;
        card) RUN_CARD=true ;;
        both) RUN_TIME=true; RUN_CARD=true ;;
        *)
            echo "Invalid --task value: $CLI_TASK (expected: time, card, both)"
            exit 1
            ;;
    esac
else
    echo ""
    echo "=== Task Selection ==="
    echo "1. time (cost estimation)"
    echo "2. card (cardinality estimation)"
    echo "3. both"
    echo "Enter choice (1, 2, or 3):"
    read -r task_choice

    if [[ "$task_choice" == "1" ]]; then
        RUN_TIME=true
    elif [[ "$task_choice" == "2" ]]; then
        RUN_CARD=true
    elif [[ "$task_choice" == "3" ]]; then
        RUN_TIME=true
        RUN_CARD=true
    else
        echo "Invalid choice, defaulting to both"
        RUN_TIME=true
        RUN_CARD=true
    fi
fi

# ─── Finetune mode ──────────────────────────────────────────────────────
# Map from number to name for CLI convenience
_resolve_finetune_mode() {
    case "$1" in
        1)  echo "False" ;;
        2)  echo "True" ;;
        3)  echo "PriceNoFT" ;;
        4)  echo "PriceLLMOnly" ;;
        5)  echo "PricePRICEOnly" ;;
        6)  echo "PriceBothSep" ;;
        7)  echo "JointPrice" ;;
        8)  echo "PriceFTwithLLM" ;;
        9)  echo "PriceFTthenJoint" ;;
        10) echo "GatedJointPrice" ;;
        11) echo "CrossAttentionJoint" ;;
        12) echo "BiCrossAttentionJoint" ;;
        *)  echo "$1" ;;  # already a name string
    esac
}

if [[ -n "$CLI_FINETUNE_MODE" ]]; then
    FINETUNE_MODE="$(_resolve_finetune_mode "$CLI_FINETUNE_MODE")"
else
    echo ""
    echo "=== Finetune Mode ==="
    echo "1. No finetune (inference only)"
    echo "2. LLM finetune (LoRA/last) — no PRICE"
    echo "3. LLM+PRICE: No finetune (PriceNoFT)"
    echo "4. LLM+PRICE: LLM finetuned only (PriceLLMOnly)"
    echo "5. LLM+PRICE: PRICE finetuned only (PricePRICEOnly)"
    echo "6. LLM+PRICE: Both separate (PriceBothSep)"
    echo "7. LLM+PRICE: Both joint (JointPrice)"
    echo "8. LLM+PRICE: PRICE finetuned w/ LLM embeddings (PriceFTwithLLM)"
    echo "9. LLM+PRICE: Frozen-init then joint (PriceFTthenJoint)"
    echo "10. LLM+PRICE: Gated joint (GatedJointPrice)"
    echo "11. LLM+PRICE: Cross-attention joint (CrossAttentionJoint)"
    echo "12. LLM+PRICE: Bidirectional cross-attention joint (BiCrossAttentionJoint)"
    echo "Enter choice (1-12):"
    read -r finetune_choice

    FINETUNE_MODE="False"
    if [[ "$finetune_choice" == "2" ]]; then
        FINETUNE_MODE="True"
    elif [[ "$finetune_choice" == "3" ]]; then
        FINETUNE_MODE="PriceNoFT"
    elif [[ "$finetune_choice" == "4" ]]; then
        FINETUNE_MODE="PriceLLMOnly"
    elif [[ "$finetune_choice" == "5" ]]; then
        FINETUNE_MODE="PricePRICEOnly"
    elif [[ "$finetune_choice" == "6" ]]; then
        FINETUNE_MODE="PriceBothSep"
    elif [[ "$finetune_choice" == "7" ]]; then
        FINETUNE_MODE="JointPrice"
    elif [[ "$finetune_choice" == "8" ]]; then
        FINETUNE_MODE="PriceFTwithLLM"
    elif [[ "$finetune_choice" == "9" ]]; then
        FINETUNE_MODE="PriceFTthenJoint"
    elif [[ "$finetune_choice" == "10" ]]; then
        FINETUNE_MODE="GatedJointPrice"
    elif [[ "$finetune_choice" == "11" ]]; then
        FINETUNE_MODE="CrossAttentionJoint"
    elif [[ "$finetune_choice" == "12" ]]; then
        FINETUNE_MODE="BiCrossAttentionJoint"
    fi
fi

echo "Finetune mode: $FINETUNE_MODE"

# ─── Finetune method (only for mode "True") ─────────────────────────────
FINETUNE_RUN_LAST=true
FINETUNE_RUN_LORA=true
if [[ "$FINETUNE_MODE" == "True" ]]; then
    if [[ -n "$CLI_FINETUNE_METHOD" ]]; then
        case "$CLI_FINETUNE_METHOD" in
            last)
                FINETUNE_RUN_LAST=true
                FINETUNE_RUN_LORA=false
                ;;
            lora)
                FINETUNE_RUN_LAST=false
                FINETUNE_RUN_LORA=true
                ;;
            both)
                FINETUNE_RUN_LAST=true
                FINETUNE_RUN_LORA=true
                ;;
            *)
                echo "Invalid --finetune_method: $CLI_FINETUNE_METHOD (expected: last, lora, both)"
                exit 1
                ;;
        esac
    else
        echo ""
        echo "=== LLM Finetuning Method ==="
        echo "1. last (finetune last layer)"
        echo "2. lora (LoRA finetuning)"
        echo "3. both"
        echo "Enter choice (1, 2, or 3):"
        read -r finetune_method_choice

        if [[ "$finetune_method_choice" == "1" ]]; then
            FINETUNE_RUN_LAST=true
            FINETUNE_RUN_LORA=false
        elif [[ "$finetune_method_choice" == "2" ]]; then
            FINETUNE_RUN_LAST=false
            FINETUNE_RUN_LORA=true
        elif [[ "$finetune_method_choice" == "3" ]]; then
            FINETUNE_RUN_LAST=true
            FINETUNE_RUN_LORA=true
        else
            echo "Invalid choice, defaulting to both"
        fi
    fi
fi

# ─── Finetune batch size ────────────────────────────────────────────────
FT_BATCH_SIZE=16
if [[ "$FINETUNE_MODE" != "False" && "$FINETUNE_MODE" != "PriceNoFT" ]]; then
    if [[ -n "$CLI_FT_BATCH_SIZE" ]]; then
        FT_BATCH_SIZE="$CLI_FT_BATCH_SIZE"
    else
        echo ""
        echo "=== Finetune Batch Size ==="
        echo "Enter finetune batch size (1, 2, 4, 8, or 16; default: 16):"
        echo "Number of epochs = batch_size to fix total optimizer steps."
        read -r ft_batch_size_input

        if [[ -n "$ft_batch_size_input" ]]; then
            FT_BATCH_SIZE=$ft_batch_size_input
        fi
    fi
    echo "Finetune batch size: $FT_BATCH_SIZE (epochs: $FT_BATCH_SIZE)"
fi

# ─── Removed fields ─────────────────────────────────────────────────────
if [[ "$CLI_REMOVED_FIELDS" != "__unset__" ]]; then
    # CLI provided (may be empty string = no removal)
    REMOVED_FIELDS=""
    if [[ -n "$CLI_REMOVED_FIELDS" ]]; then
        categories=()
        IFS=',' read -ra NUMBERS <<< "$CLI_REMOVED_FIELDS"
        for num in "${NUMBERS[@]}"; do
            num=$(echo "$num" | tr -d ' ')
            case "$num" in
                1) categories+=("operator_structure_and_config") ;;
                2) categories+=("cost") ;;
                3) categories+=("cardinality") ;;
                4) categories+=("conditions_and_filters") ;;
                5) categories+=("metadata_and_config") ;;
                *) echo "Warning: Invalid removed_fields number '$num' - skipping" ;;
            esac
        done
        REMOVED_FIELDS=$(IFS=,; echo "${categories[*]}")
    fi
else
    echo ""
    echo "=== Removed Fields ==="
    echo "Enter comma-separated numbers for field categories to remove (or press Enter for none):"
    echo "Valid options:"
    echo "  1. operator_structure_and_config - Node types, scan configs, join types, sort/hash configs"
    echo "  2. cost - Startup Cost, Total Cost, Plan Width"
    echo "  3. cardinality - Plan Rows"
    echo "  4. conditions_and_filters - Filter, Join conditions (affects cardinality)"
    echo "  5. metadata_and_config - Command, Triggers, Planning Time, Parallelism config"
    echo ""
    echo "Note: Runtime statistics (Actual*, I/O, memory, cache, workers, etc.) are ALWAYS removed"
    echo ""
    echo "Example: 2,3 (removes cost and cardinality)"
    echo "Example: 1,2,5 (removes operator_structure_and_config, cost, and metadata_and_config)"
    read -r removed_fields_input

    REMOVED_FIELDS=""
    if [[ -n "$removed_fields_input" ]]; then
        categories=()
        IFS=',' read -ra NUMBERS <<< "$removed_fields_input"
        for num in "${NUMBERS[@]}"; do
            num=$(echo "$num" | tr -d ' ')
            case "$num" in
                1) categories+=("operator_structure_and_config") ;;
                2) categories+=("cost") ;;
                3) categories+=("cardinality") ;;
                4) categories+=("conditions_and_filters") ;;
                5) categories+=("metadata_and_config") ;;
                *) echo "Warning: Invalid number '$num' - skipping" ;;
            esac
        done
        REMOVED_FIELDS=$(IFS=,; echo "${categories[*]}")

        if [[ -n "$REMOVED_FIELDS" ]]; then
            echo "Will remove fields: $REMOVED_FIELDS (+ runtime fields which are always removed)"
    else
            echo "No valid categories specified. Will only remove runtime fields (default behavior)"
        fi
    else
        echo "Will only remove runtime fields (default behavior)"
    fi
fi

# ─── Database engine ───────────────────────────────────────────────────
if [[ -n "$CLI_DB" ]]; then
    DB_ENGINE="$CLI_DB"
else
    echo ""
    echo "=== Database Engine ==="
    echo "1. postgres (default)"
    echo "2. duckdb"
    echo "Enter choice (1 or 2, default=1):"
    read -r db_choice
    if [[ "$db_choice" == "2" ]]; then
        DB_ENGINE="duckdb"
    else
        DB_ENGINE="postgres"
    fi
fi
export DB_ENGINE

# ─── PRICE_M (extended filter encoding) ───────────────────────────────
if [[ -n "$CLI_PRICE_M" ]]; then
    PRICE_M="$CLI_PRICE_M"
elif [[ "$CLI_MODE" == true ]]; then
    PRICE_M="false"
else
    echo ""
    echo "=== PRICE_M (extended filter encoding for IN/LIKE/NOT LIKE) ==="
    echo "1. No (default)"
    echo "2. Yes"
    echo "Enter choice (1 or 2):"
    read -r price_m_choice
    if [[ "$price_m_choice" == "2" ]]; then
        PRICE_M="true"
    else
        PRICE_M="false"
    fi
fi
export PRICE_M

# ─── PRICE_S (bounding-box range encoding for IN/LIKE/NOT LIKE) ─────
if [[ -n "$CLI_PRICE_S" ]]; then
    PRICE_S="$CLI_PRICE_S"
elif [[ "$CLI_MODE" == true ]]; then
    PRICE_S="false"
else
    echo ""
    echo "=== PRICE_S (bounding-box range encoding for IN/LIKE/NOT LIKE, 43-dim) ==="
    echo "1. No (default)"
    echo "2. Yes"
    echo "Enter choice (1 or 2):"
    read -r price_s_choice
    if [[ "$price_s_choice" == "2" ]]; then
        PRICE_S="true"
    else
        PRICE_S="false"
    fi
fi
export PRICE_S

echo ""
echo "=== Configuration Summary ==="
echo "Database: $DB_ENGINE"
echo "Models: ${selected_models[*]}"
echo "Workloads: ${selected_workloads[*]}"
echo "Bucketize: $BUCKETIZE"
echo "Quantification: $QUANTIFICATION"
echo "Seeds: ${seeds[*]}"
echo "Embed Size: $EMBED_SIZE"
echo "Tasks: $(if [ "$RUN_TIME" = true ]; then echo -n "time "; fi)$(if [ "$RUN_CARD" = true ]; then echo -n "card"; fi)"
echo "Finetune mode: $FINETUNE_MODE"
if [[ "$FINETUNE_MODE" == "True" ]]; then
    echo "Finetuning methods: $(if [ "$FINETUNE_RUN_LAST" = true ]; then echo -n "last "; fi)$(if [ "$FINETUNE_RUN_LORA" = true ]; then echo -n "lora"; fi)"
fi
echo "Finetune batch size: $FT_BATCH_SIZE (epochs: $FT_BATCH_SIZE)"
echo "PRICE_M: $PRICE_M"
echo "PRICE_S: $PRICE_S"
echo "PRICE Random Init: ${PRICE_RANDOM_INIT:-false}"
echo "Removed Fields: ${REMOVED_FIELDS:-none}"
echo "Concat queries_true: $CONCAT_TRUE_EMBEDDINGS"
if [[ "$CONCAT_TRUE_EMBEDDINGS" == "true" ]]; then
    echo "queries_true dir: $QUERIES_TRUE_DIR"
fi
echo ""
echo "Starting experiments..."

# Run experiments with SEED and WORKLOAD as outer loops, model_name as inner loop
for SEED in "${seeds[@]}"; do
    for WORKLOAD in "${selected_workloads[@]}"; do
        echo ""
        echo "=== Running experiments for Workload: $WORKLOAD, Seed: $SEED ==="

        # Map to canonical training workload to avoid redundant finetuning.
        # syn and job_full share the same training CSV as job (long_raw_postgres_imdb.csv),
        # so finetuned models are identical. jobm has its own queries and trains separately.
        # We use "job" as the canonical name (not "imdb" which collides with deepdb).
        TRAIN_WL="$WORKLOAD"
        case "$WORKLOAD" in
            syn|job_full) TRAIN_WL="job" ;;
        esac

        for model_name in "${selected_models[@]}"; do
            echo "Running: Model=$model_name, Workload=$WORKLOAD (train=$TRAIN_WL), Seed=$SEED"

            # Create model name for file naming (replace / with -)
            model_name1="${model_name//\//-}"

            # Set environment variables
            export BUCKETIZE_INPUT="$BUCKETIZE"
            export QUANTIFICATION="$QUANTIFICATION"
            export EMBED_SIZE="$EMBED_SIZE"
            export FT_BATCH_SIZE="$FT_BATCH_SIZE"
            if [[ -n "$CLI_FT_NUM_EPOCH" ]]; then
                export FT_NUM_EPOCH="$CLI_FT_NUM_EPOCH"
            else
                export FT_NUM_EPOCH="$FT_BATCH_SIZE"
            fi
            if [[ -n "$CLI_PRICE_LR" ]]; then
                export PRICE_LR="$CLI_PRICE_LR"
            fi
            if [[ -n "$CLI_CHECKPOINT_INTERVAL" ]]; then
                export CHECKPOINT_INTERVAL="$CLI_CHECKPOINT_INTERVAL"
            fi
            if [[ -n "$CLI_PRICE_RANDOM_INIT" ]]; then
                export PRICE_RANDOM_INIT="$CLI_PRICE_RANDOM_INIT"
            fi
            if [[ -n "$CLI_PRICE_N_LAYERS" ]]; then
                export PRICE_N_LAYERS="$CLI_PRICE_N_LAYERS"
            fi
            if [[ -n "$CLI_N_CROSS_LAYERS" ]]; then
                export N_CROSS_LAYERS="$CLI_N_CROSS_LAYERS"
            fi
            if [[ -n "$CLI_CROSS_ATTN_LR" ]]; then
                export CROSS_ATTN_LR="$CLI_CROSS_ATTN_LR"
            fi
            if [[ -n "$CLI_RETRAIN_MLP" ]]; then
                export RETRAIN_MLP="$CLI_RETRAIN_MLP"
            fi
            if [[ -n "$CLI_REFINED_POOL" ]]; then
                export REFINED_POOL="$CLI_REFINED_POOL"
            fi
            if [[ -n "$CLI_TRIPLE_CONCAT" ]]; then
                export TRIPLE_CONCAT="$CLI_TRIPLE_CONCAT"
            fi
            if [[ -n "$CLI_EARLY_STOP_PATIENCE" ]]; then
                export EARLY_STOP_PATIENCE="$CLI_EARLY_STOP_PATIENCE"
            fi
            export FINETUNE_RUN_LAST="$FINETUNE_RUN_LAST"
            export FINETUNE_RUN_LORA="$FINETUNE_RUN_LORA"
            export REMOVED_FIELDS="$REMOVED_FIELDS"
            export CONCAT_TRUE_EMBEDDINGS="$CONCAT_TRUE_EMBEDDINGS"
            if [[ "$CONCAT_TRUE_EMBEDDINGS" == "true" ]]; then
                export QUERIES_TRUE_DIR="$QUERIES_TRUE_DIR"
            fi

            # Run time prediction experiment if selected
            if [ "$RUN_TIME" = true ]; then
                export LLM_DOWNSTREAM
                bash experiment_scripts/core_scripts/run_llm_time.sh $TRAIN_WL $WORKLOAD 1.0 $FINETUNE_MODE $model_name $model_name1 $SEED
            fi

            # Run cardinality prediction experiment if selected and workload supports it
            if [ "$RUN_CARD" = true ]; then
                if [[ "$WORKLOAD" == "job" || "$WORKLOAD" == "syn" || "$WORKLOAD" == "stats" ]]; then
                    export LLM_DOWNSTREAM
                    bash experiment_scripts/core_scripts/run_llm_card.sh $TRAIN_WL $WORKLOAD 1.0 $FINETUNE_MODE $model_name $model_name1 $SEED
                fi
            fi
        done
    done
done

echo ""
echo "Different LLMs Comparison Experiments completed!"
