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

### 1.2 Clone the Repository and Install Dependencies
```bash
# Clone this repository
git clone https://github.com/explicitcontextualunderstanding/audiobook.git
cd audiobook

# Make scripts executable
chmod +x *.py *.sh

# Install required dependencies
pip install -r requirements.txt
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

## 2. Command-Line Options

The quickstart script now supports the following command-line options:

```
Usage: ./quickstart.sh [options]

Required options:
  --input FILE               Path to input book file (EPUB or PDF)

Optional options:
  --method METHOD            TTS method to use: 'piper' (faster) or 'sesame' (higher quality)
                             Default: piper
  --voice VOICE              Voice preset to use
                             For piper: lessac (default), ryan, jenny, kathleen, alan
                             For sesame: calm (default), excited, authoritative, gentle, narrative
  --chapter-range RANGE      Range of chapters to process (e.g., '1-5')
  --memory-per-chunk SIZE    Memory usage per chunk in MB
  --max-batch-size SIZE      Maximum batch size for processing
  --output-format FORMAT     Output format: mp3 (default), wav, flac
  --help                     Show this help message
```

The quickstart script handles:
- Installing dependencies
- Setting up the right environment (launches the appropriate container)
- Running the appropriate audiobook generation script inside the container
- Managing container volume mounts automatically
- Auto-detecting memory parameters based on the TTS method
- Processing specific chapter ranges if requested
- Choosing appropriate voice models based on preferences

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

### 3.4 Piper Script Parameters

The `generate_audiobook_piper.py` script supports the following parameters:

```
--input          Path to the input book file (ePub or PDF)
--output         Output combined audiobook file path
--output_dir     Output directory for chapter files
--model          Piper voice model to use
--temp_dir       Directory for temporary audio files
--chunk_size     Maximum characters per chunk
--max_batch_size Maximum chunks to process before pausing
--memory_per_chunk Estimated memory usage per chunk in MB
--chapter_range  Range of chapters to process (e.g., '1-5')
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

### 4.4 Sesame Script Parameters

The `generate_audiobook_sesame.py` script supports the following parameters:

```
--input            Path to the input EPUB or PDF file
--output           Path to the output audio file
--model_path       Path to the directory containing the Sesame model files
--voice_preset     Name of the voice preset (e.g., 'calm')
--chunk_length     Approximate maximum character length for text chunks
--temp_dir         Directory to store temporary audio chunks
--keep_temp        Keep temporary audio chunk files after generation
--chapter_range    Range of chapters to process (e.g., '1-5')
--memory_per_chunk Estimated memory usage per chunk in MB
--max_batch_size   Maximum number of chunks to process in a single batch
```

## 5. New Features and Improvements

### 5.1 Batch Processing for Memory Management

Both TTS engines now support batch processing to manage memory usage on the Jetson Nano. This is particularly important for the Sesame CSM model, which requires more memory.

```bash
# Example with explicit memory management
./quickstart.sh --input book.epub --method sesame --memory-per-chunk 150 --max-batch-size 8
```

The scripts will automatically split processing into batches and clean up GPU memory between batches.

### 5.2 Voice Preset Discovery

The Sesame CSM script now has improved voice preset discovery. It will search for voice preset files in multiple locations:

1. The model directory root
2. The `prompts` subdirectory
3. The `presets` subdirectory 
4. The `voices` subdirectory

It will also try multiple file extensions (.wav, .mp3) and handle cases where the file extension is or isn't included in the preset name.

### 5.3 Chapter Range Processing

Both TTS engines now support processing specific chapter ranges, which is useful for testing or for splitting the audiobook generation process:

```bash
# Process chapters 1 through 5 only
./quickstart.sh --input book.epub --chapter-range 1-5
```

### 5.4 Resume Capability

Both TTS engines now have robust resume capability. If the process is interrupted, you can run the same command again, and it will skip chunks that have already been processed.

## 6. Docker Container Structure

### 6.1 Piper TTS Container

The Piper TTS container is based on the `dustynv/piper-tts` image from jetson-containers. It includes:

- Piper TTS engine
- Pre-trained voice models
- CUDA acceleration
- Text processing utilities

### 6.2 Sesame CSM Container

The Sesame CSM container is custom-built for this project. It uses:

- Base image: `dustynv/pytorch:2.6-r36.4.0-cu128-24.04` (optimized for Jetson)
- Conda environment with PyTorch and CUDA support
- Customized audiobook_generator module for enhanced error handling
- Triton Inference Server for model serving
- Support for voice preset contexts

## 7. Understanding Container and Host File Locations

Important path mappings:
    
