# Dependency Analysis Tools for Jetson Docker Builds

This document explains how to use the dependency analysis tools to understand and resolve dependency issues in Docker container builds for Jetson devices.

## Understanding the Problem

Building Docker containers for Jetson devices (ARM64 architecture) involves several challenging dependency constraints:

1. **Architecture Compatibility**: Many Python packages don't provide pre-built wheels for ARM64, requiring source builds that can fail.

2. **Version Mismatches**: The Jetson-optimized PyPI index (`pypi.jetson-ai-lab.dev`) may have different versions available than the main PyPI repository.

3. **Circular Dependencies**: Complex dependency graphs can lead to circular dependencies that pip can't resolve.

4. **Conflicting Requirements**: Different packages may have conflicting version requirements for shared dependencies.

## Dependency Analysis Tools

We've created a suite of tools to help analyze and resolve these issues:

### 1. Comprehensive Analysis

To run all analysis tools and generate a complete dependency report:

```bash
# Make the script executable if needed
chmod +x scripts/dependency/analyze_all.sh

# Run the analysis
./scripts/dependency/analyze_all.sh
```

This will generate a comprehensive set of artifacts in the `dependency_artifacts` directory, including:
- Dependency trees showing package relationships
- Wheel availability reports for ARM64
- Version compatibility matrices
- Recommended package versions

### 2. Individual Analysis Tools

You can also run individual analysis tools:

#### Dependency Tree Visualization

```bash
./scripts/dependency/generate_dependency_tree.sh
```
Generates a hierarchical view of package dependencies, including detection of circular dependencies.

#### Version Compatibility Matrix

```bash
python3 scripts/dependency/generate_compatibility_matrix.py
```
Creates a matrix showing which versions of packages are compatible with each other.

#### Wheel Availability Checker

```bash
python3 scripts/dependency/check_wheel_availability.py
```
Identifies which packages have pre-built wheels available for ARM64 architecture.

#### Dependency Resolution Simulator

```bash
python3 scripts/dependency/simulate_resolution.py
```
Simulates pip's dependency resolution process to identify potential conflicts before actual installation.

#### Version Resolver

```bash
python3 scripts/dependency/resolve_best_versions.py
```
Analyzes all data and recommends the optimal versions of packages to use in your requirements.in file.

## Understanding the Artifacts

The analysis tools generate several files to help you understand dependencies:

### Key Files to Review

1. **version_analysis_report.txt**: Contains recommendations for each package with detailed explanations of why specific versions were selected.

2. **dependency_conflicts.txt**: Lists any circular dependencies or version conflicts detected.

3. **wheel_availability_summary.txt**: Shows which packages have ARM64 wheels available on different package repositories.

4. **recommended_requirements.in**: A suggested requirements.in file with optimal versions for Jetson compatibility.

### Example Workflow

When facing Docker build issues with Jetson:

1. **Analyze dependencies**:
   ```bash
   ./scripts/dependency/analyze_all.sh
   ```

2. **Review the key findings**:
   - Check for circular dependencies
   - Identify packages without ARM64 wheels
   - Review version recommendations

3. **Update requirements.in**:
   ```bash
   cp dependency_artifacts/recommended_requirements.in docker/sesame-tts/requirements.in
   ```

4. **Rebuild the Docker container**:
   ```bash
   DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .
   ```

## Tips for Resolving Common Issues

### Packages without ARM64 Wheels

For packages without ARM64 wheels, you have several options:

1. **Find an alternative package** that provides similar functionality but has ARM64 support.

2. **Use an older version** that may have ARM64 wheels available.

3. **Ensure build dependencies are installed** in your Dockerfile for source builds:
   ```dockerfile
   RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential python3-dev gcc g++ gfortran \
       libopenblas-dev liblapack-dev
   ```

### Circular Dependencies

To resolve circular dependencies:

1. **Pin specific versions** of problematic packages to versions known to work together.

2. **Use compatibility ranges** (`>=1.0.0,<2.0.0`) rather than exact versions when possible.

3. **Separate installations** into multiple steps, installing the circular dependencies last.

### Version Conflicts

For version conflicts:

1. **Use the version compatible with the most critical package** if you have to choose.

2. **Consider using a different base image** with a different PyTorch version if needed.

3. **Use `--no-deps`** when installing problematic packages and manually install their dependencies.

## Conclusion

These tools are designed to help you understand and resolve the complex dependency issues that can arise when building Docker containers for Jetson devices. By systematically analyzing dependencies, you can make informed decisions about which versions to use, avoiding circular resolution issues.

If you encounter persistent issues, consider:

1. **Checking the base image**: Ensure your base image (`dustynv/pytorch:*`) is up-to-date.

2. **Using source builds**: For some packages, source builds may be more reliable than wheels.

3. **Creating a custom wheel repository**: For frequently used packages, building and hosting your own wheels can speed up builds.
