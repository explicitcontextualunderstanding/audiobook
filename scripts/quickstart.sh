#!/bin/bash

# Improved Quick Start Script for Audiobook Generation on Jetson Orin Nano
# This script provides an enhanced experience for audiobook generation

# Display header
echo "===================================================="
echo "      Audiobook Generation Quick Start Script       "
echo "===================================================="
echo

# Check if running on Jetson
if ! grep -q "NVIDIA Jetson" /proc/device-tree/model 2>/dev/null; then
    echo "WARNING: This doesn't appear to be a Jetson device."
    echo "This script is optimized for Jetson Orin Nano."
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ $continue_anyway != "y" ]]; then
        echo "Exiting."
        exit 1
    fi
fi

# Parse command line arguments
BOOK_FILE=""
METHOD="piper"  # Default to piper
VOICE_PRESET="lessac"  # Default voice preset for Piper
CHAPTER_RANGE=""  # Default to process all chapters
MEMORY_PER_CHUNK=0  # Default to auto-detection
MAX_BATCH_SIZE=0    # Default to auto-detection
OUTPUT_FORMAT="mp3" # Default output format

# Function to show usage
show_usage() {
    echo "Usage: ./quickstart.sh [options]"
    echo
    echo "Required options:"
    echo "  --input FILE               Path to input book file (EPUB or PDF)"
    echo
    echo "Optional options:"
    echo "  --method METHOD            TTS method to use: 'piper' (faster) or 'sesame' (higher quality)"
    echo "                             Default: piper"
    echo "  --voice VOICE              Voice preset to use"
    echo "                             For piper: lessac (default), ryan, jenny, kathleen, alan"
    echo "                             For sesame: calm (default), excited, authoritative, gentle, narrative"
    echo "  --chapter-range RANGE      Range of chapters to process (e.g., '1-5')"
    echo "  --memory-per-chunk SIZE    Memory usage per chunk in MB"
    echo "  --max-batch-size SIZE      Maximum batch size for processing"
    echo "  --output-format FORMAT     Output format: mp3 (default), wav, flac"
    echo "  --help                     Show this help message"
    echo
    echo "Examples:"
    echo "  ./quickstart.sh --input book.epub"
    echo "  ./quickstart.sh --input book.epub --method sesame --voice calm"
    echo "  ./quickstart.sh --input book.epub --method piper --voice ryan --chapter-range 1-5"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --input)
            BOOK_FILE="$2"
            shift 2
            ;;
        --method)
            METHOD="$2"
            shift 2
            ;;
        --voice)
            VOICE_PRESET="$2"
            shift 2
            ;;
        --chapter-range)
            CHAPTER_RANGE="$2"
            shift 2
            ;;
        --memory-per-chunk)
            MEMORY_PER_CHUNK="$2"
            shift 2
            ;;
        --max-batch-size)
            MAX_BATCH_SIZE="$2"
            shift 2
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check if input file is provided
if [ -z "$BOOK_FILE" ]; then
    echo "Error: No input file specified."
    show_usage
fi

# Check if input file exists
if [ ! -f "$BOOK_FILE" ]; then
    echo "Error: Input file '$BOOK_FILE' does not exist."
    exit 1
fi

# Setup directories with improved error handling
echo "Setting up directories..."
mkdir -p ~/audiobook_data || { echo "Error: Failed to create directory ~/audiobook_data"; exit 1; }
mkdir -p ~/audiobook || { echo "Error: Failed to create directory ~/audiobook"; exit 1; }

# Copy book file to audiobook directory
BOOK_FILENAME=$(basename "$BOOK_FILE")
cp "$BOOK_FILE" ~/audiobook/ || { echo "Error: Failed to copy $BOOK_FILE to ~/audiobook/"; exit 1; }
echo "Copied $BOOK_FILENAME to ~/audiobook/"

# Set auto-detected memory parameters based on the method
if [ "$MEMORY_PER_CHUNK" -eq 0 ]; then
    if [ "$METHOD" == "piper" ]; then
        MEMORY_PER_CHUNK=50
    else
        MEMORY_PER_CHUNK=150
    fi
fi

