FROM dustynv/l4t-pytorch:r35.4.1

# Install system dependencies including curl for rustup
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    python3-pip \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Rust/Cargo
ENV PATH="/root/.cargo/bin:${PATH}"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    PyPDF2 \
    pdfminer.six \
    nltk \
    tqdm \
    pydub \
    transformers \
    huggingface_hub \
    numpy \
    scipy \
    librosa \
    soundfile \
    psutil \
    ebooklib \
    beautifulsoup4

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt')"

# --- Pre-install silentcipher with modified dependencies ---
WORKDIR /opt
# Clone silentcipher
RUN git clone https://github.com/SesameAILabs/silentcipher.git
WORKDIR /opt/silentcipher
# Relax numpy and scipy requirements in silentcipher's setup files
RUN sed -i "s/numpy>=[0-9.]*/numpy/" setup.py requirements.txt || true
RUN sed -i "s/scipy>=[0-9.]*/scipy/" setup.py requirements.txt || true
# Install the modified silentcipher globally
RUN pip install .
# --- End of silentcipher pre-installation ---

# Clone, prepare, and copy Sesame CSM source in one step
WORKDIR /opt
# Note: All commands run relative to /opt unless changed by cd
RUN git clone https://github.com/SesameAILabs/csm.git && \
    # --- Verification after clone ---
    echo "--- Verifying /opt contents after clone ---" && \
    ls -l /opt && \
    echo "--- Verifying /opt/csm contents after clone ---" && \
    ls -l /opt/csm && \
    # --- End verification ---
    # Modify files inside /opt/csm
    cd csm && \
    sed -i '/^transformers==/d' requirements.txt setup.py && \
    sed -i '/^moshi==/d' requirements.txt setup.py && \
    sed -i '/^torchtune==/d' requirements.txt setup.py && \
    sed -i '/silentcipher @ git/d' setup.py && \
    # Go back to /opt
    cd .. && \
    # Create target directory in site-packages
    mkdir -p /usr/local/lib/python3.8/dist-packages/csm && \
    # Copy Python files from /opt/csm into the target directory
    cp /opt/csm/*.py /usr/local/lib/python3.8/dist-packages/csm/ && \
    # Create an empty __init__.py to ensure it's treated as a package
    touch /usr/local/lib/python3.8/dist-packages/csm/__init__.py && \
    # Verify that the copy happened and list contents
    echo "--- Verifying CSM copy in site-packages ---" && \
    ls -l /usr/local/lib/python3.8/dist-packages/csm && \
    echo "--- Verification complete ---"

# Download the model - REMOVED FROM DOCKERFILE
# RUN python3 -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"

# Create directories for mounting volumes
RUN mkdir -p /audiobook_data /books /models

# Set working directory
WORKDIR /audiobook_data