#!/bin/bash
set -e

# Set up CUDA environment variables
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export TORCH_USE_CUDA_DSA=1

# Fix NVIDIA device visibility
export NVIDIA_VISIBLE_DEVICES=all

# Print CUDA environment variables for debugging
echo "CUDA Environment Variables:"
env | grep -E 'CUDA|NVIDIA'

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate tts

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
  python /books/generate_audiobook_sesame.py \
    --input /books/your_book.epub \
    --output /audiobook_data/audiobook_sesame.mp3 \
    --model_path /models/sesame-csm-1b \
    --voice_preset calm

Test the CSM installation by running:
  python /usr/local/bin/utils/test_csm.py /models/sesame-csm-1b

Note: The 'tts' conda environment is active in this shell.

=====================================================
EOF


# Execute the command passed to the container (which will be the CMD from Dockerfile)
exec "$@"