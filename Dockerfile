FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Set environment
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3.11-dev python3-pip git curl build-essential \
    libglib2.0-0 libsm6 libxext6 libxrender-dev ninja-build \
    && apt-get clean

# Create venv
RUN python3.11 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch (CUDA 12.6 wheels)
RUN pip install \
    torch==2.7.0 \
    torchvision==0.22.0 \
    torchaudio==2.7.0 \
    --index-url https://download.pytorch.org/whl/cu126

# Core Python packages
RUN pip install huggingface_hub wheel alive_progress seaborn
RUN pip install transformers==4.55.2
RUN pip install bitsandbytes==0.46.0
RUN pip install pandas
RUN pip install scikit-learn einops numpy pyparsing
RUN pip install peft==0.15.2

# FlashAttention prebuilt wheel
# NOTE: This wheel is built for Python 3.12 (cp312). If you keep Python 3.11 in this image,
# you may need to change the wheel URL to a cp311-compatible one.
RUN pip install \
  https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu12torch2.7cxx11abiFALSE-cp312-cp312-linux_x86_64.whl || \
  echo "Flash-attn installation failed (likely Python version mismatch), continuing without it"

# Set working directory
WORKDIR /workspace
