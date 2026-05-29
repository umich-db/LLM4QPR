# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM4QPR evaluates pretrained LLMs for database query plan representation — predicting query execution costs and cardinalities from query plans. It implements multiple baseline algorithms (PostgreSQL, QueryFormer, BAO, AIMeetsAI) alongside LLM-based approaches with LoRA finetuning, quantization, and joint LLM+PRICE training.

## Running Experiments

All commands run from the `experiments/` directory.

### Single training run
```bash
cd experiments
python train.py \
  --db postgres --workload tpch --algo llm \
  --model_name "meta-llama/Llama-3.1-8B" \
  --llm_mode inference --quantification 4-bit \
  --batch_size 64 --num_epoch 100 --learning_rate 1e-4 \
  --log_file logs/example.log --output_dir_qerror results/example.csv
```

### Experiment suites (from `experiments/`)
```bash
bash experiment_scripts/run_baseline_comparison.sh    # LLM vs baselines
bash experiment_scripts/run_different_llms.sh         # Compare LLM families
bash experiment_scripts/run_finetuning_experiments.sh # LoRA finetuning
bash experiment_scripts/run_cross_workload_experiments.sh
```

### Key CLI arguments for train.py
- `--db postgres|mysql|duckdb` — database engine
- `--algo llm|llm_finetune|bao|queryformer|postgres|aimeetsai|price_finetune|llm_price_finetune`
- `--card` — cardinality task (default is cost/time estimation)
- `--llm_mode inference|lora|last` — LLM usage mode
- `--quantification 4-bit|8-bit` — model quantization
- `--embeddings_exist` — skip re-generating cached embeddings
- `--train_ratio 0.2-1.0` — fraction of training data
- `--seed 42` — reproducibility seed (experiments use 42, 43, 44)
- `--stats_token_inject` — enable statistics token embedding injection

## Environment Setup

Requires NVIDIA GPU with CUDA. Set `HF_TOKEN` env var for HuggingFace model access.

```bash
# Manual setup
bash setup_manual.sh

# Docker (preferred)
docker build -t llm4qpr .
docker run --gpus all -it --shm-size 16g -v $(pwd):/workspace llm4qpr bash
```

Key dependencies: PyTorch 2.7.0 (cu126), Transformers 4.55.2, PEFT 0.15.2, bitsandbytes 0.46.0, Flash-Attention 2.8.3.

## Architecture

### Data Pipeline
```
Query Plans (JSON/CSV in queryPlans/)
  → dataset_utils.get_new() → TreeNode trees
  → Algorithm-specific encoding (LLM tokenization / BAO tree conv / etc.)
  → Training (MSE loss) → Evaluation (Q-error metrics)
```

### Module Layout

**`evaluation/`** — Core shared library, imported by experiments via `sys.path.append`:
- `trainer.py` — Training loop (`train()`), evaluation (`evaluate()`), Q-error computation (`print_qerror()`), `Prediction` MLP class
- `dataset_utils.py` — Data loading (`get_new()`, `df2nodes()`, `construct_from_plans()`)
- `feature_extractor.py` — `TreeNode` class (plan node representation), `DatasetInfo` (dataset-level normalization metadata), plan traversal
- `utils.py` — `Normalizer` (log-scale normalization clamped to [0.001, 1.0])
- `algorithms/` — Baseline implementations: `postgres.py`, `aimeetsai.py`, `bao/` (TreeConvolution), `queryformer/`, `e2e_cost/`

**`experiments/`** — Experiment orchestration:
- `train.py` — Main entry point; parses args, initializes LLM, loads data, calls trainer
- `utilsTrain.py` — Argument parser (`parse_args()`), path setup (`prepare_paths()`), dual logger setup
- `utilsLLM.py` — `QueryPlanPredictor` (wraps HuggingFace models with tokenization, quantization, sliding windows), `QueryPlanDataset`, embedding generation/caching
- `field_categories.py` / `field_categories_duckdb.py` — Query plan field categorization
- `experiment_scripts/` — Shell scripts orchestrating multi-seed, multi-workload experiment runs
- `experiment_scripts/core_scripts/` — Low-level scripts: `run_baseline.sh`, `run_llm_card.sh`, `run_llm_time.sh`

**`queryPlans/`** — Pre-generated query plans (TPC-H, TPC-DS, IMDB, STATS). Download per `queryPlans/README.md`.

**`deepdb_augmented/`** — 20 datasets for cross-workload experiments.

### Key Classes

