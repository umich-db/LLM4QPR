#!/bin/bash
# Verbose Results Experiments
# Runs LLM experiments with verbose output enabled

echo "Running Verbose Results Experiments..."

model_name=meta-llama/Llama-3.1-8B
model_name1="${model_name//\//-}"

# Export verbose_info environment variable
export VERBOSE_INFO="true"

for SEED in 42 43 44; do
  # for WORKLOAD in "tpch" "tpcds" "syn" "job" "stats"; do
  for WORKLOAD in "tpch"; do
        for BUCKETIZE in "unified"; do
        # for BUCKETIZE in "separate" "unified"; do
            export BUCKETIZE_INPUT="$BUCKETIZE"
            bash experiment_scripts/core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
            if [[ "$WORKLOAD" == "job" || "$WORKLOAD" == "job_full" || "$WORKLOAD" == "syn" || "$WORKLOAD" == "stats" ]]; then
                bash experiment_scripts/core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
            fi
        done
  done
done

echo "Verbose Results Experiments completed!"
