# Optimized Dockerfile for faster build times with BuildKit
# Use with: DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson .
ARG BASE_IMAGE=dustynv/pytorch:2.6-r36.4.0-cu128-24.04

# ============================================================================
# DEPENDENCIES STAGE: Cache dependency installation
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
    TORCH_USE_CUDA_DSA=1

# Install only essential system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Configure pip for faster installations
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 60" >> ~/.config/pip/pip.conf && \
    echo "retries = 3" >> ~/.config/pip/pip.conf

# Install Miniconda and set up the environment
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o Miniconda3.sh && \
    bash Miniconda3.sh -b -p /opt/conda && \
    rm Miniconda3.sh && \
    /opt/conda/bin/conda config --set channel_priority flexible && \
    /opt/conda/bin/conda config --set pip_interop_enabled True && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda create -y -n tts python=3.10 pip setuptools wheel && \
    /opt/conda/bin/conda clean -ya

# Ensure Conda is available in PATH
ENV PATH="/opt/conda/bin:$PATH"

# Install ffmpeg separately if not found in Conda
RUN /opt/conda/bin/conda install -n tts -c conda-forge ffmpeg || \
    (apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository -y ppa:jonathonf/ffmpeg-4 && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*) || \
    (echo "Failed to install ffmpeg. Please check your repositories and try again." && exit 1)

# Copy requirements files
COPY docker/sesame-tts/requirements.txt /tmp/requirements.txt

# Install Rust toolchain (cargo) for compiling extensions
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y && \
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> /etc/profile.d/rust.sh && \
    chmod +x /etc/profile.d/rust.sh && \
    . $HOME/.cargo/env && \
    rustup default stable && \
    rustup update

# Ensure Rust binaries are available in PATH for all subsequent steps
ENV PATH="/root/.cargo/bin:$PATH"

# Activate conda environment and install PyTorch dependencies
SHELL ["/bin/bash", "-c"]
RUN source /opt/conda/bin/activate tts && \
    python -m pip install --no-cache-dir --upgrade pip && \
    # Install PyTorch stack with compatible versions
    pip install --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0

# Install the rest of the requirements (separated to leverage caching)
SHELL ["/bin/bash", "-c"]
RUN source /opt/conda/bin/activate tts && \
    # Install general dependencies, filtering out comments and empty lines
    pip install --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    $(grep -vE "^\s*(#|$)" /tmp/requirements.txt) || \
    (echo "Attempting fallback installation for vector_quantize_pytorch" && \
    pip install --no-cache-dir --prefer-binary \
    "vector_quantize_pytorch @ git+https://github.com/lucidrains/vector-quantize-pytorch.git@1.8.6")

# Install specialized dependencies in a separate layer
SHELL ["/bin/bash", "-c"]
RUN source /opt/conda/bin/activate tts && \
    # Install specialized packages separately
    pip install --no-cache-dir --prefer-binary \
    "torchao==0.1.0" "torchtune==0.3.0" && \
    # Force reinstall moshi to ensure correct version
    pip install --force-reinstall --no-cache-dir --prefer-binary \
    "moshi==0.2.2" && \
    # Special dependencies
    pip install --no-cache-dir --prefer-binary \
    "silentcipher @ git+https://github.com/SesameAILabs/silentcipher@v1.0.2" && \
    # Install triton for torchao kernels
    pip install --no-cache-dir --prefer-binary \
    triton

# Verify critical imports to ensure dependencies are correctly installed
SHELL ["/bin/bash", "-c"]
RUN source /opt/conda/bin/activate tts && \
    python -c "import torch; print(f'PyTorch version: {torch.__version__}'); import torchao; import torchtune; import moshi; print('All imports successful')"

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

# Pre-download NLTK data
SHELL ["/bin/bash", "-c"]
RUN source /opt/conda/bin/activate tts && \
    python -c 'import nltk; nltk.download("punkt", quiet=True)'

# Create CSM package __init__.py
RUN echo '"""Sesame CSM Text-to-Speech package.\n\nThis package provides access to the Sesame CSM text-to-speech model with optimizations for audiobook generation on Jetson devices."""\n\nfrom .generator import load_csm_1b, Segment, Generator\n\n__all__ = ["load_csm_1b", "Segment", "Generator"]' > /opt/csm/__init__.py

# Create directories needed at runtime
RUN mkdir -p /models /audiobook_data /books /segments

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
RUN chmod +x /entrypoint.sh /opt/csm/watermarking.py /opt/utils/* && \
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