if [ "$MAX_BATCH_SIZE" -eq 0 ]; then
    if [ "$METHOD" == "piper" ]; then
        MAX_BATCH_SIZE=15
    else
        MAX_BATCH_SIZE=8
    fi
fi

# Process based on method
if [ "$METHOD" == "piper" ]; then
    echo "===================================================="
    echo "     Starting audiobook generation using Piper      "
    echo "===================================================="
    
    # Check if jetson-containers exists, clone if not
    if [ ! -d ~/jetson-containers ]; then
        echo "Cloning jetson-containers repository..."
        git clone https://github.com/dusty-nv/jetson-containers ~/jetson-containers || {
            echo "Error: Failed to clone jetson-containers repository."
            exit 1
        }
    fi
    
    # Navigate to jetson-containers
    cd ~/jetson-containers
    
    # Set voice model path based on preset
    case "$VOICE_PRESET" in
        lessac)
            MODEL_PATH="/opt/piper/voices/en/en_US-lessac-medium.onnx"
            ;;
        ryan)
            MODEL_PATH="/opt/piper/voices/en/en_US-ryan-medium.onnx"
            ;;
        jenny)
            MODEL_PATH="/opt/piper/voices/en/en_GB-jenny-medium.onnx"
            ;;
        kathleen)
            MODEL_PATH="/opt/piper/voices/en/en_US-kathleen-medium.onnx"
            ;;
        alan)
            MODEL_PATH="/opt/piper/voices/en/en_GB-alan-medium.onnx"
            ;;
        *)
            echo "Warning: Unknown voice preset '$VOICE_PRESET' for Piper. Using lessac."
            MODEL_PATH="/opt/piper/voices/en/en_US-lessac-medium.onnx"
            ;;
    esac
    
    # Check for existing container
    CONTAINER_ID=$(docker ps -aq --filter "name=piper-tts" --filter "status=running")
    
    if [ -n "$CONTAINER_ID" ]; then
        echo "Using existing Piper TTS container (ID: $CONTAINER_ID)..."
        
        # Create a command to run inside the container
        CMD="python /books/generate_audiobook_piper.py --input /books/$BOOK_FILENAME --output /audiobook_data/audiobook_piper.$OUTPUT_FORMAT --model $MODEL_PATH --temp_dir /audiobook_data/temp_audio_piper --max_batch_size $MAX_BATCH_SIZE --memory_per_chunk $MEMORY_PER_CHUNK"
        
        # Add chapter range if specified
        if [ -n "$CHAPTER_RANGE" ]; then
            CMD="$CMD --chapter_range $CHAPTER_RANGE"
        fi
        
        # Execute the command in the existing container
        docker exec -it $CONTAINER_ID /bin/bash -c "pip install -q PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4 psutil && $CMD"
    else
        # Run the piper-tts container
        echo "Starting Piper TTS container..."
        
        # Create a script to run inside the container
        SCRIPT_FILE=$(mktemp)
        cat > $SCRIPT_FILE << EOL
#!/bin/bash
pip install -q PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4 psutil
python /books/generate_audiobook_piper.py --input /books/$BOOK_FILENAME --output /audiobook_data/audiobook_piper.$OUTPUT_FORMAT --model $MODEL_PATH --temp_dir /audiobook_data/temp_audio_piper --max_batch_size $MAX_BATCH_SIZE --memory_per_chunk $MEMORY_PER_CHUNK $([ -n "$CHAPTER_RANGE" ] && echo "--chapter_range $CHAPTER_RANGE")
EOL
        
        chmod +x $SCRIPT_FILE
        
        # Run the container with the script
        ./jetson-containers run \
            --volume ~/audiobook_data:/audiobook_data \
            --volume ~/audiobook:/books \
            --volume $SCRIPT_FILE:/tmp/run_piper.sh \
            --workdir /audiobook_data \
            $(./autotag piper-tts) \
            /tmp/run_piper.sh
            
        # Clean up temporary script
        rm $SCRIPT_FILE
    fi
    
    echo "Audiobook generation with Piper complete!"
    echo "Your audiobook is available at: ~/audiobook_data/audiobook_piper.$OUTPUT_FORMAT"
    