- **`TreeNode`** (`evaluation/feature_extractor.py`) — Represents one node in a query plan tree. Properties: nodeType, cost, card, filters, joins, children.
- **`DatasetInfo`** (`evaluation/feature_extractor.py`) — Aggregates min/max bounds for normalization across a dataset; holds `Normalizer` instances.
- **`Normalizer`** (`evaluation/utils.py`) — Log-scale normalization: `(log(val+0.001) - min) / (max - min)`, clamped to [0.001, 1.0].
- **`QueryPlanPredictor`** (`experiments/utilsLLM.py`) — Wraps HuggingFace LLMs (Llama, BERT, Qwen, Gemma, ModernBERT). Handles tokenization, 4/8-bit quantization, sliding windows for long sequences, LoRA adapter loading.
- **`Prediction`** (`evaluation/trainer.py`) — Downstream MLP: input → hidden → bottleneck → 1 output.

### Evaluation Metrics
- **Q-error**: `max(pred/true, true/pred)` — reported at median, p90, p95, pmax
- **Absolute error**: RMSE, median, percentiles
- **Correlation**: Pearson (raw and log-space)

### Import Convention
`experiments/train.py` adds `../evaluation/` to `sys.path` and imports directly from `dataset_utils`, `feature_extractor`, `trainer`, etc. (no package install).

## Output Artifacts

- `experiments/results/` — CSV files with error distributions
- `experiments/logs/` — Training logs + separate `_inference.log` for LLM runs
- `experiments/embeddings/` — Cached LLM/baseline embeddings (reuse with `--embeddings_exist`)
- `experiments/finetuned_models/` — Saved LoRA adapters and model weights

## Experiment Modes & Comparison Harness

`experiment_scripts/_compare_modes_lib.sh` is the shared library (sourced, not run) that defines the comparison "modes" and drives multi-`(db × workload × mode)` sweeps via `run_ablation`. Callers set `DB_ENGINES`, `WORKLOADS_ARR`, `MODES_ARR`, `MODEL`, `SEEDS`, then call `run_ablation`.

Mode taxonomy (modes 7/7b/12/12w are `--algo llm_price_finetune`):
- **1** — pretrained LLM inference, no LoRA, no PRICE (`--finetune_mode 1`)
- **2** — LoRA finetune, no PRICE (`--finetune_mode 2`)
- **7** — JointPrice with PRICE_N (`PRICE_N_FLAGS = --price_n --price_n_or --price_random_init`)
- **7b** — JointPrice with original PRICE_B (`PRICE_B_FLAGS = --price_b --price_random_init`)
- **12** — biCrossAttn + inflatePRICE + cx4 **with** warmup schedule (`MODE12_SCHED = --price_warmup_epochs 5 --freeze_llm_until_epoch 5`)
- **12w** — mode 12 **without** the warmup/freeze schedule (`MODE12W_SCHED = --price_warmup_epochs 0 --freeze_llm_until_epoch 0`)

Notes:
- `CUDA_VISIBLE_DEVICES` defaults to **0** (was 1; on single-GPU hosts the old default hid the GPU → silent CPU fallback).
- `build_shared` drops `ft_batch_size` to 4 with `grad_accum=6` for tpch/tpcds (OOM guard on 16 GB GPUs).
- `plans_exist` canonicalizes `syn`/`job`/`job_full` → `imdb` (one imdb-canonical LoRA is reused across those three workloads).
- One-off reruns: `rerun_duckdb_tpch_L4_12_12w_7b.sh`, `rerun_duckdb_tpch_bert2_sentbert_crashes.sh`. Coverage-fill: `fill_missing_modes_{A,B,C}.sh`.

## Result Aggregation & Tables

