#!/bin/bash
# Make the script executable
chmod +x "$0"
# setup_multistage.sh
# Sets up the multi-stage Dockerfile approach for better dependency management

set -e

echo "==== Setting up Multi-Stage Dockerfile for Improved Dependency Management ===="
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE="${REPO_ROOT}/docker/sesame-tts/Dockerfile"
DOCKERFILE_BACKUP="${REPO_ROOT}/docker/sesame-tts/Dockerfile.bak.$(date +%Y%m%d%H%M%S)"
REQUIREMENTS_TXT="${REPO_ROOT}/docker/sesame-tts/requirements.txt"
REQUIREMENTS_IN="${REPO_ROOT}/docker/sesame-tts/requirements.in"

# Check if files exist
if [ ! -f "${DOCKERFILE}" ]; then
    echo "Error: Dockerfile not found at ${DOCKERFILE}"
    exit 1
fi

if [ ! -f "${REQUIREMENTS_TXT}" ]; then
    echo "Error: requirements.txt not found at ${REQUIREMENTS_TXT}"
    exit 1
fi

# Backup the original Dockerfile
echo "Backing up original Dockerfile to ${DOCKERFILE_BACKUP}"
cp "${DOCKERFILE}" "${DOCKERFILE_BACKUP}"
echo "Backup created successfully"

# Create requirements.in from requirements.txt if it doesn't exist
if [ ! -f "${REQUIREMENTS_IN}" ]; then
    echo "Creating requirements.in from requirements.txt..."
    cp "${REQUIREMENTS_TXT}" "${REQUIREMENTS_IN}"
    echo "Created ${REQUIREMENTS_IN}"
fi

# Generate the new multi-stage Dockerfile
echo "Generating new multi-stage Dockerfile..."

cat > "${DOCKERFILE}" << 'EOF'
# Optimized Dockerfile for faster build times with BuildKit
# Use with: DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson .
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
    # Add Cargo to PATH for Rust compilation
    CARGO_HOME=/root/.cargo \
    PATH="/root/.cargo/bin:${PATH}"

