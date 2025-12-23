#!/bin/bash
# Cross-Workload Experiments
# Tests model generalization across different workloads with and without finetuning

echo "Running Cross-Workload Experiments..."

# Define available models
models=(
    "meta-llama/Llama-3.1-8B"
    "meta-llama/Llama-3.2-3B"
)

# Define all training workloads (used for cross-workload experiments)
all_train_workloads=(
    "genome"
    "financial"
    "movielens"
    "geneea"
    "seznam"
    "tpc_h"
    "walmart"
    "airline"
    "carcinogenesis"
    "baseball"
    "imdb"
    "accidents"
    "ssb"
    "basketball"
    "employee"
    "fhnk"
    "consumer"
    "tournament"
    "credit"
    "hepatitis"
)

# Define available test workloads
test_workloads=(
    "tpc_h"
    "synthetic"
    "job-light"
)

# Get model selection
echo "=== Model Selection ==="
echo "Choose model(s):"
for i in "${!models[@]}"; do
    echo "$((i+1)). ${models[i]}"
done
echo "Enter numbers separated by spaces (e.g., 1 2) or 'all' for all options:"
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

echo "Selected models: ${selected_models[*]}"

# Get test workload selection
echo ""
echo "=== Test Workload Selection ==="
echo "Choose test workload(s):"
for i in "${!test_workloads[@]}"; do
    echo "$((i+1)). ${test_workloads[i]}"
done
echo "Enter numbers separated by spaces (e.g., 1 3) or 'all' for all options:"
read -r test_workload_selection

selected_test_workloads=()
if [[ "$test_workload_selection" == "all" ]]; then
    selected_test_workloads=("${test_workloads[@]}")
else
    for num in $test_workload_selection; do
        if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#test_workloads[@]}" ]]; then
            selected_test_workloads+=("${test_workloads[$((num-1))]}")
        else
            echo "Invalid selection: $num"
            exit 1
        fi
    done
fi

echo "Selected test workloads: ${selected_test_workloads[*]}"

# Get downstream learner
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
echo "Using downstream: $LLM_DOWNSTREAM"

# Get bucketize option
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
    echo "Invalid choice, defaulting to separate"
    BUCKETIZE="separate"
fi

# Get quantification option
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
    echo "Invalid choice, defaulting to None"
    QUANTIFICATION="None"
fi

# Get seeds
echo ""
echo "=== Seeds ==="
echo "Enter seed numbers separated by spaces (e.g., 42 43 44):"
read -r seeds_input

if [[ -z "$seeds_input" ]]; then
    echo "No seeds provided, using default: 42"
    seeds=(42)
else
    seeds=($seeds_input)
fi

# Get embed_size
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

# Get experiment type selection
echo ""
echo "=== Experiment Type Selection ==="
echo "1. without finetuning only"
echo "2. with finetuning only"
echo "3. both (without and with finetuning)"
echo "Enter choice (1, 2, or 3):"
read -r experiment_type_choice

RUN_WITHOUT_FINETUNE=false
RUN_WITH_FINETUNE=false

if [[ "$experiment_type_choice" == "1" ]]; then
    RUN_WITHOUT_FINETUNE=true
elif [[ "$experiment_type_choice" == "2" ]]; then
    RUN_WITH_FINETUNE=true
elif [[ "$experiment_type_choice" == "3" ]]; then
    RUN_WITHOUT_FINETUNE=true
    RUN_WITH_FINETUNE=true
else
    echo "Invalid choice, defaulting to both"
    RUN_WITHOUT_FINETUNE=true
    RUN_WITH_FINETUNE=true
fi

# Get finetuning mode selection (if running with finetuning)
RUN_LAST=false
RUN_LORA=false
if [ "$RUN_WITH_FINETUNE" = true ]; then
    echo ""
    echo "=== Finetuning Mode Selection ==="
    echo "Choose which pretrained model(s) to use for inference:"
    echo "1. last (finetune last layer)"
    echo "2. lora (LoRA finetuning)"
    echo "3. both"
    echo "Enter choice (1, 2, or 3):"
    read -r finetune_mode_choice

    if [[ "$finetune_mode_choice" == "1" ]]; then
        RUN_LAST=true
    elif [[ "$finetune_mode_choice" == "2" ]]; then
        RUN_LORA=true
    elif [[ "$finetune_mode_choice" == "3" ]]; then
        RUN_LAST=true
        RUN_LORA=true
    else
        echo "Invalid choice, defaulting to both"
        RUN_LAST=true
        RUN_LORA=true
    fi
fi

