#!/bin/bash
# Manual Installation Script for LLM4QPR
# This script sets up the environment for LLM4QPR manually
# Assumes you have already created and activated a Python 3.12 environment
# and have an NVIDIA driver / CUDA 12.x-compatible system.

echo "Setting up LLM4QPR environment manually..."

echo "Installing PyTorch (CUDA 12.6 wheels) and Python packages..."

# Upgrade pip
python -m pip install --upgrade pip

# PyTorch + CUDA 12.6 wheels
python -m pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 \
  --index-url https://download.pytorch.org/whl/cu128

# Core Python packages
python -m pip install huggingface_hub wheel alive_progress seaborn
python -m pip install transformers==4.55.2
python -m pip install bitsandbytes==0.46.0
python -m pip install pandas
python -m pip install scikit-learn einops numpy pyparsing
python -m pip install peft==0.15.2

# FlashAttention prebuilt wheel
python -m pip install \
  https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu12torch2.7cxx11abiFALSE-cp312-cp312-linux_x86_64.whl

echo "Manual installation completed!"
echo ""
echo "Make sure you have an appropriate NVIDIA driver and a Python 3.12 environment activated before running this script."
