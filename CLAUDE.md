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

### Building the candidate pool — raw artifacts → ready-for-use data

`all_models_full_e16.csv` is the consumed artifact; new candidate models arrive as a **HuggingFace snapshot** (`HCAHOI/llm4qpr`, cached at `~/.cache/huggingface/hub/models--HCAHOI--llm4qpr/snapshots/<rev>/llm4qpr/<org>/<model>/seed42/`) holding, per model: `finetuned_models/checkpoint/state.pkl` (weights), `logs/*.log`+`*.console.log`, `results/*.{csv,_abs.txt,_predictions.csv}`, `manifest/upload_manifest.json`. These are **TPU v4 JAX/NNX** mode-12 (`priceBiCrossAttnJoint`, inflatePRICE) e16 runs. Two scripts process them (run from `experiment_scripts/`):

1. **`add_jax_snapshot_to_pool.py`** — appends one CSV pool row per model. Flags: `--snapshot`, `--profile_csv_dir`, `--pool`, `--dry-run`. **Accuracy** from the snapshot `.log`/`.console.log` (final `qerror_summary` → `test_*_e16`; per-epoch stage-1 `val_q_median` → `val_median_e{4,8,12,16}`, copied to `val_p90_e*` too — stage-1 logs no q90). **Timing** from the H100 profiling runs (see below). Idempotent, backs up the CSV, skips keys already present.
2. **`place_jax_snapshot.py`** — flags `--snapshot`, `--no-weights`, `--dry-run`. (a) COPY-dereferences raw artifacts to their canonical homes (paths from each `upload_manifest.json` `local`, host prefix `/home/<user>/LLM4QPR/experiments/` stripped): weights → `finetuned_models/postgres/expanded_pool_tpu_jax_nnx_full_20260428/<MD>/seed42/checkpoint/`, logs/results → the matching `..._jax_nnx_full_20260428/` dirs. (b) Generates the per-model pool dir `.../all_models/expanded_pool_tpu__<KEY>__e16/{summary.txt,train.log,inference.log}` byte-faithful to existing rows (upstream builder absent). `KEY = postgres_0.0001_b<bs>_h2048_<MD>_quant-4-bit_priceS_inflatePRICE_randInit_cx4`; `<MD>` = model name with `/`→`-`. **Copies, never moves** — snapshot files are symlinks into the HF blob cache; copying leaves the cache intact (it can be pruned afterward to reclaim ~8 GB of weights).

