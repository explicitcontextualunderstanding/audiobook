FROM dustynv/l4t-pytorch:r35.4.1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    PATH="/root/.cargo/bin:${PATH}" \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    python3-pip \
    git \
    wget \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Rust/Cargo (needed for some Python dependencies)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Create necessary directories
RUN mkdir -p /opt/csm /audiobook_data /books /models

# Upgrade pip and install core dependencies
# We use the base image's PyTorch installation instead of reinstalling
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
    nltk

# Install CSM additional dependencies (with fallbacks for packages that might fail)
RUN pip3 install --no-cache-dir einops || echo "Warning: Failed to install einops" && \
    pip3 install --no-cache-dir rotary_embedding_torch || echo "Warning: Failed to install rotary_embedding_torch" && \
    pip3 install --no-cache-dir vector_quantize_pytorch || echo "Warning: Failed to install vector_quantize_pytorch" && \
    pip3 install --no-cache-dir datasets || echo "Warning: Failed to install datasets"

# Install silentcipher (trying PyPI first, then GitHub)
RUN pip3 install --no-cache-dir silentcipher || \
    pip3 install --no-cache-dir git+https://github.com/SesameAILabs/silentcipher.git@master || \
    echo "Warning: Failed to install silentcipher. Some watermarking features might not work."

# Download essential CSM files instead of cloning the full repository
WORKDIR /opt/csm
RUN wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/generator.py && \
    wget -q https://raw.githubusercontent.com/SesameAILabs/csm/main/models.py 

# Create simple Python module to make imports work
RUN echo '# CSM package\n\
from .generator import load_csm_1b, Segment, Generator\n\
__all__ = ["load_csm_1b", "Segment", "Generator"]\n\
' > /opt/csm/__init__.py

# Add CSM to Python path directly instead of installing it
RUN echo 'import sys; sys.path.append("/opt/csm")' > /usr/local/lib/python3.8/dist-packages/csm_path.pth

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt')"

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
    logger.info(f"Generating speech for: \"{text}\"")\n\
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
' > /usr/local/bin/utils/test_csm.py && chmod +x /usr/local/bin/utils/test_csm.py

# Create entrypoint script with fixed syntax
RUN echo '#!/bin/bash\n\
\n\
echo "=================================================="\n\
echo "Sesame CSM Audiobook Generator for Jetson"\n\
echo "=================================================="\n\
echo ""\n\
echo "Available commands:"\n\
echo ""\n\
echo "  • Test CSM installation:"\n\
echo "    python /usr/local/bin/utils/test_csm.py /models/sesame-csm-1b"\n\
echo ""\n\
echo "  • Generate audiobook:"\n\
echo "    python /books/generate_audiobook_sesame.py \\"\n\
echo "      --input /books/your_book.epub \\"\n\
echo "      --output /audiobook_data/audiobook.mp3 \\"\n\
echo "      --model_path /models/sesame-csm-1b"\n\
echo ""\n\
echo "Volume mounts:"\n\
echo "  • /models/sesame-csm-1b: Model files"\n\
echo "  • /books: Source books"\n\
echo "  • /audiobook_data: Output directory"\n\
echo ""\n\
echo "=================================================="\n\
\n\
exec "$@"\n\
' > /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

# Set working directory
WORKDIR /audiobook_data

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["bash"]