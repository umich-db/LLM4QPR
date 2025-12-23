## 📑 Project Overview

This repository contains the code and experiments for **"An Empirical Evaluation of Pretrained LLMs for Query Plan Representation."**
All results in the paper were produced on Ubuntu 22.04 with CUDA-enabled NVIDIA GPUs.

---

## 📊 Dataset Structure

The repository contains query plans from two different sets of datasets:

- **Standard experiments** (baseline comparison, model size comparison, training ratio analysis, finetuning) use four datasets: **TPC-H**, **TPC-DS**, **IMDB**, and **STATS**.
- **Cross-workload experiments** use a different set of 20 datasets to evaluate model generalization across diverse workloads.

### Required Data Files
- **`queryPlans/`** (~1.42 GB) - Query plans of TPC-H, TPC-DS, IMDB, and STATS
- **`deepdb_augmented/`** (~1.3 GB) - Query plans for cross-workload experiments

**Download**: 
- **`queryPlans/`**: See [queryPlans/README.md](queryPlans/README.md) for download instructions.
- **`deepdb_augmented/`**: See [deepdb_augmented/README.md](deepdb_augmented/README.md) for download instructions.

---

## 🔄 Reproducing Query Plans

If you want to reproduce the query plans in **`queryPlans/`** from scratch, you'll need the following additional data:

### Required for Reproduction
- **`queries/`** - SQL queries used to generate the query plans
- **Database data** - Raw data for each dataset
  - **TPC-H & TPC-DS**: Generated using official TPC toolkits (https://www.tpc.org/)
  - **IMDB**: Downloaded from [Learning-based-cost-estimator](https://github.com/greatji/Learning-based-cost-estimator?tab=readme-ov-file)
  - **STATS**: Downloaded from [End-to-End-CardEst-Benchmark](https://github.com/wuziniu/End-to-End-CardEst-Benchmark/tree/master/datasets/stats_simplified)

---

## 🔑 Model Access Requirements

This project uses Meta's Llama models which require authentication:

1. **Apply for access** to the following models on Hugging Face:
   - [Meta Llama 3.2 Collection](https://huggingface.co/collections/meta-llama/llama-32-66f448ffc8c32f949b04c8cf)
   - [Meta Llama 3.1 Collection](https://huggingface.co/collections/meta-llama/llama-31-669fc079a0c406a149a5738f)

2. **Get your Hugging Face token** from  
   https://huggingface.co/settings/tokens

3. **Set up your token** using environment variables:

**macOS/Linux (bash/zsh)**
```bash
export HF_TOKEN="hf_xxx"
```

**Windows PowerShell**
```powershell
$env:HF_TOKEN="hf_xxx"
setx HF_TOKEN "hf_xxx"
```

---

## ⚙️ Environment Setup

| Option                       | When to use                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------- |
| **A. Manual** | You prefer a local/conda environment or need to tweak CUDA, Python, etc.         |
| **B. Docker**    | You want a plug-and-play environment with GPU support                             |

---

## A. Manual installation

```bash
# Run the manual installation script
bash setup_manual.sh
```

**Note**: The script installs PyTorch 2.7.0 (cu126), Transformers 4.55.2, FlashAttention 2.8.3 (prebuilt), and other dependencies.

---

## B. Reproduce with Docker

```bash
# 1. Build the image (takes ~5 min)
docker build -t llm4qpr .

# 2. Run with GPU passthrough and mount your workspace
docker run --gpus all -it \
  --shm-size 16g \
  -v $(pwd):/workspace \
  --name my-container \
  llm4qpr \
  bash

# 3. Stop the container
docker stop my-container

# 4. Restart the container
docker start -ai my-container

# 5. Remove the container
docker rm my-container
```

The Dockerfile (see `Dockerfile`) is based on **`nvidia/cuda:12.1.1-devel-ubuntu22.04`** and installs:

* Python 3.11 (in `/venv`)
* PyTorch 2.7.0 (cu126)
* `transformers==4.55.2`, `peft==0.15.2`, `bitsandbytes==0.46.0`
* FlashAttention 2.8.3 prebuilt (CUDA 12 + Torch 2.7)

---

## 🏃 Quick Start

### Prerequisites
1. **NVIDIA GPU**  
2. **Hugging Face token** with Llama, Qwen, Gemma, Bert access  

### Step-by-Step Setup

```bash
# 1. Clone the repo
git clone https://github.com/umich-db/LLM4QPR.git
cd LLM4QPR

# 2. Download query plans (see subdirectory README files)

# 3. Set your Hugging Face token
export HF_TOKEN="your_hf_token_here"

# 4. Build & run Docker OR run manual setup script

# 5. Run experiments

# For pretrained LLM experiments:
bash experiment_scripts/run_different_llms.sh

# For baselines:
bash experiment_scripts/run_baseline_comparison.sh

# For finetuning LLM experiments:
bash experiment_scripts/run_finetuning_experiments.sh

# For cross-workload experiments:
bash experiment_scripts/run_cross_workload_experiments.sh
```

### Output Files

After running experiments, you'll find:
- **`experiments/results/`** — error distribution CSVs  
- **`experiments/logs/`** — training & inference logs  
- **`experiments/embeddings/`** — saved query plan embeddings  
- **`experiments/finetuned_models/`** — fine-tuned LLMs  

---

## 📚 Citations

If you use this code in your research, please cite the related works:

### Related Work
This repository is based on:

```
@article{DBLP:journals/pvldb/ZhaoLC23,
  author       = {Yue Zhao and
                  Zhaodonghui Li and
                  Gao Cong},
  title        = {A Comparative Study and Component Analysis of Query Plan Representation
                  Techniques in {ML4DB} Studies},
  journal      = {Proc. {VLDB} Endow.},
  volume       = {17},
  number       = {4},
  pages        = {823--835},
  year         = {2023},
  url          = {https://www.vldb.org/pvldb/vol17/p823-zhao.pdf},
  doi          = {10.14778/3636218.3636235}
}
```

### Datasets

**IMDB Dataset**
```
@article{DBLP:journals/pvldb/SunL19,
  author       = {Ji Sun and Guoliang Li},
  title        = {An End-to-End Learning-based Cost Estimator},
  journal      = {Proc. {VLDB} Endow.},
  volume       = {13},
  number       = {3},
  pages        = {307--319},
  year         = {2019},
  url          = {http://www.vldb.org/pvldb/vol13/p307-sun.pdf},
  doi          = {10.14778/3368289.3368296}
}
```

**STATS Dataset**
```
@article{DBLP:journals/pvldb/HanWWZYTZCQPQZL21,
  author       = {Yuxing Han and
                  Ziniu Wu and
                  Peizhi Wu and
                  Rong Zhu and
                  Jingyi Yang and
                  Liang Wei Tan and
                  Kai Zeng and
                  Gao Cong and
                  Yanzhao Qin and
                  Andreas Pfadler and
                  Zhengping Qian and
                  Jingren Zhou and
                  Jiangneng Li and
                  Bin Cui},
  title        = {Cardinality Estimation in {DBMS:} {A} Comprehensive Benchmark Evaluation},
  journal      = {Proc. {VLDB} Endow.},
  volume       = {15},
  number       = {4},
  pages        = {752--765},
  year         = {2021},
  url          = {https://www.vldb.org/pvldb/vol15/p752-zhu.pdf},
  doi          = {10.14778/3503585.3503586}
}
```

**DeepDB Augmented Dataset**
```
@article{DBLP:journals/pvldb/HilprechtB22,
  author       = {Benjamin Hilprecht and
                  Carsten Binnig},
  title        = {Zero-Shot Cost Models for Out-of-the-box Learned Cost Prediction},
  journal      = {Proc. {VLDB} Endow.},
  volume       = {15},
  number       = {11},
  pages        = {2361--2374},
  year         = {2022},
  url          = {https://www.vldb.org/pvldb/vol15/p2361-hilprecht.pdf},
  doi          = {10.14778/3551793.3551799}
}
```