Run from `experiments/`:
- `to_table_relative.py --dirs results/<db>/... --task time --anchor {50,90,95,max}` — per-dataset **relative** Q-error (each dataset divided by the best method's value at the anchor quantile), averaged across a db's workloads → `results/<db>/relative_qerror_<db>_<task>_anchor<N>.csv` + heatmap (anchor `50` → no `_anchorN` suffix). Heatmap-only filters: `--bert2_only`, `--bert_only`/`--bert4_only`, `--sentbert_only`, `--exclude_retrain_mlp`, `--retrain_mlp_only` (CSV stays complete).
- `cross_engine_aggregate.py --anchor 90` — aggregates those per-db CSVs across `{postgres,duckdb,spark}` per model (`bert2`=L-2_H-256, `bert4`=L-4_H-768, `sentbert`=all-MiniLM), two methods: `_simple` (arithmetic mean) and `_normalized` (anchor-min re-normalized within the model subset) → `results/cross_engine/relative_qerror_<model>_<task>_anchor<N>_{simple,normalized}.csv` + heatmaps. `--jointmlp_only` restricts heatmaps to `_jointMLP` columns.
- `compare_modes_table.py` (env `ANCHOR=90`) — 3×9 mode-vs-mode win/loss table reading the relative CSVs; cell ∈ {−1,0,+1} by quantile-win majority over {50,90,95,max}.

## Model Selection Experiments

Model-selection experiments live in `experiment_scripts/` and are driven by the runbook **`analyze_overall.sh`** (its top ~17 lines are the active model-selection section). The method is **round-based Pareto filtering under a compute budget** — multi-objective (inference latency vs Q-error). This is the current framework; the older single-objective surrogate prototype (`model_selection_v2.py`, `visualize_search.py`, …) is **archived** under `experiments/_archive/model_selection_v2/` — do not mistake it for live code.

Core pieces (in `experiment_scripts/`):
- **`compare_round_pareto.py`** — main driver (`run_ours()`). Trains the candidate pool in 4-epoch chunks `[e1-4, e5-8, e9-12, e13-16]`; at decision epochs (subset of {4,8,12}) prunes survivors by Pareto-level rank (`pareto_levels()`) down to a floor `keep_n = max(n_buckets, frontier_size, ceil(n*keep_ratio))`; scores hypervolume (`hv_2d_min()`) + recall vs a precomputed true frontier; compares against a cost-matched random monotonic baseline (`random_monotonic_prefix()`).
  - Flags: `--init_strategy {stratified(default),random,kmeans,stratified_metadata,stratified_centroid,stratified_arch,stratified_arch_round,stratified_kmeans_round}`, `--rounds {1,2,3,4}` (legacy alias: 1→[], 2→[8], 3→[8,12], 4→[4,8,12]), `--decision_epochs 4 8 12` (overrides `--rounds`), `--keep_ratio` (0.75), `--keep_strategy {topval(default),stratified,random}`, `--init_Ks`, `--seeds`, `--n_init_bins`, `--hv_ref_margin` (1.05), `--sweep`/`--sweep_rounds`/`--sweep_keep_ratios`, `--output`, `--per_seed_output`.
  - Filtering decisions use validation p90 (`val_p90_e{4,8,12}`); final HV/recall use `test_p90_e16`.
- **`select_pareto_next_round.py`** — `pareto_levels(points)` (1-indexed Pareto levels; both axes minimized). Live dependency of the driver.
- **`rank_correlation_epochs.py`** — Spearman/Kendall + top-K Jaccard between epoch rankings (does early val predict final test?).
- **`ablate_init_and_keep.py`** — fixed configs A–E to attribute HV gains to init vs keep vs filter.
- **`compare_selection_budgets.py`** — sequential selection under a strict training-time budget (KMeans-metadata init → RandomForest-guided greedy expansion) vs random.
- **`plot_hv_vs_hours.py`** — HV vs compute-hours curves for configs A–H (`--settings C D F G H`, `--output ./model_selection.png`); re-runs `compare_round_pareto.py` per config (expensive).
- **`plot_true_frontier.py`** — test-side Pareto frontier on (avg_ms latency × test_p90_e16) → `./true_pareto_frontier.png` (`--annotate --logy --max_qerror --max_latency`).

Inputs: `logs/postgres/logs_Train_stats_Test_stats_ours/all_models/all_models_full_e16.csv` (`--all_models_csv`) and `experiment_scripts/model_profile_with_nonemb.csv` (`--profile_csv`).

Despite their names, **not** part of the archived prototype: `random_model_selection.py` (random baseline used by `master_random_inflatePRICE_e16_group_{A,B,C,D}.sh`) and `experiments/model_selection.png` (a live `plot_hv_vs_hours.py` output).

> A separate top-level package `model_selection/` (`pareto_frontier_search.py`, `multi_fidelity/`) implements a related surrogate/Pareto search; it is distinct from the `analyze_overall.sh` experiment framework above.

## Gotchas

- **DuckDB tpch/tpcds latency must be scaled to nanoseconds.** `utilsLLM._find_actual_total_time(root_node, db, workload)` multiplies latency by `1e9` when `db == 'duckdb' and workload in ('tpch','tpcds')` (`utilsLLM.py:1978-1979`; call site ~2660 passes `workload=getattr(argsP, 'workload_test', None)`). DuckDB serves these from memory in sub-microsecond time; without the scale the `Normalizer`'s `+0.001` epsilon collapses the log dynamic range to ≈0 and training diverges. **Regression symptom:** catastrophic Q-errors (p90 ≈ 1e5–1e6) on duckdb tpch/tpcds only, while other db/workload cells are fine.
