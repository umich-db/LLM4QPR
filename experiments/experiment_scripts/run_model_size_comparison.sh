#!/bin/bash
# Model Size Comparison Experiments
# Compares performance across different Llama model sizes

echo "Running Model Size Comparison Experiments..."

for SEED in 42 43 44; do
  for WORKLOAD in "tpch" "tpcds" "stats"; do
      for model_name in "meta-llama/Llama-3.2-1B" "meta-llama/Llama-3.2-3B" "meta-llama/Llama-3.1-8B" "meta-llama/Llama-3.1-70B"; do
          model_name1="${model_name//\//-}"
          if [[ $WORKLOAD == "stats" ]]; then
            bash core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
          fi
          bash core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
      done
  done
done

echo "Model Size Comparison Experiments completed!" 