# Experiment Scripts

This directory contains individual experiment scripts that were extracted from the original `master.sh` file.

## Available Experiments

### 1. `run_model_size_comparison.sh`
**Purpose**: Compares performance across different Llama model sizes  
**Models**: Llama-3.2-1B, Llama-3.2-3B, Llama-3.1-8B, Llama-3.1-70B  
**Workloads**: TPC-H, TPC-DS, STATS  
**Seeds**: 42, 43, 44

### 2. `run_baseline_comparison.sh`
**Purpose**: Compares LLM performance against baseline methods  
**Model**: Llama-3.1-8B  
**Workloads**: TPC-H, TPC-DS, JOB, SYN, STATS  
**Seeds**: 42

### 3. `run_training_ratio_analysis.sh`
**Purpose**: Analyzes performance with different training data ratios  
**Model**: Llama-3.1-8B  
**Training Ratios**: 0.2, 0.4, 0.6, 0.8, 1.0  
**Workloads**: TPC-H, TPC-DS, JOB, SYN, STATS  
**Seeds**: 42, 43, 44

### 4. `run_finetuning_experiments.sh`
**Purpose**: Tests LLM finetuning performance  
**Model**: Llama-3.1-8B  
**Workloads**: TPC-H, TPC-DS, STATS  
**Training Ratio**: 0.1 (finetuning)  
**Seeds**: 42, 43, 44

### 5. `run_cross_workload_generalization.sh`
**Purpose**: Tests model generalization across different workloads  
**Model**: Llama-3.1-8B  
**Test Workloads**: TPC-H, synthetic, job-light  
**Training**: All other workloads except test workload  
**Seeds**: 42, 43, 44

### 6. `run_finetune_cross_workload.sh`
**Purpose**: Tests finetuning performance across different workloads  
**Model**: Llama-3.1-8B  
**Test Workloads**: TPC-H, synthetic  
**Training**: All other workloads except test workload  
**Training Ratio**: 0.1 (finetuning)  
**Seeds**: 42

## Core Scripts

The `core_scripts/` directory contains the fundamental execution scripts:

### `run_baseline.sh`
Executes baseline algorithms (BAO, PostgreSQL, etc.) for comparison.

### `run_llm_card.sh`
Runs LLM-based cardinality estimation experiments.

### `run_llm_time.sh`
Runs LLM-based execution time prediction experiments.

## Usage

### Interactive Mode (Recommended)
```bash
cd experiments
bash run_experiments.sh
```

### Direct Execution
```bash
cd experiments
bash experiment_scripts/run_model_size_comparison.sh
```

## Directory Structure

```
experiments/
├── run_experiments.sh                    # Main interactive runner
├── experiment_scripts/                   # Experiment configurations
│   ├── core_scripts/                     # Core execution scripts
│   │   ├── run_baseline.sh              # Baseline algorithm runner
│   │   ├── run_llm_card.sh              # LLM cardinality estimation
│   │   └── run_llm_time.sh              # LLM execution time prediction
│   ├── run_model_size_comparison.sh     # Model size experiments
│   ├── run_baseline_comparison.sh       # Baseline comparison
│   ├── run_training_ratio_analysis.sh   # Training ratio experiments
│   ├── run_finetuning_experiments.sh    # Finetuning experiments
│   ├── run_cross_workload_generalization.sh  # Cross-workload tests
│   └── run_finetune_cross_workload.sh   # Finetune cross-workload
├── train.py                             # Main training script
└── utils*.py                            # Utility modules
```

## Requirements

- `HF_TOKEN` environment variable must be set
- All required data files must be present
- CUDA-enabled environment with required packages installed

## Output

Results are saved to:
- `results/` - CSV files with error distributions
- `logs/` - Training and inference logs
- `best_model/` - Saved model checkpoints 