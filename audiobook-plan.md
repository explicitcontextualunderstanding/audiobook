# Comprehensive Plan for Generating an Audiobook on Jetson Orin Nano

This document outlines a comprehensive plan for converting a book into an audiobook using two different approaches on the Jetson Orin Nano:
1. Piper TTS using jetson-containers (recommended first approach)
2. Sesame CSM for higher quality voice synthesis (alternative approach)

The plan supports both ePub and PDF formats, with ePub being the recommended format due to its better structure for chapter detection and text extraction.

## 1. Setup and Environment Preparation

### 1.1 System Requirements
- Jetson Orin Nano with JetPack/L4T
- At least 5GB of available RAM
- At least 20GB of free storage space
- Internet connection for downloading models

### 1.2 Clone the Repository and Install Dependencies
```bash
# Clone this repository
git clone https://github.com/explicitcontextualunderstanding/audiobook.git
cd audiobook

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

# Run the script with your book file (default uses Piper TTS engine)
./quickstart.sh learning_ai.epub piper lessac

# General syntax:
# ./quickstart.sh [book_filename] [engine] [voice]
# Where:
#  - book_filename: Your EPUB or PDF file
#  - engine: piper or sesame
#  - voice: voice model name (e.g., lessac, ryan, etc. for piper)
```

The quickstart script handles:
- Installing dependencies
- Setting up the right environment (launches the Piper container when using Piper TTS)
- Running the appropriate audiobook generation script inside the container
- Applying chapter markers to the final audio file
- Managing container volume mounts and cleanup automatically

Note: When using the `-e piper` (default) option, the script automatically:
1. Launches the jetson-containers Piper container with the correct volume mounts
2. Executes the generation script inside the container
3. Manages file permissions between the container and host
4. Cleans up the container when processing is complete

## 2. Approach 1: Generating Audiobook with Piper (via jetson-containers)

### 2.1 Check Available Piper Models
```bash
# Show details about the piper-tts container
./jetson-containers show piper-tts
```

### 2.2 Run the Piper Container
```bash
# Run the piper-tts container with correct volume mounts
# IMPORTANT: Volume arguments must come BEFORE the container name
./jetson-containers run --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --workdir /audiobook_data $(./autotag piper-tts)
```

### 2.3 Test Piper with a Simple Example
Inside the container, first test Piper with the included test voice model:

```bash
# Test Piper with a simple sentence (note: Piper reads from stdin)
echo "This is a test of the Piper text to speech system." > test.txt
cat test.txt | piper -m /opt/piper/etc/test_voice.onnx -f /audiobook_data/test.wav

# Install ffmpeg and convert to MP3 format
apt-get update && apt-get install -y ffmpeg
ffmpeg -i /audiobook_data/test.wav -y -codec:a libmp3lame -qscale:a 2 /audiobook_data/test.mp3
```

### 2.4 Install Required Python Packages in the Container
```bash
# Install required packages
pip install PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4
```

### 2.5 Using the Audiobook Generation Scripts

The repository contains several Python scripts:

1. `generate_audiobook_piper.py` - Main script for generating audiobooks using Piper TTS (works with both EPUB and PDF)
2. `generate_audiobook_piper_epub.py` - Specialized script for EPUB files using Piper TTS (optimized for EPUB with simpler parameters)
3. `generate_audiobook_sesame.py` - Main script for generating audiobooks using Sesame CSM (works with both EPUB and PDF)
4. `generate_audiobook_sesame_epub.py` - Specialized script for EPUB files using Sesame CSM (optimized for EPUB with simpler parameters)
5. `extract_chapters.py` - Utility for extracting chapter information from books

**Difference between general and EPUB-specific scripts:**
- General scripts (`generate_audiobook_piper.py`, `generate_audiobook_sesame.py`) support both EPUB and PDF files with more configuration options
- EPUB-specific scripts (`generate_audiobook_piper_epub.py`, `generate_audiobook_sesame_epub.py`) are optimized for EPUB files with simplified parameters

#### 2.5.1 Extracting Chapter Information

Before generating the audiobook, you can extract chapter information from your book to create chapter markers in the final audio file:

```bash
python extract_chapters.py --file /books/your_book.epub --output /audiobook_data/chapters.txt --duration 7200
```

