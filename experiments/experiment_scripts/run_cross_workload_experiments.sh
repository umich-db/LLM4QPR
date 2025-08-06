#!/bin/bash
# Cross-Workload Experiments
# Tests model generalization across different workloads with and without finetuning

echo "Running Cross-Workload Experiments..."

model_name=meta-llama/Llama-3.1-8B
model_name1="${model_name//\//-}"
ALL_WORKLOADS="genome financial movielens geneea seznam tpc_h walmart airline carcinogenesis baseball imdb accidents ssb basketball employee fhnk consumer tournament credit hepatitis"
WORKLOAD_TEST_OPTIONS="tpc_h synthetic job-light"

for SEED in 42 43 44; do
  for WORKLOAD_TEST in $WORKLOAD_TEST_OPTIONS; do
    # build a string of "the WORKLOADS_TRAIN"
    WORKLOADS_TRAIN=""
    for o in $ALL_WORKLOADS; do
      if [[ $o != $WORKLOAD_TEST ]]; then
        # Remove imdb from training if testing on synthetic or job-light
        if [[ ($WORKLOAD_TEST == "synthetic" || $WORKLOAD_TEST == "job-light") && $o == "imdb" ]]; then
          continue
        fi
        WORKLOADS_TRAIN="$WORKLOADS_TRAIN $o"
      fi
    done
    # strip leading space
    WORKLOADS_TRAIN=${WORKLOADS_TRAIN# }

    echo "Testing on: $WORKLOAD_TEST"
    echo "Training on: $WORKLOADS_TRAIN"
    
    # Without finetuning
    echo "Running without finetuning..."
    bash experiment_scripts/core_scripts/run_llm_time.sh "$WORKLOADS_TRAIN" "$WORKLOAD_TEST" 1.0 False $model_name $model_name1 $SEED
    
    # With finetuning
    echo "Running with finetuning..."
    bash experiment_scripts/core_scripts/run_llm_time.sh "$WORKLOADS_TRAIN" "$WORKLOAD_TEST" 0.1 True $model_name $model_name1 $SEED
  done
done

echo "Cross-Workload Experiments completed!" 