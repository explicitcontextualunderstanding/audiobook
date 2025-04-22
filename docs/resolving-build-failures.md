# Resolving Docker Build Failures Due to Dependency Conflicts

This guide provides a step-by-step approach to resolving dependency conflicts that prevent your Docker container from building successfully.

## Common Causes of Build Failures

Docker builds for Jetson devices can fail for several reasons:

1. **Missing ARM64 Wheels**: Many Python packages don't provide pre-built wheels for ARM64, requiring source builds that can fail if build dependencies are missing.

2. **Version Conflicts**: Incompatible version requirements between packages (e.g., Package A requires einops==0.7.0 while Package B requires einops>=0.8.0).

3. **Circular Dependencies**: A dependency loop where Package A depends on B, which depends on C, which depends on A.

4. **Architecture-Specific Code**: Packages with architecture-specific code that isn't compatible with ARM64.

## Extracting Dependency Information When Builds Fail

When your Docker build fails, it can be difficult to diagnose the problem. We've created a special analysis container that can extract dependency information even when the main build would fail:

```bash
# Run the extraction script
./scripts/dependency/extract_during_build.sh
```

This script:
1. Builds a separate analysis container that isolates each dependency
2. Tests package installation individually to identify problematic packages
3. Checks for ARM64 wheel availability for each package
4. Generates a recommended requirements.in file with potential fixes
5. Extracts all analysis artifacts to `./dependency_artifacts/build_analysis/`

## Analyzing the Results

After running the extraction script, review these key files:

1. **analysis_report.md**: A comprehensive report of the analysis findings

2. **package_install_results.csv**: Shows which packages installed successfully and which failed, with error messages

3. **wheel_availability.txt**: Shows which packages have ARM64 wheels available and which require source builds

4. **dependency_tree.txt**: Shows the dependencies that were successfully resolved

5. **dependency_conflicts.txt**: Shows detected dependency conflicts

6. **recommended_requirements.in**: A suggested requirements.in file with potential fixes

## Common Problems and Solutions

### 1. Missing ARM64 Wheels

**Symptoms**: 
- Error messages about "Could not find a version that satisfies the requirement"
- Errors about Python package not found for architecture "aarch64"

**Solutions**:
- Check `wheel_availability.txt` to identify packages without ARM64 wheels
- Add necessary build dependencies to your Dockerfile:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential python3-dev gcc g++ gfortran \
      libopenblas-dev liblapack-dev
  ```
- Consider pinning to older versions that might have ARM64 wheels
- Look for alternative packages with ARM64 support

### 2. Version Conflicts

**Symptoms**:
- Error messages about conflicting requirements
- "Cannot install X and Y because these package versions have conflicting dependencies"

**Solutions**:
- Check `package_install_results.csv` for specific error messages
- Review `recommended_requirements.in` for suggested version adjustments
- Try updating conflicting packages to newer versions (usually preferable)
- Or pin to specific versions known to work together

### 3. Circular Dependencies

**Symptoms**:
- Pip enters an infinite loop or times out during installation
- Error messages about "Maximum recursion depth exceeded"

**Solutions**:
- Identify the circular dependency from `dependency_conflicts.txt`
- Break the circle by installing one of the packages with `--no-deps`
- Split installation into multiple stages, installing circular dependencies last

### 4. PyTorch Compatibility Issues

**Symptoms**:
- Errors related to CUDA, PyTorch, or NVIDIA components
- Extensions failing to compile against PyTorch

**Solutions**:
- Use Jetson-optimized versions of PyTorch packages:
  ```
  torch>=2.7.0
  torchvision>=0.22.0
  torchaudio>=2.7.0
  ```
- Ensure CUDA architecture flags match your Jetson hardware:
  ```dockerfile
  ENV TORCH_CUDA_ARCH_LIST="8.7"  # For Jetson Orin
  ```
- Install PyTorch/CUDA dependencies before other packages

## Step-by-Step Resolution Process

1. **Run the extraction script**:
   ```bash
   ./scripts/dependency/extract_during_build.sh
   ```

2. **Review the analysis report**:
   ```bash
   less ./dependency_artifacts/build_analysis/analysis_report.md
   ```

3. **Identify problematic packages**:
   ```bash
   cat ./dependency_artifacts/build_analysis/package_install_results.csv | grep "Failed"
   ```

4. **Apply the recommended requirements**:
   ```bash
   cp ./dependency_artifacts/build_analysis/recommended_requirements.in ./docker/sesame-tts/requirements.in
   ```

5. **Rebuild the container**:
   ```bash
   DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .
   ```

6. **If the build still fails, iterate**:
   - Adjust requirements.in based on specific error messages
   - Consider splitting the installation into multiple stages
   - Add specific build dependencies for problematic packages

## Advanced Troubleshooting

If the recommended requirements don't solve the issue:

1. **Try building in stages**:
   Modify your Dockerfile to install packages in groups, with the most problematic ones last:
   ```dockerfile
   # Install core packages first
   RUN pip install torch torchvision torchaudio
   
   # Install non-problematic packages
   RUN pip install requests numpy pillow
   
   # Install potentially problematic packages last
   RUN pip install vector_quantize_pytorch einops
   ```

2. **Use a different base image**:
   ```dockerfile
   FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3
   ```

3. **Add logging to pip to see more details**:
   ```dockerfile
   RUN pip install --verbose package_name 2>&1 | tee pip_log.txt
   ```

4. **Build from source with specific compiler flags**:
   ```dockerfile
   ENV CFLAGS="-march=armv8-a"
   ```

## Getting Help

If you're still stuck after trying these solutions:

1. Check the Jetson forums for similar issues
2. Look for architecture-specific installation guides for problematic packages
3. Consider creating a GitHub issue with your specific error messages and Dockerfile

## Conclusion

Resolving dependency conflicts for ARM64/Jetson Docker builds can be challenging, but with systematic analysis and the right troubleshooting steps, most issues can be overcome. Focus on identifying the root causes, make targeted adjustments to your requirements, and build in stages when necessary.
