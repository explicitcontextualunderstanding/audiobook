#!/bin/bash
# Make the script executable
chmod +x "$0"
# build.sh
# Script to build the Docker container with improved dependency management

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE="${REPO_ROOT}/docker/sesame-tts/Dockerfile"

# Parse arguments
USE_BUILDKIT=1
CACHE=1
VERBOSE=0

for arg in "$@"; do
  case $arg in
    --no-buildkit)
      USE_BUILDKIT=0
      shift
      ;;
    --no-cache)
      CACHE=0
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --help)
      echo "Usage: $0 [--no-buildkit] [--no-cache] [--verbose]"
      echo "  --no-buildkit  : Disable BuildKit"
      echo "  --no-cache     : Disable caching"
      echo "  --verbose      : Show detailed build output"
      exit 0
      ;;
  esac
done

# Set BuildKit
if [ $USE_BUILDKIT -eq 1 ]; then
  export DOCKER_BUILDKIT=1
  echo "BuildKit enabled"
else
  export DOCKER_BUILDKIT=0
  echo "BuildKit disabled"
fi

# Set cache options
CACHE_OPT=""
if [ $CACHE -eq 0 ]; then
  CACHE_OPT="--no-cache"
  echo "Cache disabled"
else
  echo "Cache enabled"
fi

# Set progress options
PROGRESS_OPT="--progress=auto"
if [ $VERBOSE -eq 1 ]; then
  PROGRESS_OPT="--progress=plain"
  echo "Verbose output enabled"
fi

echo "Building Docker container..."
docker build $CACHE_OPT $PROGRESS_OPT \
  -t sesame-tts-jetson \
  -f $DOCKERFILE \
  $REPO_ROOT

echo "Build complete!"
echo "You can run the container with:"
echo "docker run --runtime nvidia -it --rm --name sesame-tts \\"
echo "  --volume ~/audiobook_data:/audiobook_data \\"
echo "  --volume ~/audiobook:/books \\"
echo "  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \\"
echo "  sesame-tts-jetson"
