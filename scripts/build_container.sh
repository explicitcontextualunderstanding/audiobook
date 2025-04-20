#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# args: [TAG] [PUSH]
TAG=${1:-$(date +"%Y%m%d")}
PUSH=${2:-false}

IMAGE_NAME="sesame-ai/sesame-tts:${TAG}"
DOCKERFILE="docker/sesame-tts/Dockerfile"

# build
docker build \
  --file "$DOCKERFILE" \
  --tag "$IMAGE_NAME" \
  --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
  .

docker tag "$IMAGE_NAME" "sesame-ai/sesame-tts:latest"

if [ "$PUSH" = "true" ]; then
  docker push "$IMAGE_NAME"
  docker push "sesame-ai/sesame-tts:latest"
fi

echo "✅ Built $IMAGE_NAME"
