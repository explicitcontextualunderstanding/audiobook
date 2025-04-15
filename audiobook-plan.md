# Comprehensive Plan for Generating an Audiobook on Jetson Orin Nano

This document outlines a comprehensive plan for converting a book into an audiobook using two different approaches on the Jetson Orin Nano:
1. Piper TTS using jetson-containers (recommended first approach)
2. Sesame CSM for higher quality voice synthesis (alternative approach)

The plan supports both ePub and PDF formats, with ePub being the recommended format due to its better structure for chapter detection and text extraction.

## 1. Setup and Environment Preparation

### 1.1 System Requirements
- Jetson Orin Nano with **JetPack 6.1 or newer (L4T r36.4.0+)**
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

Note: When using the `piper` engine option, the script automatically:
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
```

### 2.4 Install Required Python Packages in the Container
```bash
# Install required packages INSIDE the container
pip install PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4
```

**Important:** Make sure to run this command inside the container before attempting to run any of the scripts. If you get a "ModuleNotFoundError" message like "No module named 'PyPDF2'", it means you need to install the dependencies first.

To verify successful installation, you can run:
```bash
# Verify the packages are installed
pip list | grep -E "PyPDF2|nltk|tqdm|pydub|ebooklib|beautifulsoup4"
```

**Note for Future Improvements:** For a more streamlined experience, these dependencies could be included directly in the Piper container's Dockerfile. This would eliminate the need to manually install packages each time you launch the container. If you're maintaining your own fork of the jetson-containers repository, consider adding these requirements to the piper-tts container definition.

**How to Modify the Piper Dockerfile:**

If you want to create a custom Piper container with the required dependencies, you can modify the existing Dockerfile located at:

```
<path_to_jetson_containers_repo>/containers/piper-tts/Dockerfile
```

Add the necessary `RUN` commands to install the Python packages using `pip` and any other system-level dependencies required. After modifying, build the Docker image and use it for your audiobook generation tasks.

### 2.5 Using the Audiobook Generation Scripts

The repository contains several Python scripts:

1. `generate_audiobook_piper.py` - Main script for generating audiobooks using Piper TTS (works with both EPUB and PDF)
2. `generate_audiobook_piper_epub.py` - Specialized script for EPUB files using Piper TTS (optimized for EPUB with simpler parameters)
3. `generate_audiobook_sesame.py` - Main script for generating audiobooks using Sesame CSM (works with both EPUB and PDF)
4. `generate_audiobook_sesame_epub.py` - Specialized script for EPUB files using Sesame CSM (optimized for EPUB with simpler parameters)
5. `extract_chapters.py` - Utility for extracting chapter information from books

**Important:** All Python scripts for Piper TTS should be executed INSIDE the container. Do NOT exit the container to run these scripts. The container has all the necessary dependencies and access to the Piper TTS models.

**Script Location:** When you launch the container using the quickstart.sh script or manually, the scripts are automatically mounted inside the container at:
```
/books/
```

To execute a script inside the container, use the full path to the script:
```bash
# List the available scripts
ls -la /books/*.py

# Execute a specific script (example)
python /books/generate_audiobook_piper.py --input /books/your_book.epub [other options]
```

If you used the quickstart.sh script, you're already inside the container with a prompt similar to `root@amazon1148:/audiobook_data#` and should run all commands from there.

If you manually launched the container with `jetson-containers run`, you should execute all Python scripts from within that container session.

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

### 2.7 Generating Per-Chapter Audio Files

To generate separate audio files for each chapter (rather than one combined audiobook):

```bash
# Create a directory specifically for individual chapter audio files
mkdir -p /audiobook_data/individual_chapters

# Generate per-chapter audio files using the --per_chapter flag
python generate_audiobook_piper.py \
  --input /books/your_book.epub \
  --output_dir /audiobook_data/individual_chapters \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --temp_dir /audiobook_data/temp_audio_piper \
  --per_chapter

# For EPUB files using the specialized script
python generate_audiobook_piper_epub.py \
  --input /books/your_book.epub \
  --output_dir /audiobook_data/individual_chapters \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --per_chapter
```

This will create individual MP3 files for each chapter in the specified `--output_dir` directory. The files will be named according to the chapter number and title, for example:
- `Chapter_01_Introduction.mp3`
- `Chapter_02_Getting_Started.mp3`
- ...and so on.

You can access these individual chapter files directly from your host machine at `~/audiobook_data/individual_chapters/`.

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

### 4.4 Using Docker Container for Sesame CSM (Recommended)

For a more streamlined experience, similar to the Piper TTS approach, you can use the included Docker container for Sesame CSM:

**Important Pre-requisites:**

1.  **JetPack Version:** Ensure your Jetson device is running **JetPack 6.1 or newer (L4T r36.4.0+)**. The Docker container now uses a base image (`dustynv/torchao:0.11.0-r36.4.0-cu128-24.04`) built specifically for this environment.
2.  **Download the Model Manually:**
    The `sesame/csm-1b` model requires authentication. Download it manually on your host machine first.
    ```bash
    # Install Hugging Face Hub CLI
    pip install -U huggingface_hub
    # Log in (requires Hugging Face account and token)
    huggingface-cli login
    # Create target directory
    mkdir -p ~/huggingface_models
    # Download model (disabling symlinks for Docker)
    huggingface-cli download sesame/csm-1b --local-dir ~/huggingface_models/sesame-csm-1b --local-dir-use-symlinks False
    ```
    *Note: You may need to visit the model page (https://huggingface.co/sesame/csm-1b) and accept terms.*

3.  **Llama 3.2 1B Access:**
    The CSM model uses `meta-llama/Llama-3.2-1B` internally. Ensure you have requested access and been granted permission for this model on Hugging Face. Your `huggingface-cli login` should provide the necessary authentication when the script runs inside the container.

Now you can proceed with building and running the container.

```bash
# Option 1: Using the quickstart.sh script
# (Future improvement: Update quickstart.sh for Sesame)
# ./quickstart.sh your_book.epub sesame [voice_preset_name]

# Option 2: Manual Docker approach
# Check if sesame-tts-jetson image exists, build if not
# Use a distinct tag like 'sesame-tts-jetson' to avoid conflicts
if ! sudo docker image inspect sesame-tts-jetson &>/dev/null; then
    echo "Building Sesame TTS Docker container for Jetson..."
    # Build using the modified Dockerfile (docker/sesame-tts/Dockerfile)
    # NOTE: The Dockerfile now uses the following strategy:
    #   - Uses the dustynv/torchao:0.11.0-r36.4.0-cu128-24.04 base image (Requires JetPack 6.1+ / L4T r36.4.0+).
    #   - Relies on PyTorch 2.6, CUDA 12.8, Torchaudio, and torchao 0.11.0 provided by the base image.
    #   - Installs other dependencies (transformers, CSM deps, etc.) via pip.
    #   - Installs torchtune (trying PyPI first).
    #   - Downloads specific CSM source files (generator.py, models.py).
    #   - Creates a minimal CSM package structure and adds it to the Python path.
    #   - Includes a test script and a helpful entrypoint.
    sudo docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .
fi

# Run the container with direct script execution
# The script now uses generator.load_csm_1b() and generate()
# The --voice_preset argument provides context audio
# Note: The entrypoint script will run first, displaying usage info.
# Use the 'sesame-tts-jetson' tag
sudo docker run --runtime nvidia --rm \
  --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
  --volume ${HOME}/.cache/huggingface:/root/.cache/huggingface \
  --workdir /audiobook_data \
  sesame-tts-jetson python3 /books/generate_audiobook_sesame.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3 \
  --model_path /models/sesame-csm-1b \
  --voice_preset calm # Optional: Name of wav file in model_path/prompts

# Alternatively, run the container in interactive mode
# The entrypoint script will display usage info, then drop you into a bash shell.
# Use the 'sesame-tts-jetson' tag
sudo docker run --runtime nvidia -it --rm \
  --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
  --volume ${HOME}/.cache/huggingface:/root/.cache/huggingface \
  --workdir /audiobook_data \
  sesame-tts-jetson
```
*Note: We mount the host's Hugging Face cache (`~/.cache/huggingface`) to `/root/.cache/huggingface` inside the container. This allows the container to use the host's login token and potentially cached Llama model files.*

When using the interactive mode, you can first test the installation and then run the generation script:

```bash
# Test CSM installation (inside container)
# This script verifies model loading and performs a basic generation.
# Use python3 explicitly
python3 /usr/local/bin/utils/test_csm.py /models/sesame-csm-1b
# Note: If you encounter an error like:
# ImportError: torchao not installed...
# or
# ModuleNotFoundError: No module named 'torchao'
# This indicates an issue with the base Docker image (dustynv/torchao:...)
# or a conflict during the installation of other packages. Verify you are
# running JetPack 6.1+ (L4T r36.4.0+) as required by the base image.
# Check the Docker build logs for errors during the 'pip3 install' steps,
# especially for 'torchtune'.
#
# The Dockerfile no longer builds torchao manually; it relies on the version
# provided in the base image (torchao 0.11.0). Compatibility issues related
# to older torchao versions (like v0.2.0) or missing attributes
# (like 'needs_fixed_stride_order') should be resolved by using this updated base image.

# Generate an audiobook using Sesame (inside container)
# Use python3 explicitly
python3 /books/generate_audiobook_sesame.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3 \
  --model_path /models/sesame-csm-1b \
  --voice_preset calm # Optional
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

### Troubleshooting Disk Space Issues

If you encounter "No space left on device" errors during `git pull`, Docker builds, or other operations, you need to free up disk space. A large drive (like 1TB NVMe) can still fill up, especially with Docker images, build caches, and large datasets.

1.  **Check Disk Usage:**
    See how much space is used on your main storage device (usually mounted at `/`).
    ```bash
    df -h /
    # Look at the 'Use%' column. If it's near 100%, you need to clean up.
    ```
    Also check overall disk usage across all mounted filesystems:
    ```bash
    df -h
    ```
    **Note:** If `Use%` for `/` is very high (e.g., 95% or more, like the example 97%), cleanup is **urgent**. Docker builds and other operations will likely fail.

2.  **Clean Docker Resources:** Docker build caches, images, containers, and volumes are often major consumers of space. **Prioritize these steps if disk space is critically low.**
    ```bash
    # Remove stopped containers
    sudo docker container prune -f
    # Remove unused networks
    sudo docker network prune -f
    # Remove unused images (dangling and unreferenced) - Often recovers significant space
    sudo docker image prune -a -f
    # Remove build cache - Also often recovers significant space
    sudo docker builder prune -f
    # Remove unused volumes (Use with caution if you store persistent data in volumes)
    # sudo docker volume prune -f
    # Comprehensive cleanup (Use with extreme caution - removes all unused resources)
    # sudo docker system prune -a -f --volumes
    ```

3.  **Clean Apt Cache:** Remove downloaded package files (`.deb`).
    ```bash
    sudo apt-get clean
    # Remove packages that were automatically installed to satisfy dependencies
    # for other packages and are now no longer needed.
    sudo apt-get autoremove -y
    ```

4.  **Check Large Directories/Files:** Find large files or directories in your home folder or common data locations.
    ```bash
    # Check size of key directories (adjust paths as needed)
    du -sh ~/.cache/huggingface
    du -sh ~/audiobook_data
    du -sh ~/jetson-containers/data # If using jetson-containers
    du -sh ~/Downloads
    du -sh ~/.local/share/Trash # Check the trash folder
    du -sh /var/log # Check system log files size

    # Find top 10 largest files/dirs in your home directory (can take time)
    du -a ~ | sort -n -r | head -n 10

    # Optional: Install and use ncdu for interactive analysis
    # sudo apt install ncdu
    # ncdu ~  # Analyze home directory
    # ncdu /  # Analyze root filesystem (requires sudo)
    ```
    Delete files or directories you no longer need. Be careful not to delete essential system files. Empty the trash if applicable. Rotate or clear large log files in `/var/log` if necessary (advanced).

5.  **Reboot (Optional):** Sometimes a reboot can clear temporary files held by running processes.

After freeing up space using these methods, check `df -h /` again. If usage is well below 100% (e.g., < 90%), you should be able to retry the operation that failed (e.g., `git pull`, `docker build`).