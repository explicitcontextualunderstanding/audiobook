#!/bin/bash
set -e

# Run the container and perform a basic health check
docker run --rm sesame-tts-jetson /opt/conda/bin/conda run -n tts python -c "
import torch
import transformers
print('Torch version:', torch.__version__)
print('Transformers version:', transformers.__version__)
print('Health check passed.')
"
