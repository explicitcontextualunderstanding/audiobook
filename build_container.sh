#!/bin/bash
set -e

# Ensure necessary directories exist
mkdir -p ~/audiobook/docker/sesame-tts/utils

# Check if Dockerfile exists, creating it if not
if [ ! -f ~/audiobook/docker/sesame-tts/Dockerfile ]; then
    echo "Creating Dockerfile..."
    cat > ~/audiobook/docker/sesame-tts/Dockerfile << 'EOF'
# Use NVIDIA's CUDA base image for Jetson Orin
FROM nvcr.io/nvidia/cuda:12.8.0-devel-ubuntu22.04

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    DEBIAN_FRONTEND=noninteractive \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    CONDA_DIR=/opt/conda \
    PATH="/root/.cargo/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    cmake \
    libopus-dev \
    build-essential \
    git \
    wget \
    curl \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "✓ System dependencies installed"

# Install Rust (needed for moshi/sphn)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustc --version && \
    cargo --version && \
    echo "✓ Rust installed"

# Install Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh

# Add conda to PATH
ENV PATH=$CONDA_DIR/bin:$PATH

# Create conda environment with Python 3.10
RUN conda create -y -n tts python=3.10 && \
    conda clean -ya

# Make RUN commands use the conda environment
SHELL ["conda", "run", "-n", "tts", "/bin/bash", "-c"]

# Set environment activation on interactive shells
RUN echo "conda activate tts" >> ~/.bashrc

# Create necessary directories
RUN mkdir -p /opt/csm ${AUDIOBOOK_DATA} ${BOOKS_DIR} ${MODELS_DIR} /segments

# Install Python dependencies within conda environment
RUN conda install -y -c conda-forge ffmpeg && \
    pip install --upgrade pip setuptools wheel && \
    # Install torch packages first
    pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 && \
    # Install specific versions of packages known to work together
    pip install tokenizers==0.13.3 transformers==4.31.0 huggingface_hub==0.16.4 accelerate==0.25.0 && \
    pip install soundfile tqdm pydub psutil ebooklib beautifulsoup4 PyPDF2 pdfminer.six nltk && \
    # Install einops with specific version for moshi
    pip install einops==0.7.0 && \
    # Install moshi specific dependencies
    pip install "sphn>=0.1.4" sounddevice==0.5.0 && \
    # Install other dependencies
    pip install rotary_embedding_torch vector_quantize_pytorch datasets && \
    # Install torchtune and torchao with compatible versions
    pip install "torchtune<0.4.0" "torchao<0.5.0"