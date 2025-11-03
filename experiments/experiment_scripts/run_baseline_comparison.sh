#!/bin/bash
# Baseline Comparison Experiments
# Compares LLM performance against baseline methods

echo "Running Baseline Comparison Experiments..."

# Get verbose output option
echo ""
echo "=== Verbose Output Option ==="
echo "Enable verbose output with embeddings and KNN information?"
echo "1. Yes (enable verbose output)"
echo "2. No (disable verbose output)"
echo "Enter choice (1 or 2):"
read -r verbose_choice

if [[ "$verbose_choice" == "1" ]]; then
    export VERBOSE_INFO="true"
    echo "Verbose output enabled"
elif [[ "$verbose_choice" == "2" ]]; then
    export VERBOSE_INFO="false"
    echo "Verbose output disabled"
else
    echo "Invalid choice, defaulting to disabled"
    export VERBOSE_INFO="false"
fi

model_name=meta-llama/Llama-3.1-8B
model_name1="${model_name//\//-}"

## Define available AIME feature masks
feature_masks=(
  "11111"  # all features
  "01111"  # disable cost
  "10111"  # disable card
  "11011"  # disable wei_rows
  "11101"  # disable byte
  "11110"  # disable wei_costs
  "01110"  # disable cost and wei_costs
  "10011"  # disable card and wei_rows
)

echo "=== AIME Feature Mask Selection ==="
echo "Choose feature mask(s):"
for i in "${!feature_masks[@]}"; do
  echo "$((i+1)). ${feature_masks[i]}"
done
echo "Enter numbers separated by spaces (e.g., 1 3 5) or 'all' for all options:"
read -r mask_selection

selected_masks=()
if [[ "$mask_selection" == "all" ]]; then
  selected_masks=("${feature_masks[@]}")
else
  for num in $mask_selection; do
    if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#feature_masks[@]}" ]]; then
      selected_masks+=("${feature_masks[$((num-1))]}")
    else
      echo "Invalid selection: $num"
      exit 1
    fi
  done
fi

echo "Selected masks: ${selected_masks[*]}"

# Algorithm selection
algorithms=("aimai" "qf" "bao" "postgres" "e2e_cost")
echo ""
echo "=== Algorithm Selection ==="
echo "Choose algorithm(s):"
for i in "${!algorithms[@]}"; do
  echo "$((i+1)). ${algorithms[i]}"
done
echo "Enter numbers separated by spaces (e.g., 1 3) or 'all' for all options:"
read -r algo_selection

selected_algorithms=()
if [[ "$algo_selection" == "all" ]]; then
  selected_algorithms=("${algorithms[@]}")
else
  for num in $algo_selection; do
    if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le "${#algorithms[@]}" ]]; then
      selected_algorithms+=("${algorithms[$((num-1))]}")
    else
      echo "Invalid selection: $num"
      exit 1
    fi
  done
fi

echo "Selected algorithms: ${selected_algorithms[*]}"

# Task selection (card or time)
echo ""
echo "=== Task Selection ==="
echo "1. card (cardinality estimation)"
echo "2. time (cost estimation)"
echo "3. both"
echo "Enter choice (1, 2, or 3):"
read -r task_choice

RUN_CARD=false
RUN_TIME=false

if [[ "$task_choice" == "1" ]]; then
    RUN_CARD=true
elif [[ "$task_choice" == "2" ]]; then
    RUN_TIME=true
elif [[ "$task_choice" == "3" ]]; then
    RUN_CARD=true
    RUN_TIME=true
else
    echo "Invalid choice, defaulting to both"
    RUN_CARD=true
    RUN_TIME=true
fi

echo "Selected tasks: $(if [ "$RUN_CARD" = true ]; then echo -n "card "; fi)$(if [ "$RUN_TIME" = true ]; then echo -n "time"; fi)"

# Workload selection
workloads=(
    "tpch"
    "tpcds"
    "syn"
    "job"
    "job_full"
    "stats"
)

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

# Seed selection
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

echo "Selected seeds: ${seeds[*]}"

echo ""
echo "=== Configuration Summary ==="
echo "Algorithms: ${selected_algorithms[*]}"
echo "Workloads: ${selected_workloads[*]}"
echo "AIME Feature Masks: ${selected_masks[*]}"
echo "Seeds: ${seeds[*]}"
echo "Tasks: $(if [ "$RUN_CARD" = true ]; then echo -n "card "; fi)$(if [ "$RUN_TIME" = true ]; then echo -n "time"; fi)"
echo "Verbose Output: $VERBOSE_INFO"
echo ""
echo "Starting experiments..."

for SEED in "${seeds[@]}"; do
  for WORKLOAD in "${selected_workloads[@]}"; do
    for ALGO in "${selected_algorithms[@]}"; do
      # Run card task if selected
      if [ "$RUN_CARD" = true ]; then
        if [[ "$ALGO" == "aimai" ]]; then
          # For aimai, iterate through feature masks
          for AIME_FEATURES in "${selected_masks[@]}"; do
            bash experiment_scripts/core_scripts/run_baseline.sh $WORKLOAD $WORKLOAD 1.0 $SEED $AIME_FEATURES $ALGO "card"
          done
        else
          # For other algorithms, use default feature mask (ignored)
          bash experiment_scripts/core_scripts/run_baseline.sh $WORKLOAD $WORKLOAD 1.0 $SEED 11111 $ALGO "card"
        fi
      fi
      
      # Run time task if selected
      if [ "$RUN_TIME" = true ]; then
        if [[ "$ALGO" == "aimai" ]]; then
          # For aimai, iterate through feature masks
          for AIME_FEATURES in "${selected_masks[@]}"; do
            bash experiment_scripts/core_scripts/run_baseline.sh $WORKLOAD $WORKLOAD 1.0 $SEED $AIME_FEATURES $ALGO "time"
          done
        else
          # For other algorithms, use default feature mask (ignored)
          bash experiment_scripts/core_scripts/run_baseline.sh $WORKLOAD $WORKLOAD 1.0 $SEED 11111 $ALGO "time"
        fi
      fi
    done
  done
done

echo "Baseline Comparison Experiments completed!" 