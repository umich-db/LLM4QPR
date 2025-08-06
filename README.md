## 📑 Project Overview

This repository contains the code and experiments for **"An Empirical Evaluation of Pretrained LLMs for Query Plan Representation."**
All results in the paper were produced on Ubuntu 22.04 with CUDA‑enabled NVIDIA GPUs.

---

## 📊 Dataset Structure

The experiments use query plans from four datasets: **TPC-H**, **TPC-DS**, **IMDB**, and **STATS**.

### Required Data Files
- **`queryPlans/`** (1.42 GB) - Pre-generated query plans for all datasets

**Download**: See [queryPlans/README.md](queryPlans/README.md) for download instructions.

---

## 🔄 Reproducing Query Plans

If you want to reproduce the query plans from scratch, you'll need the following additional data:

### Required for Reproduction
- **`queries/`** - SQL queries used to generate the query plans
- **Database data** - Raw data for each dataset
  - **TPC-H & TPC-DS**: Generated using official TPC toolkits (https://www.tpc.org/)
  - **IMDB**: Downloaded from [Learning-based-cost-estimator](https://github.com/greatji/Learning-based-cost-estimator?tab=readme-ov-file) repository
  - **STATS**: Downloaded from [End-to-End-CardEst-Benchmark](https://github.com/wuziniu/End-to-End-CardEst-Benchmark/tree/master/datasets/stats_simplified) repository

---

## 🔑 Model Access Requirements

This project uses Meta's Llama models which require authentication:

1. **Apply for access** to the following models on Hugging Face:
   - [Meta Llama 3.2 Collection](https://huggingface.co/collections/meta-llama/llama-32-66f448ffc8c32f949b04c8cf)
   - [Meta Llama 3.1 Collection](https://huggingface.co/collections/meta-llama/llama-31-669fc079a0c406a149a5738f)

2. **Get your Hugging Face token** from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

3. **Set up your token** using environment variables:

**macOS/Linux (bash/zsh)**
```bash
export HF_TOKEN="hf_xxx"    # current shell only
# or add the same line to ~/.zshrc or ~/.bashrc to persist
```

**Windows PowerShell**
```powershell
$env:HF_TOKEN="hf_xxx"      # current session
setx HF_TOKEN "hf_xxx"      # persist for new sessions
```

---

## ⚙️ Environment Setup

| Option                       | When to use                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------- |
| **A. Docker (automated)**    | You have Docker + NVIDIA GPU support                                             |
| **B. Manual (shell script)** | You prefer a local/conda virtual environment or need to tweak CUDA, Python, etc. |

> **Note**: "NVIDIA GPU support" means you have Docker with NVIDIA Container Toolkit installed. This allows Docker containers to access your NVIDIA GPU. If you don't have this set up, see [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

### A. Reproduce with Docker (automated setup)

```bash
# 1. Build the image (takes ~5 min)
docker build -t llm4qpr .

# 2. Run with GPU passthrough and mount your workspace
docker run --gpus all -it \
  -v $(pwd):/workspace \
  llm4qpr /bin/bash
```

The Dockerfile (see `Dockerfile`) is based on **`nvidia/cuda:12.1.1‑devel‑ubuntu22.04`** and installs:

* Python 3.11 (isolated in `/venv`)
* CUDA 12.x toolkit & driver headers
* `transformers==4.49.0`, `peft==0.15.2`, `bitsandbytes==0.46.0`
* `flash‑attn==2.8.0.post2` built with the same compiler flags we used

### B. Manual installation

```bash
# Run the manual installation script
bash setup_manual.sh
```

**Note**: The script installs CUDA 12.4, Python packages, and sets up environment variables.

---

## 🏃 Quick Start

### Prerequisites
1. **NVIDIA GPU** with CUDA support
2. **Docker** (for automated setup) OR **Python 3.11** (for manual setup)
3. **Hugging Face account** with access to Llama models

### Step-by-Step Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/umich-db/LLM4QPR.git
cd LLM4QPR

# 2. Download and extract query plans
# See queryPlans/README.md for download instructions

# 3. Set up Hugging Face token
export HF_TOKEN="your_hf_token_here"

# 4. (Docker) Build & run OR (Manual) create your venv and install packages

# 5. Run experiments
cd experiments
bash run_experiments.sh
```

### Output Files

After running experiments, you'll find:
- **`experiments/results/`** - CSV files with error distributions
- **`experiments/logs/`** - Training and inference logs
- **`experiments/embeddings/`** - Saved query plan embeddings
- **`experiments/finetuned_models/`** - Finetuned LLM models


---

## 📚 Citations

If you use this code in your research, please cite the related works:

### Related Work
This repository is based on the [qp_evaluation](https://github.com/zhaoyue-ntu/qp_evaluation) framework:

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
If you use the IMDB or STATS datasets, please cite the original papers:

**IMDB Dataset:**
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

**STATS Dataset:**
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

