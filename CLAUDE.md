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
  - `--frzeven_tpcx_use_retrainMLP` (requires `--jointmlp_only`) — for the frzEven999 method, substitute its retrainMLP result for its jointMLP result on tpch+tpcds (all systems). `--frzeven_retrainMLP_cells [MODEL:]DB:WL …` (e.g. `bert2:duckdb:tpcds sentbert:spark:tpcds`) does the same for explicit cells only (WL ∈ {tpch,tpcds}; mutually exclusive with the all-systems flag). Both are a **surgical patch** of just the frzEven999 jointMLP column on the canonical table — valid because tpch/tpcds carry **no** priceB staging, so the per-workload anchor-min is unchanged by the swap (the retrainMLP cdf is already in the min and the jointMLP value isn't the min). Outputs tagged `_frzEvenTPCxRetrain` / `_frzEvenRetrain-<…>`. In the *simple* table only the frzEven999 jointMLP column moves; in *normalized* the rest may rescale (by-design, when frzEven999 is the per-system best).
- `compare_modes_table.py` (env `ANCHOR=90`) — 3×9 mode-vs-mode win/loss table reading the relative CSVs; cell ∈ {−1,0,+1} by quantile-win majority over {50,90,95,max}.
- `experiment_scripts/aggregate_tables.sh` — driver for `to_table_seeds.py`+`to_table_relative.py`. The priceB←priceN aliasing (on `syn job job_full stats`, where mode-7b priceB ≡ mode-7 priceN) is now a flag, not hardcoded: `--no-priceb-equiv` disables it, `--priceb-equiv-workloads "<list>"` customizes (env `PRICEB_EQUIV_WORKLOADS` still works; `""` disables). Note: `to_table_relative.py --exclude_workload` / `cross_engine_aggregate.py`'s re-derive path do NOT apply this staging, so their priceB columns differ from the canonical CSVs.

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

**The canonical list of the 87 candidate-pool models** is `logs/postgres/logs_Train_stats_Test_stats_ours/all_models/all_models_full_e16.csv` (one row per model). Recover each model's HuggingFace name from its `key` by extracting the `h2048_<MODEL>_quant-4-bit` token and mapping `<MODEL>` (`/`→`-`) back against `model_selection/model_ground_truth.csv` (the `model` column). Per-model stats-workload training time = sum of `time_e{1_4,5_8,9_12,13_16}_ms`.

### Building the candidate pool — raw artifacts → ready-for-use data

`all_models_full_e16.csv` is the consumed artifact; new candidate models arrive as a **HuggingFace snapshot** (`HCAHOI/llm4qpr`, cached at `~/.cache/huggingface/hub/models--HCAHOI--llm4qpr/snapshots/<rev>/llm4qpr/<org>/<model>/seed42/`) holding, per model: `finetuned_models/checkpoint/state.pkl` (weights), `logs/*.log`+`*.console.log`, `results/*.{csv,_abs.txt,_predictions.csv}`, `manifest/upload_manifest.json`. These are **TPU v4 JAX/NNX** mode-12 (`priceBiCrossAttnJoint`, inflatePRICE) e16 runs. Two scripts process them (run from `experiment_scripts/`):

1. **`add_jax_snapshot_to_pool.py`** — appends one CSV pool row per model. Flags: `--snapshot`, `--profile_csv_dir`, `--pool`, `--dry-run`. **Accuracy** from the snapshot `.log`/`.console.log` (final `qerror_summary` → `test_*_e16`; per-epoch stage-1 `val_q_median` → `val_median_e{4,8,12,16}`, copied to `val_p90_e*` too — stage-1 logs no q90). **Timing** from the H100 profiling runs (see below). Idempotent, backs up the CSV, skips keys already present.
2. **`place_jax_snapshot.py`** — flags `--snapshot`, `--no-weights`, `--dry-run`. (a) COPY-dereferences raw artifacts to their canonical homes (paths from each `upload_manifest.json` `local`, host prefix `/home/<user>/LLM4QPR/experiments/` stripped): weights → `finetuned_models/postgres/expanded_pool_tpu_jax_nnx_full_20260428/<MD>/seed42/checkpoint/`, logs/results → the matching `..._jax_nnx_full_20260428/` dirs. (b) Generates the per-model pool dir `.../all_models/expanded_pool_tpu__<KEY>__e16/{summary.txt,train.log,inference.log}` byte-faithful to existing rows (upstream builder absent). `KEY = postgres_0.0001_b<bs>_h2048_<MD>_quant-4-bit_priceS_inflatePRICE_randInit_cx4`; `<MD>` = model name with `/`→`-`. **Copies, never moves** — snapshot files are symlinks into the HF blob cache; copying leaves the cache intact (it can be pruned afterward to reclaim ~8 GB of weights).

**Timing = the three time-consumption metrics** (the pool's `*_h100_ms` columns are what `compare_round_pareto.py:663` reads). Source: H100 probes in `/root/h100_profile_runs_2026-05-18/` — short `pwm1_frzLLM1_e2_tr0.1` runs (1 frozen warmup epoch + 1 unfrozen epoch, 10% data). `csvs/profile_model_db_warmup_e2.csv` gives `warmup_ms` (**warmup phase**) and `after_warmup_ms` (**post-warmup phase**); `csvs/profile_model_db_h100_per_query_ms.csv` gives `mean_per_query_ms` (**inference**). Verified-exact column formulas: `time_e1_4_*` = `warmup_ms`×40, `time_{e5_8,e9_12,e13_16}_*` = `after_warmup_ms`×40 (×10 for 0.1→full data, ×4 epochs/chunk), `test_per_query_ms` = `test_testing_took_ms` = `mean_per_query_ms`, `pieces_gpu` = `e0:H100|...`. **Fallback** when the H100 training probe failed (exit≠0): `time_*` = `stage1_finetune_sec/4`, `time_*_h100` = ×0.3, `pieces_gpu=e0:tpuv4|...` (TPU-v4 wall × the 0.3 H100-equiv factor) — eval still uses the per-query probe if *it* succeeded. The JAX snapshot logs alone cannot split warmup vs post-warmup (only one aggregate `stage1_finetune_sec`, no per-epoch wall-clock) — that's what the H100 probes are for. The per-dir `summary.txt`/`train.log`/`inference.log` always report the TPU-v4 raw wall ×0.3 provenance (a different number from the CSV's H100-native timing — intentional). `model_profile_with_nonemb.csv` (latency axis `avg_ms`) is maintained separately.

**Caveat — albert ≥ xlarge OOM the H100 probe.** The biCrossAttn joint path keeps the quantized LLM + 805M-param inflated cross-attn + MLP in one autograd graph at batch 24; when the LLM unfreezes post-warmup, full-sequence activations through ALBERT's parameter-shared layers exceed 79 GiB. xlarge-v1/v2 OOM at the unfreeze (epoch 1, after a clean warmup); xxlarge-v2 OOMs in `loss.backward()` mid-warmup (never reaches unfreeze → no per-query eval either). They trained fine on TPU only because that path uses batch 4 + a decoupled two-stage design (LLM never in the graph at large batch); 4-bit quant doesn't help (the OOM is activation/gradient memory, not weights). These three rows therefore use the TPU×0.3 timing fallback.

**Per-workload time-only pools (tpch/tpcds).** Besides the stats pool, `logs/postgres/logs_Train_{tpch,tpcds}_Test_{tpch,tpcds}_ours/all_models/all_models_full_e16.csv` hold the same 87 rows (identical `subdir,key`) but with **only the time columns filled and accuracy columns blank** (e16 accuracy not yet run). Built by **`experiment_scripts/build_pool_time_from_warmup_logs.py`** (`--stats_csv` template, `--prof_dir <wl>/warmup_e2_profile`, `--write`) which parses the `warmup_e2_profile/` training logs: `warmup_ms`=`[Train] Epoch 0 total`, `after_warmup_ms`=`[Train] Epoch 1 total`, `time_e1_4`=warmup×40 / `time_{e5_8,e9_12,e13_16}`=after_warmup×40 (raw==h100, `pieces=e0:H100|…`), and **inference = mean per-batch ms** (mean of the first `[Test] Batch N` pass, excluding cold-start batch 1) into `test_per_query_ms`/`test_testing_took_ms`. NB this differs from the stats pool, whose inference is single-query latency from a dedicated per-query profiler. It prefers a COMPLETE log when several batch-size variants exist. Models whose **post-warmup (unfrozen) epoch OOM'd/truncated** have NO `after_warmup_ms` → their **entire row is left blank** (tpch: 2 = albert-large-v1/v2; tpcds: 13 = albert base/large/xlarge-v2/xxlarge-v2, mpnet variants, paraphrase-albert, mobilebert, electra-large-discriminator). Re-collect them with **`experiment_scripts/recollect_missing_pool_warmup_e2.sh <tpch|tpcds>`** (mirrors `profile_pool_{tpch,tpcds}_warmup_e2.sh` but reads the blank rows, reduces b16→`REDUCED_BIG_BATCH`=4; models already at b1 — albert xlarge/xxlarge — can't be decreased, flagged/`SKIP_B1`); new complete logs land beside the truncated ones and `build_pool_time_from_warmup_logs.py` auto-prefers them. The stats pool's albert-xlarge-v1/v2 + xxlarge-v2 rows were updated from the TPU×0.3 fallback to real H100 warmup-profile timing (`pieces tpuv4→H100`, accuracy preserved).

**Collecting the tpcds e16 accuracy pool (3-GPU fan-out).** `experiment_scripts/master_tpcds_inflatePRICE_e16_group_{A,B,C}.sh` run the 87-model pool's mode-12 inflatePRICE cx4 recipe on **tpcds** (same COMMON as `master_finish_inflatePRICE_e16_group_*.sh` but `--workloads tpcds` and `--ft_batch_size 4` — tpcds plans are longer than stats; b4 mirrors `build_shared`'s tpch/tpcds 16 GB OOM guard). **3 models are excluded** (OOM even on the 32 GB 5090 with the 805M inflated cross-attn): `albert/albert-{xlarge-v1,xlarge-v2,xxlarge-v2}` → 84 models run. Split is GPU-aware + load-balanced by stats train-time (5090≈1.85× a 5080): **A=14 → 5090 (dbresearch3)** holds the unmovable big dense models (8×Qwen-0.5B + 4×SmolLM-360M + roberta-large + electra-large-discriminator, which won't fit 16 GB at b4); **B=35 → 5080 (dbresearch2)** and **C=35 → 5080 (local, `CUDA_VISIBLE_DEVICES=1`)** hold the smaller models, perfectly balanced. Launch each in tmux per the `llm4qpr-remote-gpus` skill.

Despite their names, **not** part of the archived prototype: `random_model_selection.py` (random baseline used by `master_random_inflatePRICE_e16_group_{A,B,C,D}.sh`) and `experiments/model_selection.png` (a live `plot_hv_vs_hours.py` output).

### Separate `model_selection/` package (top-level, live parallel track)

`model_selection/` (repo root, **not** `experiment_scripts/`) is a distinct, still-live research codebase implementing **surrogate-guided Pareto-frontier recovery** — a different algorithm from the `compare_round_pareto.py` round-based filtering above (the two do **not** import each other; `compare_round_pareto.py` uses its own `pareto_levels()`).

- **`pareto_frontier_search.py`** — `ParetoFrontierSearch` (Python API). Latency is offline-known; accuracy is fit by a bootstrap ensemble of random forests (`BootstrapEnsembleRegressor`); batch acquisition is latency-specific frontier Expected Improvement (`expected_improvement_maximization`). `SearchConfig` knobs: `init_budget`, `batch_size`, `max_evals`, `exploration_weight`, `coverage_weight`, `diversity_weight`, `family_weight`, `ensemble_size`, `enable_feature_filtering`, `patience_rounds`, `anchor_init`. Recovers the full frontier, not a single best.
- **`multi_fidelity/multifidelity_pareto_search.py`** — `MultiFidelityParetoSearch` / `MFSearchConfig` / `MFSearchResult`: successive-halving over staged training epochs. **Wired into the main pipeline** via `experiment_scripts/compare_mf_pareto.py` (which `sys.path.insert`s `model_selection/multi_fidelity/` and imports it), run over the same `all_models_full_e16.csv` 43-model pool as `compare_round_pareto.py`. Drivers: `run_mf_experiment.py`, `run_mf_sweep.py`.
- **Analysis/diagnostic scripts** (`ablation_pareto.py`, `sweep_strategies.py`, `diagnose_pareto.py`, `test_pareto.py`, `plot_pareto.py`, `plot_pareto_comparison.py`, `rank_stability_analysis.py`, `robustness_experiment.py`, `size_vs_accuracy_analysis.py`, `surrogate_quality_experiment.py`) — run directly with `python model_selection/<script>.py`; outputs land in `model_selection/` (`pareto_results/`, `*.png`, `*.csv`).
- **`model_ground_truth.csv`** — oracle latency/accuracy table; read externally by `experiments/run_price_bicross_experiment.sh` and `run_joint_full_10models.sh`.

Shared helpers: many of these scripts import `load_candidates`, `find_cdf_file`, `parse_qerror` from **`experiment_scripts/model_selection_utils.py`** (via their existing `sys.path.insert('../experiments/experiment_scripts')`). Those helpers were extracted there from the archived `model_selection_v2.py`, so the live package no longer depends on archived code.

## Baselines (qf / aimai / bao / e2e_cost / postgres)

Run via `experiment_scripts/core_scripts/run_baseline.sh "<train_wls>" <test_wl> <train_ratio> <seed> <algo> <task>` (env `DB_ENGINE`). CLI algo names are `qf, aimai, e2e_cost, bao, postgres`; result cdfs are named `time_<algo>_<train_ratio>_cdf_<db>_<lr>_b<bs>_h<hid>_seed<N>.csv` (e.g. `time_qf_1.0_cdf_postgres_…`). There is **no** `postgres` native-baseline cdf unless explicitly run (algo `postgres`, `lr=-1`, huge bs/hid).

- **Model caching is keyed by TRAINING data, not the test workload** — so a model trained on `job` is reused (no re-train) when only the test workload changes (the imdb-canonical `train=job` is shared across test=syn/job/job_full). Cache: `finetuned_models/<db>/<train_data>_<task>_<algo>…_model[.pt]`. Applies to **aimai/qf/e2e_cost** (`train.py` cache block) AND **bao** (`trainer.train_and_test_bao` → `BaoRegression.save/load`, model.py:75/92). `postgres` has no training. Different training data ⇒ different cache ⇒ retrains.
- **Early stopping**: `--early_stop_patience` (default 0=off) + `--early_stop_after_epoch` monitor **val p90 Q-error** in the generic `trainer.train()` loop (aimai/qf/e2e_cost). **bao** now honors the same criterion too — `bao.fit(…, val_X, val_y)` (val threaded from `train.py`); breaks keeping current weights (no rollback), matching `train()`. `run_baseline.sh` passes them via env `EARLY_STOP_PATIENCE`/`EARLY_STOP_AFTER_EPOCH`, and `--num_epoch` via env `NUM_EPOCH` (default 100).
- **Coverage fill**: `experiment_scripts/fill_baselines_{A,B,C}.sh` regenerate the missing baseline cells (seed 42, `NUM_EPOCH=30`, `EARLY_STOP_PATIENCE=5`, `EARLY_STOP_AFTER_EPOCH=20`), balanced by per-training cost (qf>bao>e2e_cost>aimai>postgres) so A is ~1.5× B and C; disjoint per-(algo,db) caches → safe to run in parallel. `DRY_RUN=1` prints the planned runs.
- **`--baseline_price_concat`** (time-only; errors on `--card` or `--algo postgres`) concatenates a **mode-7-style PRICE/stats embedding** (the same `PRICEEmbedder` at cx=0 → 512-dim, trained jointly) onto the baseline plan embedding before the prediction MLP — the baseline analogue of LLM mode 7. Reuses the PRICE flags (`--price_model_path/--price_bin_size/--price_n[_or]/--price_random_init`); the per-query PRICE features come from the **same `queries_true_sql/<wl>.sql` files the LLM path uses**, aligned 1:1 to the baseline `get_new` split by `dat_dict` ids (`experiments/baseline_price_data.py::build_aligned_price_feats_for_splits`). Two mechanisms under one flag: **qf/aimai/e2e_cost** route through `BaselinePriceJointModel` (`experiments/models/baseline_price_model.py`) with the `(base_batch, price_batch)` tuple threaded through `trainer.train()/evaluate()` (gated on `model.is_baseline_price_joint`); **bao** gets an optional `price_embedder`+head MLP inside `BaoRegression` (replaces the column-0 readout), wired via `train_and_test_bao`. MLP `input_dim = base_emb_dim + 512` (qf 393, e2e_cost 32, aimai `nodeParallels*5`, bao 64). Cache key and result/log stems gain a `_priceConcat` tag so joint runs never collide with the plain-baseline cells. NB under `--price_n_or` the price tuple's `num_clauses` MUST be passed to `PRICEEmbedder.forward` as a **keyword** (it's the 9th positional, after the `llm_*` slots) — both joint models do this; passing it positionally silently skips OR aggregation and crashes on multi-clause batches.

## Gotchas

- **DuckDB latency is always rescaled to nanoseconds (uniform `×1e9`, ALL workloads).** `utilsLLM._find_actual_total_time(root_node, db, workload)` multiplies the raw duckdb `latency` (seconds) by `1e9` for **every** workload (`utilsLLM.py:2042-2065`; the `workload` arg is retained for call-site compat but no longer gates the scaling). DuckDB serves from memory, so latencies sit near the `Normalizer`'s `+0.001` epsilon (in seconds that epsilon is 1 ms): tpch/tpcds are sub-µs and the epsilon collapses the log range entirely (model untrainable); the imdb family is ms-range but ~16% of queries are sub-10 ms and get blurred. ns lifts every workload far above the epsilon and makes duckdb absolute-error metrics consistent across workloads. `×1e9` is scale-invariant on Q-error *except* for the epsilon term (the point). **History:** before 2026-06-01 only tpch/tpcds were scaled and the imdb family stayed in seconds. **CAUTION:** the scaling must be identical at train and inference — a model trained on the old seconds labels must be retrained, not re-evaluated under ns. Postgres/spark are already in ms (epsilon negligible) and unchanged; the **baseline** path (`evaluation/dataset_utils.py:72`) scales duckdb `×1000`→ms (also epsilon-safe) and is intentionally left as-is (changing it would shift baseline absolute-error numbers). **Regression symptom (old bug):** catastrophic Q-errors (p90 ≈ 1e5–1e6) on duckdb tpch/tpcds if scaling is ever removed.

- **`to_table_relative.py` silently drops a method if an *uncaptured* filename token makes two files share a display name.** `extract_display_name()` builds a clean, **batch-size-agnostic** label from a whitelist of tokens (`frzLLM`, `frzAll`, `frzOdd`, `frzEven`, `pwm`, `cx`, `inflatePRICE`, `pL`, …; `frzEven` was added this session so `frzEven999` runs get a distinct column — mirrored in `to_table_seeds.py`). If a file carries an ablation token the function doesn't parse (e.g. `_pLR0.0001`, a price-LR sweep), it collapses to the **same** display name as the canonical run. The collision handler (step 2, ~line 389) then renames *all* colliding columns to their **raw filename prefix**, which includes the `b24`/`b4` micro-batch token (tpch/tpcds use `b4` via `build_shared`'s OOM guard). Since no single raw prefix exists in *every* workload, the "methods present in ALL datasets" intersection (~line 420) eliminates the method outright, and `cross_engine_aggregate.py` then drops it from that db's `relative_qerror_<db>_*` table and the per-model `relative_qerror_<model>_*` cross-engine table. **Symptom:** a method (e.g. mode-12 jointMLP) whose cdf is present on disk for all workloads is **missing from one db's / one model's aggregated table** while peer models are fine. **Fix:** add a capture for the new token in `extract_display_name()` so the ablation gets a distinct name (it's then correctly excluded as a single-workload method instead of poisoning the canonical run).
