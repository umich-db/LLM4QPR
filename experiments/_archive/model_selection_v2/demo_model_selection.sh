#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# Demo: Latency-Aware Model Selection Pipeline
# ─────────────────────────────────────────────────────────────────────
# This script demonstrates the model selection pipeline end-to-end
# using a small subset of models and a generous latency budget.
#
# It exercises all 4 phases:
#   1. Binary search for latency feasibility
#   2. Inference-only accuracy evaluation of nearby models
#   3. Best-model selection (fastest within 10% of best p90)
#   4. Full JointPrice finetuning (mode 7) with selected model
#
# Requirements:
#   - GPU (RTX 5080 or similar with >=8 GB VRAM)
#   - queryPlans/stats/postgres/long_raw_postgres_stats.csv
#   - HF_TOKEN set if using gated models
#
# Runtime estimate: ~15-30 min depending on GPU and network speed
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # move to experiments/

echo "============================================================"
echo " Demo: Latency-Aware Model Selection"
echo "============================================================"
echo ""
echo "This demo uses:"
echo "  - Workload:       stats (smallest IMDB-derived workload)"
echo "  - Latency limit:  200 ms/query (generous, to see multiple feasible models)"
echo "  - Probe queries:  20 (fast probing)"
echo "  - Task:           time (cost estimation)"
echo "  - Single seed:    42"
echo "  - Finetune:       5 epochs (quick demo)"
echo ""

# ─── Phase-by-phase walkthrough ──────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Running full pipeline..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash experiment_scripts/run_model_selection.sh \
    --latency_limit 10 \
    --workloads "stats" \
    --task "time" \
    --seeds "42" \
    --db "postgres" \
    --quantification "4-bit" \
    --ft_batch_size 16 \
    --ft_num_epoch 20 \
    --epsilon 0.1 \
    --price_s \
    --checkpoint_interval 5 \
    --num_probe_queries 20 \
    --embed_size 1000

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Demo complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "What happened:"
echo "  Phase 1 - Binary-searched 15 models to find the largest"
echo "            one that embeds a query in ≤200 ms."
echo "  Phase 2 - Ran inference-only (mode 1) on up to 3 nearby"
echo "            models to measure p90 Q-error."
echo "  Phase 3 - Picked the fastest model within 10% of the best"
echo "            p90 Q-error."
echo "  Phase 4 - Ran JointPrice finetuning (mode 7, 5 epochs)"
echo "            with pretrained PRICE weights + PRICE_S."
echo ""
echo "Results are in:"
echo "  experiments/results/postgres/results_Train_stats_Test_stats_ours/"
echo ""
echo "Logs (review the full selection process):"
echo "  ls -lt logs/model_selection/"
echo ""
echo "  .log file — timestamped trace of every phase, every model probed,"
echo "              binary search steps, latency measurements, Q-error results"
echo "  .json file — machine-readable summary: selected model, all candidates,"
echo "               latencies, p90 scores, and full run config"
echo ""
echo "Example:"
echo "  cat logs/model_selection/model_selection_*.log   # full trace"
echo "  python3 -m json.tool logs/model_selection/model_selection_*.json  # summary"
echo ""
echo "To run with a tighter latency budget (selects a smaller model):"
echo "  bash experiment_scripts/run_model_selection.sh \\"
echo "      --latency_limit 15 --workloads 'stats' --task time \\"
echo "      --seeds '42' --db postgres --quantification 4-bit \\"
echo "      --ft_batch_size 16 --ft_num_epoch 5 --price_s"
