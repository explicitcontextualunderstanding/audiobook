#!/bin/bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Base directory of the project
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default tag with date (YYYYMMDD)
DEFAULT_TAG=$(date +"%Y%m%d")

# Parse command line arguments
TAG=${1:-$DEFAULT_TAG}
PUSH=${2:-false}

echo "Building containers with tag: $TAG"
cd "$PROJECT_DIR"

# Build the sesame-tts container
CONTAINER_NAME="sesame-tts"
DOCKERFILE_PATH="docker/sesame-tts/Dockerfile"
IMAGE_NAME="sesame-ai/$CONTAINER_NAME:$TAG"

echo "Building $IMAGE_NAME..."
docker build \
  --file "$DOCKERFILE_PATH" \
  --tag "$IMAGE_NAME" \
  --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
  .

# Tag as latest
docker tag "$IMAGE_NAME" "sesame-ai/$CONTAINER_NAME:latest"

echo "Finished building $IMAGE_NAME"
docker images | grep "sesame-ai/$CONTAINER_NAME"

# Push if requested
if [ "$PUSH" = "true" ]; then
  echo "Pushing $IMAGE_NAME..."
  docker push "$IMAGE_NAME"
  docker push "sesame-ai/$CONTAINER_NAME:latest"
  echo "Finished pushing $IMAGE_NAME"
fi

echo "✅ All containers built successfully!"
