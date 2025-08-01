#!/bin/bash
# Finetuning Experiments
# Tests LLM finetuning performance

echo "Running Finetuning Experiments..."

model_name=meta-llama/Llama-3.1-8B
model_name1="${model_name//\//-}"

for SEED in 42 43 44; do
  for WORKLOAD in "tpch" "tpcds" "stats"; do        
      if [[ $WORKLOAD == "stats" ]]; then
          bash core_scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 0.1 True $model_name $model_name1 $SEED
      fi
      bash core_scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 0.1 True $model_name $model_name1 $SEED
  done
done

echo "Finetuning Experiments completed!" 