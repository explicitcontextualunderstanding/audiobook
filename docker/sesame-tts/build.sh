#!/bin/bash
set -euo pipefail

echo "📦 Installing system dependencies..."
apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 cmake libopus-dev build-essential git wget curl pkg-config \
  && rm -rf /var/lib/apt/lists/*

echo "🦀 Installing Rust toolchain..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

echo "🐍 Installing Miniconda..."
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O miniconda.sh
bash miniconda.sh -b -p "$CONDA_DIR" && rm miniconda.sh
export PATH="$CONDA_DIR/bin:$PATH"

echo "🌐 Creating conda env with Python 3.10..."
conda create -y -n tts python=3.10
conda clean -ya

echo "📚 Installing Python packages..."
# Activate the conda environment
source $CONDA_DIR/bin/activate tts

# Install ffmpeg via conda
conda install -y -c conda-forge ffmpeg
conda clean -ya

# Update pip and install core packages
pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch stack with explicit versions and extra index URLs
pip install --no-cache-dir \
    torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0 \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.jetson-ai-lab.dev/simple

# Install requirements with specific versions
pip install --no-cache-dir -r requirements.txt

# Install silentcipher with specific version
pip install --no-cache-dir "silentcipher @ git+https://github.com/SesameAILabs/silentcipher@v1.0.2"

# Force reinstall moshi to ensure correct version
pip install --force-reinstall --no-cache-dir "moshi==0.2.2"

# Verify imports
echo "🔍 Verifying critical imports..."
python - <<'PYCODE'
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

import moshi
print(f"Moshi version: {moshi.__version__}")

import torchaudio
print(f"Torchaudio version: {torchaudio.__version__}")

import torchao
print(f"TorchAO version: {torchao.__version__ if hasattr(torchao, '__version__') else 'unknown'}")

import nltk
nltk.download('punkt', quiet=True)
print("NLTK punkt downloaded")
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

echo "✅ Build complete!"
