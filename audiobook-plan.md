# Comprehensive Plan for Generating an Audiobook on Jetson Orin Nano

This document outlines a comprehensive plan for converting a book into an audiobook using two different approaches on the Jetson Orin Nano:
1. Piper TTS using jetson-containers (faster but lower quality)
2. Sesame CSM for higher quality voice synthesis (higher quality but slower)

The plan supports both ePub and PDF formats, with ePub being the recommended format due to its better structure for chapter detection and text extraction.

## 1. Setup and Environment Preparation

### 1.1 System Requirements
- Jetson Orin Nano with **JetPack 6.1 or newer (L4T r36.4.0+)**
- At least 5GB of available RAM
- At least 20GB of free storage space
- Internet connection for downloading models
- Docker installed for container-based execution
- NVIDIA runtime enabled for Docker

### 1.2 Clone the Repository and Install Dependencies
```bash
# Clone this repository
git clone https://github.com/explicitcontextualunderstanding/audiobook.git
cd audiobook

# Make scripts executable
chmod +x *.py *.sh

# Install dependencies using the centralized script
./scripts/install_dependencies.sh
```

### 1.3 Prepare Data Directory
```bash
# Create directories for your data and book files
mkdir -p ~/audiobook_data
mkdir -p ~/audiobook

# Copy your book file to the books directory
cp ~/your_book.epub ~/audiobook/
# or
cp ~/your_book.pdf ~/audiobook/
```

Note: The repository includes a sample EPUB file (`learning_ai.epub`) that you can use for testing.

### 1.4 Using the Quick Start Script

For convenience, you can use the included `quickstart.sh` script to automatically set up the environment and generate an audiobook:

```bash
# Make the script executable
chmod +x quickstart.sh

# Run with an EPUB or PDF file
./quickstart.sh --input /path/to/your/book.epub --method piper  # For Piper TTS (faster)
# or
./quickstart.sh --input /path/to/your/book.epub --method sesame # For Sesame CSM (higher quality)
```

## 2. Docker Container Build Improvements

Based on our recent development history, we've made several key improvements to the Docker build process:

### 2.1 BuildKit Optimization
Use BuildKit for faster, more efficient builds:
```bash
DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .
```

### 2.2 Dependency Management Evolution
Our dependency management strategy has evolved to address several challenges:

#### 2.2.1 Critical Version Mismatch Issues

We've identified critical version mismatches between our pinned requirements and what's available on the Jetson PyPI index:

| Package | In requirements.txt | Available on Jetson Index |
|---------|---------------------|---------------------------|
| torch | 2.2.0 | 2.7.0 |
| torchvision | 0.17.0 | 0.22.0 |
| torchaudio | 2.2.0 | 2.7.0 |
| torchao | 0.1.0 | 0.11.0+ |
| triton | 2.1.0 | 3.3.0 |

**Important**: Due to these mismatches, pinned packages may be sourced from standard PyPI or NGC repositories instead of the Jetson-optimized index, potentially leading to:
- Installation failures for ARM64 architecture
- Sub-optimal performance
- Missing hardware acceleration

#### 2.2.2 Recommended Approach for requirements.txt

**Option 1**: Use the Jetson-optimized versions (higher performance but less tested):
```
# Core PyTorch - use Jetson-optimized versions
torch==2.7.0
torchvision==0.22.0
torchaudio==2.7.0
torchao==0.11.0
triton==3.3.0

# Keep other critical dependencies at tested versions
vector_quantize_pytorch==1.22.15
torchtune==0.3.0
moshi==0.2.2
```

**Option 2**: Create a requirements.lock.txt file to ensure reproducible builds:
```
# Core dependencies pinned to tested versions
torch==2.2.0
torchvision==0.17.0
torchaudio==2.2.0
vector_quantize_pytorch==1.22.15
tokenizers==0.13.3
transformers==4.31.0
huggingface_hub==0.16.4
accelerate==0.25.0
soundfile==0.12.1
pydub==0.25.1
sounddevice==0.5.0
ebooklib==0.18.0
beautifulsoup4==4.12.2
PyPDF2==3.0.1
pdfminer.six==20221105
nltk==3.8.1
librosa==0.10.1
einops==0.8.0
torchao==0.1.0
torchtune==0.3.0
moshi==0.2.2
silentcipher==1.0.1
triton==2.1.0

# Common transitive dependencies (not exhaustive)
numpy==1.26.0
packaging==23.2
pillow==10.1.0
tqdm==4.66.1
psutil==5.9.6
```

#### 2.2.3 Custom PyPI Index Configuration

For better control over package sources, modify the Dockerfile to explicitly specify indices:

```bash
# Configure pip for faster installations
RUN mkdir -p ~/.config/pip && \
    echo "[global]" > ~/.config/pip/pip.conf && \
    echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf && \
    echo "extra-index-url = https://pypi.ngc.nvidia.com https://pypi.org/simple" >> ~/.config/pip/pip.conf && \
    echo "timeout = 60" >> ~/.config/pip/pip.conf && \
    echo "retries = 3" >> ~/.config/pip/pip.conf
```

Or use the `--index-url` flags directly with pip in the Dockerfile:

```bash
pip install --no-cache-dir --prefer-binary \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.ngc.nvidia.com \
    --extra-index-url https://pypi.org/simple \
    -r requirements.txt
```

### 2.3 Multi-Stage Docker Build

We've optimized the Dockerfile with a multi-stage approach:
1. **Dependencies Stage**: Installs all dependencies and caches them
2. **Builder Stage**: Sets up models, utilities, and configuration
3. **Runtime Stage**: Creates the minimal runtime image

