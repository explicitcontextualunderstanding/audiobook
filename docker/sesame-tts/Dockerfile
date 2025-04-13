FROM dustynv/l4t-pytorch:r35.4.1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.cargo/bin:${PATH}" \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    python3-pip \
    python3-venv \
    git \
    wget \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Rust/Cargo (required for silentcipher dependency)
RUN wget -q -O - https://sh.rustup.rs | sh -s -- -y

# Disable Triton compilation which can cause issues on Jetson
ENV NO_TORCH_COMPILE=1

# Create directory for CSM code
RUN mkdir -p /opt/csm

# Install Python dependencies with exact versions from CSM's requirements.txt
# Avoid git clone by installing packages through pip
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    torch==2.4.0 \
    torchaudio==2.4.0 \
    tokenizers==0.21.0 \
    transformers==4.49.0 \
    huggingface_hub==0.28.1 \
    moshi==0.2.2 \
    torchtune==0.4.0 \
    torchao==0.9.0

# Handle silentcipher - try PyPI first, fall back to minimal git clone if needed
RUN pip3 install --no-cache-dir silentcipher || \
    (mkdir -p /tmp/silentcipher && \
     cd /tmp/silentcipher && \
     git init && \
     git remote add origin https://github.com/SesameAILabs/silentcipher.git && \
     git fetch --depth 1 origin master && \
     git checkout FETCH_HEAD && \
     pip install . && \
     cd / && \
     rm -rf /tmp/silentcipher)

# Install additional dependencies needed for audiobook generation
RUN pip3 install --no-cache-dir \
    PyPDF2 \
    pdfminer.six \
    nltk \
    tqdm \
    pydub \
    psutil \
    ebooklib \
    beautifulsoup4 \
    einops \
    rotary_embedding_torch \
    vector_quantize_pytorch \
    accelerate \
    soundfile \
    datasets[audio]

# Download key CSM files instead of cloning the whole repo
WORKDIR /opt/csm
RUN wget -q https://raw.githubusercontent.com/SesameAILabs/csm/2d720827843b653c4d67bb4445b1c0a4f59e646f/generator.py && \
    wget -q https://raw.githubusercontent.com/SesameAILabs/csm/2d720827843b653c4d67bb4445b1c0a4f59e646f/models.py && \
    wget -q https://raw.githubusercontent.com/SesameAILabs/csm/2d720827843b653c4d67bb4445b1c0a4f59e646f/setup.py

# Create an __init__.py file to make the directory a Python package
RUN touch __init__.py && \
    echo 'from .generator import load_csm_1b, Segment, Generator' > __init__.py

# Install the package in development mode with minimal files
WORKDIR /opt/csm
RUN pip install -e .

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt')"

# Create directories for mounting volumes
RUN mkdir -p /audiobook_data /books /models

# Create a compatibility module for newer CSM API
RUN echo '"""\nCompatibility module for CSM API changes\n"""\n\
import os\n\
import sys\n\
import torch\n\
import logging\n\
from pathlib import Path\n\
\n\
# Setup logging\n\
logging.basicConfig(level=logging.INFO)\n\
logger = logging.getLogger("csm_compat")\n\
\n\
# Add the CSM module path if present\n\
if os.path.exists("/opt/csm"):\n\
    sys.path.insert(0, "/opt/csm")\n\
\n\
try:\n\
    # Try to import directly from the downloaded files\n\
    from generator import load_csm_1b as _original_load_csm_1b, Segment, Generator\n\
    logger.info("Using direct generator.py imports")\n\
except ImportError as e:\n\
    logger.error(f"Failed to import from generator.py: {e}")\n\
    # Fallback implementation\n\
    from dataclasses import dataclass\n\
    import torch\n\
    \n\
    @dataclass\n\
    class Segment:\n\
        text: str\n\
        speaker: int = 0\n\
        audio: torch.Tensor = None\n\
    \n\
    class Generator:\n\
        def __init__(self):\n\
            self.sample_rate = 24000\n\
        \n\
        def generate(self, text, speaker=0, context=None, max_audio_length_ms=10000):\n\
            logger.error("Placeholder Generator - no real implementation available")\n\
            # Return empty audio of correct shape\n\
            return torch.zeros(int(self.sample_rate * max_audio_length_ms / 1000))\n\
    \n\
    def _original_load_csm_1b(model_path, device="cuda"):\n\
        logger.error("Placeholder load_csm_1b - no real implementation available")\n\
        return Generator()\n\
\n\
def load_csm_1b(model_path=None, device="cuda"):\n\
    """\n\
    Compatible loader that handles API changes between versions\n\
    """\n\
    logger.info(f"Loading CSM model from {model_path} on {device}")\n\
    \n\
    try:\n\
        # Original loading function from generator.py\n\
        return _original_load_csm_1b(model_path=model_path, device=device)\n\
        \n\
    except Exception as e:\n\
        logger.error(f"Error loading CSM model: {e}")\n\
        raise\n\
\n\
__all__ = ["load_csm_1b", "Segment", "Generator"]\n\
' > /opt/csm/csm_compat.py

# Create an __init__.py to re-export from the compatibility module
RUN echo 'from .csm_compat import load_csm_1b, Segment, Generator\n\
__all__ = ["load_csm_1b", "Segment", "Generator"]\n\
' > /opt/csm/__init__.py

