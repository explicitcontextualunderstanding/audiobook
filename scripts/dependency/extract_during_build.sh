#!/bin/bash
# Make sure the script is executable
# extract_during_build.sh
# Extracts dependency information during the build process
# This is useful when the main container build fails due to dependency conflicts

set -e

echo "==== Extracting Dependency Information During Build Process ===="
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/dependency_artifacts/build_analysis"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

echo "Building the analysis container..."
echo "This container will extract dependency information even if the normal build would fail"
echo ""

# Build the analysis container with BuildKit
DOCKER_BUILDKIT=1 docker build \
    --target analysis \
    -t sesame-tts-analysis \
    -f ${REPO_ROOT}/docker/sesame-tts/Dockerfile.analysis \
    ${REPO_ROOT}

echo ""
echo "Analysis container built successfully!"
echo "Extracting dependency information..."

# Run the container to extract the dependency information
docker run --rm \
    -v "${OUTPUT_DIR}:/output" \
    sesame-tts-analysis

echo ""
echo "==== Dependency Analysis Complete ===="
echo "All dependency information has been extracted to ${OUTPUT_DIR}"
echo ""
echo "Key files to review:"
echo "- ${OUTPUT_DIR}/analysis_report.md (overview of findings)"
echo "- ${OUTPUT_DIR}/package_install_results.csv (individual package installation results)"
echo "- ${OUTPUT_DIR}/wheel_availability.txt (ARM64 wheel availability)"
echo "- ${OUTPUT_DIR}/recommended_requirements.in (suggested requirements.in with fixes)"
echo ""
echo "To apply the recommended requirements:"
echo "cp ${OUTPUT_DIR}/recommended_requirements.in ${REPO_ROOT}/docker/sesame-tts/requirements.in"
echo ""
echo "Then rebuild the main container:"
echo "DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f ${REPO_ROOT}/docker/sesame-tts/Dockerfile ${REPO_ROOT}"
