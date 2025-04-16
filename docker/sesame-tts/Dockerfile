# Use NVIDIA's CUDA base image for Jetson Orin
FROM nvcr.io/nvidia/cuda:12.8.0-devel-ubuntu22.04

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
    CONDA_DIR=/opt/conda

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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "✓ System dependencies installed"

# Install Miniconda
# Use the aarch64 installer for Jetson (ARM architecture)
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
    pip install -U torch torchvision torchaudio \
    tokenizers transformers huggingface_hub accelerate \
    soundfile tqdm pydub psutil ebooklib beautifulsoup4 \
    PyPDF2 pdfminer.six nltk einops rotary_embedding_torch \
    vector_quantize_pytorch datasets && \
    pip install torchtune torchao moshi && \
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

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD conda run -n tts python -c "import torch, torchao, moshi; print('Health check passed.')" || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["conda", "run", "--no-capture-output", "-n", "tts", "bash"]