elif [ "$METHOD" == "sesame" ]; then
    echo "===================================================="
    echo "    Starting audiobook generation using Sesame CSM  "
    echo "===================================================="
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Please install Docker first."
        echo "Visit https://docs.docker.com/engine/install/ for installation instructions."
        exit 1
    fi

    # Check for Hugging Face models
    if [ ! -d ~/huggingface_models/sesame-csm-1b ]; then
        echo "Sesame CSM model not found at ~/huggingface_models/sesame-csm-1b"
        echo "Would you like to attempt to download it? (Requires Hugging Face account and login) [y/n]"
        read -p "> " download_model
        
        if [[ $download_model == "y" ]]; then
            echo "Installing Hugging Face Hub CLI..."
            pip install -q -U huggingface_hub
            
            echo "Please log in to Hugging Face (requires account and token)..."
            huggingface-cli login
            
            echo "Creating target directory..."
            mkdir -p ~/huggingface_models
            
            echo "Downloading model (this may take some time)..."
            huggingface-cli download sesame/csm-1b --local-dir ~/huggingface_models/sesame-csm-1b --local-dir-use-symlinks False
        else
            echo "Model download cancelled. Cannot proceed without the model."
            exit 1
        fi
    fi
    
    # Check for existing sesame-tts image
    if ! docker image inspect sesame-tts-jetson &>/dev/null; then
        echo "Sesame TTS image not found. Building it now (this may take a while)..."
        
        # Build the Docker image using the provided Dockerfile
        (cd ~/workspace/audiobook && \
         docker build -t sesame-tts-jetson -f docker/sesame-tts/Dockerfile .) || {
            echo "Error: Failed to build Sesame TTS Docker image."
            exit 1
        }
    fi
    
    # Determine the voice preset file path
    VOICE_PRESET_ARG=""
    if [ -n "$VOICE_PRESET" ]; then
        VOICE_PRESET_ARG="--voice_preset $VOICE_PRESET"
    fi
    
    # Build the command for running in the container
    CMD="python3 /books/generate_audiobook_sesame.py --input /books/$BOOK_FILENAME --output /audiobook_data/audiobook_sesame.$OUTPUT_FORMAT --model_path /models/sesame-csm-1b $VOICE_PRESET_ARG --max_batch_size $MAX_BATCH_SIZE --memory_per_chunk $MEMORY_PER_CHUNK"
    
    # Add chapter range if specified
    if [ -n "$CHAPTER_RANGE" ]; then
        CMD="$CMD --chapter_range $CHAPTER_RANGE"
    fi
    
    # Check for existing container
    CONTAINER_ID=$(docker ps -aq --filter "name=sesame-tts" --filter "status=running")
    
    if [ -n "$CONTAINER_ID" ]; then
        echo "Using existing Sesame TTS container (ID: $CONTAINER_ID)..."
        
        # Execute the command in the existing container
        docker exec -it $CONTAINER_ID /bin/bash -c "$CMD"
    else
        echo "Starting Sesame TTS container..."
        echo
        echo "Your audiobook will be available at: ~/audiobook_data/audiobook_sesame.$OUTPUT_FORMAT"
        echo
        
        # Run the container with the script
        docker run --runtime nvidia -it --rm \
            --name sesame-tts \
            --volume ~/audiobook_data:/audiobook_data \
            --volume ~/audiobook:/books \
            --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
            --volume ${HOME}/.cache/huggingface:/root/.cache/huggingface \
            --workdir /audiobook_data \
            sesame-tts-jetson /opt/conda/bin/conda run -n tts --no-capture-output $CMD
    fi
    
    echo "Audiobook generation with Sesame CSM complete!"
    echo "Your audiobook is available at: ~/audiobook_data/audiobook_sesame.$OUTPUT_FORMAT"
else
    echo "Unknown method: $METHOD"
    echo "Valid methods are: piper, sesame"
    exit 1
fi

echo
echo "===================================================="
echo "             Setup process completed                "
echo "===================================================="
echo
echo "Your book is located at: ~/audiobook/$BOOK_FILENAME"
echo "Output saved to: ~/audiobook_data/"
echo
echo "For more options and advanced configuration, see:"
echo "~/audiobook/audiobook-plan.md"
echo
