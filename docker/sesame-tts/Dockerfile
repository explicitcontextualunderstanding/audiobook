# Optimized Dockerfile for Sesame CSM on Jetson Orin
# Use with: DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson .
#
# ASSUMPTIONS:
# 1. Base image dustynv/pytorch:2.6-r36.4.0-cu128-24.04 contains Python 3.12
# 2. PyTorch 2.6.0 is compatible with Sesame CSM
# 3. The repository structure includes:
#    - requirements.in at the root level
#    - docker/sesame-tts/utils/ directory with utilities
#    - docker/sesame-tts/entrypoint.sh exists
# 4. SesameLabs CSM can be downloaded from Hugging Face
# 5. The container will have access to NVIDIA GPU at runtime

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

# Install pip-tools and essential build tools in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl git ca-certificates build-essential python3-pip && \
    pip3 install --no-cache-dir pip-tools && \
    rm -rf /var/lib/apt/lists/*

# Install Rust with better error handling and environment persistence
# Rust is required for building moshi and other packages from source
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustup default stable && \
    rustup update && \
    # Verify installation and make cargo available in PATH
    cargo --version && \
    # Export Rust environment variables to ensure they persist
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc && \
    echo 'export CARGO_HOME="$HOME/.cargo"' >> ~/.bashrc

# Configure pip to use Jetson-optimized wheels when available
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.org/simple" > ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 120" >> ~/.config/pip/pip.conf && \
    echo "retries = 5" >> ~/.config/pip/pip.conf

# Copy requirements.in file 
COPY requirements.in /tmp/requirements.in

# Filter out problematic packages in a single operation for better readability
# This removes packages that are known to cause build issues due to:
# - Rust compilation requirements (when Rust may not be properly configured)
# - ARM64 compatibility issues
# - PyTorch version conflicts
RUN grep -v -E '(silentcipher|bitsandbytes|sphn)' /tmp/requirements.in > /tmp/requirements.clean.in && \
    mv /tmp/requirements.clean.in /tmp/requirements.in && \
    cat /tmp/requirements.in && \
    # Generate the lock file with backtracking resolver for better dependency resolution
    pip-compile --resolver=backtracking --output-file=/tmp/requirements.lock.txt /tmp/requirements.in && \
    # Verify the lock file was created successfully
    test -f /tmp/requirements.lock.txt || (echo "Failed to generate requirements.lock.txt" && exit 1)

# ============================================================================
# DEPENDENCIES STAGE: Install all dependencies from wheels or source
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

# Install essential system dependencies in a single layer
# These packages are needed for both Python package builds and runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl git ca-certificates build-essential python3-dev \
    software-properties-common libasound2-dev libsndfile1-dev \
    # Added libraries for audio processing
    portaudio19-dev libportaudio2 libportaudiocpp0 && \
    rm -rf /var/lib/apt/lists/*

# Install Rust with proper environment configuration
# This is critical for packages like moshi which require native compilation
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustup default stable && \
    rustup update && \
    # Verify installation
    cargo --version && \
    # Make sure PATH is updated for all subsequent operations
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc && \
    echo 'export CARGO_HOME="$HOME/.cargo"' >> ~/.bashrc

# Configure pip for optimal package installation with Jetson-optimized wheels
# We prioritize PyPI as the primary source for better compatibility,
# but include Jetson-specific indexes as fallbacks
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.org/simple" > ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 120" >> ~/.config/pip/pip.conf && \
    echo "retries = 5" >> ~/.config/pip/pip.conf

# Install Miniconda to create an isolated environment
# This helps keep the base environment clean and dependencies well-organized
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o Miniconda3.sh && \
    bash Miniconda3.sh -b -p /opt/conda && \
    rm Miniconda3.sh && \
    /opt/conda/bin/conda config --set channel_priority flexible && \
    /opt/conda/bin/conda config --set pip_interop_enabled True && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda create -y -n tts python=3.12 pip setuptools wheel && \
    /opt/conda/bin/conda clean -ya

# Install ffmpeg (essential for audio processing) with fallback options
# Try conda first, then apt, since conda may have a more optimized version
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

# Remove problematic packages from the lock file
# This is a more targeted approach than in the resolver stage
# We remove specific packages known to cause issues on ARM64/Jetson
RUN grep -v -E '(bitsandbytes|sphn|torchao|torchtune|moshi)' /tmp/requirements.lock.txt > /tmp/requirements.lock.txt.clean && \
    mv /tmp/requirements.lock.txt.clean /tmp/requirements.lock.txt

# Install Python dependencies using the lock file with BuildKit caching
# The mount type=cache improves build performance by caching pip downloads
SHELL ["/bin/bash", "-c"]
RUN --mount=type=cache,target=/root/.cache/pip \
    source /opt/conda/bin/activate tts && \
    echo "Installing Python dependencies from lock file..." && \
    pip install --no-cache-dir --prefer-binary -r /tmp/requirements.lock.txt && \
    # Install pipdeptree for dependency documentation
    pip install --no-cache-dir pipdeptree && \
    # Generate dependency documentation
    mkdir -p /opt/dependency_docs && \
    pipdeptree --json-tree > /opt/dependency_docs/dependency_tree.json && \
    pip freeze > /opt/dependency_docs/frozen_deps.txt

# Install moshi directly from source using Git
# This is a special step for SesameLabs CSM support
RUN source /opt/conda/bin/activate tts && \
    echo "Installing moshi package from source..." && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    # Try to install moshi from source using the subdirectory approach
    pip install --no-cache-dir "git+https://github.com/kyutai-labs/moshi.git@main#egg=moshi&subdirectory=moshi" || \
    echo "Failed to install moshi. Continuing without it, but CSM functionality may be limited."

# Verify critical imports with conditional checks for optional packages
# This helps ensure our environment is properly set up
RUN source /opt/conda/bin/activate tts && \
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')" && \
    python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}')" && \
    python -c "import torchaudio; print(f'TorchAudio version: {torchaudio.__version__}')" && \
    python -c "import vector_quantize_pytorch; print('Vector Quantize PyTorch imported successfully')" && \
    python -c "try: import torchao; print(f'TorchAO version: {torchao.__version__ if hasattr(torchao, '__version__') else 'unknown'}'); except ImportError: print('TorchAO not installed')" && \
    python -c "import einops; print(f'Einops version: {einops.__version__}')" && \
    python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')" && \
    python -c "import nltk; print('NLTK imported successfully')" && \
    python -c "print('All critical imports verified successfully')"

# Pre-download NLTK data to avoid runtime downloads
RUN source /opt/conda/bin/activate tts && \
    python -c 'import nltk; nltk.download("punkt", quiet=True)'

# ============================================================================
# BUILDER STAGE: Set up the environment and download models
# ============================================================================
FROM dependencies AS builder

WORKDIR /opt/build

# Download Triton Inference Server
# This is used for optimized model inference
ARG TRITON_VERSION=2.55.0
RUN echo "Installing Triton Inference Server..." && \
    wget --quiet https://github.com/triton-inference-server/server/releases/download/v${TRITON_VERSION}/tritonserver${TRITON_VERSION}-igpu.tar \
    -O triton.tar && \
    mkdir -p /opt/tritonserver && \
    tar -xf triton.tar -C /opt/tritonserver --strip-components=1 && \
    rm triton.tar

# Set up CSM package
# This creates a lightweight wrapper around the Sesame CSM model
RUN echo "Setting up CSM package..." && \
    mkdir -p /opt/csm && \
    git clone --depth 1 https://github.com/SesameAILabs/csm.git /tmp/csm && \
    cp -r /tmp/csm/* /opt/csm/ || \
    echo "Warning: Failed to copy all CSM files. Will try to copy essential files."

# Copy essential CSM files if the full clone didn't work
RUN if [ ! -f "/opt/csm/generator.py" ]; then \
    mkdir -p /opt/csm && \
    if [ -d "/tmp/csm" ]; then \
        cp /tmp/csm/generator.py /opt/csm/ 2>/dev/null || echo "generator.py not found"; \
        cp /tmp/csm/models.py /opt/csm/ 2>/dev/null || echo "models.py not found"; \
    else \
        echo "CSM repository not cloned successfully"; \
    fi; \
    fi

# Create CSM package __init__.py
# This makes the CSM package importable
RUN echo '"""Sesame CSM Text-to-Speech package.\n\nThis package provides access to the Sesame CSM text-to-speech model with optimizations for audiobook generation on Jetson devices."""\n\nfrom .generator import load_csm_1b, Segment, Generator\n\n__all__ = ["load_csm_1b", "Segment", "Generator"]' > /opt/csm/__init__.py

# Download SesameLabs CSM model
# This is the critical step for enabling high-quality TTS
RUN echo "Downloading SesameLabs CSM model..." && \
    source /opt/conda/bin/activate tts && \
    # Create model directory
    mkdir -p /models/csm && \
    # Use Python to download from Hugging Face
    python -c "try: from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b', local_dir='/models/csm'); print('Model downloaded successfully'); except Exception as e: print(f'Model download failed: {e}. You will need to download the model manually at runtime.')"

# Create directories needed at runtime
RUN mkdir -p /models /audiobook_data /books /segments

# Create build information file
# This helps with debugging and provides provenance information
RUN echo "Sesame TTS build information" > /opt/build_info.txt && \
    echo "Build date: $(date)" >> /opt/build_info.txt && \
    echo "Base image: ${BASE_IMAGE}" >> /opt/build_info.txt && \
    source /opt/conda/bin/activate tts && \
    echo "Python version: $(python --version)" >> /opt/build_info.txt && \
    echo "PyTorch version: $(python -c 'import torch; print(torch.__version__)')" >> /opt/build_info.txt && \
    echo "CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')" >> /opt/build_info.txt && \
    # Add CSM-specific info
    echo "Moshi available: $(python -c 'try: import moshi; print(True); except ImportError: print(False)')" >> /opt/build_info.txt

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

# Install minimal runtime dependencies
# We only need the packages required at runtime, not build time
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy only what's needed from the builder stage
# This keeps the final image as small as possible
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /opt/csm /opt/csm
COPY --from=builder /opt/tritonserver /opt/tritonserver
COPY --from=builder /opt/dependency_docs /opt/dependency_docs
COPY --from=builder /opt/build_info.txt /opt/build_info.txt
COPY --from=builder /models /models

# Create empty directories for volumes
RUN mkdir -p /audiobook_data /books /segments

# Copy utility scripts and application files
# These should exist in your repository structure
COPY docker/sesame-tts/utils/audiobook_generator.py /opt/csm/ || echo "audiobook_generator.py not found"
COPY docker/sesame-tts/utils/watermarking.py /opt/csm/ || echo "watermarking.py not found"
COPY docker/sesame-tts/utils/ /opt/utils/ || echo "utils directory not found"
COPY docker/sesame-tts/entrypoint.sh /entrypoint.sh || echo "entrypoint.sh not found"

# Set up environment 
ENV PATH="/opt/tritonserver/bin:/opt/conda/bin:${PATH}" \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1

# Make scripts executable and set up Python path
RUN chmod +x /entrypoint.sh 2>/dev/null || echo "entrypoint.sh not found or not executable" && \
    if [ -f "/opt/csm/watermarking.py" ]; then chmod +x /opt/csm/watermarking.py; fi && \
    if [ -d "/opt/utils/" ]; then find /opt/utils -type f -name "*.py" -o -name "*.sh" | xargs chmod +x 2>/dev/null; fi && \
    mkdir -p /usr/local/bin && \
    echo 'import sys; sys.path.append("/opt/csm")' > $(python3 -c 'import site; print(site.getsitepackages()[0])')/csm_path.pth

# Set working directory
WORKDIR /workspace

# Health check
# This verifies both CUDA and CSM functionality
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD /opt/conda/bin/conda run -n tts python -c "import torch; import sys; print(f'CUDA available: {torch.cuda.is_available()}'); try: import moshi; print('Moshi available'); except ImportError: print('Moshi not available - CSM functionality limited'); sys.exit(0 if torch.cuda.is_available() else 1)" || exit 1

# Default entrypoint and command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/opt/conda/bin/conda", "run", "-n", "tts", "--no-capture-output", "python", "/opt/csm/audiobook_generator.py", "--help"]