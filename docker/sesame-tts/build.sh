#!/bin/bash
set -e  # Exit on error
set -x  # Print commands

# Environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export NO_TORCH_COMPILE=1
export DEBIAN_FRONTEND=noninteractive
export MODELS_DIR=/models
export AUDIOBOOK_DATA=/audiobook_data
export BOOKS_DIR=/books
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=all
export CONDA_DIR=/opt/conda
export PATH="/root/.cargo/bin:${PATH}"

echo "📦 Installing system dependencies..."
apt-get update && apt-get install -y --no-install-recommends \
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
    && rm -rf /var/lib/apt/lists/*

echo "🦀 Installing Rust (needed for moshi/sphn)..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
. "$HOME/.cargo/env"
rustc --version
cargo --version

echo "🐍 Installing Miniconda..."
wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O ~/miniconda.sh
/bin/bash ~/miniconda.sh -b -p $CONDA_DIR
rm ~/miniconda.sh

# Add conda to PATH
export PATH=$CONDA_DIR/bin:$PATH

echo "🌐 Creating conda environment with Python 3.10..."
conda create -y -n tts python=3.10
conda clean -ya

echo "📂 Creating necessary directories..."
mkdir -p /opt/csm ${AUDIOBOOK_DATA} ${BOOKS_DIR} ${MODELS_DIR} /segments

echo "📚 Installing Python dependencies..."
# Use the conda environment for installation
source $CONDA_DIR/bin/activate tts

# Install dependencies via conda and pip
conda install -y -c conda-forge ffmpeg
pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch and related packages specifically for Jetson
# First uninstall any existing PyTorch packages
pip uninstall -y torch torchvision torchaudio

# Install NVIDIA's Jetson-specific PyTorch packages
pip install --no-cache-dir --verbose \
    torch torchvision torchaudio \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.jetson-ai-lab.dev/simple

# Then install the remaining requirements
pip install --no-cache-dir --verbose -r requirements.txt

# Install silentcipher for watermarking
pip install --no-cache-dir "silentcipher @ git+https://github.com/SesameAILabs/silentcipher@master"

# Force reinstall moshi and verify import
pip install --force-reinstall --no-cache-dir "moshi<=0.2.2"
python -c "import moshi; import moshi.models"

echo "🔄 Downloading essential CSM files..."
mkdir -p /opt/csm
cd /opt/csm
wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/generator.py
wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/models.py
# Create CSM package init file
echo '# CSM package
from .generator import load_csm_1b, Segment, Generator

__all__ = ["load_csm_1b", "Segment", "Generator"]
' > /opt/csm/__init__.py

echo "📝 Copying utility files..."
cp /opt/build/utils/watermarking.py /opt/csm/
chmod +x /opt/csm/watermarking.py

# Copy the generator patch
cp /opt/build/utils/audiobook_generator.py /opt/csm/

echo "🐍 Adding CSM to Python path..."
python -c "import sys; import site; print(site.getsitepackages()[0])" > /tmp/python_path
echo 'import sys; sys.path.append("/opt/csm")' > $(cat /tmp/python_path)/csm_path.pth
rm /tmp/python_path

echo "📥 Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt')"

echo "🔧 Setting up utilities..."
mkdir -p /usr/local/bin/utils
cp /opt/build/utils/test_csm.py /usr/local/bin/utils/
chmod +x /usr/local/bin/utils/test_csm.py

# Copy the entrypoint script if it exists
if [ -f /opt/build/entrypoint.sh ]; then
    cp /opt/build/entrypoint.sh /usr/local/bin/entrypoint.sh
    chmod +x /usr/local/bin/entrypoint.sh
fi

echo "✅ Build completed successfully!"
