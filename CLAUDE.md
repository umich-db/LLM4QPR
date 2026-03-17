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