The `--duration` parameter should be set to the expected length of your audiobook in seconds.

### 2.6 Run the Audiobook Generation Script
```bash
# Create necessary directories
mkdir -p /audiobook_data/temp_audio_piper
mkdir -p /audiobook_data/audiobook_chapters_piper

# For ePub format with a specific voice model
python generate_audiobook_piper.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_piper.mp3 \
  --output_dir /audiobook_data/audiobook_chapters_piper \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --temp_dir /audiobook_data/temp_audio_piper

# For EPUB files specifically (using dedicated script)
python generate_audiobook_piper_epub.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_piper.mp3 \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx

# For large books, process specific chapter ranges
python generate_audiobook_piper.py \
  --input /books/your_large_book.epub \
  --output /audiobook_data/audiobook_piper_part1.mp3 \
  --output_dir /audiobook_data/audiobook_chapters_piper \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --temp_dir /audiobook_data/temp_audio_piper \
  --chapter_range 1-10
```

## 3. Understanding Container and Host File Locations

Important path mappings:
    
| Inside Container | On Jetson Host |
|-----------------|----------------|
| `/audiobook_data` | `~/audiobook_data` |
| `/books` | `~/audiobook` |
| `/data` | `~/jetson-containers/data` (default mapping) |

When running commands:
- Use container paths (like `/audiobook_data`) when inside the container
- Use host paths (like `~/audiobook_data`) when on the Jetson host
        
Note: Files saved to `/data` inside the container will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`.

## 4. Approach 2: Using Sesame CSM for Higher Quality Voice

### 4.1 Set Up Environment for Sesame CSM
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg libsndfile1
    
# Create project directory
mkdir -p ~/sesame_project
cd ~/sesame_project
    
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install PyPDF2 pdfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch ebooklib beautifulsoup4
```

### 4.2 Install Sesame CSM
```bash
# Clone the repository
git clone https://github.com/SesameAILabs/csm.git
cd csm
    
# Install in development mode
pip install -e .
    
# Download the model
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"
    
# Go back to project directory
cd ..
```

### 4.3 Using the Sesame Audiobook Script

```bash
# For general use
python generate_audiobook_sesame.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3

# For EPUB files specifically
python generate_audiobook_sesame_epub.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3
```

## 5. Voice Model Selection Guide

| Voice | Language | Gender | Style | Quality | File Path | Good For |
|-------|----------|--------|-------|---------|----------|----------|
| Lessac | English (US) | Female | Professional | Medium/High | `/opt/piper/voices/en/en_US-lessac-medium.onnx` | Audiobooks, narration |
| Ryan | English (US) | Male | Clear | Medium/High | `/opt/piper/voices/en/en_US-ryan-medium.onnx` | Technical content |
| Jenny | English (GB) | Female | Warm | Medium/High | `/opt/piper/voices/en/en_GB-jenny-medium.onnx` | Storytelling |
| Kathleen | English (US) | Female | Warm | Medium/High | `/opt/piper/voices/en/en_US-kathleen-medium.onnx` | Children's books |
| Alan | English (UK) | Male | Formal | Medium/High | `/opt/piper/voices/en/en_GB-alan-medium.onnx` | Academic content |

**Note:** For smaller memory footprint but lower quality, you can use the `-low.onnx` versions instead of `-medium.onnx`.

## 6. Monitoring and Managing the Process

To check the progress of the generation:
```bash
ls -la /audiobook_data/audiobook_chapters_piper | wc -l
```

To resume if interrupted, just run the same command again - the script includes resume capability to skip already processed chunks.

For extra safety, you can backup your generated chapters before making changes:
```bash
rsync -a ~/audiobook_data/audiobook_chapters_piper/ ~/audiobook_data/audiobook_chapters_piper_bak/
```

## 7. Troubleshooting

If you encounter issues with the audiobook generation:

1. **Memory Issues**: If the Jetson runs out of memory, try processing the book in smaller chunks using the `--chapter_range` option
2. **Container Errors**: Make sure the volume mounts are specified correctly and come BEFORE the container name
3. **Model Loading**: Verify that the voice model path is correct
4. **Missing Dependencies**: Run `pip install -r requirements.txt` to install all needed packages
5. **CUDA Problems**: Ensure your Jetson has the latest JetPack/L4T version installed