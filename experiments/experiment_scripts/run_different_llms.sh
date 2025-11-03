#!/bin/bash
# Different LLMs Comparison Experiments
# Interactive script to run experiments with different models and workloads

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
    "stats"
)

# Get model selection
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
    echo "Invalid choice, defaulting to unified"
    BUCKETIZE="unified"
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
    echo "Invalid choice, defaulting to 4-bit"
    QUANTIFICATION="4-bit"
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
            
            # Run time prediction experiment if selected
            if [ "$RUN_TIME" = true ]; then
                bash experiment_scripts/core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
            fi
            
            # Run cardinality prediction experiment if selected and workload supports it
            if [ "$RUN_CARD" = true ]; then
                if [[ "$WORKLOAD" == "job" || "$WORKLOAD" == "job_full" || "$WORKLOAD" == "syn" || "$WORKLOAD" == "stats" ]]; then
                    bash experiment_scripts/core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
                fi
            fi
        done
    done
done

echo ""
echo "Different LLMs Comparison Experiments completed!"
