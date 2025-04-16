# Use DustyNV's PyTorch container for Jetson Orin (JP 6.1 / L4T r36.4.x / Ubuntu 24.04)
# Includes PyTorch 2.6 and CUDA 12.8
FROM dustynv/pytorch:2.6-r36.4.0-cu128-24.04

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    DEBIAN_FRONTEND=noninteractive \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    CONDA_DIR=/opt/conda \
    PATH="/root/.cargo/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    cmake \
    libopus-dev \
    build-essential \
    git \
    wget \
    curl \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "✓ System dependencies installed"

# Install Rust (needed for moshi/sphn)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustc --version && \
    cargo --version && \
    echo "✓ Rust installed"

# Install Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh

# Add conda to PATH
ENV PATH=$CONDA_DIR/bin:$PATH

# Create conda environment with Python 3.10
RUN conda create -y -n tts python=3.10 && \
    conda clean -ya

# Make RUN commands use the conda environment
SHELL ["conda", "run", "-n", "tts", "/bin/bash", "-c"]

# Set environment activation on interactive shells
RUN echo "conda activate tts" >> ~/.bashrc

# Create necessary directories
RUN mkdir -p /opt/csm ${AUDIOBOOK_DATA} ${BOOKS_DIR} ${MODELS_DIR} /segments

# Install Python dependencies within conda environment
RUN conda install -y -c conda-forge ffmpeg && \
    pip install --upgrade pip setuptools wheel && \
    # Install torch==2.6.0 and compatible torchvision/torchaudio from the Jetson index
    pip install torch==2.6.0 torchvision torchaudio && \
    # Install specific versions of packages known to work together
    pip install tokenizers==0.13.3 transformers==4.31.0 huggingface_hub==0.16.4 accelerate==0.25.0 && \
    pip install soundfile tqdm pydub psutil ebooklib beautifulsoup4 PyPDF2 pdfminer.six nltk && \
    # Install einops with specific version for moshi
    pip install einops==0.7.0 && \
    # Install moshi specific dependencies
    pip install "sphn>=0.1.4" sounddevice==0.5.0 && \
    # Install other dependencies
    pip install rotary_embedding_torch vector_quantize_pytorch datasets && \
    # REMOVED Install torchtune and torchao
    # pip install "torchtune<0.4.0" torchao && \
    # Install moshi (older version for compatibility)
    pip install "moshi<=0.2.2" && \
    echo "✓ Core Python dependencies installed"

# Install silentcipher for watermarking
RUN pip install "silentcipher @ git+https://github.com/SesameAILabs/silentcipher@master"

# Download essential CSM files
WORKDIR /opt/csm
RUN wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/generator.py && \
    wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/models.py && \
    echo '# CSM package\n\
from .generator import load_csm_1b, Segment, Generator\n\
__all__ = ["load_csm_1b", "Segment", "Generator"]\n\
' > /opt/csm/__init__.py

# Copy watermarking module
COPY docker/sesame-tts/utils/watermarking.py /opt/csm/
RUN chmod +x /opt/csm/watermarking.py

# Add CSM to Python path
RUN python -c "import sys; import site; print(site.getsitepackages()[0])" > /tmp/python_path && \
    echo 'import sys; sys.path.append("/opt/csm")' > $(cat /tmp/python_path)/csm_path.pth && \
    rm /tmp/python_path && \
    echo "✓ CSM added to Python path"

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')" && \
    echo "✓ NLTK punkt downloaded"

# Create a utilities directory and copy the test script
RUN mkdir -p /usr/local/bin/utils
COPY docker/sesame-tts/utils/test_csm.py /usr/local/bin/utils/
RUN chmod +x /usr/local/bin/utils/test_csm.py

# Copy the audiobook generation scripts
COPY generate_audiobook_sesame.py ${BOOKS_DIR}/
COPY generate_audiobook_sesame_epub.py ${BOOKS_DIR}/
COPY extract_chapters.py ${BOOKS_DIR}/

# Copy the entrypoint script
COPY docker/sesame-tts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set working directory
WORKDIR ${AUDIOBOOK_DATA}

# Add health check - Removed torchao import
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD conda run -n tts python -c "import torch, moshi; print('Health check passed.')" || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command - Changed to just bash
CMD ["bash"]