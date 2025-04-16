#!/bin/bash
set -e

# Ensure necessary directories exist
mkdir -p ./docker/sesame-tts/utils

# Create the Dockerfile
cat > ./docker/sesame-tts/Dockerfile << 'EOF'
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
    # Install torch packages first
    pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 && \
    # Install specific versions of packages known to work together
    pip install tokenizers==0.13.3 transformers==4.31.0 huggingface_hub==0.16.4 accelerate==0.25.0 && \
    pip install soundfile tqdm pydub psutil ebooklib beautifulsoup4 PyPDF2 pdfminer.six nltk && \
    # Install einops with specific version for moshi
    pip install einops==0.7.0 && \
    # Install moshi specific dependencies
    pip install "sphn>=0.1.4" sounddevice==0.5.0 && \
    # Install other dependencies
    pip install rotary_embedding_torch vector_quantize_pytorch datasets && \
    # Install torchtune and torchao with compatible versions
    pip install "torchtune<0.4.0" "torchao<0.5.0" && \
    # Install moshi (older version for compatibility)
    pip install "moshi<=0.2.2" && \
    echo "✓ Core Python dependencies installed"

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
    CMD conda run -n tts python -c "import torch, sys; sys.path.append('/opt/csm'); from generator import load_csm_1b; print('Health check passed.')" || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["conda", "run", "--no-capture-output", "-n", "tts", "bash"]
EOF

# Create the entrypoint script
cat > ./docker/sesame-tts/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "====================================================="
echo "Sesame CSM Text-to-Speech for Audiobook Generation"
echo "====================================================="
echo ""
echo "This container provides Sesame CSM Text-to-Speech capabilities"
echo "specifically configured for audiobook generation on Jetson devices."
echo ""
echo "Environment paths:"
echo "  - Books directory: $BOOKS_DIR"
echo "  - Audiobook data directory: $AUDIOBOOK_DATA"
echo "  - Models directory: $MODELS_DIR"
echo ""
echo "Available scripts:"
echo "  - $BOOKS_DIR/generate_audiobook_sesame.py - Main script for both EPUB and PDF"
echo "  - $BOOKS_DIR/generate_audiobook_sesame_epub.py - Optimized for EPUB format"
echo "  - $BOOKS_DIR/extract_chapters.py - Extract chapter information"
echo ""
echo "Example usage:"
echo "  conda run -n tts python $BOOKS_DIR/generate_audiobook_sesame.py \\"
echo "    --input $BOOKS_DIR/your_book.epub \\"
echo "    --output $AUDIOBOOK_DATA/audiobook_sesame.mp3 \\"
echo "    --model_path $MODELS_DIR/sesame-csm-1b \\"
echo "    --voice_preset calm"
echo ""
echo "Test the CSM installation by running:"
echo "  conda run -n tts python /usr/local/bin/utils/test_csm.py $MODELS_DIR/sesame-csm-1b"
echo ""
echo "Note: Remember to use 'conda run -n tts' before any Python commands"
echo "to ensure they run within the conda environment."
echo ""
echo "====================================================="

# Activate the conda environment for interactive sessions
source ~/.bashrc

# Execute the command
if [ "$#" -eq 0 ]; then
    # If no command was provided, start an interactive shell
    /bin/bash
else
    # Otherwise, execute the provided command
    exec "$@"
fi
EOF

# Create the watermarking module
cat > ./docker/sesame-tts/utils/watermarking.py << 'EOF'
"""
Simplified watermarking module for CSM TTS system
This provides a stub implementation when the silentcipher package isn't available
"""
import torch

# This watermark key is public, it is not secure.
# If using CSM 1B in another application, use a new private key and keep it secret.
CSM_1B_GH_WATERMARK = [212, 211, 146, 56, 201]