# Create an optimized script to test CSM
RUN echo '#!/usr/bin/env python3\n\
import sys\n\
import torch\n\
import torchaudio\n\
import os\n\
import importlib.util\n\
from pathlib import Path\n\
\n\
# Add CSM root to path\n\
if os.path.exists("/opt/csm"):\n\
    sys.path.insert(0, "/opt/csm")\n\
\n\
try:\n\
    # First try to import from CSM package\n\
    try:\n\
        from csm import load_csm_1b, Segment\n\
        print("Successfully imported from csm package")\n\
    except ImportError:\n\
        # Fall back to importing directly from generator.py\n\
        print("Falling back to direct generator.py import")\n\
        if os.path.exists("/opt/csm/generator.py"):\n\
            sys.path.insert(0, "/opt/csm")\n\
            from generator import load_csm_1b, Segment\n\
        else:\n\
            raise ImportError("Could not find generator.py or csm package")\n\
    \n\
    device = "cuda" if torch.cuda.is_available() else "cpu"\n\
    print(f"\\nUsing device: {device}\\n")\n\
    \n\
    # Path to model\n\
    model_path = sys.argv[1] if len(sys.argv) > 1 else "/models/sesame-csm-1b"\n\
    print(f"Loading model from: {model_path}")\n\
    \n\
    # Check if model exists\n\
    if not os.path.exists(model_path):\n\
        print(f"ERROR: Model path {model_path} does not exist!")\n\
        print("Make sure you have mounted the model directory correctly.")\n\
        sys.exit(1)\n\
    \n\
    # Load model\n\
    print("Initializing CSM model...")\n\
    generator = load_csm_1b(model_path=model_path, device=device)\n\
    print(f"Model loaded successfully. Sample rate: {generator.sample_rate}")\n\
    \n\
    # Test generate a short sample\n\
    print("\\nGenerating test audio...")\n\
    output_file = Path("/audiobook_data/test_sample.wav")\n\
    \n\
    # Get voice presets if available\n\
    preset_dir = Path(model_path) / "prompts"\n\
    presets = list(preset_dir.glob("*.wav")) if preset_dir.exists() else []\n\
    if presets:\n\
        print(f"Available voice presets: {[p.stem for p in presets]}")\n\
    else:\n\
        print("No voice presets found")\n\
    \n\
    # Test generate with simple text\n\
    text = "This is a test of the CSM text to speech system."\n\
    print(f"Generating speech for text: \\\"{text}\\\"")\n\
    audio = generator.generate(text=text)\n\
    \n\
    # Save the audio\n\
    torchaudio.save(output_file, audio.unsqueeze(0).cpu(), generator.sample_rate)\n\
    print(f"Test audio saved to {output_file}")\n\
    \n\
    # Success\n\
    print("\\n✅ CSM is working correctly!")\n\
    \n\
except Exception as e:\n\
    print(f"\\n❌ Error testing CSM: {e}")\n\
    import traceback\n\
    traceback.print_exc()\n\
    \n\
    # Print more diagnostic information\n\
    print("\\nDiagnostic information:")\n\
    print(f"Python version: {sys.version}")\n\
    print(f"Torch version: {torch.__version__}")\n\
    print(f"CUDA available: {torch.cuda.is_available()}")\n\
    if torch.cuda.is_available():\n\
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")\n\
    \n\
    sys.exit(1)\n\
' > /usr/local/bin/test_csm.py && chmod +x /usr/local/bin/test_csm.py

# Create a helper script for usage instructions
RUN echo '#!/bin/bash\n\
echo "=================================================="\n\
echo "Sesame CSM Audiobook Generation Container"\n\
echo "=================================================="\n\
echo ""\n\
echo "This container includes Sesame CSM (Conversational Speech Model)"\n\
echo "optimized for audiobook generation on Jetson Orin Nano."\n\
echo ""\n\
echo "KEY REQUIREMENTS:"\n\
echo " 1. Hugging Face access to models:"\n\
echo "    - sesame/csm-1b"\n\
echo "    - meta-llama/Llama-3.2-1B"\n\
echo ""\n\
echo "QUICK COMMANDS:"\n\
echo " - Test CSM installation:"\n\
echo "   python /usr/local/bin/test_csm.py /models/sesame-csm-1b"\n\
echo ""\n\
echo " - Generate audiobook:"\n\
echo "   python /books/generate_audiobook_sesame.py \\"\n\
echo "     --input /books/your_book.epub \\"\n\
echo "     --output /audiobook_data/audiobook.mp3 \\"\n\
echo "     --model_path /models/sesame-csm-1b \\"\n\
echo "     --voice_preset calm"\n\
echo ""\n\
echo "TROUBLESHOOTING:"\n\
echo " - If model loading fails, ensure you have:"\n\
echo "   1. Logged in to Hugging Face: huggingface-cli login"\n\
echo "   2. Accepted terms for meta-llama/Llama-3.2-1B on HF website"\n\
echo "   3. Mounted your HF cache directory correctly"\n\
echo ""\n\
echo "IMPORTANT VOLUME MOUNTS:"\n\
echo " - /models/sesame-csm-1b: Mount the downloaded model files here"\n\
echo " - /books: Mount directory containing your books"\n\
echo " - /audiobook_data: Mount directory to save output files"\n\
echo " - \${HOME}/.cache/huggingface:/root/.cache/huggingface: For HF credentials"\n\
echo ""\n\
echo "EXAMPLE DOCKER RUN COMMAND:"\n\
echo "docker run --runtime nvidia -it --rm \\"\n\
echo "  --volume ~/audiobook_data:/audiobook_data \\"\n\
echo "  --volume ~/audiobook:/books \\"\n\
echo "  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \\"\n\
echo "  --volume \${HOME}/.cache/huggingface:/root/.cache/huggingface \\"\n\
echo "  --workdir /audiobook_data \\"\n\
echo "  sesame-tts"\n\
echo ""\n\
echo "=================================================="\n\
echo ""\n\
exec "$@"\n\
' > /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

# Set working directory
WORKDIR /audiobook_data

# Set the entrypoint script
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["bash"]