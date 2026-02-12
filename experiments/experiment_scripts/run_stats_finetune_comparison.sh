#!/bin/bash
# Compare finetuned LLMs with and without stats token injection.

# Optional env:
#   BUCKETIZE_INPUT, QUANTIFICATION, REMOVED_FIELDS, VERBOSE_INFO,
#   STATS_PG_STATS_PATH, STATS_TABLE_SIZES_PATH, STATS_TOKEN_STR, STATS_TOKEN_DIM

export EMBEDDINGS_EXIST=${EMBEDDINGS_EXIST:-False}
export FINETUNE_RUN_LAST=${FINETUNE_RUN_LAST:-true}
export FINETUNE_RUN_LORA=${FINETUNE_RUN_LORA:-true}

# Optional stats token parameters
if [[ -n "$STATS_TOKEN_STR" ]]; then
  export STATS_TOKEN_STR
fi
if [[ -n "$STATS_TOKEN_MODE" ]]; then
  export STATS_TOKEN_MODE
fi
if [[ -n "$STATS_TOKEN_DIM" ]]; then
  export STATS_TOKEN_DIM
fi
if [[ -n "$STATS_PG_STATS_PATH" ]]; then
  export STATS_PG_STATS_PATH
fi
if [[ -n "$STATS_TABLE_SIZES_PATH" ]]; then
  export STATS_TABLE_SIZES_PATH
fi

# Default knobs (can be overridden via interactive prompts)
TRAIN_RATIO=${TRAIN_RATIO:-1.0}
EMBED_SIZE=${EMBED_SIZE:-1000}

# Available models/workloads (same as run_different_llms.sh)
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

workloads=(
  "tpch"
  "tpcds"
  "syn"
  "job"
  "job_full"
  "stats"
)

run_time_card() {
  local task_label=$1
  local mode=${STATS_TOKEN_INJECT_MODE:-both}

  if [[ "$mode" == "without" || "$mode" == "both" ]]; then
    export STATS_TOKEN_INJECT=false
    bash experiment_scripts/core_scripts/run_llm_${task_label}.sh "${TRAIN_WLS[*]}" "$WORKLOAD_TEST" "$TRAIN_RATIO" True "$MODEL_NAME" "$MODEL_NAME1" "$SEED"
  fi

  if [[ "$mode" == "with" || "$mode" == "both" ]]; then
    export STATS_TOKEN_INJECT=true
    bash experiment_scripts/core_scripts/run_llm_${task_label}.sh "${TRAIN_WLS[*]}" "$WORKLOAD_TEST" "$TRAIN_RATIO" True "$MODEL_NAME" "$MODEL_NAME1" "$SEED"
  fi
}

