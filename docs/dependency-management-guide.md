# Dependency Management Guide for Audiobook Project

This document outlines our optimized approach for managing Python dependencies in the audiobook project's Docker containers, with special consideration for Jetson's ARM architecture and reproducible builds.

## 1. Dependency Management Strategy

### 1.1 Multi-Stage Lock File Generation

We now use pip-tools to generate a deterministic lock file that captures all direct and transitive dependencies:

```dockerfile
# Resolver Stage
FROM ${BASE_IMAGE} AS resolver
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip git && \
    pip install pip-tools

# Copy only requirements file to leverage Docker caching
COPY docker/sesame-tts/requirements.in .

# Generate lock file with backtracking resolver for complex dependency graphs
RUN pip-compile --resolver=backtracking --output-file=requirements.lock.txt requirements.in
```

### 1.2 Architecture-Specific Wheel Handling

For Jetson's ARM64 architecture, we build or source appropriate wheels:

```dockerfile
# Wheel Builder Stage - for dependencies that need compilation
FROM ${BASE_IMAGE} AS wheel-builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev wget curl

# Copy the lock file from the resolver stage
COPY --from=resolver requirements.lock.txt .

# Set up Jetson-specific pip configuration
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf

# Download wheels to a dedicated directory
RUN pip wheel --wheel-dir=/wheels -r requirements.lock.txt

# Final Stage
FROM ${BASE_IMAGE} AS final
COPY --from=wheel-builder /wheels /wheels
COPY --from=resolver requirements.lock.txt .

# Install from local wheels first, then fall back to indexes if needed
RUN pip install --no-cache-dir --find-links=/wheels -r requirements.lock.txt && \
    rm -rf /wheels
```

## 2. Key Dependency Management Features

### 2.1 Version Pinning Strategy

Our approach to version pinning balances stability with flexibility:

#### requirements.in Structure:

```
# Core PyTorch - pinned for compatibility with Jetson
torch==2.2.0
torchvision==0.17.0
torchaudio==2.2.0

# Libraries with specific version requirements
vector_quantize_pytorch==1.22.15  # Must use this version for compatibility
torchtune==0.3.0                  # Performance-critical component
torchao==0.1.0                    # Performance-critical component
moshi==0.2.2                      # Required for model interface

# Libraries with minimum version constraints
transformers>=4.31.0
huggingface_hub>=0.16.4
accelerate>=0.25.0
```

### 2.2 Transitive Dependency Documentation

We now generate and store complete dependency trees for better debugging and auditing:

```dockerfile
# Generate dependency tree artifacts
RUN pip install pipdeptree && \
    pipdeptree --warn silence > /opt/dependency_artifacts/dependencies.txt && \
    pipdeptree --json-tree > /opt/dependency_artifacts/dependency_tree.json
```

### 2.3 Environment Documentation

We document the complete environment for reproducibility:

```dockerfile
# Create environment information artifacts
RUN mkdir -p /opt/environment_info && \
    python -c "import sys, platform, torch; print(f'Python {sys.version}\nPlatform: {platform.platform()}\nPyTorch: {torch.__version__} (CUDA available: {torch.cuda.is_available()})')" > /opt/environment_info/environment.txt && \
    pip freeze > /opt/environment_info/frozen_deps.txt && \
    pip list --format=freeze > /opt/environment_info/explicit_deps.txt
```

## 3. Conflict Resolution Techniques

### 3.1 Dependency Analysis

We implement systematic dependency analysis to identify and resolve conflicts:

```bash
#!/bin/bash
# scripts/analyze_dependencies.sh

echo "Analyzing Python dependencies..."

# Generate requirements.lock.txt if it doesn't exist
if [ ! -f requirements.lock.txt ]; then
    pip-compile --resolver=backtracking -o requirements.lock.txt docker/sesame-tts/requirements.in
fi

# Check for conflicts
echo "Checking for conflicts..."
pip check || echo "Conflicts detected!"

# Show dependency tree for specific packages
echo "Dependency tree for critical packages:"
pipdeptree --packages torch,torchvision,torchaudio,vector_quantize_pytorch,torchao,moshi

# Check for packages without wheels
echo "Checking packages that will need to be built from source..."
python -c "
import pkg_resources
import subprocess
import sys

for req in pkg_resources.parse_requirements(open('requirements.lock.txt')):
    try:
        subprocess.check_output(['pip', 'download', '--no-deps', '--python-version', '3.12', '--platform', 'linux_aarch64', '--only-binary=:all:', str(req)])
    except subprocess.CalledProcessError:
        print(f'{req} - needs to be built from source')
"
```

