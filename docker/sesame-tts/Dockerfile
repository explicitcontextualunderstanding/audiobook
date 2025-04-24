# Optimized Dockerfile for faster build times with BuildKit
# Use with: DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson .
# dustynv/pytorch:2.7-r36.4.0-cu128-24.04
# NOTE:
# The base image dustynv/pytorch:2.6-r36.4.0-cu128-24.04 is built with Python 3.12 (cp312).
# Jetson-optimized wheels on https://pypi.jetson-ai-lab.dev/jp6/cu128 are available for Python 3.12,
# but not for previous versions of Python. If you use this base image, ensure all dependencies and wheels are for Python 3.12.
# If you need previous versions of Python support, you may need to build from source or use a different base image.

ARG BASE_IMAGE=dustynv/pytorch:2.6-r36.4.0-cu128-24.04


# ============================================================================
# RESOLVER STAGE: Generate the lock file to capture all dependencies
# ============================================================================
FROM ${BASE_IMAGE} AS resolver

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    DEBIAN_FRONTEND=noninteractive \
    CONDA_DIR=/opt/conda \
    PYTHONHASHSEED=0 \
    PIP_DEFAULT_TIMEOUT=100 \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1 \
    CARGO_HOME=/root/.cargo \
    PATH="/root/.cargo/bin:/opt/conda/bin:$PATH"