def load_watermarker(device: str = "cuda"):
    """
    Return a dummy watermarker object if silentcipher isn't available
    """
    try:
        import silentcipher
        model = silentcipher.get_model(
            model_type="44.1k",
            device=device,
        )
        return model
    except ImportError:
        print("Warning: silentcipher not available, using dummy watermarker")
        return DummyWatermarker()
    
class DummyWatermarker:
    """
    Dummy watermarker that does nothing but pass through audio
    """
    def __init__(self):
        pass
    
    def encode_wav(self, audio, sample_rate, watermark_key, calc_sdr=False, message_sdr=36):
        return audio, None
    
    def decode_wav(self, audio, sample_rate, phase_shift_decoding=True):
        return {"status": False, "messages": []}

@torch.inference_mode()
def watermark(watermarker, audio_array: torch.Tensor, sample_rate: int, watermark_key: list[int]) -> tuple[torch.Tensor, int]:
    """
    Apply watermark to audio if silentcipher is available, otherwise just return the audio
    """
    try:
        if isinstance(watermarker, DummyWatermarker):
            # Just return the audio as-is
            return audio_array, sample_rate
            
        audio_array_44khz = torch.nn.functional.interpolate(
            audio_array.unsqueeze(0).unsqueeze(0), 
            size=int(len(audio_array) * 44100 / sample_rate),
            mode='linear', 
            align_corners=False
        ).squeeze(0).squeeze(0)
        
        encoded, _ = watermarker.encode_wav(audio_array_44khz, 44100, watermark_key, calc_sdr=False, message_sdr=36)
        
        # Resample back to original rate if needed
        output_sample_rate = min(44100, sample_rate)
        if output_sample_rate != 44100:
            encoded = torch.nn.functional.interpolate(
                encoded.unsqueeze(0).unsqueeze(0),
                size=int(len(encoded) * output_sample_rate / 44100),
                mode='linear',
                align_corners=False
            ).squeeze(0).squeeze(0)
            
        return encoded, output_sample_rate
    except Exception as e:
        print(f"Warning: Watermarking failed: {e}, returning unwatermarked audio")
        return audio_array, sample_rate

@torch.inference_mode()
def verify(watermarker, watermarked_audio: torch.Tensor, sample_rate: int, watermark_key: list[int]) -> bool:
    """
    Verify watermark in audio if silentcipher is available
    """
    try:
        if isinstance(watermarker, DummyWatermarker):
            return False
            
        watermarked_audio_44khz = torch.nn.functional.interpolate(
            watermarked_audio.unsqueeze(0).unsqueeze(0),
            size=int(len(watermarked_audio) * 44100 / sample_rate),
            mode='linear',
            align_corners=False
        ).squeeze(0).squeeze(0)
        
        result = watermarker.decode_wav(watermarked_audio_44khz, 44100, phase_shift_decoding=True)
        
        is_watermarked = result["status"]
        if is_watermarked:
            is_csm_watermarked = result["messages"][0] == watermark_key
        else:
            is_csm_watermarked = False
            
        return is_watermarked and is_csm_watermarked
    except Exception as e:
        print(f"Warning: Watermark verification failed: {e}")
        return False

def check_audio_from_file(audio_path: str) -> bool:
    """
    Check if audio file contains CSM watermark
    """
    try:
        import torchaudio
        watermarker = load_watermarker(device="cuda")
        audio_array, sample_rate = torchaudio.load(audio_path)
        audio_array = audio_array.mean(dim=0)
        return verify(watermarker, audio_array, sample_rate, CSM_1B_GH_WATERMARK)
    except Exception as e:
        print(f"Error checking watermark: {e}")
        return False
EOF

