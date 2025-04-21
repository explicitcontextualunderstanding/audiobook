# Build Validation and Optimization

This document outlines steps to validate our build assumptions and optimize build times for the audiobook project on Jetson Orin Nano.

## 1. Current Build Issues

The current build process for the Sesame CSM container is taking an excessive amount of time. This may be due to invalid assumptions about:
- The availability and usability of pre-built wheels
- Dependency chain requirements
- The need for source compilation
- Optimal container strategies

## 2. Testing PyPI Wheels Compatibility

### 2.1 Wheel Compatibility Analysis

To validate whether standard or Jetson-specific wheels can be used:

```bash
# Create a test environment
mkdir -p ~/wheel-test
cd ~/wheel-test
python -m venv wheel-env
source wheel-env/bin/activate

# Test standard PyPI wheels
pip install --no-cache-dir torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

# Test Jetson-specific wheels
pip install --no-cache-dir --index-url https://pypi.jetson-ai-lab.dev/simple torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 2.2 Dependency Chain Validation

Test the key dependency chain (torch → torchao → torchtune) to identify compatibility issues:

```bash
# In the test environment, try installing the chain
pip install torch==2.6.0
pip install torchao==0.1.0
pip install torchtune==0.3.0

# Test imports
python -c "import torch; import torchao; import torchtune; print('All imports successful')"
```

### 2.3 Build with Different Base Images

Compare build times using different base images:

```bash
# Test with NVIDIA PyTorch image
time docker build -t sesame-test-nvidia -f docker/sesame-tts/Dockerfile.test-nvidia .

# Test with Dusty's PyTorch image
time docker build -t sesame-test-dusty -f docker/sesame-tts/Dockerfile.test-dusty .

# Test with pre-built torchao image
time docker build -t sesame-test-torchao -f docker/sesame-tts/Dockerfile.test-torchao .
```

## 3. Caching Strategies

### 3.1 Layer Optimization

Reorder Dockerfile commands to maximize layer caching:

```dockerfile
# Example optimized layer ordering
FROM ${BASE_IMAGE}

# System packages first (change rarely)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 cmake build-essential git wget curl pkg-config \
    ca-certificates gnupg \
  && rm -rf /var/lib/apt/lists/*

# Create directories (change rarely)
RUN mkdir -p /models /audiobook_data /books /segments /opt/csm /opt/tritonserver

# Core dependencies with fixed versions (change occasionally)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Application-specific files (change frequently)
COPY src/ /app/src/
```

### 3.2 Multi-stage Builds

Implement multi-stage builds to separate build-time dependencies from runtime:

```dockerfile
# Build stage
FROM ${BASE_IMAGE} AS builder
# ... build dependencies and compilations ...

# Runtime stage
FROM ${BASE_IMAGE} AS runtime
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /opt/csm /opt/csm
# ... only copy what's needed for runtime ...
```

### 3.3 Pre-build and Cache Key Dependencies

Identify the slowest dependencies to build and pre-build them:

```bash
# Create a script to pre-build key dependencies
cat > prebuild.sh << 'EOF'
#!/bin/bash
mkdir -p ~/prebuild-cache
docker build -t torch-builder -f Dockerfile.torch-builder .
docker run --rm -v ~/prebuild-cache:/cache torch-builder
EOF
chmod +x prebuild.sh
```

## 4. Measuring and Comparing Build Times

Create a benchmarking script to track build times consistently:

```bash
#!/bin/bash
# build-benchmark.sh
LOGFILE="build-benchmark-results.log"
echo "=== Build Benchmark $(date) ===" >> $LOGFILE

echo "Testing standard build..." | tee -a $LOGFILE
time (docker build -t sesame-standard -f docker/sesame-tts/Dockerfile . 2>&1) | tee -a build-standard.log
echo "Standard build finished with exit code $?" | tee -a $LOGFILE
grep "real" /proc/$$/fd/1 | tail -1 >> $LOGFILE

echo "Testing optimized build..." | tee -a $LOGFILE
time (docker build -t sesame-optimized -f docker/sesame-tts/Dockerfile.optimized . 2>&1) | tee -a build-optimized.log
echo "Optimized build finished with exit code $?" | tee -a $LOGFILE
grep "real" /proc/$$/fd/1 | tail -1 >> $LOGFILE
```

## 5. Alternative Approaches

### 5.1 Test a Simpler Container Structure

Create a minimal container and install dependencies at runtime:

```bash
# Minimal Dockerfile
FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip
COPY requirements-minimal.txt /tmp/
RUN pip3 install -r /tmp/requirements-minimal.txt

CMD ["/bin/bash"]
```

Then install specific dependencies at runtime:

```bash
# In the quickstart.sh script
docker run --runtime nvidia -it --rm -v ~/audiobook:/books my-minimal-container \
  bash -c "pip install git+https://github.com/SesameAILabs/csm.git && python /books/generate_audiobook_minimal.py ..."
```

### 5.2 Package-Based Approach

Test if we can package our scripts as a Python module and install them inside an existing container:

```bash
# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="audiobook_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyPDF2>=3.0.1",
        "ebooklib>=0.18.0",
        "beautifulsoup4>=4.12.2",
        "pydub>=0.25.1",
        "nltk>=3.8.1",
        "tqdm>=4.66.1",
    ],
    entry_points={
        'console_scripts': [
            'generate-audiobook-piper=audiobook_generator.piper:main',
            'generate-audiobook-sesame=audiobook_generator.sesame:main',
        ],
    },
)
EOF
```

## 6. Document and Share Findings

Create a shared document to track what worked and what didn't:

```
## What Worked
- Using dustynv/pytorch base image reduced build time by X%
- Pre-building torchao and caching it saved Y minutes
- Multi-stage builds reduced final image size by Z%

## What Didn't Work
- Standard PyPI wheels failed because...
- Attempting to use pip's --only-binary flag caused issues with...
- Skipping the Triton Inference Server resulted in runtime errors because...
```

## 7. Validation Results

Record the actual time measurements here once the validation tests have been completed:

| Approach | Build Time | Run Time | Notes |
|----------|------------|----------|-------|
| Original | TBD | TBD | Current approach |
| PyPI wheels | TBD | TBD | Standard PyPI |
| Jetson wheels | TBD | TBD | Jetson AI Lab wheels |
| Pre-built cache | TBD | TBD | With dependency caching |
| Multi-stage | TBD | TBD | Using multi-stage Dockerfile |
| Minimal + runtime | TBD | TBD | Minimal container + runtime install |
| Package-based | TBD | TBD | Using installable package |