# Install pip-tools for dependency resolution and other essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl git ca-certificates build-essential python3-pip && \
    pip3 install --no-cache-dir pip-tools && \
    rm -rf /var/lib/apt/lists/*

# Install Rust (needed for some packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustup default stable && \
    rustup update && \
    cargo --version

# Configure pip to use Jetson-optimized wheels
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 120" >> ~/.config/pip/pip.conf && \
    echo "retries = 5" >> ~/.config/pip/pip.conf

# Copy requirements.in file 
COPY requirements.in /tmp/requirements.in

# Generate the lock file with backtracking resolver
# Remove silentcipher and bitsandbytes from requirements.in before compiling to avoid torch version conflicts and ARM64 wheel issues.
# If using moshi, bitsandbytes may still be pulled in as a transitive dependency.
RUN sed -i '/silentcipher/d' /tmp/requirements.in && \
    sed -i '/bitsandbytes/d' /tmp/requirements.in && \
    sed -i '/sphn/d' /tmp/requirements.in && \
    pip-compile --resolver=backtracking --output-file=/tmp/requirements.lock.txt /tmp/requirements.in && \
    # Verify the lock file was created
    test -f /tmp/requirements.lock.txt || (echo "Failed to generate requirements.lock.txt" && exit 1)

# ============================================================================
# DEPENDENCIES STAGE: Install all dependencies from wheels
# ============================================================================
FROM ${BASE_IMAGE} AS dependencies

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    DEBIAN_FRONTEND=noninteractive \
    CONDA_DIR=/opt/conda \
    PYTHONHASHSEED=0 \
    PIP_DEFAULT_TIMEOUT=100 \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1 \
    CARGO_HOME=/root/.cargo \
    PATH="/root/.cargo/bin:/opt/conda/bin:$PATH" \
    # Set CUDA architecture for Jetson Orin
    TORCH_CUDA_ARCH_LIST="8.7"

# Install only essential system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl git ca-certificates build-essential python3-dev software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# Install Rust (needed for some packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustup default stable && \
    rustup update && \
    cargo --version

# Configure pip for faster installations with Jetson-optimized wheels
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 120" >> ~/.config/pip/pip.conf && \
    echo "retries = 5" >> ~/.config/pip/pip.conf

# Install Miniconda and set up the environment
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o Miniconda3.sh && \
    bash Miniconda3.sh -b -p /opt/conda && \
    rm Miniconda3.sh && \
    /opt/conda/bin/conda config --set channel_priority flexible && \
    /opt/conda/bin/conda config --set pip_interop_enabled True && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda create -y -n tts python=3.12 pip setuptools wheel && \
    /opt/conda/bin/conda clean -ya

# Install ffmpeg
RUN /opt/conda/bin/conda install -n tts -y -c conda-forge ffmpeg || \
    (apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository -y ppa:jonathonf/ffmpeg-4 && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*) || \
    (echo "Failed to install ffmpeg. Please check your repositories and try again." && exit 1)

# Copy the lock file from the resolver stage
COPY --from=resolver /tmp/requirements.lock.txt /tmp/requirements.lock.txt

# Install Python dependencies using the lock file with BuildKit caching
SHELL ["/bin/bash", "-c"]
RUN --mount=type=cache,target=/root/.cache/pip \
    sed -i '/bitsandbytes/d' /tmp/requirements.lock.txt && \
    sed -i '/sphn/d' /tmp/requirements.lock.txt && \
    sed -i '/torchao/d' /tmp/requirements.lock.txt && \
    sed -i '/torchtune/d' /tmp/requirements.lock.txt && \
    sed -i '/sphn@/d' /tmp/requirements.lock.txt && \
    sed -i '/sphn==/d' /tmp/requirements.lock.txt && \
    sed -i '/moshi@/d' /tmp/requirements.lock.txt && \
    # Remove any lines that reference sphn or moshi as a dependency of another package (e.g., "sphn" or "moshi" in a subdependency line)
    grep -vE '(^|\s)(sphn|moshi)([= @:]|$)' /tmp/requirements.lock.txt > /tmp/requirements.lock.txt.clean && \
    mv /tmp/requirements.lock.txt.clean /tmp/requirements.lock.txt && \
    source /opt/conda/bin/activate tts && \
    echo "Installing Python dependencies from lock file..." && \
    pip install --no-cache-dir --prefer-binary -r /tmp/requirements.lock.txt && \
    # Install pipdeptree for dependency documentation
    pip install --no-cache-dir pipdeptree && \
    # Generate dependency documentation
    mkdir -p /opt/dependency_docs && \
    pipdeptree --json-tree > /opt/dependency_docs/dependency_tree.json && \
    pip freeze > /opt/dependency_docs/frozen_deps.txt

# Verify critical imports to ensure dependencies are correctly installed
RUN source /opt/conda/bin/activate tts && \
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')" && \
    python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}')" && \
    python -c "import torchaudio; print(f'TorchAudio version: {torchaudio.__version__}')" && \
    python -c "import vector_quantize_pytorch; print('Vector Quantize PyTorch imported successfully')" && \
    python -c "import torchao; print(f'TorchAO version: {torchao.__version__ if hasattr(torchao, \"__version__\") else \"unknown\"}')" && \
    python -c "import einops; print(f'Einops version: {einops.__version__}')" && \
    python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')" && \
    python -c "import nltk; print('NLTK imported successfully')" && \
    python -c "print('All critical imports verified successfully')"

# Pre-download NLTK data
RUN source /opt/conda/bin/activate tts && \
    python -c 'import nltk; nltk.download("punkt", quiet=True)'

# ============================================================================
# BUILDER STAGE: Set up the environment
# ============================================================================
FROM dependencies AS builder

WORKDIR /opt/build

# Download Triton Inference Server in a single layer
ARG TRITON_VERSION=2.55.0
RUN echo "Installing Triton Inference Server..." && \
    wget --quiet https://github.com/triton-inference-server/server/releases/download/v${TRITON_VERSION}/tritonserver${TRITON_VERSION}-igpu.tar \
    -O triton.tar && \
    mkdir -p /opt/tritonserver && \
    tar -xf triton.tar -C /opt/tritonserver --strip-components=1 && \
    rm triton.tar

# Set up CSM package
RUN echo "Setting up CSM package..." && \
    mkdir -p /opt/csm && \
    git clone --depth 1 https://github.com/SesameAILabs/csm.git /tmp/csm && \
    cp /tmp/csm/generator.py /opt/csm/ && \
    cp /tmp/csm/models.py /opt/csm/ && \
    rm -rf /tmp/csm

# Create CSM package __init__.py
RUN echo '"""Sesame CSM Text-to-Speech package.\n\nThis package provides access to the Sesame CSM text-to-speech model with optimizations for audiobook generation on Jetson devices."""\n\nfrom .generator import load_csm_1b, Segment, Generator\n\n__all__ = ["load_csm_1b", "Segment", "Generator"]' > /opt/csm/__init__.py

# Create directories needed at runtime
RUN mkdir -p /models /audiobook_data /books /segments

# Create build information file
RUN echo "Sesame TTS build information" > /opt/build_info.txt && \
    echo "Build date: $(date)" >> /opt/build_info.txt && \
    echo "Base image: ${BASE_IMAGE}" >> /opt/build_info.txt && \
    source /opt/conda/bin/activate tts && \
    echo "Python version: $(python --version)" >> /opt/build_info.txt && \
    echo "PyTorch version: $(python -c 'import torch; print(torch.__version__)')" >> /opt/build_info.txt && \
    echo "CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')" >> /opt/build_info.txt

# Final cleanup to reduce image size
RUN find /opt/conda -name "*.a" -delete && \
    find /opt/conda -name "*.js.map" -delete && \
    rm -rf /opt/conda/pkgs && \
    rm -rf /root/.cache /tmp/* /var/tmp/*

# ============================================================================
# RUNTIME STAGE: Create the minimal runtime image
# ============================================================================
FROM ${BASE_IMAGE} AS runtime

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson (optimized build)"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# Copy only what's needed from the builder stage
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /opt/csm /opt/csm
COPY --from=builder /opt/tritonserver /opt/tritonserver
COPY --from=builder /opt/dependency_docs /opt/dependency_docs
COPY --from=builder /opt/build_info.txt /opt/build_info.txt

# Create empty directories for volumes
RUN mkdir -p /models /audiobook_data /books /segments

# Copy utility scripts and application files
COPY docker/sesame-tts/utils/audiobook_generator.py /opt/csm/
COPY docker/sesame-tts/utils/watermarking.py /opt/csm/
COPY docker/sesame-tts/utils/ /opt/utils/
COPY docker/sesame-tts/entrypoint.sh /entrypoint.sh

# Set up environment 
ENV PATH="/opt/tritonserver/bin:/opt/conda/bin:${PATH}" \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1

# Make scripts executable
RUN chmod +x /entrypoint.sh && \
    if [ -f "/opt/csm/watermarking.py" ]; then chmod +x /opt/csm/watermarking.py; fi && \
    if [ -d "/opt/utils/" ]; then chmod +x /opt/utils/*; fi && \
    mkdir -p /usr/local/bin && \
    echo 'import sys; sys.path.append("/opt/csm")' > $(python3 -c 'import site; print(site.getsitepackages()[0])')/csm_path.pth

# Set working directory
WORKDIR /workspace

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD /opt/conda/bin/conda run -n tts python -c "import torch, moshi, torchao; print(f'Health check passed. CUDA available: {torch.cuda.is_available()}'); exit(0 if torch.cuda.is_available() else 1)" || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/opt/conda/bin/conda", "run", "-n", "tts", "--no-capture-output", "bash"]
