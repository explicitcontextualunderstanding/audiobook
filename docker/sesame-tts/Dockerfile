FROM dustynv/l4t-pytorch:r35.4.1

# Install system dependencies including curl, git (still needed for pip?), and unzip
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    python3-pip \
    git \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Rust/Cargo
ENV PATH="/root/.cargo/bin:${PATH}"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install base Python dependencies (already included: transformers, torch, torchaudio, numpy, scipy, librosa, soundfile)
RUN pip3 install --no-cache-dir \
    PyPDF2 \
    pdfminer.six \
    nltk \
    tqdm \
    pydub \
    huggingface_hub \
    psutil \
    ebooklib \
    beautifulsoup4

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt')"

# --- Pre-install silentcipher with modified dependencies ---
WORKDIR /opt
# Download and unzip silentcipher
RUN curl -L -o silentcipher.zip https://github.com/SesameAILabs/silentcipher/archive/refs/heads/main.zip && \
    unzip silentcipher.zip && \
    rm silentcipher.zip && \
    # Rename extracted folder (usually repo-branch)
    mv silentcipher-main silentcipher

WORKDIR /opt/silentcipher
# Relax numpy and scipy requirements in silentcipher's setup files
RUN sed -i "s/numpy>=[0-9.]*/numpy/" setup.py requirements.txt || true
RUN sed -i "s/scipy>=[0-9.]*/scipy/" setup.py requirements.txt || true
RUN pip install .
# --- End silentcipher ---

# --- Install CSM dependencies and CSM itself ---
WORKDIR /opt
# Download, unzip, and install mimi locally
RUN curl -L -o mimi.zip https://github.com/SesameAILabs/mimi/archive/refs/heads/main.zip && \
    unzip mimi.zip && \
    rm mimi.zip && \
    # Rename extracted folder
    mv mimi-main mimi && \
    cd mimi && \
    pip install . && \
    cd .. && \
    rm -rf mimi # Clean up extracted repo after install

# Install other specific CSM dependencies
RUN pip install einops rotary_embedding_torch vector_quantize_pytorch xformers accelerate

# Download and unzip CSM repo
RUN curl -L -o csm.zip https://github.com/SesameAILabs/csm/archive/refs/heads/main.zip && \
    unzip csm.zip && \
    rm csm.zip && \
    # Rename extracted folder
    mv csm-main csm

WORKDIR /opt/csm
# Remove dependencies we installed manually or are in the base image from setup.py
RUN sed -i '/^transformers/d' setup.py && \
    sed -i '/^torch/d' setup.py && \
    sed -i '/^torchaudio/d' setup.py && \
    sed -i '/^numpy/d' setup.py && \
    sed -i '/^scipy/d' setup.py && \
    sed -i '/^librosa/d' setup.py && \
    sed -i '/^soundfile/d' setup.py && \
    sed -i '/^einops/d' setup.py && \
    sed -i '/^rotary_embedding_torch/d' setup.py && \
    sed -i '/^vector_quantize_pytorch/d' setup.py && \
    sed -i '/^xformers/d' setup.py && \
    sed -i '/^accelerate/d' setup.py && \
    sed -i '/mimi @ git/d' setup.py && \
    sed -i '/silentcipher @ git/d' setup.py

# Install CSM in editable mode (adds /opt/csm to path implicitly for the build)
RUN pip install -e .
# --- End CSM ---

# Create directories for mounting volumes
RUN mkdir -p /audiobook_data /books /models

# Set working directory
WORKDIR /audiobook_data