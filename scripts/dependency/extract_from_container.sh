#!/bin/bash
# Make the script executable
chmod +x "$0"
# extract_from_container.sh
# Extracts dependency information from a running Docker container

set -e

CONTAINER_NAME=${1:-"sesame-tts"}
OUTPUT_DIR="./dependency_artifacts/container_extracted"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

echo "==== Extracting Dependency Information from Container: $CONTAINER_NAME ===="
echo ""

# Check if the container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    # Try to start the container if it exists but isn't running
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        echo "Container $CONTAINER_NAME exists but is not running. Starting it..."
        docker start "$CONTAINER_NAME"
    else
        echo "Error: Container $CONTAINER_NAME doesn't exist."
        echo "Please start the container first with:"
        echo "docker run --name $CONTAINER_NAME --rm -d sesame-tts-jetson sleep infinity"
        exit 1
    fi
fi

echo "Extracting pip freeze output..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pip freeze > "$OUTPUT_DIR/pip_freeze.txt"
echo "✅ Saved to $OUTPUT_DIR/pip_freeze.txt"

echo "Extracting pip list output..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pip list > "$OUTPUT_DIR/pip_list.txt"
echo "✅ Saved to $OUTPUT_DIR/pip_list.txt"

echo "Installing pipdeptree in container..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pip install pipdeptree

echo "Extracting dependency tree..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pipdeptree > "$OUTPUT_DIR/dependency_tree.txt"
echo "✅ Saved to $OUTPUT_DIR/dependency_tree.txt"

echo "Extracting reverse dependency tree..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pipdeptree --reverse > "$OUTPUT_DIR/reverse_dependency_tree.txt"
echo "✅ Saved to $OUTPUT_DIR/reverse_dependency_tree.txt"

echo "Extracting dependency conflicts..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pipdeptree --warn all > "$OUTPUT_DIR/dependency_conflicts.txt"
echo "✅ Saved to $OUTPUT_DIR/dependency_conflicts.txt"

echo "Extracting JSON dependency tree..."
docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pipdeptree --json-tree > "$OUTPUT_DIR/dependency_tree.json"
echo "✅ Saved to $OUTPUT_DIR/dependency_tree.json"

echo "Extracting package metadata for key packages..."
mkdir -p "$OUTPUT_DIR/package_info"

# List of key packages to extract detailed information for
KEY_PACKAGES="torch torchvision torchaudio torchao vector_quantize_pytorch einops triton moshi transformers librosa"

for pkg in $KEY_PACKAGES; do
    echo "Extracting info for $pkg..."
    docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pip show $pkg > "$OUTPUT_DIR/package_info/$pkg.txt" 2>/dev/null || true
    
    # Also extract the dependency tree for this specific package
    docker exec -it "$CONTAINER_NAME" /opt/conda/bin/conda run -n tts pipdeptree --packages $pkg > "$OUTPUT_DIR/package_info/${pkg}_deps.txt" 2>/dev/null || true
done

echo "Extracting system information..."
docker exec -it "$CONTAINER_NAME" /bin/bash -c 'echo "Docker Container: $HOSTNAME" > /tmp/sysinfo.txt'
docker exec -it "$CONTAINER_NAME" /bin/bash -c 'echo "OS:" >> /tmp/sysinfo.txt && cat /etc/os-release | grep "PRETTY_NAME" >> /tmp/sysinfo.txt'
docker exec -it "$CONTAINER_NAME" /bin/bash -c 'echo "Python:" >> /tmp/sysinfo.txt && python3 --version >> /tmp/sysinfo.txt'
docker exec -it "$CONTAINER_NAME" /bin/bash -c 'echo "Conda:" >> /tmp/sysinfo.txt && conda --version >> /tmp/sysinfo.txt'
docker exec -it "$CONTAINER_NAME" /bin/bash -c 'echo "CUDA:" >> /tmp/sysinfo.txt && nvcc --version | head -n 1 >> /tmp/sysinfo.txt || echo "CUDA not found" >> /tmp/sysinfo.txt'
docker exec -it "$CONTAINER_NAME" /bin/bash -c 'echo "GPU:" >> /tmp/sysinfo.txt && nvidia-smi -L >> /tmp/sysinfo.txt || echo "nvidia-smi not available" >> /tmp/sysinfo.txt'
docker cp "$CONTAINER_NAME:/tmp/sysinfo.txt" "$OUTPUT_DIR/system_info.txt"
echo "✅ Saved to $OUTPUT_DIR/system_info.txt"

# Create a summary report
echo "Generating summary report..."
cat > "$OUTPUT_DIR/summary_report.md" << EOF
# Docker Container Dependency Analysis

## System Information

\`\`\`
$(cat "$OUTPUT_DIR/system_info.txt")
\`\`\`

## Installed Packages

Total packages installed: $(grep -c "^[a-zA-Z]" "$OUTPUT_DIR/pip_list.txt")

### Key Package Versions

| Package | Version | Source | Dependencies |
|---------|---------|--------|-------------|
EOF

for pkg in $KEY_PACKAGES; do
    if [ -f "$OUTPUT_DIR/package_info/$pkg.txt" ]; then
        version=$(grep "^Version:" "$OUTPUT_DIR/package_info/$pkg.txt" | awk '{print $2}')
        source=$(grep "^Location:" "$OUTPUT_DIR/package_info/$pkg.txt" | awk '{print $2}')
        dep_count=$(grep "^Requires:" "$OUTPUT_DIR/package_info/$pkg.txt" | awk '{print $2}' | tr ',' '\n' | wc -l)
        echo "| $pkg | $version | $(basename $source) | $dep_count |" >> "$OUTPUT_DIR/summary_report.md"
    else
        echo "| $pkg | Not installed | - | - |" >> "$OUTPUT_DIR/summary_report.md"
    fi
done

cat >> "$OUTPUT_DIR/summary_report.md" << EOF

## Dependency Conflicts

\`\`\`
$(grep -A 2 "!" "$OUTPUT_DIR/dependency_conflicts.txt" || echo "No conflicts detected")
\`\`\`

## Next Steps

1. Review the detailed dependency tree in \`dependency_tree.txt\`
2. Check for conflicts in \`dependency_conflicts.txt\`
3. Examine specific package information in the \`package_info\` directory
4. Compare with the dependency artifacts from the build-time analysis
EOF

echo "✅ Summary report saved to $OUTPUT_DIR/summary_report.md"

echo ""
echo "==== Extraction Complete ===="
echo "All dependency information has been extracted to $OUTPUT_DIR"
echo ""
echo "Key files to review:"
echo "- $OUTPUT_DIR/summary_report.md (overview of findings)"
echo "- $OUTPUT_DIR/dependency_tree.txt (full dependency hierarchy)"
echo "- $OUTPUT_DIR/dependency_conflicts.txt (potential issues)"
echo ""
echo "To compare with build-time analysis, run:"
echo "diff -y ./dependency_artifacts/dependency_tree.txt $OUTPUT_DIR/dependency_tree.txt | less"
