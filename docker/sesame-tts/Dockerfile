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
# Add ffmpeg, libsndfile1, python3-pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    python3-pip \
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

# Upgrade pip and install core dependencies
# NOTE: PyTorch and torchao are provided by the base image, but torchaudio is not
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
    # Install torchaudio explicitly - will use the custom pip server
    torchaudio \
    && echo "✓ Core Python dependencies installed" \
    # Verify imports and check versions
    && python3 -c "import torch; print(f'✓ PyTorch version: {torch.__version__}')" \
    && python3 -c "import torchaudio; print(f'✓ Torchaudio version: {torchaudio.__version__}')" \
    && python3 -c "import torchao; print(f'✓ torchao version: {torchao.__version__}')" \
    && python3 -c "import transformers; print(f'✓ Transformers version: {transformers.__version__}')"

# Install CSM additional dependencies (with fallbacks for packages that might fail)
RUN pip3 install --no-cache-dir einops && \
    echo "✓ Installed einops: $(pip show einops | grep Version)" || echo "Warning: Failed to install einops" && \
    pip3 install --no-cache-dir rotary_embedding_torch && \
    echo "✓ Installed rotary_embedding_torch: $(pip show rotary_embedding_torch | grep Version)" || echo "Warning: Failed to install rotary_embedding_torch" && \
    pip3 install --no-cache-dir vector_quantize_pytorch && \
    echo "✓ Installed vector_quantize_pytorch: $(pip show vector_quantize_pytorch | grep Version)" || echo "Warning: Failed to install vector_quantize_pytorch" && \
    pip3 install --no-cache-dir datasets && \
    echo "✓ Installed datasets: $(pip show datasets | grep Version)" || echo "Warning: Failed to install datasets"

# Install silentcipher (trying PyPI first, then GitHub)
RUN pip3 install --no-cache-dir silentcipher && \
    echo "✓ Installed silentcipher from PyPI: $(pip show silentcipher | grep Version)" || \
    (export GIT_TERMINAL_PROMPT=0 && pip3 install --no-cache-dir git+https://github.com/SesameAILabs/silentcipher.git@master && \
    echo "✓ Installed silentcipher from GitHub") || \
    echo "Warning: Failed to install silentcipher. Some watermarking features might not work."

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

# Create a script to test CSM
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import sys\n\
import logging\n\
from pathlib import Path\n\
\n\
# Configure logging\n\
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")\n\
logger = logging.getLogger("test_csm")\n\
\n\
try:\n\
    import torch\n\
    import torchaudio\n\
    import torchao # Verify torchao import\n\
    # Try multiple import paths for flexibility\n\
    try:\n\
        from csm import load_csm_1b, Segment\n\
        logger.info("Successfully imported from csm package")\n\
    except ImportError:\n\
        # Direct import from module path\n\
        sys.path.insert(0, "/opt/csm")\n\
        from generator import load_csm_1b, Segment\n\
        logger.info("Successfully imported directly from generator.py")\n\
    \n\
    logger.info("CSM imports successful")\n\
    \n\
    # Determine device\n\
    device = "cuda" if torch.cuda.is_available() else "cpu"\n\
    logger.info(f"Using device: {device}")\n\
    \n\
    # Get model path from argument or use default\n\
    model_path = sys.argv[1] if len(sys.argv) > 1 else "/models/sesame-csm-1b"\n\
    \n\
    # Verify model path exists\n\
    if not os.path.exists(model_path):\n\
        logger.error(f"Model path does not exist: {model_path}")\n\
        sys.exit(1)\n\
    \n\
    # Load the model\n\
    logger.info(f"Loading CSM model from {model_path}...")\n\
    generator = load_csm_1b(model_path=model_path, device=device)\n\
    \n\
    # Generate test audio\n\
    text = "This is a test of the CSM text to speech system."\n\
    logger.info(f"Generating speech for: \\"{text}\\"")\n\
    audio = generator.generate(text=text)\n\
    \n\
    # Save the audio\n\
    output_file = Path("/audiobook_data/test_sample.wav")\n\
    torchaudio.save(output_file, audio.unsqueeze(0).cpu(), generator.sample_rate)\n\
    logger.info(f"Test audio saved to {output_file}")\n\
    \n\
    logger.info("✅ Test completed successfully!")\n\
\n\
except Exception as e:\n\
    logger.error(f"❌ Error: {e}")\n\
    import traceback\n\
    traceback.print_exc()\n\
    sys.exit(1)\n\
' > /usr/local/bin/utils/test_csm.py && chmod +x /usr/local/bin/utils/test_csm.py && \
    echo "✓ Test script created"

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
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import torch, torchaudio, torchao, csm; print('Health check passed.')" || exit 1

# Print build completion message
RUN echo "✓ Sesame-TTS container build completed successfully!"

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["bash"]