#!/bin/bash
# Baseline Comparison Experiments
# Compares LLM performance against baseline methods

echo "Running Baseline Comparison Experiments..."

model_name=meta-llama/Llama-3.1-8B
model_name1="${model_name//\//-}"

for SEED in 42 43 44; do
  for WORKLOAD in "tpch" "tpcds" "job" "syn" "stats"; do
        bash core_scripts/run_baseline.sh $WORKLOAD $WORKLOAD 1.0 $SEED
        bash core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
        if [[ "$WORKLOAD" == "job" || "$WORKLOAD" == "syn" || "$WORKLOAD" == "stats" ]]; then
            bash core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
        fi
  done
done

echo "Baseline Comparison Experiments completed!" 