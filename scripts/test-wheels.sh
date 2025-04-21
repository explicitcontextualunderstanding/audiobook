#!/bin/bash
# Make this script executable with: chmod +x scripts/test-wheels.sh
# Script to test and validate Python wheel assumptions for the audiobook project

set -e  # Exit on error

# Display header
echo "===================================================="
echo "      Python Wheel Validation for Audiobook TTS     "
echo "===================================================="
echo

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH."
    exit 1
fi

# Check if running on Jetson
if ! grep -q "NVIDIA Jetson" /proc/device-tree/model 2>/dev/null; then
    echo "WARNING: This doesn't appear to be a Jetson device."
    echo "This test is specifically for validating wheel compatibility on Jetson hardware."
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ $continue_anyway != "y" ]]; then
        echo "Exiting."
        exit 1
    fi
fi

# Navigate to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "Running wheel validation tests..."
echo "This will build a test Docker image and run several package installation tests."
echo "Results will be saved to ./wheel-test-results/"

# Create output directory
mkdir -p "${PROJECT_ROOT}/wheel-test-results"

# Build the test image with timing
echo "Building test Docker image..."
time docker build -t audiobook-wheel-test -f docker/sesame-tts/Dockerfile.test-wheels . 2>&1 | tee "${PROJECT_ROOT}/wheel-test-results/build.log"

# Run the test image to get results
echo "Running tests and collecting results..."
docker run --rm -v "${PROJECT_ROOT}/wheel-test-results:/output" audiobook-wheel-test bash -c "cp /test-results/wheel-test.log /output/"

# Create a summary
echo "Creating summary report..."
echo "===================================================" > "${PROJECT_ROOT}/wheel-test-results/summary.txt"
echo "              Wheel Validation Summary             " >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"
echo "===================================================" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"
echo "" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"

echo "Test results overview:" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"
grep -A1 "=== Test" "${PROJECT_ROOT}/wheel-test-results/wheel-test.log" | grep -v "\-\-" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"

echo "" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"
echo "Build time:" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"
grep "real" "${PROJECT_ROOT}/wheel-test-results/build.log" | tail -1 >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"

echo "" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"
echo "Full test results available in wheel-test-results/wheel-test.log" >> "${PROJECT_ROOT}/wheel-test-results/summary.txt"

# Display the summary
cat "${PROJECT_ROOT}/wheel-test-results/summary.txt"

echo ""
echo "Tests completed. Results saved to ./wheel-test-results/"
echo ""
echo "Based on these results, you should update the Dockerfile strategy"
echo "in audiobook-plan.md and the build-validation.md document."
echo ""
echo "Next steps:"
echo "1. If standard PyPI wheels failed but Jetson wheels worked, prioritize the"
echo "   Jetson PyPI mirror in the Dockerfile."
echo "2. For any failed imports, consider source-based installation or alternative versions."
echo "3. Update the Dockerfile to implement the most efficient approach."
echo ""
