#!/bin/bash
set -e

# Set up CUDA environment variables
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/aarch64-linux-gnu
export TORCH_USE_CUDA_DSA=1

# Fix NVIDIA device visibility
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=all

# Add JETSON specific environment variables
export JETSON_DEVICE=1
export TORCH_DISABLE_HIP=1
export CUDA_MODULE_LOADING=LAZY

# Fix Torch library paths - crucial for Jetson CUDA detection
export LD_LIBRARY_PATH=$CONDA_DIR/envs/tts/lib/python3.10/site-packages/torch/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_DIR/envs/tts/lib

# Check CUDA setup
echo "Testing CUDA setup with nvidia-smi:"
nvidia-smi || echo "Warning: nvidia-smi failed, CUDA might not be properly configured"

# Print CUDA environment variables for debugging
echo "CUDA Environment Variables:"
env | grep -E 'CUDA|NVIDIA'

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate tts

# Apply CSM import fix
echo "Running CSM import fix..."
python /opt/utils/fix_csm.py
echo "CSM import fix applied."

# Print welcome message
cat << 'EOF'
=====================================================
Sesame CSM Text-to-Speech for Audiobook Generation
=====================================================

This container provides Sesame CSM Text-to-Speech capabilities
specifically configured for audiobook generation on Jetson devices.

Environment paths:
  - Books directory: /books
  - Audiobook data directory: /audiobook_data
  - Models directory: /models

Available scripts:
  - /books/generate_audiobook_sesame.py - Main script for both EPUB and PDF
  - /books/generate_audiobook_sesame_epub.py - Optimized for EPUB format
  - /books/extract_chapters.py - Extract chapter information

Example usage:
  # Generate a single audiobook file (combined)
  python /books/generate_audiobook_sesame.py \
    --input /books/your_book.epub \
    --output /audiobook_data/audiobook_sesame.mp3 \
    --model_path /models/sesame-csm-1b \
    --voice_preset calm

  # Generate per-chapter audio files from an EPUB
  python /books/generate_audiobook_sesame_epub.py \
    --epub /books/your_book.epub \
    --output_dir /audiobook_data/audiobook_chapters_sesame

Test the CSM installation by running:
  python /usr/local/bin/utils/test_csm.py /models/sesame-csm-1b

Note: The 'tts' conda environment is active in this shell.

=====================================================
EOF


# Execute the command passed to the container (which will be the CMD from Dockerfile)
exec "$@"