This approach significantly reduces the final image size and improves build times through better caching.

### 2.4 Testing the Build

Use our provided scripts to build and test the container:
```bash
# Build the container with BuildKit enabled
./scripts/build.sh --use-buildkit --cache

# Test the container
./scripts/test_container.sh
```

## 3. Approach 1: Generating Audiobook with Piper (via jetson-containers)

### 3.1 Overview of Piper TTS
Piper TTS is a fast, local text-to-speech system that runs efficiently on the Jetson Nano. It uses a neural vocoder model to generate speech from text and provides several different voice models to choose from.

### 3.2 Available Voice Models

| Voice | Language | Gender | Style | Good For |
|-------|----------|--------|-------|----------|
| Lessac | English (US) | Female | Professional | Audiobooks, narration |
| Ryan | English (US) | Male | Clear | Technical content |
| Jenny | English (GB) | Female | Warm | Storytelling |
| Kathleen | English (US) | Female | Warm | Children's books |
| Alan | English (GB) | Male | Formal | Academic content |

### 3.3 Using Piper Directly

If you prefer to run Piper TTS container manually instead of using the quickstart script:

```bash
# Run the piper-tts container with correct volume mounts
./jetson-containers run --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --workdir /audiobook_data $(./autotag piper-tts)

# Inside the container, install required packages
pip install PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4 psutil

# Run the generator script
python /books/generate_audiobook_piper.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_piper.mp3 \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --temp_dir /audiobook_data/temp_audio_piper \
  --max_batch_size 15 \
  --memory_per_chunk 50
```

## 4. Approach 2: Using Sesame CSM for Higher Quality Voice

### 4.1 Overview of Sesame CSM
Sesame CSM (Compact Speech Model) is a high-quality text-to-speech system that produces more natural sounding voices. It is larger and slower than Piper but produces better quality speech output.

### 4.2 Available Voice Presets

| Voice Preset | Style | Good For |
|--------------|-------|----------|
| calm | Gentle, measured pace | Audiobooks, meditation |
| excited | Energetic, engaging | Educational content, entertainment |
| authoritative | Formal, clear | Technical documentation, academic content |
| gentle | Soft, soothing | Children's books, bedtime stories |
| narrative | Storytelling flow | Fiction books, narratives |

### 4.3 Using Sesame CSM Directly

If you prefer to run the Sesame CSM container manually instead of using the quickstart script:

```bash
# Run the container with needed volume mounts
docker run --runtime nvidia -it --rm \
  --name sesame-tts \
  --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
  --volume ${HOME}/.cache/huggingface:/root/.cache/huggingface \
  --workdir /audiobook_data \
  sesame-tts-jetson /opt/conda/bin/conda run -n tts --no-capture-output \
  python3 /books/generate_audiobook_sesame.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3 \
  --model_path /models/sesame-csm-1b \
  --voice_preset calm \
  --max_batch_size 8 \
  --memory_per_chunk 150
```

## 5. Troubleshooting Docker Build Issues

Based on our development history, here are common issues and solutions:

### 5.1 Package Installation Failures

If you encounter package installation failures:

1. **Version Mismatch Issues**:
   The most likely cause of build failures is the version mismatch between your requirements.txt and the Jetson-optimized index. Consider:
   - Using the latest Jetson-optimized versions instead of pinned versions
   - Using a base image with pre-installed PyTorch compatible with your requirements
   - Checking for ARM64-compatible wheels for your pinned versions

2. **Check Base Image Availability**:
   ```bash
   docker pull dustynv/pytorch:2.6-r36.4.0-cu128-24.04
   ```

3. **Network/PyPI Mirror Issues**:
   If the Jetson-specific PyPI mirrors are inaccessible, modify the Dockerfile to use standard PyPI:
   ```bash
   # Comment out this line:
   # echo "index-url = https://pypi.jetson-ai-lab.dev/simple" >> ~/.config/pip/pip.conf
   ```

4. **Architecture Issues**:
   If building on an x86 machine for Jetson (ARM64), use cross-platform building:
   ```bash
   docker buildx create --use
   docker buildx build --platform linux/arm64 -t sesame-tts-jetson .
   ```

5. **Debug Specific Stage**:
   Target a specific build stage to identify where the failure occurs:
   ```bash
   docker build --target dependencies -t sesame-tts-deps .
   ```

6. **Verbose Output**:
   Use verbose output to see detailed error messages:
   ```bash
   DOCKER_BUILDKIT=1 docker build --progress=plain -t sesame-tts-jetson .
   ```

### 5.2 Recommended Environment Variables

Set these environment variables for optimal builds:
```bash
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export PYTHONHASHSEED=0
export PIP_DEFAULT_TIMEOUT=100
```

## 6. Future Improvements

Planned improvements for the project include:
1. **Multi-voice Audiobooks**: Support for using different voices for dialogue vs. narration.
2. **Improved EPUB Navigation**: Better chapter detection for complex EPUB structures.
3. **Custom Voice Training**: Support for training your own voice models.
4. **Web Interface**: A simple web UI for generating audiobooks without the command line.
5. **Chapter Metadata**: Adding chapter metadata to the generated MP3 files for better navigation.
6. **Further Build Optimization**: Continue refining dependency management and build process based on our learnings.
7. **Cross-Platform Support**: Improve compatibility across different host architectures.
8. **Dependency Harmonization**: Better align our package version requirements with the Jetson-optimized PyPI index.

## 7. License

This project is open source and available under the MIT License.
