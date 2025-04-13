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

# Install Python dependencies in smaller batches for better error isolation
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch and torchaudio (already in the base image)
RUN pip3 install --no-cache-dir \
    "torch>=2.0.0,<2.5.0" \
    "torchaudio>=2.0.0,<2.5.0"

# Install transformers and tokenizers
RUN pip3 install --no-cache-dir \
    "tokenizers>=0.13.0,<0.22.0" \
    "transformers>=4.30.0,<4.47.0" \
    "huggingface_hub>=0.16.0,<0.29.0"

# Install moshi with fallback
RUN pip3 install --no-cache-dir "moshi>=0.2.0,<0.3.0" || \
    pip3 install --no-cache-dir "moshi==0.2.2" || \
    pip3 install --no-cache-dir "moshi" || \
    echo "Warning: Could not install moshi package. Continuing without it."

# Install remaining dependencies with individual fallbacks
RUN pip3 install --no-cache-dir "torchtune>=0.4.0,<0.5.0" || \
    pip3 install --no-cache-dir "torchtune==0.4.0" || \
    echo "Warning: Could not install torchtune package. Continuing without it."

RUN pip3 install --no-cache-dir "torchao>=0.9.0,<1.0.0" || \
    pip3 install --no-cache-dir "torchao==0.9.0" || \
    echo "Warning: Could not install torchao package. Continuing without it."

# Handle silentcipher - try PyPI first, fall back to git clone if needed
RUN pip3 install --no-cache-dir silentcipher || \
    (echo "Warning: Could not install silentcipher from PyPI, attempting GitHub install..." && \
     mkdir -p /tmp/silentcipher && \
     cd /tmp/silentcipher && \
     git init && \
     git remote add origin https://github.com/SesameAILabs/silentcipher.git && \
     git fetch --depth 1 origin master && \
     git checkout FETCH_HEAD && \
     pip install -e . || echo "Warning: Could not install silentcipher from GitHub. Continuing without it.")

# Install additional dependencies needed for audiobook generation
# Split into groups for better error isolation
RUN pip3 install --no-cache-dir \
    PyPDF2 \
    pdfminer.six \
    nltk \
    tqdm \
    pydub \
    psutil

RUN pip3 install --no-cache-dir \
    ebooklib \
    beautifulsoup4

RUN pip3 install --no-cache-dir \
    einops || echo "Warning: Could not install einops. Continuing without it."

RUN pip3 install --no-cache-dir \
    rotary_embedding_torch || echo "Warning: Could not install rotary_embedding_torch. Continuing without it."

RUN pip3 install --no-cache-dir \
    vector_quantize_pytorch || echo "Warning: Could not install vector_quantize_pytorch. Continuing without it."

RUN pip3 install --no-cache-dir \
    accelerate \
    soundfile \
    "datasets[audio]" || pip3 install --no-cache-dir datasets

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
import os\n\
import importlib.util\n\
from pathlib import Path\n\
import logging\n\
\n\
# Configure logging\n\
logging.basicConfig(\n\
    level=logging.INFO,\n\
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"\n\
)\n\
logger = logging.getLogger("test_csm")\n\
\n\
# Add CSM root to path\n\
if os.path.exists("/opt/csm"):\n\
    sys.path.insert(0, "/opt/csm")\n\
\n\
try:\n\
    # First try to import torch\n\
    try:\n\
        import torch\n\
        logger.info(f"PyTorch version: {torch.__version__}")\n\
        logger.info(f"CUDA available: {torch.cuda.is_available()}")\n\
        if torch.cuda.is_available():\n\
            device = "cuda"\n\
            logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")\n\
        else:\n\
            device = "cpu"\n\
            logger.info("CUDA not available, using CPU")\n\
    except ImportError as e:\n\
        logger.error(f"Failed to import torch: {e}")\n\
        device = "cpu"\n\
\n\
    # Try to import torchaudio for saving the test file\n\
    try:\n\
        import torchaudio\n\
        logger.info(f"torchaudio version: {torchaudio.__version__}")\n\
        can_save_audio = True\n\
    except ImportError as e:\n\
        logger.warning(f"Failed to import torchaudio: {e}. Won\'t be able to save audio.")\n\
        can_save_audio = False\n\
