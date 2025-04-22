#!/bin/bash
# analyze_dependencies.sh
# A tool for analyzing Python dependencies in the audiobook project

set -e

echo "==== Audiobook Project Dependency Analyzer ===="
echo "This script helps identify and resolve dependency conflicts"
echo ""

# Check if pip-tools is installed
if ! command -v pip-compile &> /dev/null; then
    echo "Installing pip-tools..."
    pip install pip-tools
fi

# Check if pipdeptree is installed
if ! command -v pipdeptree &> /dev/null; then
    echo "Installing pipdeptree..."
    pip install pipdeptree
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REQUIREMENTS_IN="${REPO_ROOT}/docker/sesame-tts/requirements.in"
REQUIREMENTS_LOCK="${REPO_ROOT}/docker/sesame-tts/requirements.lock.txt"

# Check if requirements.in exists
if [ ! -f "${REQUIREMENTS_IN}" ]; then
    echo "Creating requirements.in from requirements.txt..."
    cp "${REPO_ROOT}/docker/sesame-tts/requirements.txt" "${REQUIREMENTS_IN}"
    echo "Created ${REQUIREMENTS_IN}"
fi

echo "Analyzing Python dependencies..."

# Generate requirements.lock.txt if it doesn't exist
if [ ! -f "${REQUIREMENTS_LOCK}" ] || [ "${REQUIREMENTS_IN}" -nt "${REQUIREMENTS_LOCK}" ]; then
    echo "Generating lock file from requirements.in..."
    pip-compile --resolver=backtracking "${REQUIREMENTS_IN}" -o "${REQUIREMENTS_LOCK}"
    echo "Generated ${REQUIREMENTS_LOCK}"
fi

# Check for conflicts
echo ""
echo "Checking for conflicts..."
pip check || echo "^ Conflicts detected!"

# Show dependency tree for specific packages
echo ""
echo "Dependency tree for critical packages:"
pipdeptree --packages torch,torchvision,torchaudio,vector_quantize_pytorch,torchao,moshi,einops

# Check compatibility with Jetson PyPI index
echo ""
echo "Checking version compatibility with Jetson PyPI index..."

# Critical packages to check
PACKAGES=(
    "torch==2.2.0:2.7.0"
    "torchvision==0.17.0:0.22.0"
    "torchaudio==2.2.0:2.7.0"
    "torchao==0.1.0:0.11.0"
    "triton==2.1.0:3.3.0"
)

# Print table header
printf "%-20s %-15s %-15s %-30s\n" "Package" "Required" "Available" "Status"
printf "%-20s %-15s %-15s %-30s\n" "-------" "--------" "---------" "------"

# Check each package
for pkg in "${PACKAGES[@]}"; do
    IFS=':' read -r package jetson_ver <<< "$pkg"
    pkg_name=${package%%==*}
    pkg_ver=${package##*==}
    
    if grep -q "^${pkg_name}==" "${REQUIREMENTS_LOCK}"; then
        status="⚠️ May use non-Jetson wheel"
    else
        status="✅ Compatible"
    fi
    
    printf "%-20s %-15s %-15s %-30s\n" "$pkg_name" "$pkg_ver" "$jetson_ver" "$status"
done

echo ""
echo "Checking packages that might need to be built from source..."
echo "(This will take a moment to check each package)"

# Use pip download to check which packages might need to be built from source
for pkg in $(grep -v "^#" "${REQUIREMENTS_LOCK}" | grep -v "^-e" | grep -v "^$"); do
    pkg_name=${pkg%%==*}
    pkg_ver=${pkg##*==}
    
    echo -n "Checking ${pkg_name}... "
    if pip download --no-deps --python-version 3.10 --platform linux_aarch64 --only-binary=:all: "${pkg}" &>/dev/null; then
        echo "✅ Has ARM64 wheel"
    else
        echo "⚠️ Needs source build"
    fi
done

echo ""
echo "Analysis complete!"
echo ""
echo "Recommendations:"
echo "1. Review any conflicts identified above"
echo "2. Consider updating packages with version mismatches to use Jetson-optimized versions"
echo "3. For packages that need source builds, ensure build dependencies are installed in the Dockerfile"
