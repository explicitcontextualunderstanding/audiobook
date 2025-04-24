#!/bin/bash
set -euo pipefail

# Enable parallel downloads for apt
echo "📦 Configuring apt for faster downloads..."
cat > /etc/apt/apt.conf.d/80parallel << EOF
Acquire::Queue-mode "host";
Acquire::http::Pipeline-Depth 5;
Acquire::http::Dl-Limit "50";
Acquire::https::Pipeline-Depth 5;
Acquire::https::Dl-Limit "50";
EOF

# Install system dependencies with optimized download
echo "📦 Installing system dependencies..."
apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 cmake libopus-dev build-essential git wget curl pkg-config \
    ca-certificates gnupg \
  && rm -rf /var/lib/apt/lists/*

# Setup Rust & Miniconda in parallel
echo "🚀 Setting up build environment in parallel..."
{
  echo "🦀 Installing Rust toolchain..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
  source "$HOME/.cargo/env"
} &
RUST_PID=$!

{
  echo "🐍 Installing Miniconda..."
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O miniconda.sh
  bash miniconda.sh -b -p "$CONDA_DIR" && rm miniconda.sh
  export PATH="$CONDA_DIR/bin:$PATH"
  
  # Configure conda for faster installs
  conda config --set channel_priority flexible
  conda config --set pip_interop_enabled True
  conda config --add channels conda-forge
} &
CONDA_PID=$!

# Wait for parallel processes to complete
wait $RUST_PID
wait $CONDA_PID

export PATH="$CONDA_DIR/bin:$PATH"

echo "🌐 Creating optimized conda env with Python 3.12..."
conda create -y -n tts python=3.12 \
    pip setuptools wheel
conda clean -ya

echo "📚 Installing Python packages..."
# Activate the conda environment
source $CONDA_DIR/bin/activate tts

# Configure pip for faster installs
cat > ~/.config/pip/pip.conf << EOF
[global]
index-url = https://pypi.org/simple
extra-index-url = 
    https://pypi.jetson-ai-lab.dev/simple
    https://pypi.ngc.nvidia.com
timeout = 60
retries = 3
EOF

# Update pip first
python -m pip install --no-cache-dir --upgrade pip

# Install PyTorch stack with prioritized Jetson wheels
echo "🔥 Installing PyTorch from Jetson AI Lab repository first..."
pip install --no-cache-dir \
    --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0

# Install requirements with specific versions (parallelized)
echo "📦 Installing dependencies with priority for pre-built wheels..."
pip install --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    -r requirements.txt

# Force reinstall moshi to ensure correct version
pip install --force-reinstall --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    "moshi==0.2.2"

# Pre-download NLTK data to avoid runtime downloads
echo "📚 Downloading NLTK data..."
python -c 'import nltk; nltk.download("punkt", quiet=True)'

# Verify imports
echo "🔍 Verifying critical imports..."
python - <<'PYCODE'
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name()}")

import moshi
print(f"Moshi version: {moshi.__version__}")

import torchaudio
print(f"Torchaudio version: {torchaudio.__version__}")

import torchao
print(f"TorchAO version: {torchao.__version__ if hasattr(torchao, '__version__') else 'unknown'}")

import nltk
print("NLTK punkt installed")
PYCODE

echo "🔧 Setting up CSM package..."
mkdir -p /opt/csm
cat > /opt/csm/__init__.py << 'CSMPI'
"""
Sesame CSM Text-to-Speech package.

This package provides access to the Sesame CSM text-to-speech model
with optimizations for audiobook generation on Jetson devices.
"""

from .generator import load_csm_1b, Segment, Generator

__all__ = ["load_csm_1b", "Segment", "Generator"]
CSMPI

# Cleanup to reduce image size
echo "🧹 Cleaning up build artifacts..."
rm -rf ~/.cache/pip
rm -rf ~/.rustup/toolchains/*/share/doc
rm -rf ~/.cargo/registry/cache

echo "✅ Build complete!"
