#!/bin/bash
# Make the script executable
chmod +x "$0"
# generate_dependency_tree.sh
# Creates a visual dependency tree for better understanding package relationships

set -e

echo "==== Generating Dependency Tree Visualization ===="
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/dependency_artifacts"

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

# Check if necessary tools are installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed"
    exit 1
fi

# Install pipdeptree if not already installed
if ! command -v pipdeptree &> /dev/null; then
    echo "Installing pipdeptree..."
    pip install pipdeptree
fi

echo "Generating text-based dependency tree for all packages..."
pipdeptree > "${OUTPUT_DIR}/dependency_tree_all.txt"
echo "Created ${OUTPUT_DIR}/dependency_tree_all.txt"

echo "Generating JSON dependency tree for machine processing..."
pipdeptree --json-tree > "${OUTPUT_DIR}/dependency_tree.json"
echo "Created ${OUTPUT_DIR}/dependency_tree.json"

echo "Generating dependency tree for key packages..."
for pkg in torch torchvision torchaudio vector_quantize_pytorch torchao moshi einops triton librosa; do
    echo "Analyzing dependencies for ${pkg}..."
    pipdeptree --packages ${pkg} > "${OUTPUT_DIR}/dependency_tree_${pkg}.txt"
    echo "Created ${OUTPUT_DIR}/dependency_tree_${pkg}.txt"
done

echo "Generating reverse dependency tree (shows what depends on each package)..."
pipdeptree --reverse > "${OUTPUT_DIR}/reverse_dependency_tree.txt"
echo "Created ${OUTPUT_DIR}/reverse_dependency_tree.txt"

echo "Checking for dependency conflicts..."
pipdeptree --warn all > "${OUTPUT_DIR}/dependency_conflicts.txt"
echo "Created ${OUTPUT_DIR}/dependency_conflicts.txt"

echo ""
echo "Dependency tree artifacts generated successfully in ${OUTPUT_DIR}"
echo "Use these files to analyze package relationships and identify circular dependencies"