### 3.2 Selective Dependency Overriding

For critical conflicts, we implement selective overriding:

```python
# requirements.in
# Force specific version of einops to avoid conflict with vector_quantize_pytorch
einops==0.8.0

# Set constraints to avoid incompatible version combinations
torch==2.2.0
torchvision==0.17.0
torchaudio==2.2.0

# Add constraints to satisfy multiple dependencies
numpy>=1.24.0,<2.0.0
```

## 4. Optimization for Jetson ARM Architecture

### 4.1 Jetson-Specific Index Configuration

We've optimized our Dockerfile to better handle Jetson-specific packages:

```dockerfile
# Configure pip to use Jetson-optimized wheels first
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 60" >> ~/.config/pip/pip.conf && \
    echo "retries = 3" >> ~/.config/pip/pip.conf
```

### 4.2 CUDA Configuration

We set appropriate CUDA configurations for Jetson Orin:

```dockerfile
# Set CUDA architecture flags for Jetson Orin Nano
ENV TORCH_CUDA_ARCH_LIST="8.7" \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1
```

## 5. Verification Steps

We now include verification for critical dependencies:

```dockerfile
# Verify critical dependencies are correctly installed
RUN python -c "import torch; print(f'PyTorch version: {torch.__version__}'); assert torch.__version__ == '2.2.0', 'Incorrect torch version'" && \
    python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}'); assert torchvision.__version__ == '0.17.0', 'Incorrect torchvision version'" && \
    python -c "import torchaudio; print(f'TorchAudio version: {torchaudio.__version__}'); assert torchaudio.__version__ == '2.2.0', 'Incorrect torchaudio version'" && \
    python -c "import einops; print(f'Einops version: {einops.__version__}')" && \
    python -c "import vector_quantize_pytorch; print('Vector Quantize PyTorch installed successfully')" && \
    python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 6. BuildKit Optimizations

We leverage BuildKit's advanced caching features:

```dockerfile
# Enable BuildKit caching for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --prefer-binary -r requirements.lock.txt
```

## 7. Implementation Workflow

### 7.1 Setup the New Dependency System

1. Create the requirements.in file:

```bash
# Create the requirements.in file from current requirements.txt
cp ~/workspace/audiobook/docker/sesame-tts/requirements.txt ~/workspace/audiobook/docker/sesame-tts/requirements.in

# Edit to use the correct constraint syntax
sed -i 's/^# /# /' ~/workspace/audiobook/docker/sesame-tts/requirements.in
```

2. Update the Dockerfile to use the multi-stage approach:

```bash
# Create a backup of the current Dockerfile
cp ~/workspace/audiobook/docker/sesame-tts/Dockerfile ~/workspace/audiobook/docker/sesame-tts/Dockerfile.backup

# Edit the Dockerfile to implement the multi-stage approach
# (This would be a manual edit with the changes outlined above)
```

3. Create dependency analysis scripts:

```bash
mkdir -p ~/workspace/audiobook/scripts/dependency
touch ~/workspace/audiobook/scripts/dependency/analyze.sh
chmod +x ~/workspace/audiobook/scripts/dependency/analyze.sh
```

### 7.2 Usage Instructions

1. **Generating the lock file**:

```bash
# Navigate to the repository root
cd ~/workspace/audiobook

# Generate the lock file
docker run --rm -v $(pwd)/docker/sesame-tts:/work -w /work python:3.12 pip-compile --resolver=backtracking -o requirements.lock.txt requirements.in
```

2. **Building with the new dependency system**:

```bash
# Use the enhanced build script
DOCKER_BUILDKIT=1 ./scripts/build.sh --use-buildkit --cache --verbose
```

3. **Analyzing dependencies**:

```bash
# Run the dependency analysis script
./scripts/dependency/analyze.sh
```

## 8. Conclusion

This dependency management approach addresses the key challenges we've faced:

1. **Reproducibility**: By using lock files and artifact generation, we ensure consistent builds.
2. **ARM64 Compatibility**: We prioritize Jetson-optimized wheels and handle architecture-specific builds.
3. **Conflict Resolution**: We systematically identify and resolve dependency conflicts.
4. **Performance**: We ensure the correct CUDA configurations for optimal Jetson performance.
5. **Documentation**: We generate comprehensive dependency documentation for debugging and auditing.

Implementing this system will significantly improve our build reliability and help us avoid the dependency issues we've encountered in the past.
