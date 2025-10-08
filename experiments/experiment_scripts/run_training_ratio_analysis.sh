#!/bin/bash
# Training Ratio Analysis Experiments
# Analyzes performance with different training data ratios

echo "Running Training Ratio Analysis Experiments..."

model_name=meta-llama/Llama-3.1-8B
model_name1="${model_name//\//-}"
export BUCKETIZE_INPUT="separate"
export EMBEDDINGS_EXIST="True"

for SEED in 42 43 44; do
  for WORKLOAD in "tpch" "tpcds" "stats"; do
#   for WORKLOAD in "tpch" "tpcds" "job" "syn" "stats"; do
      for train_ratio in 0.2 0.4 0.6 0.8; do
    #   for train_ratio in 0.2 0.4 0.6 0.8 1.0; do
          bash experiment_scripts/core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
          if [[ $WORKLOAD == "job" || $WORKLOAD == "job_full" || $WORKLOAD == "syn" || $WORKLOAD == "stats" ]]; then
              bash experiment_scripts/core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
          fi
      done
  done
done

echo "Training Ratio Analysis Experiments completed!" 