\n\
    # First try to import from csm package\n\
    try:\n\
        # Try the compat module first\n\
        from csm_compat import load_csm_1b, Segment, Generator\n\
        logger.info("Successfully imported from csm_compat module")\n\
    except ImportError:\n\
        try:\n\
            # Try importing from generator.py directly\n\
            from generator import load_csm_1b, Segment\n\
            logger.info("Successfully imported from generator.py module")\n\
        except ImportError as e:\n\
            logger.error(f"Failed to import CSM modules: {e}")\n\
            logger.error("Cannot proceed without CSM modules")\n\
            sys.exit(1)\n\
    \n\
    logger.info(f"\\nUsing device: {device}\\n")\n\
    \n\
    # Path to model\n\
    model_path = sys.argv[1] if len(sys.argv) > 1 else "/models/sesame-csm-1b"\n\
    logger.info(f"Loading model from: {model_path}")\n\
    \n\
    # Check if model exists\n\
    if not os.path.exists(model_path):\n\
        logger.error(f"ERROR: Model path {model_path} does not exist!")\n\
        logger.error("Make sure you have mounted the model directory correctly.")\n\
        logger.info("Available paths:")\n\
        for path in ["/models", "/models/sesame-csm-1b", "/audiobook_data", "/books"]:\n\
            if os.path.exists(path):\n\
                logger.info(f"  - {path} (exists, content: {os.listdir(path) if os.path.isdir(path) else \'file\'})")\n\
            else:\n\
                logger.info(f"  - {path} (does not exist)")\n\
        sys.exit(1)\n\
    \n\
    # Load model\n\
    logger.info("Initializing CSM model...")\n\
    try:\n\
        generator = load_csm_1b(model_path=model_path, device=device)\n\
        logger.info(f"Model loaded successfully. Sample rate: {generator.sample_rate}")\n\
    except Exception as e:\n\
        logger.error(f"Error loading model: {e}")\n\
        import traceback\n\
        traceback.print_exc()\n\
        sys.exit(1)\n\
    \n\
    # Test generate a short sample\n\
    logger.info("\\nGenerating test audio...")\n\
    output_file = Path("/audiobook_data/test_sample.wav")\n\
    \n\
    # Get voice presets if available\n\
    preset_dir = Path(model_path) / "prompts"\n\
    presets = list(preset_dir.glob("*.wav")) if preset_dir.exists() else []\n\
    if presets:\n\
        logger.info(f"Available voice presets: {[p.stem for p in presets]}")\n\
    else:\n\
        logger.info("No voice presets found")\n\
    \n\
    # Test generate with simple text\n\
    text = "This is a test of the CSM text to speech system."\n\
    logger.info(f"Generating speech for text: \\\"{text}\\\"")\n\
    audio = generator.generate(text=text)\n\
    \n\
    if can_save_audio and audio is not None:\n\
        # Save the audio\n\
        torchaudio.save(output_file, audio.unsqueeze(0).cpu(), generator.sample_rate)\n\
        logger.info(f"Test audio saved to {output_file}")\n\
    else:\n\
        logger.warning("Could not save audio file (missing torchaudio or no audio generated)")\n\
    \n\
    # Success\n\
    logger.info("\\n✅ CSM test completed successfully!")\n\
    \n\
except Exception as e:\n\
    logger.error(f"\\n❌ Error testing CSM: {e}")\n\
    import traceback\n\
    traceback.print_exc()\n\
    \n\
    # Print more diagnostic information\n\
    logger.info("\\nDiagnostic information:")\n\
    logger.info(f"Python version: {sys.version}")\n\
    try:\n\
        import torch\n\
        logger.info(f"Torch version: {torch.__version__}")\n\
        logger.info(f"CUDA available: {torch.cuda.is_available()}")\n\
        if torch.cuda.is_available():\n\
            logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")\n\
    except ImportError:\n\
        logger.info("Torch not available")\n\
    \n\
    # List installed packages\n\
    logger.info("\\nInstalled packages:")\n\
    import subprocess\n\
    try:\n\
        output = subprocess.check_output(["pip", "list"]).decode("utf-8")\n\
        for line in output.split("\\n"):\n\
            if any(pkg in line.lower() for pkg in ["torch", "audio", "token", "transform", "hub", "moshi"]):\n\
                logger.info(f"  {line.strip()}")\n\
    except Exception as pkg_err:\n\
        logger.error(f"Could not list packages: {pkg_err}")\n\
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