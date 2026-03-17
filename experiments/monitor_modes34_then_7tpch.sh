#!/bin/bash
# Monitor modes 3+4 for job-light, then launch mode 7 for tpc_h
set -e

RESULTS_DIR="/root/LLM4QPR/experiments/results/postgres/results_Train_genome-financial-movielens-geneea-seznam-tpc_h-walmart-airline-carcinogenesis-baseball-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_job-light_ours"

# Mode 3 (PriceNoFT) result pattern
M3_PATTERN="time_llm_price_pretrained-None_*_priceS_seed"
# Mode 4 (PriceLLMOnly) result pattern
M4_PATTERN="time_llm_price_pretrained-lora_*_priceS_seed"

wait_for_results() {
    local pattern="$1"
    local mode_name="$2"
    while true; do
        count=$(ls "$RESULTS_DIR"/${pattern}*.csv 2>/dev/null | grep -v cdf | grep -v length_vs | wc -l)
        if [[ "$count" -ge 3 ]]; then
            echo "$(date): $mode_name complete ($count result CSVs found)"
            return 0
        fi
        echo "$(date): $mode_name — $count/3 result CSVs so far, waiting..."
        sleep 120
    done
}

echo "$(date): Monitoring modes 3+4 for job-light..."

# Wait for mode 3 (PriceNoFT) - 3 seeds
wait_for_results "$M3_PATTERN" "Mode 3 (PriceNoFT)"

# Wait for mode 4 (PriceLLMOnly) - 3 seeds
wait_for_results "$M4_PATTERN" "Mode 4 (PriceLLMOnly)"

echo "$(date): Modes 3+4 all done! Launching mode 7 for tpc_h..."

cd /root/LLM4QPR/experiments
source ~/venvs/tmpenv/bin/activate

bash experiment_scripts/run_cross_workload_experiments.sh \
    --models "sentence-transformers/all-MiniLM-L6-v2" \
    --workloads "tpc_h" \
    --task "time" \
    --downstream "mlp" \
    --quantification "4-bit" \
    --bucketize "None" \
    --embed_size "1000" \
    --concat_true "false" \
    --ft_batch_size "8" \
    --grad_accum_steps "4" \
    --ft_num_epoch "20" \
    --removed_fields "" \
    --seeds "42 43 44" \
    --price_s \
    --checkpoint_interval "5" \
    --finetune_mode 7 \
    --finetune_method "lora"

echo "$(date): Mode 7 tpc_h completed!"
