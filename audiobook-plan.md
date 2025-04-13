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

**Important Pre-requisite: Download the Model Manually**

The `sesame/csm-1b` model requires authentication. You need to download it manually on your host machine first.

1.  **Install Hugging Face Hub CLI:**
    ```bash
    pip install -U huggingface_hub
    ```
2.  **Log in:**
    ```bash
    huggingface-cli login
    # Follow the prompts, you might need to create a token on huggingface.co
    ```
3.  **Download the model:** This will download the model files to a local cache directory (usually `~/.cache/huggingface/hub/models--sesame--csm-1b`).
    ```bash
    huggingface-cli download sesame/csm-1b --local-dir ~/huggingface_models/sesame-csm-1b --local-dir-use-symlinks False
    # We use a specific local dir and disable symlinks for easier mounting into Docker.
    # Make sure the directory ~/huggingface_models exists or adjust the path.
    mkdir -p ~/huggingface_models
    ```
    *Note: You may need to visit the model page on Hugging Face first (https://huggingface.co/sesame/csm-1b) and accept any terms or agreements.*

Now you can proceed with building and running the container.

```bash
# Option 1: Using the quickstart.sh script (recommended)
# The quickstart script needs modification to handle the pre-downloaded model.
# (Future improvement: Update quickstart.sh to detect/mount ~/huggingface_models/sesame-csm-1b)
# For now, use Option 2 (Manual Docker) for Sesame.
# ./quickstart.sh your_book.epub sesame

# Option 2: Manual Docker approach
# Check if sesame-tts image exists, build if not
if ! docker image inspect sesame-tts &>/dev/null; then
    echo "Building Sesame TTS Docker container..."
    # Build using the modified Dockerfile (model download step removed)
    sudo docker build -t sesame-tts -f docker/sesame-tts/Dockerfile .
fi

# Run the container with direct script execution, mounting the downloaded model
docker run --runtime nvidia --rm \
  --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
  --workdir /audiobook_data \
  sesame-tts python /books/generate_audiobook_sesame.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3 \
  --model_path /models/sesame-csm-1b \
  --voice_preset "calm"

# Alternatively, run the container in interactive mode, mounting the model
docker run --runtime nvidia -it --rm \
  --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
  --workdir /audiobook_data \
  sesame-tts
```

When using the interactive mode, you can then run commands inside the container, specifying the model path:

```bash
# Generate an audiobook using Sesame (inside container)
python /books/generate_audiobook_sesame.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_sesame.mp3 \
  --model_path /models/sesame-csm-1b \
  --voice_preset "calm"
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

### Monitoring the Build Process

**Monitoring from Another Terminal:** While the build is running in Terminal 1, you can monitor its progress from a second terminal by "tailing" the log file:
```bash
# On the Jetson host (Terminal 2)
tail -f ~/jetson-containers/build_log.txt 
```
Press `Ctrl+C` in Terminal 2 to stop monitoring.

**Alternative Monitoring (If Logs Weren't Redirected):** If you didn't redirect the build output, you can use system tools in Terminal 2 to see if the build is still active:
```bash
# Install monitoring tools (if not already installed)
sudo apt update
sudo apt install -y htop iotop

# Check CPU/Memory usage (look for docker, buildkitd, make, cc1plus, nvcc, etc.)
htop 
# (Press 'q' to quit)

# Check Disk I/O
sudo iotop
# (Press 'q' to quit)

# Check if the build was killed due to low memory (requires sudo)
sudo dmesg | grep -i kill
```
High CPU or disk activity suggests the build is still running. No activity might mean it's stalled or finished/failed. Output lines containing "oom-kill" or "Killed process" related to `docker` or build processes (like `cicc`, `cc1plus`, `nvcc`) strongly indicate the build failed due to running out of memory.

Try these solutions if the build failed:

1.  **Increase Swap Space**: (Recommended first step if OOM errors occurred *and* current swap is small)
    ```bash
    # Check current swap size and total memory
    # Look at the 'Swap:' line. If 'total' is 0 or very small (e.g., < 4Gi), you might need more swap.
    free -h
    # Example Output: Swap: 11Gi 309Mi 11Gi  <-- This shows 11Gi total swap already exists.

    # Check available disk space on the root filesystem (where swap file is usually created)
    # Look at the 'Avail' column for the '/' mount point. Ensure you have enough space 
    # (e.g., > 8GB) if you decide to create a *new* or *larger* swap file.
    df -h /
    # Example Output: /dev/nvme0n1p1 115G 65G 46G 59% / <-- This shows 46G available.

    # --- If your current swap is small (< 4Gi) AND you have disk space, create/increase it: ---
    # Create a 8GB swap file (adjust size '8G' if needed and if space permits)
    # sudo fallocate -l 8G /var/swapfile
    # sudo chmod 600 /var/swapfile
    # sudo mkswap /var/swapfile
    # sudo swapon /var/swapfile

    # Verify swap is active (check 'Swap:' line again)
    # free -h

    # Make swap permanent (add to /etc/fstab)
    # CAUTION: Only do this if you created a new swap file successfully.
    # Check if the line already exists before adding: grep -qxF '/var/swapfile swap swap defaults 0 0' /etc/fstab || echo '/var/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
    # echo '/var/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
    ```
    After increasing swap, **reboot your Jetson** or ensure the swap is active after creating it, then try the build again.
    **Note:** If `free -h` already shows significant swap (e.g., 8Gi or more), adding even more might not help, and you should proceed to Step 3.

2.  **Try Pre-built Container Layers**: (Usually automatic, but can be forced)
    ```bash
    # The build command automatically tries to pull pre-built layers
    ./jetson-containers build piper-tts
    ```

3.  **Build with Reduced Parallelism**: (Recommended if OOM errors occurred even with sufficient swap)
    If memory is still an issue even with swap, reduce the number of parallel build jobs. This significantly lowers peak memory usage during compilation.
    ```bash
    # On the Jetson host, navigate to the jetson-containers directory
    cd ~/jetson-containers

    # Try building with only 2 parallel jobs
    sudo ./jetson-containers build --make-flags="-j2" piper-tts

    # If that still fails, try with only 1 job (slowest but uses least memory)
    # sudo ./jetson-containers build --make-flags="-j1" piper-tts
    ```
    **Remember to capture logs** (`> build_log.txt 2>&1`) when trying these builds to analyze any further errors.

4.  **Reduce Compilation Resources**: (Advanced)
    ```bash
    # Modify /home/username/jetson-containers/packages/ml/onnxruntime/build.sh
    # Find the cmake command line and add:
    # -DONNX_USE_REDUCED_OPERATOR_TYPE_SET=1
    # Then rebuild using reduced parallelism (Step 3).
    ```

5.  **Use Sesame Approach**: If the Piper container build consistently fails, consider using the Sesame CSM approach instead, which uses a pre-built container or a simpler build process described in section 4.4.