**Timing = the three time-consumption metrics** (the pool's `*_h100_ms` columns are what `compare_round_pareto.py:663` reads). Source: H100 probes in `/root/h100_profile_runs_2026-05-18/` — short `pwm1_frzLLM1_e2_tr0.1` runs (1 frozen warmup epoch + 1 unfrozen epoch, 10% data). `csvs/profile_model_db_warmup_e2.csv` gives `warmup_ms` (**warmup phase**) and `after_warmup_ms` (**post-warmup phase**); `csvs/profile_model_db_h100_per_query_ms.csv` gives `mean_per_query_ms` (**inference**). Verified-exact column formulas: `time_e1_4_*` = `warmup_ms`×40, `time_{e5_8,e9_12,e13_16}_*` = `after_warmup_ms`×40 (×10 for 0.1→full data, ×4 epochs/chunk), `test_total_eval_ms` = `test_testing_took_ms` = `mean_per_query_ms`, `pieces_gpu` = `e0:H100|...`. **Fallback** when the H100 training probe failed (exit≠0): `time_*` = `stage1_finetune_sec/4`, `time_*_h100` = ×0.3, `pieces_gpu=e0:tpuv4|...` (TPU-v4 wall × the 0.3 H100-equiv factor) — eval still uses the per-query probe if *it* succeeded. The JAX snapshot logs alone cannot split warmup vs post-warmup (only one aggregate `stage1_finetune_sec`, no per-epoch wall-clock) — that's what the H100 probes are for. The per-dir `summary.txt`/`train.log`/`inference.log` always report the TPU-v4 raw wall ×0.3 provenance (a different number from the CSV's H100-native timing — intentional). `model_profile_with_nonemb.csv` (latency axis `avg_ms`) is maintained separately.

**Caveat — albert ≥ xlarge OOM the H100 probe.** The biCrossAttn joint path keeps the quantized LLM + 805M-param inflated cross-attn + MLP in one autograd graph at batch 24; when the LLM unfreezes post-warmup, full-sequence activations through ALBERT's parameter-shared layers exceed 79 GiB. xlarge-v1/v2 OOM at the unfreeze (epoch 1, after a clean warmup); xxlarge-v2 OOMs in `loss.backward()` mid-warmup (never reaches unfreeze → no per-query eval either). They trained fine on TPU only because that path uses batch 4 + a decoupled two-stage design (LLM never in the graph at large batch); 4-bit quant doesn't help (the OOM is activation/gradient memory, not weights). These three rows therefore use the TPU×0.3 timing fallback.

Despite their names, **not** part of the archived prototype: `random_model_selection.py` (random baseline used by `master_random_inflatePRICE_e16_group_{A,B,C,D}.sh`) and `experiments/model_selection.png` (a live `plot_hv_vs_hours.py` output).

### Separate `model_selection/` package (top-level, live parallel track)

`model_selection/` (repo root, **not** `experiment_scripts/`) is a distinct, still-live research codebase implementing **surrogate-guided Pareto-frontier recovery** — a different algorithm from the `compare_round_pareto.py` round-based filtering above (the two do **not** import each other; `compare_round_pareto.py` uses its own `pareto_levels()`).

- **`pareto_frontier_search.py`** — `ParetoFrontierSearch` (Python API). Latency is offline-known; accuracy is fit by a bootstrap ensemble of random forests (`BootstrapEnsembleRegressor`); batch acquisition is latency-specific frontier Expected Improvement (`expected_improvement_maximization`). `SearchConfig` knobs: `init_budget`, `batch_size`, `max_evals`, `exploration_weight`, `coverage_weight`, `diversity_weight`, `family_weight`, `ensemble_size`, `enable_feature_filtering`, `patience_rounds`, `anchor_init`. Recovers the full frontier, not a single best.
- **`multi_fidelity/multifidelity_pareto_search.py`** — `MultiFidelityParetoSearch` / `MFSearchConfig` / `MFSearchResult`: successive-halving over staged training epochs. **Wired into the main pipeline** via `experiment_scripts/compare_mf_pareto.py` (which `sys.path.insert`s `model_selection/multi_fidelity/` and imports it), run over the same `all_models_full_e16.csv` 43-model pool as `compare_round_pareto.py`. Drivers: `run_mf_experiment.py`, `run_mf_sweep.py`.
- **Analysis/diagnostic scripts** (`ablation_pareto.py`, `sweep_strategies.py`, `diagnose_pareto.py`, `test_pareto.py`, `plot_pareto.py`, `plot_pareto_comparison.py`, `rank_stability_analysis.py`, `robustness_experiment.py`, `size_vs_accuracy_analysis.py`, `surrogate_quality_experiment.py`) — run directly with `python model_selection/<script>.py`; outputs land in `model_selection/` (`pareto_results/`, `*.png`, `*.csv`).
- **`model_ground_truth.csv`** — oracle latency/accuracy table; read externally by `experiments/run_price_bicross_experiment.sh` and `run_joint_full_10models.sh`.

Shared helpers: many of these scripts import `load_candidates`, `find_cdf_file`, `parse_qerror` from **`experiment_scripts/model_selection_utils.py`** (via their existing `sys.path.insert('../experiments/experiment_scripts')`). Those helpers were extracted there from the archived `model_selection_v2.py`, so the live package no longer depends on archived code.

## Gotchas

- **DuckDB tpch/tpcds latency must be scaled to nanoseconds.** `utilsLLM._find_actual_total_time(root_node, db, workload)` multiplies latency by `1e9` when `db == 'duckdb' and workload in ('tpch','tpcds')` (`utilsLLM.py:1978-1979`; call site ~2660 passes `workload=getattr(argsP, 'workload_test', None)`). DuckDB serves these from memory in sub-microsecond time; without the scale the `Normalizer`'s `+0.001` epsilon collapses the log dynamic range to ≈0 and training diverges. **Regression symptom:** catastrophic Q-errors (p90 ≈ 1e5–1e6) on duckdb tpch/tpcds only, while other db/workload cells are fine.

- **`to_table_relative.py` silently drops a method if an *uncaptured* filename token makes two files share a display name.** `extract_display_name()` builds a clean, **batch-size-agnostic** label from a whitelist of tokens (`frzLLM`, `pwm`, `cx`, `inflatePRICE`, `pL`, …). If a file carries an ablation token the function doesn't parse (e.g. `_pLR0.0001`, a price-LR sweep), it collapses to the **same** display name as the canonical run. The collision handler (step 2, ~line 389) then renames *all* colliding columns to their **raw filename prefix**, which includes the `b24`/`b4` micro-batch token (tpch/tpcds use `b4` via `build_shared`'s OOM guard). Since no single raw prefix exists in *every* workload, the "methods present in ALL datasets" intersection (~line 420) eliminates the method outright, and `cross_engine_aggregate.py` then drops it from that db's `relative_qerror_<db>_*` table and the per-model `relative_qerror_<model>_*` cross-engine table. **Symptom:** a method (e.g. mode-12 jointMLP) whose cdf is present on disk for all workloads is **missing from one db's / one model's aggregated table** while peer models are fine. **Fix:** add a capture for the new token in `extract_display_name()` so the ablation gets a distinct name (it's then correctly excluded as a single-workload method instead of poisoning the canonical run).
