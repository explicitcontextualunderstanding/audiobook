#!/usr/bin/env bash
# Test script for sesame-tts container
set -e

echo "📋 Testing Sesame TTS container..."

# 1. Test basic Python imports
echo "🔍 Testing Python imports..."
python3 -c "
import torch
import moshi
import torchaudio
import torchao
import nltk
import sys

print(f'Python {sys.version}')
print(f'PyTorch {torch.__version__} (CUDA available: {torch.cuda.is_available()})')
print(f'Moshi {moshi.__version__}')
print(f'TorchAudio {torchaudio.__version__}')

# Check GPU info if available
if torch.cuda.is_available():
    print(f'CUDA Device: {torch.cuda.get_device_name(0)}')
    print(f'CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB')
    # Test basic tensor operations on GPU
    x = torch.randn(1000, 1000, device='cuda')
    y = torch.matmul(x, x.t())
    print(f'GPU tensor test passed: {y.shape}')
"

# 2. Test CSM module import
echo "🔬 Testing CSM module..."
python3 -c "
import sys
import os

# Check if CSM is in path
sys.path.append('/opt/csm')
import generator
print('CSM module import successful')

# Verify generators are available
for attr in dir(generator):
    if attr.startswith('load_') or attr == 'Generator':
        print(f'Found CSM component: {attr}')
"

# 3. Check Triton server
echo "🧪 Testing Triton server..."
if [ -f "/opt/tritonserver/bin/tritonserver" ]; then
    echo "Triton server binary found"
    /opt/tritonserver/bin/tritonserver --version
else
    echo "ERROR: Triton server binary not found"
    exit 1
fi

# 4. Check directories
echo "📂 Checking directories..."
for dir in "/models" "/audiobook_data" "/books" "/segments"; do
    if [ -d "$dir" ]; then
        echo "$dir directory exists"
    else
        echo "ERROR: $dir directory not found"
        exit 1
    fi
done

echo "✅ All tests passed!"
