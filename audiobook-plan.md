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

## 2. Dockerfile Overview

The Dockerfile has been optimized for faster builds and includes the following key features:
- **Multi-stage builds**: Separate stages for dependencies, building, and runtime to minimize the final image size.
- **Conda-based environment**: Miniconda is used to manage Python dependencies, ensuring compatibility with Jetson's ARM64 architecture.
- **Custom PyPI index**: The `https://pypi.jetson-ai-lab.dev/simple` index is used to prioritize pre-built wheels optimized for Jetson devices.
- **Fallback mechanisms**: If `ffmpeg` installation via Conda fails, the Dockerfile falls back to installing it via `apt-get` with the `jonathonf/ffmpeg-4` PPA.

### Key Dockerfile Commands
- **Install Miniconda**:
  ```bash
  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o Miniconda3.sh
  bash Miniconda3.sh -b -p /opt/conda
  ```
- **Install PyTorch stack**:
  ```bash
  pip install --no-cache-dir --prefer-binary \
      --index-url https://pypi.jetson-ai-lab.dev/simple \
      torch==2.6.0 torchvision==0.17.0 torchaudio==2.6.0
  ```
- **Install `ffmpeg`**:
  ```bash
  /opt/conda/bin/conda install -n tts -c conda-forge ffmpeg || \
      (apt-get update && \
      apt-get install -y --no-install-recommends software-properties-common && \
      add-apt-repository -y ppa:jonathonf/ffmpeg-4 && \
      apt-get update && \
      apt-get install -y --no-install-recommends ffmpeg)
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

## 5. Future Improvements

Planned improvements for the project include:
1. **Multi-voice Audiobooks**: Support for using different voices for dialogue vs. narration.
2. **Improved EPUB Navigation**: Better chapter detection for complex EPUB structures.
3. **Custom Voice Training**: Support for training your own voice models.
4. **Web Interface**: A simple web UI for generating audiobooks without the command line.
5. **Chapter Metadata**: Adding chapter metadata to the generated MP3 files for better navigation.
6. **Optimized Build Process**: Further reducing build times and image sizes.

## 6. License

This project is open source and available under the MIT License.
