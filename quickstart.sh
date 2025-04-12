#!/bin/bash

# Quick Start Script for Audiobook Generation on Jetson Orin Nano
# This script provides a simple way to get started with audiobook generation

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

# Setup directories
echo "Setting up directories..."
mkdir -p ~/audiobook_data
mkdir -p ~/audiobook

# Check for input file
if [ "$1" == "" ]; then
    echo "No input file specified."
    echo "Usage: ./quickstart.sh /path/to/your/book.epub [piper|sesame]"
    exit 1
fi

# Copy book file to audiobook directory
BOOK_FILE="$1"
BOOK_FILENAME=$(basename "$BOOK_FILE")
cp "$BOOK_FILE" ~/audiobook/
echo "Copied $BOOK_FILENAME to ~/audiobook/"

# Determine which method to use
METHOD=${2:-piper}  # Default to piper if not specified

if [ "$METHOD" == "piper" ]; then
    echo "===================================================="
    echo "     Starting audiobook generation using Piper      "
    echo "===================================================="
    
    # Check if jetson-containers exists, clone if not
    if [ ! -d ~/jetson-containers ]; then
        echo "Cloning jetson-containers repository..."
        git clone https://github.com/dusty-nv/jetson-containers ~/jetson-containers
    fi
    
    # Navigate to jetson-containers
    cd ~/jetson-containers
    
    # Run the piper-tts container
    echo "Starting Piper TTS container..."
    ./jetson-containers run --volume ~/audiobook_data:/audiobook_data \
        --volume ~/audiobook:/books \
        --workdir /audiobook_data $(./autotag piper-tts)
    
    echo 
    echo "Now inside the container, run:"
    echo "pip install PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4 psutil"
    echo "python /books/generate_audiobook_piper.py --input /books/$BOOK_FILENAME --output /audiobook_data/audiobook_piper.mp3 --model /opt/piper/voices/en/en_US-lessac-medium.onnx"
    
elif [ "$METHOD" == "sesame" ]; then
    echo "===================================================="
    echo "    Starting audiobook generation using Sesame CSM  "
    echo "===================================================="
    
    # Setup environment for Sesame CSM
    echo "Setting up environment for Sesame CSM..."
    sudo apt update
    sudo apt install -y python3-venv python3-pip ffmpeg libsndfile1
    
    # Create project directory
    mkdir -p ~/sesame_project
    cd ~/sesame_project
    
    # Create and activate virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    echo "Installing dependencies (this may take a while)..."
    pip install --upgrade pip
    pip install PyPDF2 pdfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch ebooklib beautifulsoup4
    
    # Clone the repository if it doesn't exist
    if [ ! -d ~/sesame_project/csm ]; then
        echo "Cloning Sesame CSM repository..."
        git clone https://github.com/SesameAILabs/csm.git
        cd csm
        pip install -e .
        
        # Download the model
        echo "Downloading the CSM model (this may take a while)..."
        python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"
        cd ..
    fi
    
    echo
    echo "Now run:"
    echo "source ~/sesame_project/venv/bin/activate"
    echo "python ~/audiobook/generate_audiobook_sesame.py --input ~/audiobook/$BOOK_FILENAME --output ~/audiobook_data/audiobook_sesame.mp3 --voice_preset 'calm'"
    
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
echo "Output will be saved to: ~/audiobook_data/"
echo
echo "For more options and advanced configuration, see:"
echo "~/audiobook/audiobook-plan.md"
echo
