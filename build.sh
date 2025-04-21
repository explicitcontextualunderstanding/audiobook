#!/bin/bash
set -e

# Build the Docker image
DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .

# Run tests to validate the build
bash scripts/test_container.sh