| Inside Container | On Jetson Host |
|-----------------|----------------|
| `/audiobook_data` | `~/audiobook_data` |
| `/books` | `~/audiobook` |
| `/models/sesame-csm-1b` | `~/huggingface_models/sesame-csm-1b` |
| `/data` | `~/jetson-containers/data` (for Piper only) |

When running commands:
- Use container paths (like `/audiobook_data`) when inside the container
- Use host paths (like `~/audiobook_data`) when on the Jetson host
        
Note: Files saved to `/data` inside the container will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`.

## 8. Troubleshooting

### 8.1 Common Issues and Solutions

#### Out of memory errors

If you encounter CUDA out of memory errors, try:
- Reducing the `--max_batch_size` (e.g., to 4 or 2)
- Increasing the frequency of memory cleanup by reducing `--memory_per_chunk`
- Using the Piper TTS engine instead, which requires less memory

#### Model not found errors

If the Sesame model is not found, ensure:
- You've downloaded the model to `~/huggingface_models/sesame-csm-1b`
- You're logged in to Hugging Face: `huggingface-cli login`
- You have accepted the terms for `meta-llama/Llama-3.2-1B`

#### Docker errors

If you encounter Docker errors:
- Make sure Docker is installed: `docker --version`
- Check that the NVIDIA runtime is available: `docker info | grep -i runtime`
- Ensure you have sufficient permissions: try using `sudo` or add your user to the docker group

### 8.2 Disk Space Management

If you encounter "No space left on device" errors:

```bash
# Check disk usage
df -h /

# Clean Docker resources
sudo docker container prune -f
sudo docker image prune -a -f
sudo docker builder prune -f

# Clean apt cache
sudo apt-get clean
sudo apt-get autoremove -y

# Find and remove large files
du -sh ~/audiobook_data
du -sh ~/.cache/huggingface
```

## 9. Build Optimization and Python Wheels

The build process for the Docker containers, particularly the Sesame CSM container, can be time-consuming. We need to validate our build assumptions and optimize the process.

### 9.1 Python Wheels Considerations

Using pre-built Python wheels could potentially reduce build times, but several factors need consideration:

1. **Architecture Compatibility**: Standard PyPI wheels are typically compiled for x86_64 architecture, while Jetson uses ARM64 (aarch64).

2. **CUDA Compatibility**: Our application requires CUDA 12.8 support, which may not be available in standard wheels.

3. **Dependency Chain Complexity**: Complex interdependencies between torchao, torchtune, and moshi must be satisfied.

4. **Jetson-specific Optimizations**: Some performance optimizations require specific compilation flags.

### 9.3 Optimized Build System

To address the long build times, the project now includes an optimized build system:

1. **Enhanced Dockerfile**: The Dockerfile has been optimized with:
   - Multi-stage builds (dependencies → builder → runtime)
   - Better layer caching through strategic command ordering
   - Selective dependency installation for faster builds
   - Proper separation of build-time and runtime components

2. **Optimized Requirements**: The requirements.txt file has been reorganized to:
   - Install PyTorch stack first to leverage caching
   - Separate specialized dependencies that may require compilation
   - Group related dependencies for clearer organization

3. **Improved .dockerignore**: More comprehensive exclusions to reduce context size

4. **BuildKit-enabled Build Script**: A new build.sh script that provides:
   - Parallel processing with BuildKit
   - Progress indicators during builds
   - Cache utilization for faster repeat builds
   - Build time tracking and logs

To use the optimized build system:

```bash
# Make the script executable (first time only)
chmod +x build.sh

# Basic build
./build.sh

# Advanced options
./build.sh --verbose              # Show detailed output
./build.sh --no-cache             # Force clean build
./build.sh --cache-from=IMAGE     # Use previous build as cache
./build.sh --tag=NAME             # Specify custom image tag
```

This approach significantly reduces build times, especially for subsequent builds where the cache can be utilized effectively.

## 10. Future Improvements

Planned improvements for the project include:

1. **Multi-voice Audiobooks**: Support for using different voices for dialogue vs. narration
2. **Improved EPUB Navigation**: Better chapter detection for complex EPUB structures
3. **Custom Voice Training**: Support for training your own voice models
4. **Web Interface**: A simple web UI for generating audiobooks without the command line
5. **Chapter Metadata**: Adding chapter metadata to the generated MP3 files for better navigation
6. **Fine-tuned models**: Specialized models for different types of content (fiction, technical, etc.)
7. **Batch job management**: Ability to queue multiple books for sequential processing
8. **Optimized Build Process**: Implementing the validated approaches from the build optimization tests

## 11. License

This project is open source and available under the MIT License.
