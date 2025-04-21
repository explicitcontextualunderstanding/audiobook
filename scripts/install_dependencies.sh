#!/bin/bash
set -e

# Install Miniconda
echo "Installing Miniconda..."
curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o Miniconda3.sh
bash Miniconda3.sh -b -p /opt/conda
rm Miniconda3.sh

# Configure Conda
echo "Configuring Conda..."
/opt/conda/bin/conda config --set channel_priority flexible
/opt/conda/bin/conda config --set pip_interop_enabled True
/opt/conda/bin/conda config --add channels conda-forge

# Create Conda environment
echo "Creating Conda environment..."
/opt/conda/bin/conda create -y -n tts python=3.10 pip setuptools wheel
/opt/conda/bin/conda clean -ya

# Install Python dependencies
echo "Installing Python dependencies..."
/opt/conda/bin/conda run -n tts pip install -r /books/requirements.txt

# Install system packages
echo "Installing system packages..."
apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

echo "Dependencies installed successfully."