# Get removed fields option
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
    # Convert numbers to category names
    categories=()
    IFS=',' read -ra NUMBERS <<< "$removed_fields_input"
    for num in "${NUMBERS[@]}"; do
        num=$(echo "$num" | tr -d ' ')  # Trim whitespace
        case "$num" in
            1) categories+=("operator_structure_and_config") ;;
            2) categories+=("cost") ;;
            3) categories+=("cardinality") ;;
            4) categories+=("conditions_and_filters") ;;
            5) categories+=("metadata_and_config") ;;
            *) echo "Warning: Invalid number '$num' - skipping" ;;
        esac
    done
    
    # Join categories with commas
    REMOVED_FIELDS=$(IFS=,; echo "${categories[*]}")
    
    if [[ -n "$REMOVED_FIELDS" ]]; then
        echo "Will remove fields: $REMOVED_FIELDS (+ runtime fields which are always removed)"
    else
        echo "No valid categories specified. Will only remove runtime fields (default behavior)"
    fi
else
    echo "Will only remove runtime fields (default behavior)"
fi

echo ""
echo "=== Configuration Summary ==="
echo "Models: ${selected_models[*]}"
echo "Test Workloads: ${selected_test_workloads[*]}"
echo "Training Workloads: All workloads except test workload (and imdb excluded for synthetic/job-light)"
echo "Bucketize: $BUCKETIZE"
echo "Quantification: $QUANTIFICATION"
echo "Seeds: ${seeds[*]}"
echo "Embed Size: $EMBED_SIZE"
echo "Experiment Types: $(if [ "$RUN_WITHOUT_FINETUNE" = true ]; then echo -n "without finetuning "; fi)$(if [ "$RUN_WITH_FINETUNE" = true ]; then echo -n "with finetuning"; fi)"
if [ "$RUN_WITH_FINETUNE" = true ]; then
    echo "Finetuning Modes: $(if [ "$RUN_LAST" = true ]; then echo -n "last "; fi)$(if [ "$RUN_LORA" = true ]; then echo -n "lora"; fi)"
fi
echo "Removed Fields: ${REMOVED_FIELDS:-none}"
echo ""
echo "Starting experiments..."

# Run experiments
for SEED in "${seeds[@]}"; do
    for WORKLOAD_TEST in "${selected_test_workloads[@]}"; do
        # Build training workloads string (all workloads except test workload)
        WORKLOADS_TRAIN=""
        for o in "${all_train_workloads[@]}"; do
            if [[ $o != $WORKLOAD_TEST ]]; then
                # Remove imdb from training if testing on synthetic or job-light
                if [[ ($WORKLOAD_TEST == "synthetic" || $WORKLOAD_TEST == "job-light") && $o == "imdb" ]]; then
                    continue
                fi
                WORKLOADS_TRAIN="$WORKLOADS_TRAIN $o"
            fi
        done
        # Strip leading space
        WORKLOADS_TRAIN=${WORKLOADS_TRAIN# }

        for model_name in "${selected_models[@]}"; do
            echo ""
            echo "=========================================="
            echo "Running: Model=$model_name, Test=$WORKLOAD_TEST, Seed=$SEED"
            echo "Training on: $WORKLOADS_TRAIN"
            echo "=========================================="
            
            # Create model name for file naming (replace / with -)
            model_name1="${model_name//\//-}"
            
            # Set environment variables
            export BUCKETIZE_INPUT="$BUCKETIZE"
            export QUANTIFICATION="$QUANTIFICATION"
            export EMBED_SIZE="$EMBED_SIZE"
            export REMOVED_FIELDS="$REMOVED_FIELDS"
            export LLM_DOWNSTREAM
            
            # Without finetuning
            if [ "$RUN_WITHOUT_FINETUNE" = true ]; then
                echo "  Running without finetuning..."
                bash experiment_scripts/core_scripts/run_llm_time.sh "$WORKLOADS_TRAIN" "$WORKLOAD_TEST" 1.0 False $model_name $model_name1 $SEED
            fi
            
            # With finetuning
            if [ "$RUN_WITH_FINETUNE" = true ]; then
                echo "  Running with finetuning..."
                export FINETUNE_RUN_LAST="$RUN_LAST"
                export FINETUNE_RUN_LORA="$RUN_LORA"
                bash experiment_scripts/core_scripts/run_llm_time.sh "$WORKLOADS_TRAIN" "$WORKLOAD_TEST" 0.1 True $model_name $model_name1 $SEED
            fi
        done
    done
done

echo ""
echo "=========================================="
echo "Cross-Workload Experiments completed!"
echo "=========================================="
