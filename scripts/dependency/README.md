# Dependency Analysis & Management Tools

This directory contains a comprehensive set of tools for analyzing and managing Python dependencies in Docker containers, with a focus on ARM64/Jetson compatibility.

## Complete Workflow

For a comprehensive dependency analysis workflow:

1. **Analyze dependencies before building**:
   ```bash
   ./analyze_all.sh
   ```

2. **Build the Docker container**:
   ```bash
   cd ~/workspace/audiobook
   DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .
   ```

3. **Run the container in detached mode for analysis**:
   ```bash
   docker run --name sesame-tts --rm -d sesame-tts-jetson sleep infinity
   ```

4. **Extract dependency information from the running container**:
   ```bash
   ./extract_from_container.sh sesame-tts
   ```

5. **Compare build-time analysis with runtime container**:
   ```bash
   python3 compare_analysis.py
   ```

6. **Review the comparison report**:
   ```bash
   less ../dependency_artifacts/comparison/comparison_report.md
   ```

7. **Stop the container when done**:
   ```bash
   docker stop sesame-tts
   ```

## Individual Tools

### Pre-Build Analysis

- **`analyze_all.sh`**: Runs all pre-build analysis tools and generates a comprehensive report
- **`generate_dependency_tree.sh`**: Creates a visual dependency tree for understanding package relationships
- **`generate_compatibility_matrix.py`**: Shows which versions of packages are compatible
- **`check_wheel_availability.py`**: Identifies packages with/without ARM64 wheels
- **`simulate_resolution.py`**: Simulates dependency resolution to identify conflicts
- **`resolve_best_versions.py`**: Recommends optimal package versions

### Post-Build Analysis

- **`extract_from_container.sh`**: Extracts dependency information from a running container
- **`compare_analysis.py`**: Compares build-time and runtime dependency information

## Key Artifacts Generated

After running the complete workflow, you'll have these key artifacts:

### Pre-Build Analysis (`~/workspace/audiobook/dependency_artifacts/`)

- **`dependency_tree.txt`**: Visual representation of package dependencies
- **`wheel_availability_summary.txt`**: Shows which packages have ARM64 wheels
- **`dependency_conflicts.txt`**: Lists detected circular dependencies
- **`version_analysis_report.txt`**: Analysis of package version compatibility
- **`recommended_requirements.in`**: Suggested requirements.in with optimal versions

### Container Extraction (`~/workspace/audiobook/dependency_artifacts/container_extracted/`)

- **`pip_freeze.txt`**: Actual installed packages in the container
- **`dependency_tree.txt`**: Runtime dependency hierarchy
- **`dependency_conflicts.txt`**: Actual conflicts in the container
- **`summary_report.md`**: Overview of container dependencies

### Comparison Analysis (`~/workspace/audiobook/dependency_artifacts/comparison/`)

- **`comparison_report.md`**: Detailed comparison of build vs. runtime
- **`comparison_data.json`**: Machine-readable comparison data

## Usage Examples

### Finding Version Mismatches

To identify version differences between your requirements and what's actually installed:

```bash
./extract_from_container.sh sesame-tts
python3 compare_analysis.py
grep -A 20 "Version Differences" ../dependency_artifacts/comparison/comparison_report.md
```

### Diagnosing Circular Dependencies

To identify and resolve circular dependencies:

```bash
./analyze_all.sh
grep -A 10 "Circular" ../dependency_artifacts/dependency_resolution_report.txt
```

### Finding Packages Without ARM64 Wheels

To identify packages that need to be built from source:

```bash
./analyze_all.sh
grep -B 1 -A 1 "❌ No" ../dependency_artifacts/wheel_availability_summary.txt
```

## Best Practices

1. **Always run pre-build analysis first** to understand dependencies before building

2. **Extract and compare after successful builds** to verify that the actual container matches your expectations

3. **Update requirements.in based on comparison results** to ensure reproducible builds

4. **Focus on key packages first** (`torch`, `torchvision`, etc.) when resolving conflicts

5. **Prefer Jetson-optimized versions when available** for better performance

## Troubleshooting

If you encounter issues:

1. **Check for circular dependencies** in the dependency resolution report

2. **Verify ARM64 wheel availability** for problematic packages

3. **Compare build-time vs. runtime** analysis to identify discrepancies

4. **Try pinning problematic packages** to specific versions known to work

For more detailed guidance, refer to the comprehensive documentation in:
`~/workspace/audiobook/docker/sesame-tts/README-DEPENDENCY-ANALYSIS.md`
