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

# Install Python packages with specific versions
RUN pip install \
    torch==2.5.1 \
    torchvision==0.20.1 \
    torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124

RUN pip install wheel

RUN pip install \
    transformers==4.49.0 \
    peft==0.15.2 \
    bitsandbytes==0.46.0 \
    pandas \
    scikit-learn \
    einops numpy pyparsing

# Install flash-attn (skip if build fails - it's optional for basic functionality)
RUN pip install flash-attn==2.8.0.post2 --no-build-isolation --no-cache-dir --verbose || echo "Flash-attn installation failed, continuing without it"

# Set working directory
WORKDIR /workspace


