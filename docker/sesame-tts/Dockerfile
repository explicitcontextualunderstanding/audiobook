# Use the official torchao image for JetPack 6.1+ (L4T r36.4.0)
# Includes PyTorch 2.6, CUDA 12.8, torchao 0.11.0
ARG BASE_IMAGE=dustynv/torchao:0.11.0-r36.4.0-cu128-24.04
FROM ${BASE_IMAGE}

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# This image is based on JetPack 6.1+ (L4T r36.4.x) with Ubuntu 24.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    PATH="/root/.cargo/bin:${PATH}" \
    DEBIAN_FRONTEND=noninteractive \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    # Explicitly set the pip index URL to use the Jetson pip server
    PIP_INDEX_URL=https://pypi.jetson-ai-lab.dev/jp6/cu128

# Install system dependencies (git, wget, curl, unzip already in base)
# Add ffmpeg, libsndfile1, python3-pip, cmake, libopus-dev, build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    python3-pip \
    # Add cmake and libopus-dev for building dependencies like sphn (via audiopus_sys)
    cmake \
    libopus-dev \
    # Add build-essential for packages needing compilation
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "✓ System dependencies installed"

# Install Rust/Cargo (needed for some Python dependencies)
# Rust/Cargo might already be in the base, but installing ensures it's present
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && echo "✓ Rust installed: $(rustc --version)"

# Build dependencies (cmake, ninja-build) are no longer needed for torchao

# Create necessary directories
RUN mkdir -p /opt/csm ${AUDIOBOOK_DATA} ${BOOKS_DIR} ${MODELS_DIR} \
    && echo "✓ Directories created"

# Check if torchaudio is already in the base image
RUN python3 -c "import torchaudio; print(f'✓ Torchaudio version found in base: {torchaudio.__version__}')" || \
    echo "✓ Torchaudio not found in base image, will attempt install."

# Upgrade pip and install core dependencies
# NOTE: PyTorch and torchao are provided by the base image. Torchaudio might be.
# Rely on base image for triton if needed by torchao. Remove moshi.
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    tokenizers \
    transformers \
    huggingface_hub \
    accelerate \
    soundfile \
    tqdm \
    pydub \
    psutil \
    ebooklib \
    beautifulsoup4 \
    PyPDF2 \
    pdfminer.six \
    nltk \
    # Attempt to install torchaudio==2.6.0 only if not found in base
    && (python3 -c "import torchaudio" || pip3 install --no-cache-dir torchaudio==2.6.0 || echo "⚠️ Warning: Failed to install torchaudio==2.6.0") \
    && echo "✓ Core Python dependencies installed" \
    # Verify imports and check versions
    && python3 -c "import torch; print(f'✓ PyTorch version: {torch.__version__}')" \
    && python3 -c "import torch; print(f'✓ PyTorch CUDA version: {torch.version.cuda}')" \
    && python3 -c "import torchao; print(f'✓ torchao version: {torchao.__version__}')" \
    && python3 -c "import transformers; print(f'✓ Transformers version: {transformers.__version__}')" \
    # Verify torchaudio import again after potential install
    && (python3 -c "import torchaudio; print(f'✓ Torchaudio version: {torchaudio.__version__}')" || echo "⚠️ Warning: Torchaudio import failed after install attempt")

# Install CSM additional dependencies (with fallbacks for packages that might fail)
RUN pip3 install --no-cache-dir einops && \
    echo "✓ Installed einops: $(pip show einops | grep Version)" || echo "Warning: Failed to install einops" && \
    pip3 install --no-cache-dir rotary_embedding_torch && \
    echo "✓ Installed rotary_embedding_torch: $(pip show rotary_embedding_torch | grep Version)" || echo "Warning: Failed to install rotary_embedding_torch" && \
    pip3 install --no-cache-dir vector_quantize_pytorch && \
    echo "✓ Installed vector_quantize_pytorch: $(pip show vector_quantize_pytorch | grep Version)" || echo "Warning: Failed to install vector_quantize_pytorch" && \
    pip3 install --no-cache-dir datasets && \
    echo "✓ Installed datasets: $(pip show datasets | grep Version)" || echo "Warning: Failed to install datasets"

# Remove the redundant torchaudio installation block below
# RUN pip3 install --no-cache-dir torchaudio==2.6.0 && \
#    ... (removed) ...

# torchao is included in the base image - no manual installation needed

# Install torchtune (try PyPI first, then GitHub)
# Fail build if this step fails
RUN (pip3 install --no-cache-dir torchtune && \
     echo "✓ Installed torchtune from PyPI: $(pip show torchtune | grep Version)") || \
    (export GIT_TERMINAL_PROMPT=0 && \
     pip3 install --no-cache-dir git+https://github.com/pytorch/torchtune.git && \
     echo "✓ Installed torchtune from GitHub") || \
    (echo "ERROR: Failed to install torchtune from both PyPI and GitHub." && exit 1)


# Download essential CSM files instead of cloning the full repository
WORKDIR /opt/csm
RUN wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/generator.py && \
    wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/models.py && \
    echo "✓ CSM files downloaded"

# Create simple Python module to make imports work
RUN echo '# CSM package\n\
from .generator import load_csm_1b, Segment, Generator\n\
__all__ = ["load_csm_1b", "Segment", "Generator"]\n\
' > /opt/csm/__init__.py

# Add CSM to Python path directly instead of installing it
RUN python3 -c "import sys; import site; print(site.getsitepackages()[0])" > /tmp/python_path && \
    echo 'import sys; sys.path.append("/opt/csm")' > $(cat /tmp/python_path)/csm_path.pth && \
    rm /tmp/python_path && \
    echo "✓ CSM added to Python path"

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt')" && \
    echo "✓ NLTK punkt downloaded"

# Create a utilities directory
RUN mkdir -p /usr/local/bin/utils

# Copy the test script from the repository
COPY docker/sesame-tts/utils/test_csm.py /usr/local/bin/utils/
RUN chmod +x /usr/local/bin/utils/test_csm.py && \
    echo "✓ Test script copied"

# Verify CUDA is available
RUN echo "✓ CUDA Availability: $(python3 -c "import torch; print(torch.cuda.is_available())")" && \
    echo "✓ CUDA Version: $(python3 -c "import torch; print(torch.version.cuda if torch.cuda.is_available() else 'Not available')")" && \
    echo "✓ Device Count: $(python3 -c "import torch; print(torch.cuda.device_count())")"

# Copy the entrypoint script
COPY docker/sesame-tts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    echo "✓ Entrypoint script installed"

# Set working directory
WORKDIR ${AUDIOBOOK_DATA}

# Add health check to ensure container is functioning properly
# Remove moshi and triton checks
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import torch, torchaudio, torchao, csm; print('Health check passed.')" || exit 1

# Print build completion message
RUN echo "✓ Sesame-TTS container build completed successfully!"

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["bash"]