# Install pip-tools and essential build tools including Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip git curl build-essential && \
    pip install pip-tools && \
    # Install Rust toolchain
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y && \
    # Verify cargo installation
    cargo --version && \
    rm -rf /var/lib/apt/lists/*

# Configure pip to use Jetson-optimized wheels (helps resolver find compatible versions)
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 120" >> ~/.config/pip/pip.conf && \
    echo "retries = 5" >> ~/.config/pip/pip.conf

# Copy requirements.in to generate the lock file
COPY docker/sesame-tts/requirements.in .

# Generate the lock file with backtracking resolver
# Use --verbose flag for more detailed output if needed
RUN pip-compile --resolver=backtracking --output-file=requirements.lock.txt requirements.in && \
    # Verify the lock file was created
    test -f requirements.lock.txt || (echo "Failed to generate requirements.lock.txt" && exit 1)

# ============================================================================
# WHEEL BUILDER STAGE: Build or download all required wheels
# ============================================================================
FROM ${BASE_IMAGE} AS wheel-builder

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
    build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Configure pip for faster installations
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 60" >> ~/.config/pip/pip.conf && \
    echo "retries = 3" >> ~/.config/pip/pip.conf

# Copy the lock file from the resolver stage
COPY --from=resolver requirements.lock.txt .

# Download wheels to a dedicated directory
RUN --mount=type=cache,target=/root/.cache/pip \
    mkdir -p /wheels && \
    pip wheel --wheel-dir=/wheels -r requirements.lock.txt

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

# Copy the lock file and wheels from the wheel-builder stage
COPY --from=resolver requirements.lock.txt .
COPY --from=wheel-builder /wheels /wheels

# Install Miniconda and set up the environment
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o Miniconda3.sh && \
    bash Miniconda3.sh -b -p /opt/conda && \
    rm Miniconda3.sh && \
    /opt/conda/bin/conda config --set channel_priority flexible && \
    /opt/conda/bin/conda config --set pip_interop_enabled True && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda create -y -n tts python=3.12 pip setuptools wheel && \
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

# Activate conda environment and install dependencies from wheels
SHELL ["/bin/bash", "-c"]
RUN source /opt/conda/bin/activate tts && \
    python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --find-links=/wheels -r requirements.lock.txt && \
    rm -rf /wheels

# Verify critical dependencies are correctly installed
RUN source /opt/conda/bin/activate tts && \
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')" && \
    python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}')" && \
    python -c "import torchaudio; print(f'TorchAudio version: {torchaudio.__version__}')" && \
    python -c "import vector_quantize_pytorch; print('Vector Quantize PyTorch installed successfully')" && \
    python -c "import torchao; import torchtune; import moshi; print('All imports successful')"

# Generate environment documentation
RUN source /opt/conda/bin/activate tts && \
    mkdir -p /opt/environment_info && \
    python -c "import sys, platform, torch; print(f'Python {sys.version}\\nPlatform: {platform.platform()}\\nPyTorch: {torch.__version__} (CUDA available: {torch.cuda.is_available()})')" > /opt/environment_info/environment.txt && \
    pip freeze > /opt/environment_info/frozen_deps.txt && \
    pip list --format=freeze > /opt/environment_info/explicit_deps.txt

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
COPY --from=builder /opt/environment_info /opt/environment_info

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
EOF

echo "New multi-stage Dockerfile created!"

# Create a basic requirements.in template if one doesn't exist
if [ ! -f "${REQUIREMENTS_IN}" ]; then
    echo "Creating a template requirements.in file..."
    cat > "${REQUIREMENTS_IN}" << 'EOF'
# Core PyTorch - pinned for compatibility with Jetson
torch==2.2.0
torchvision==0.17.0
torchaudio==2.2.0

# Transformers & Tokenizers - minimal versions to reduce download size
tokenizers>=0.13.3
transformers>=4.31.0
huggingface_hub>=0.16.4
accelerate>=0.25.0

# Audio processing
soundfile>=0.12.1
pydub>=0.25.1
sounddevice>=0.5.0

# Text extraction & NLP
ebooklib>=0.18.0
beautifulsoup4>=4.12.2
PyPDF2>=3.0.1
pdfminer.six>=20221105
nltk>=3.8.1

# Core packages with specific version requirements
vector_quantize_pytorch==1.22.15  # Must use this version for compatibility
torchtune==0.3.0                  # Performance-critical component
torchao==0.1.0                    # Performance-critical component
moshi==0.2.2                      # Required for model interface

# Other utilities
einops>=0.8.0                    # Updated for compatibility
rotary_embedding_torch>=0.2.5
datasets>=2.16.1
triton>=2.1.0

# System utils
tqdm>=4.66.1
psutil>=5.9.6
EOF
    echo "Template requirements.in created"
else
    echo "Using existing requirements.in file"
fi

# Create a build script
echo "Creating a build script..."
BUILD_SCRIPT="${REPO_ROOT}/scripts/dependency/build.sh"
cat > "${BUILD_SCRIPT}" << 'EOF'
#!/bin/bash
# build.sh
# Script to build the Docker container with improved dependency management

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE="${REPO_ROOT}/docker/sesame-tts/Dockerfile"

# Parse arguments
USE_BUILDKIT=1
CACHE=1
VERBOSE=0

for arg in "$@"; do
  case $arg in
    --no-buildkit)
      USE_BUILDKIT=0
      shift
      ;;
    --no-cache)
      CACHE=0
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --help)
      echo "Usage: $0 [--no-buildkit] [--no-cache] [--verbose]"
      echo "  --no-buildkit  : Disable BuildKit"
      echo "  --no-cache     : Disable caching"
      echo "  --verbose      : Show detailed build output"
      exit 0
      ;;
  esac
done

# Set BuildKit
if [ $USE_BUILDKIT -eq 1 ]; then
  export DOCKER_BUILDKIT=1
  echo "BuildKit enabled"
else
  export DOCKER_BUILDKIT=0
  echo "BuildKit disabled"
fi

# Set cache options
CACHE_OPT=""
if [ $CACHE -eq 0 ]; then
  CACHE_OPT="--no-cache"
  echo "Cache disabled"
else
  echo "Cache enabled"
fi

# Set progress options
PROGRESS_OPT="--progress=auto"
if [ $VERBOSE -eq 1 ]; then
  PROGRESS_OPT="--progress=plain"
  echo "Verbose output enabled"
fi

echo "Building Docker container..."
docker build $CACHE_OPT $PROGRESS_OPT \
  -t sesame-tts-jetson \
  -f $DOCKERFILE \
  $REPO_ROOT

echo "Build complete!"
echo "You can run the container with:"
echo "docker run --runtime nvidia -it --rm --name sesame-tts \\"
echo "  --volume ~/audiobook_data:/audiobook_data \\"
echo "  --volume ~/audiobook:/books \\"
echo "  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \\"
echo "  sesame-tts-jetson"
EOF

chmod +x "${BUILD_SCRIPT}"
echo "Build script created at ${BUILD_SCRIPT}"

echo ""
echo "====== Setup Complete ======"
echo "The multi-stage Dockerfile has been created and your original Dockerfile has been backed up."
echo ""
echo "Next steps:"
echo "1. Review the generated requirements.in file and adjust as needed."
echo "2. Run the dependency analysis script to check for potential issues:"
echo "   ./scripts/dependency/analyze.sh"
echo "3. Build the container using the new build script:"
echo "   ./scripts/dependency/build.sh"
echo ""
echo "For more information, see the dependency management guide at:"
echo "   ./docs/dependency-management-guide.md"
