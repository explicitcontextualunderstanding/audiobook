#!/bin/bash
set -e

# Activate conda environment
source /opt/conda/bin/activate tts

echo "Testing TTS imports..."
# Test that key imports work
python3 -c "import torch; import moshi; import torchao; print('Basic imports successful')"

echo "Testing CSM module installation..."
# Test that CSM is accessible
python3 -c "from csm.generator import load_csm_1b, Generator; print('CSM module import successful')"

# Test for NLTK data
python3 -c "import nltk; nltk.data.find('tokenizers/punkt'); print('NLTK data found')"

echo "✓ Package tests completed successfully"

# Optionally run minimal TTS generation test if model files exist
if [ -d "/models/csm-1b-v1.0" ]; then
  echo "Testing TTS generation with CSM model..."
  python3 /usr/local/bin/utils/test_csm.py
else
  echo "Model directory not found at /models/csm-1b-v1.0. Skipping TTS generation test."
  echo "To test TTS generation, please download the model files."
fi
