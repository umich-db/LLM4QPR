#!/bin/bash
# Manual Installation Script for LLM4QPR
# This script sets up the environment for LLM4QPR manually

echo "Setting up LLM4QPR environment manually..."

# CUDA Toolkit 12.4 (adjust if your GPU requires 11.x)
echo "Installing CUDA Toolkit 12.4..."
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda-repo-ubuntu2204-12-4-local_12.4.0-550.54.14-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-4-local_12.4.0-550.54.14-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-4-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-4

echo "Installing Python packages..."
# Python + packages (create venv or conda env first)
python -m pip install huggingface_hub wheel
python -m pip install transformers==4.49.0
python -m pip install bitsandbytes==0.46.0
python -m pip install pandas
python -m pip install scikit-learn einops numpy pyparsing
python -m pip install peft==0.15.2
python -m pip install flash_attn==2.8.0.post2 --no-build-isolation

echo "Setting up environment variables..."
# Set environment variables for current session
export CUDA_HOME=/usr/local/cuda-12.4
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

echo "Manual installation completed!"
echo ""
echo "To make environment variables permanent, add these lines to ~/.bashrc:"
echo "export CUDA_HOME=/usr/local/cuda-12.4"
echo "export PATH=\$CUDA_HOME/bin:\$PATH"
echo "export LD_LIBRARY_PATH=\$CUDA_HOME/lib64:\$LD_LIBRARY_PATH" 