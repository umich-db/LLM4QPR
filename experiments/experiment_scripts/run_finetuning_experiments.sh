#!/bin/bash
# Finetuning Experiments
# Tests LLM finetuning performance
# 
# NOTE: This script runs inference with pretrained (finetuned) models.
# The actual finetuning step (algo=llm_finetune) is currently commented out in 
# run_llm_time.sh and run_llm_card.sh. To run the full workflow:
# 1. Uncomment the finetuning sections (algo=llm_finetune) in the core scripts
# 2. Run this script to first create finetuned models
# 3. Then run inference with those models (current behavior)
#
# Alternatively, if finetuned models already exist in finetuned_models/, 
# this script will use them for inference.

echo "Running Finetuning Experiments..."

# Define available models
models=(
    "meta-llama/Llama-3.1-8B"
    "meta-llama/Llama-3.2-3B"
)

# Define available workloads
workloads=(
    "tpch"
    "tpcds"
    "syn"
    "job"
    "job_full"
    "stats"
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

# Get workload selection
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

echo "Selected workloads: ${selected_workloads[*]}"

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
    echo "No seeds provided, using default: 42 43 44"
    seeds=(42 43 44)
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

# Get task selection (time/card)
echo ""
echo "=== Task Selection ==="
echo "1. time (cost estimation)"
echo "2. card (cardinality estimation)"
echo "3. both"
echo "Enter choice (1, 2, or 3):"
read -r task_choice

RUN_TIME=false
RUN_CARD=false

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

# Get finetuning mode selection (last/lora)
echo ""
echo "=== Finetuning Mode Selection ==="
echo "Choose which pretrained model(s) to use for inference:"
echo "1. last (finetune last layer)"
echo "2. lora (LoRA finetuning)"
echo "3. both"
echo "Enter choice (1, 2, or 3):"
read -r finetune_mode_choice

RUN_LAST=false
RUN_LORA=false

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
echo "Workloads: ${selected_workloads[*]}"
echo "Bucketize: $BUCKETIZE"
echo "Quantification: $QUANTIFICATION"
echo "Seeds: ${seeds[*]}"
echo "Embed Size: $EMBED_SIZE"
echo "Tasks: $(if [ "$RUN_TIME" = true ]; then echo -n "time "; fi)$(if [ "$RUN_CARD" = true ]; then echo -n "card"; fi)"
echo "Finetuning Modes: $(if [ "$RUN_LAST" = true ]; then echo -n "last "; fi)$(if [ "$RUN_LORA" = true ]; then echo -n "lora"; fi)"
echo "Removed Fields: ${REMOVED_FIELDS:-none}"
echo ""
echo "Starting experiments..."

# Run experiments with SEED and WORKLOAD as outer loops, model_name as inner loop
for SEED in "${seeds[@]}"; do
    for WORKLOAD in "${selected_workloads[@]}"; do
        echo ""
        echo "=== Running experiments for Workload: $WORKLOAD, Seed: $SEED ==="
        
        for model_name in "${selected_models[@]}"; do
            echo "Running: Model=$model_name, Workload=$WORKLOAD, Seed=$SEED"
            
            # Create model name for file naming (replace / with -)
            model_name1="${model_name//\//-}"
            
            # Set environment variables
            export BUCKETIZE_INPUT="$BUCKETIZE"
            export QUANTIFICATION="$QUANTIFICATION"
            export EMBED_SIZE="$EMBED_SIZE"
            export REMOVED_FIELDS="$REMOVED_FIELDS"
            export LLM_DOWNSTREAM
            
            # Determine train_ratio based on workload
            if [[ $WORKLOAD == "job" || $WORKLOAD == "syn" ]]; then
                train_ratio=0.1
            else
                train_ratio=1.0
            fi
            
            # Run time prediction experiment if selected
            if [ "$RUN_TIME" = true ]; then
                # Control which finetuning modes to run via environment variable
                export FINETUNE_RUN_LAST="$RUN_LAST"
                export FINETUNE_RUN_LORA="$RUN_LORA"
                bash experiment_scripts/core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD $train_ratio True $model_name $model_name1 $SEED
            fi
            
            # Run cardinality prediction experiment if selected and workload supports it
            if [ "$RUN_CARD" = true ]; then
                if [[ "$WORKLOAD" == "job" || "$WORKLOAD" == "syn" || "$WORKLOAD" == "stats" ]]; then
                    # Control which finetuning modes to run via environment variable
                    export FINETUNE_RUN_LAST="$RUN_LAST"
                    export FINETUNE_RUN_LORA="$RUN_LORA"
                    bash experiment_scripts/core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD $train_ratio True $model_name $model_name1 $SEED
                fi
            fi
        done
    done
done

echo ""
echo "Finetuning Experiments completed!"