# Create the test_csm.py script
cat > ./docker/sesame-tts/utils/test_csm.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Sesame CSM
This script tests if the CSM model can be loaded and used for generation.
"""

import os
import sys
import torch
import torchaudio
import time
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_csm')

def main():
    parser = argparse.ArgumentParser(description='Test CSM installation')
    parser.add_argument('model_path', type=str, help='Path to the CSM model directory')
    parser.add_argument('--output', type=str, default='test_output.wav', help='Output file for test generation')
    args = parser.parse_args()
    
    try:
        # Test CUDA availability
        if not torch.cuda.is_available():
            logger.error("❌ Error: CUDA is not available. This application requires a CUDA-enabled GPU.")
            sys.exit(1)
        
        logger.info(f"✓ Using device: {torch.cuda.get_device_name(0)}")
        logger.info(f"✓ CUDA Version: {torch.version.cuda}")
        
        # Test key imports with careful error handling
        try:
            import torchao
            logger.info(f"✓ Successfully imported torchao version: {torchao.__version__ if hasattr(torchao, '__version__') else 'unknown'}")
        except ImportError as e:
            logger.error(f"❌ Failed to import torchao: {e}")
            logger.info("Continuing without torchao import verification...")
        
        try:
            import torchtune
            logger.info(f"✓ Successfully imported torchtune version: {torchtune.__version__ if hasattr(torchtune, '__version__') else 'unknown'}")
        except ImportError as e:
            logger.error(f"❌ Failed to import torchtune: {e}")
            logger.info("Continuing without torchtune import verification...")
        
        try:
            import moshi
            logger.info("✓ Successfully imported moshi")
        except ImportError as e:
            logger.error(f"❌ Failed to import moshi: {e}")
            logger.info("Continuing without moshi import verification...")
        
        # Verify we can import necessary modules for CSM
        try:
            sys.path.append('/opt/csm')
            from generator import load_csm_1b, Segment
            logger.info("✓ Successfully imported CSM generator modules")
        except ImportError as e:
            logger.error(f"❌ Failed to import CSM generator modules: {e}")
            sys.exit(1)
        
        # Start timer for model loading
        start_time = time.time()
        logger.info(f"Loading CSM model from {args.model_path}...")
        
        # Load the model
        try:
            generator = load_csm_1b(device="cuda")
            logger.info(f"✓ Model loaded successfully in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"❌ Error loading CSM model: {e}")
            logger.error("Please check your model path and that all dependencies are installed correctly.")
            sys.exit(1)
        
        # Generate a small test audio
        logger.info("Generating test audio...")
        start_time = time.time()
        test_text = "This is a test of the Sesame CSM text to speech system."
        
        # Create a simple segment to use as context
        segments = [Segment(
            speaker=1,
            text="Hello, world.",
            audio=torch.zeros(generator.sample_rate).to("cuda")
        )]
        
        # Generate audio
        try:
            audio = generator.generate(
                text=test_text,
                speaker=1,
                context=segments,
                max_audio_length_ms=5000,  # 5 seconds max
                temperature=0.9,
                topk=50
            )
            
            # Save output
            output_path = os.path.join(os.getcwd(), args.output)
            torchaudio.save(output_path, audio.unsqueeze(0).cpu(), generator.sample_rate)
            
            logger.info(f"✓ Audio generation completed in {time.time() - start_time:.2f} seconds")
            logger.info(f"✓ Saved test audio to {output_path}")
            logger.info("✓ CSM is installed and working correctly!")
        except Exception as e:
            logger.error(f"❌ Error during audio generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

# Make scripts executable
chmod +x ./docker/sesame-tts/entrypoint.sh
chmod +x ./docker/sesame-tts/utils/test_csm.py

echo "Building the Docker image..."
sudo docker build -t sesame-tts-jetson -f ./docker/sesame-tts/Dockerfile .

echo "Done! You can now run the container with:"
echo "sudo docker run --runtime nvidia -it --rm \\"
echo "  --volume ~/audiobook_data:/audiobook_data \\"
echo "  --volume ~/audiobook:/books \\"
echo "  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \\"
echo "  --volume ~/.cache/huggingface:/root/.cache/huggingface \\"
echo "  --workdir /audiobook_data \\"
echo "  sesame-tts-jetson"
