#!/bin/bash
set -euxo pipefail

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

echo "🌐 Creating conda env..."
conda create -y -n tts python=3.10
conda clean -ya

echo "📚 Installing Python packages..."
conda install -y -c conda-forge ffmpeg
pip install --no-cache-dir --upgrade pip setuptools wheel
pip install --no-cache-dir \
    torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0 \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.jetson-ai-lab.dev/simple
pip install --no-cache-dir -r requirements.txt
pip install --no-cache-dir "silentcipher @ git+https://github.com/SesameAILabs/silentcipher@v1.0.2"
pip install --force-reinstall --no-cache-dir "moshi==0.2.2"
python - <<'PYCODE'
import moshi, moshi.models
PYCODE

echo "🔧 Setting up CSM package path..."
mkdir -p /opt/csm
cat > /opt/csm/__init__.py << 'CSMPI'
from .generator import load_csm_1b, Segment, Generator
__all__ = ["load_csm_1b", "Segment", "Generator"]
CSMPI

echo "✅ Build complete"
