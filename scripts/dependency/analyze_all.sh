#!/bin/bash
# Make the script executable
chmod +x "$0"
# analyze_all.sh
# Runs all dependency analysis tools to generate a comprehensive view of dependencies

set -e

echo "==== Comprehensive Dependency Analysis ===="
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPENDENCY_DIR="${REPO_ROOT}/scripts/dependency"
OUTPUT_DIR="${REPO_ROOT}/dependency_artifacts"

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

# Step 1: Generate dependency tree
echo "Step 1: Generating dependency tree visualization..."
${DEPENDENCY_DIR}/generate_dependency_tree.sh
echo ""

# Step 2: Generate compatibility matrix
echo "Step 2: Generating version compatibility matrix..."
python3 ${DEPENDENCY_DIR}/generate_compatibility_matrix.py
echo ""

# Step 3: Check wheel availability
echo "Step 3: Checking wheel availability..."
python3 ${DEPENDENCY_DIR}/check_wheel_availability.py
echo ""

# Step 4: Simulate dependency resolution
echo "Step 4: Simulating dependency resolution..."
python3 ${DEPENDENCY_DIR}/simulate_resolution.py
echo ""

# Step 5: Determine best versions
echo "Step 5: Determining best package versions..."
python3 ${DEPENDENCY_DIR}/resolve_best_versions.py
echo ""

echo "All analyses complete! Files generated in ${OUTPUT_DIR}:"
find "${OUTPUT_DIR}" -type f -name "*.txt" -o -name "*.json" -o -name "*.csv" | sort

echo ""
echo "==== Summary of Key Findings ===="

# Extract key information from generated files
echo "Version Conflicts:"
if [ -f "${OUTPUT_DIR}/dependency_conflicts.txt" ]; then
    grep -A 2 "Circular dependency" "${OUTPUT_DIR}/dependency_resolution_report.txt" || echo "No circular dependencies found."
fi

echo ""
echo "Packages without ARM64 wheels:"
if [ -f "${OUTPUT_DIR}/wheel_availability_summary.txt" ]; then
    grep -B 1 -A 1 "❌ No" "${OUTPUT_DIR}/wheel_availability_summary.txt" | grep -v "^--$" || echo "All packages have ARM64 wheels."
fi

echo ""
echo "Recommended Requirements File:"
if [ -f "${OUTPUT_DIR}/recommended_requirements.in" ]; then
    echo "A recommended requirements.in file has been generated at:"
    echo "${OUTPUT_DIR}/recommended_requirements.in"
    echo ""
    echo "To use this file:"
    echo "cp ${OUTPUT_DIR}/recommended_requirements.in ${REPO_ROOT}/docker/sesame-tts/requirements.in"
fi

echo ""
echo "Next Steps:"
echo "1. Review the analysis reports in ${OUTPUT_DIR}"
echo "2. Pay special attention to:"
echo "   - dependency_conflicts.txt for circular dependencies"
echo "   - wheel_availability_summary.txt for packages without ARM64 wheels"
echo "   - version_analysis_report.txt for version recommendation details"
echo "3. If satisfied with the recommendations, replace your requirements.in with the recommended one"
echo "4. Build the Docker container to verify the changes resolve your issues"
echo ""
echo "For detailed guidance, refer to ${REPO_ROOT}/docs/dependency-management-guide.md"
