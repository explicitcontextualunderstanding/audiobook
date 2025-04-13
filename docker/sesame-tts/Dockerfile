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

# Clone and prepare Sesame CSM source
WORKDIR /opt
RUN git clone https://github.com/SesameAILabs/csm.git && \
    cd csm && \
    # Remove specific version requirements causing conflicts
    sed -i '/^transformers==/d' requirements.txt setup.py && \
    sed -i '/^moshi==/d' requirements.txt setup.py && \
    sed -i '/^torchtune==/d' requirements.txt setup.py && \
    # Remove the silentcipher dependency line entirely from setup.py
    sed -i '/silentcipher @ git/d' setup.py

# Copy CSM source directly into site-packages
# Hardcode site-packages path for python3.8
RUN mkdir -p /usr/local/lib/python3.8/dist-packages && \
    # Copy the actual 'csm' package directory from the cloned repo
    cp -r /opt/csm/csm /usr/local/lib/python3.8/dist-packages/csm && \
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