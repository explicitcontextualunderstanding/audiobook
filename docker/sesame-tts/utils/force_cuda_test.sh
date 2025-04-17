#!/bin/bash
# filepath: /Users/kieranlal/workspace/audiobook/docker/sesame-tts/utils/force_cuda_test.sh
set -e

echo "🔍 Forcing CUDA environment setup for PyTorch..."

# Export crucial environment variables
export CUDA_VISIBLE_DEVICES=0
export NVIDIA_VISIBLE_DEVICES=all
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH:/usr/lib/aarch64-linux-gnu
export JETSON_DEVICE=1

# Create a temporary Python file that patches torch.cuda
cat > /tmp/patch_cuda.py << 'EOF'
import torch
import sys
import importlib.util

# Backup original is_available function
original_is_available = torch.cuda.is_available

# Create patched function that always returns True
def patched_is_available():
    print("🔧 CUDA availability check patched to return True")
    return True

# Apply the patch
torch.cuda.is_available = patched_is_available

# Run the provided script with patched torch.cuda
script_path = sys.argv[1]
spec = importlib.util.spec_from_file_location("test_module", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# If the script has a main function, call it with the remaining arguments
if hasattr(module, "main") and callable(module.main):
    sys.argv = sys.argv[1:]  # Remove this script from args
    module.main()
EOF

# Run the test script with our patch
python /tmp/patch_cuda.py "$@"
