#!/bin/bash
set -e

# Ensure necessary directories exist
# Assumes Dockerfile and scripts exist in their respective locations
mkdir -p ./docker/sesame-tts/utils

# Make scripts executable (assuming they exist)
if [ -f ./docker/sesame-tts/entrypoint.sh ]; then
    chmod +x ./docker/sesame-tts/entrypoint.sh
else
    echo "Warning: ./docker/sesame-tts/entrypoint.sh not found."
fi

if [ -f ./docker/sesame-tts/utils/test_csm.py ]; then
    chmod +x ./docker/sesame-tts/utils/test_csm.py
else
    echo "Warning: ./docker/sesame-tts/utils/test_csm.py not found."
fi

echo "Building the Docker image..."
# Assumes ./docker/sesame-tts/Dockerfile exists
if [ -f ./docker/sesame-tts/Dockerfile ]; then
    sudo docker build -t sesame-tts-jetson -f ./docker/sesame-tts/Dockerfile .
else
    echo "Error: ./docker/sesame-tts/Dockerfile not found. Cannot build image."
    exit 1
fi


echo "Done! You can now run the container with:"
echo "sudo docker run --runtime nvidia -it --rm \\"
echo "  --volume ~/audiobook_data:/audiobook_data \\"
echo "  --volume ~/audiobook:/books \\"
echo "  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \\"
echo "  --volume ~/.cache/huggingface:/root/.cache/huggingface \\"
echo "  --workdir /audiobook_data \\"
echo "  sesame-tts-jetson"
