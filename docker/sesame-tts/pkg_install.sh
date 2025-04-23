#!/usr/bin/env bash
# Package installation script for sesame-tts
# This follows the jetson-containers convention for pkg_install.sh
set -e

# Source the container environment variables
source ${L4T_ENV_SETUP_SCRIPT}

# Install system dependencies
apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 cmake libopus-dev build-essential git wget curl pkg-config \
    ca-certificates gnupg \
  && rm -rf /var/lib/apt/lists/*

# Use system python or container's python 
PYTHON_VERSION="python3"
if [ -n "${PYTHON_VERSION_NUM}" ]; then
    PYTHON_VERSION="python${PYTHON_VERSION_NUM}"
fi

# Install Rust toolchain with minimal profile
echo "🦀 Installing Rust toolchain..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --profile minimal --default-toolchain stable
source "$HOME/.cargo/env"

# Install Python dependencies
echo "📚 Installing Python dependencies..."
# Get configuration directory
pip_config_dir="$HOME/.config/pip"
mkdir -p "$pip_config_dir"

# Setup pip configuration for faster installs
cat > "$pip_config_dir/pip.conf" << EOF
[global]
index-url = https://pypi.org/simple
extra-index-url = 
    https://pypi.jetson-ai-lab.dev/simple
    https://pypi.ngc.nvidia.com
timeout = 60
retries = 3
EOF

# Install PyTorch stack with prioritized Jetson wheels
echo "🔥 Installing PyTorch from Jetson AI Lab repository first..."
$PYTHON_VERSION -m pip install --no-cache-dir \
    --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0

# Install the rest of the packages
echo "📦 Installing dependencies with priority for pre-built wheels..."
$PYTHON_VERSION -m pip install --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    tokenizers==0.13.3 \
    transformers==4.31.0 \
    huggingface_hub==0.16.4 \
    accelerate==0.25.0 \
    soundfile==0.12.1 \
    pydub==0.25.1 \
    sounddevice==0.5.0 \
    ebooklib==0.18.0 \
    beautifulsoup4==4.12.2 \
    PyPDF2==3.0.1 \
    pdfminer.six==20221105 \
    nltk==3.8.1 \
    einops==0.7.0 \
    sphn==0.1.4 \
    rotary_embedding_torch==0.2.5 \
    vector_quantize_pytorch==1.8.6 \
    datasets==2.16.1 \
    torchtune==0.3.0 \
    torchao==0.1.0 \
    tqdm==4.66.1 \
    psutil==5.9.6

# Install special packages
#$PYTHON_VERSION -m pip install --no-cache-dir --prefer-binary \
#    "silentcipher @ git+https://github.com/SesameAILabs/silentcipher@v1.0.2"

# Force reinstall moshi to ensure correct version
$PYTHON_VERSION -m pip install --force-reinstall --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    "moshi==0.2.2"

# Pre-download NLTK data to avoid runtime downloads
echo "📚 Downloading NLTK data..."
$PYTHON_VERSION -c 'import nltk; nltk.download("punkt", quiet=True)'

# Download and install Triton Inference Server
echo "🔧 Installing Triton Inference Server..."
TRITON_VERSION="2.55.0"
TRITON_DIR="${TARGET_DIR:-/opt}/tritonserver"
mkdir -p "$TRITON_DIR"

wget --quiet "https://github.com/triton-inference-server/server/releases/download/v${TRITON_VERSION}/tritonserver${TRITON_VERSION}-igpu.tar" \
    -O triton.tar
tar -xf triton.tar -C "$TRITON_DIR" --strip-components=1
rm triton.tar

# Setup CSM package
echo "🔧 Setting up CSM package..."
CSM_DIR="${TARGET_DIR:-/opt}/csm"
mkdir -p "$CSM_DIR"

git clone --depth 1 https://github.com/SesameAILabs/csm.git /tmp/csm
cp /tmp/csm/generator.py "$CSM_DIR/"
cp /tmp/csm/models.py "$CSM_DIR/"

# Add the package initialization
cat > "$CSM_DIR/__init__.py" << 'EOF'
"""
Sesame CSM Text-to-Speech package.

This package provides access to the Sesame CSM text-to-speech model
with optimizations for audiobook generation on Jetson devices.
"""

from .generator import load_csm_1b, Segment, Generator

__all__ = ["load_csm_1b", "Segment", "Generator"]
EOF

# Create auxiliary scripts if they exist
if [ -d "utils" ]; then
    cp utils/audiobook_generator.py "$CSM_DIR/" || echo "No audiobook_generator.py found"
    cp utils/watermarking.py "$CSM_DIR/" || echo "No watermarking.py found"
    chmod +x "$CSM_DIR/watermarking.py" 2>/dev/null || true
fi

# Create necessary data directories
mkdir -p /models /audiobook_data /books /segments

# Install Python Triton package for torchao kernels
echo "🔧 Installing Triton for torchao..."
$PYTHON_VERSION -m pip install --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.org/simple \
    triton

# Add CSM to Python path
echo "🔧 Adding CSM to Python path..."
site_packages=$($PYTHON_VERSION -c 'import site; print(site.getsitepackages()[0])')
echo "import sys; sys.path.append('$CSM_DIR')" > "$site_packages/csm_path.pth"

# Cleanup to reduce image size
echo "🧹 Cleaning up build artifacts..."
rm -rf ~/.cache/pip
rm -rf ~/.rustup/toolchains/*/share/doc
rm -rf ~/.cargo/registry/cache
rm -rf /tmp/csm

echo "✅ Sesame TTS installation complete!"
