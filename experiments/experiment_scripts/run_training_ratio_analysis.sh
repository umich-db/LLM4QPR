#!/bin/bash
# Training Ratio Analysis Experiments
# Interactive script to run experiments with different training data ratios

echo "Running Training Ratio Analysis Experiments..."

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

# Define available training ratios
train_ratios=(
    "0.2"
    "0.4"
    "0.6"
    "0.8"
    "1.0"
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

# Get training ratio selection
echo ""
echo "=== Training Ratio Selection ==="
echo "Choose training ratio(s):"
for i in "${!train_ratios[@]}"; do
    echo "$((i+1)). ${train_ratios[i]}"
done
echo "Enter numbers separated by spaces (e.g., 1 2 3) or 'all' for all options:"
read -r ratio_selection

selected_ratios=()
if [[ "$ratio_selection" == "all" ]]; then
    selected_ratios=("${train_ratios[@]}")
else
    for num in $ratio_selection; do
        if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#train_ratios[@]}" ]]; then
            selected_ratios+=("${train_ratios[$((num-1))]}")
        else
            echo "Invalid selection: $num"
            exit 1
        fi
    done
fi

echo "Selected training ratios: ${selected_ratios[*]}"

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

echo ""
echo "=== Configuration Summary ==="
echo "Models: ${selected_models[*]}"
echo "Workloads: ${selected_workloads[*]}"
echo "Training Ratios: ${selected_ratios[*]}"
echo "Bucketize: $BUCKETIZE"
echo "Quantification: $QUANTIFICATION"
echo "Seeds: ${seeds[*]}"
echo "Embed Size: $EMBED_SIZE"
echo "Tasks: $(if [ "$RUN_TIME" = true ]; then echo -n "time "; fi)$(if [ "$RUN_CARD" = true ]; then echo -n "card"; fi)"
echo ""
echo "Starting experiments..."

# Run experiments with SEED and WORKLOAD as outer loops, model_name and train_ratio as inner loops
for SEED in "${seeds[@]}"; do
    for WORKLOAD in "${selected_workloads[@]}"; do
        echo ""
        echo "=== Running experiments for Workload: $WORKLOAD, Seed: $SEED ==="
        
        for model_name in "${selected_models[@]}"; do
            for train_ratio in "${selected_ratios[@]}"; do
                echo "Running: Model=$model_name, Workload=$WORKLOAD, Seed=$SEED, TrainRatio=$train_ratio"
                
                # Create model name for file naming (replace / with -)
                model_name1="${model_name//\//-}"
                
                # Set environment variables
                export BUCKETIZE_INPUT="$BUCKETIZE"
                export QUANTIFICATION="$QUANTIFICATION"
                export EMBED_SIZE="$EMBED_SIZE"
                export EMBEDDINGS_EXIST="True"
                
                # Run time prediction experiment if selected
                if [ "$RUN_TIME" = true ]; then
                    export LLM_DOWNSTREAM
                    bash experiment_scripts/core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
                fi
                
                # Run cardinality prediction experiment if selected and workload supports it
                if [ "$RUN_CARD" = true ]; then
                    if [[ "$WORKLOAD" == "job" || "$WORKLOAD" == "job_full" || "$WORKLOAD" == "syn" || "$WORKLOAD" == "stats" ]]; then
                        export LLM_DOWNSTREAM
                        bash experiment_scripts/core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
                    fi
                fi
            done
        done
    done
done

echo ""
echo "Training Ratio Analysis Experiments completed!" 