if [[ $# -ge 6 ]]; then
  IFS=' ' read -r -a TRAIN_WLS <<< "$1"
  WORKLOAD_TEST=$2
  MODEL_NAME=$3
  MODEL_NAME1=$4
  SEED=$5
  TASK=$6

  if [[ "$TASK" == "time" || "$TASK" == "both" ]]; then
    run_time_card "time"
  fi
  if [[ "$TASK" == "card" || "$TASK" == "both" ]]; then
    run_time_card "card"
  fi
  exit 0
fi

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

echo ""
echo "=== Training Workloads Selection ==="
echo "Choose training workload(s):"
for i in "${!workloads[@]}"; do
  echo "$((i+1)). ${workloads[i]}"
done
echo "Enter numbers separated by spaces (e.g., 1 3) or 'all' for all options:"
read -r train_selection

TRAIN_WLS=()
if [[ "$train_selection" == "all" ]]; then
  TRAIN_WLS=("${workloads[@]}")
else
  for num in $train_selection; do
    if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#workloads[@]}" ]]; then
      TRAIN_WLS+=("${workloads[$((num-1))]}")
    else
      echo "Invalid selection: $num"
      exit 1
    fi
  done
fi
echo "Selected training workloads: ${TRAIN_WLS[*]}"

echo ""
echo "=== Test Workload Selection ==="
echo "Choose test workload:"
for i in "${!workloads[@]}"; do
  echo "$((i+1)). ${workloads[i]}"
done
echo "Enter a number (e.g., 1):"
read -r test_selection
if [[ "$test_selection" =~ ^[0-9]+$ ]] && [[ "$test_selection" -ge 1 ]] && [[ "$test_selection" -le "${#workloads[@]}" ]]; then
  WORKLOAD_TEST="${workloads[$((test_selection-1))]}"
else
  echo "Invalid selection: $test_selection"
  exit 1
fi
echo "Selected test workload: $WORKLOAD_TEST"

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
export LLM_DOWNSTREAM
echo "Using downstream: $LLM_DOWNSTREAM"

echo ""
echo "=== Bucketize Option ==="
echo "1. separate"
echo "2. unified"
echo "3. None"
echo "Enter choice (1, 2, or 3):"
read -r bucketize_choice
if [[ "$bucketize_choice" == "1" ]]; then
  BUCKETIZE_INPUT="separate"
elif [[ "$bucketize_choice" == "2" ]]; then
  BUCKETIZE_INPUT="unified"
elif [[ "$bucketize_choice" == "3" ]]; then
  BUCKETIZE_INPUT="None"
else
  echo "Invalid choice, defaulting to unified"
  BUCKETIZE_INPUT="unified"
fi
export BUCKETIZE_INPUT

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
export QUANTIFICATION

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

echo ""
echo "=== Embedding Size ==="
echo "Enter embedding size (default: 1000, or 9999999 for full):"
read -r embed_size_input
if [[ -z "$embed_size_input" ]]; then
  EMBED_SIZE=1000
else
  EMBED_SIZE=$embed_size_input
fi
export EMBED_SIZE

echo ""
echo "=== Train Ratio ==="
echo "Enter train ratio (default: 1.0):"
read -r train_ratio_input
if [[ -z "$train_ratio_input" ]]; then
  TRAIN_RATIO=1.0
else
  TRAIN_RATIO=$train_ratio_input
fi
export TRAIN_RATIO

echo ""
echo "=== Task Selection ==="
echo "1. time (cost estimation)"
echo "2. card (cardinality estimation)"
echo "3. both"
echo "Enter choice (1, 2, or 3):"
read -r task_choice
if [[ "$task_choice" == "1" ]]; then
  TASK="time"
elif [[ "$task_choice" == "2" ]]; then
  TASK="card"
elif [[ "$task_choice" == "3" ]]; then
  TASK="both"
else
  echo "Invalid choice, defaulting to both"
  TASK="both"
fi

echo ""
echo "=== Stats Token Injection ==="
echo "1. without stats token injection"
echo "2. with stats token injection"
echo "3. both"
echo "Enter choice (1, 2, or 3):"
read -r stats_choice
if [[ "$stats_choice" == "1" ]]; then
  STATS_TOKEN_INJECT_MODE="without"
elif [[ "$stats_choice" == "2" ]]; then
  STATS_TOKEN_INJECT_MODE="with"
elif [[ "$stats_choice" == "3" ]]; then
  STATS_TOKEN_INJECT_MODE="both"
else
  echo "Invalid choice, defaulting to both"
  STATS_TOKEN_INJECT_MODE="both"
fi
export STATS_TOKEN_INJECT_MODE

echo ""
echo "=== Stats Token Mode ==="
echo "1. avg (one token per predicate)"
echo "2. per_column (one token per column)"
echo "Enter choice (1 or 2):"
read -r stats_mode_choice
if [[ "$stats_mode_choice" == "1" ]]; then
  STATS_TOKEN_MODE="avg"
elif [[ "$stats_mode_choice" == "2" ]]; then
  STATS_TOKEN_MODE="per_column"
else
  echo "Invalid choice, defaulting to per_column"
  STATS_TOKEN_MODE="per_column"
fi
export STATS_TOKEN_MODE

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
export REMOVED_FIELDS

echo ""
echo "=== Finetune Modes ==="
echo "1. last"
echo "2. lora"
echo "3. both"
echo "Enter choice (1, 2, or 3):"
read -r finetune_choice
if [[ "$finetune_choice" == "1" ]]; then
  FINETUNE_RUN_LAST=true
  FINETUNE_RUN_LORA=false
elif [[ "$finetune_choice" == "2" ]]; then
  FINETUNE_RUN_LAST=false
  FINETUNE_RUN_LORA=true
else
  FINETUNE_RUN_LAST=true
  FINETUNE_RUN_LORA=true
fi
export FINETUNE_RUN_LAST
export FINETUNE_RUN_LORA

echo ""
echo "=== Configuration Summary ==="
echo "Models: ${selected_models[*]}"
echo "Train Workloads: ${TRAIN_WLS[*]}"
echo "Test Workload: $WORKLOAD_TEST"
echo "Bucketize: $BUCKETIZE_INPUT"
echo "Quantification: $QUANTIFICATION"
echo "Seeds: ${seeds[*]}"
echo "Embed Size: $EMBED_SIZE"
echo "Train Ratio: $TRAIN_RATIO"
echo "Tasks: $TASK"
echo "Stats Token Injection: ${STATS_TOKEN_INJECT_MODE:-both}"
echo "Stats Token Mode: ${STATS_TOKEN_MODE:-per_column}"
echo "Removed Fields: ${REMOVED_FIELDS:-none}"
echo "Finetune: last=${FINETUNE_RUN_LAST}, lora=${FINETUNE_RUN_LORA}"
echo ""
echo "Starting finetune comparison..."

for SEED in "${seeds[@]}"; do
  for MODEL_NAME in "${selected_models[@]}"; do
    MODEL_NAME1="${MODEL_NAME//\//-}"
    if [[ "$TASK" == "time" || "$TASK" == "both" ]]; then
      run_time_card "time"
    fi
    if [[ "$TASK" == "card" || "$TASK" == "both" ]]; then
      run_time_card "card"
    fi
  done
done
