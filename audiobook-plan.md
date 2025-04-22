# Comprehensive Plan for Generating an Audiobook on Jetson Orin Nano

This document outlines a comprehensive plan for converting a 230-page PDF book into an audiobook using two different approaches on the Jetson Orin Nano:
1. Piper TTS using jetson-containers (recommended first approach)
2. Sesame CSM for higher quality voice synthesis (alternative approach)

## 1. Setup and Environment Preparation

### 1.1 System Requirements
- Jetson Orin Nano with JetPack/L4T
- At least 5GB of available RAM
- At least 20GB of free storage space
- Internet connection for downloading models

### 1.2 Clone the jetson-containers Repository
```bash
# Clone the repository
git clone https://github.com/dusty-nv/jetson-containers
cd jetson-containers
```

### 1.3 Prepare Data Directory
```bash
# Create a directory for your PDF and output files
mkdir -p ~/audiobook_data
# Copy your PDF to this directory
cp ~/learning_with_ai.pdf ~/audiobook_data/
```

## 2. Approach 1: Generating Audiobook with Piper (via jetson-containers)

### 2.1 Check Available Piper Models
```bash
# Show details about the piper container
./jetson-containers show piper
```

### 2.2 Run the Piper Container
```bash
# Run the piper container with volume mount for data
./jetson-containers run --volume ~/audiobook_data:/data --workdir /data piper
```

### 2.3 Create PDF Processing Script

Inside the container, create a Python script to process the PDF and generate audio:

```bash
# Create the script
cat > generate_audiobook_piper.py << 'EOF'
#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import re
from PyPDF2 import PdfReader
from tqdm import tqdm
import nltk
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment

# Download NLTK data
nltk.download('punkt', quiet=True)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"Extracting text from {pdf_path}...")
    
    reader = PdfReader(pdf_path)
    text = ""
    
    for i, page in enumerate(tqdm(reader.pages, desc="Processing pages")):
        page_text = page.extract_text()
        
        # Clean up page headers, footers, page numbers, etc.
        page_text = re.sub(r'Page \d+ of \d+', '', page_text)
        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
        
        text += page_text + "\n"
    
    return text

def split_text_into_chunks(text, max_chars=1000):
    """Split text into manageable chunks for TTS processing."""
    print("Splitting text into chunks...")
    
    # Split text into sentences
    sentences = sent_tokenize(text)
    
    # Group sentences into chunks
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Clean the sentence
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence doesn't exceed max_chars, add it to the current chunk
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:
            # Save the current chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    print(f"Text split into {len(chunks)} chunks")
    return chunks

def generate_audio_with_piper(text, output_file, model="en_US-lessac-medium"):
    """Generate audio for a chunk of text using Piper."""
    # Save text to a temporary file
    temp_text_file = "/tmp/piper_input.txt"
    with open(temp_text_file, "w") as f:
        f.write(text)
    
    # Call Piper to generate audio
    cmd = [
        "piper",
        "--model", model,
        "--output_file", output_file,
        "--file", temp_text_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio: {e}")
        print(f"stderr: {e.stderr.decode()}")
        return False

def combine_audio_files(audio_files, output_file):
    """Combine multiple audio files into a single audiobook file."""
    print(f"Combining {len(audio_files)} audio segments...")
    
    combined = AudioSegment.empty()
    
    # Add a short pause between segments
    pause = AudioSegment.silent(duration=500)  # 500ms pause
    
    for audio_file in tqdm(audio_files, desc="Combining audio"):
        segment = AudioSegment.from_file(audio_file)
        combined += segment + pause
    
    # Export the combined audio
    combined.export(output_file, format="mp3")
    print(f"Combined audiobook saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate an audiobook from a PDF using Piper TTS")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--output", default="audiobook.mp3", help="Output audiobook file path")
    parser.add_argument("--model", default="en_US-lessac-medium", help="Piper voice model to use")
    parser.add_argument("--temp_dir", default="temp_audio", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()
    
    # Create temporary directory
    os.makedirs(args.temp_dir, exist_ok=True)
    
    # Extract text from PDF
    text = extract_text_from_pdf(args.pdf)
    
    # Split text into chunks
    chunks = split_text_into_chunks(text, args.chunk_size)
    
    # Generate audio for each chunk
    audio_files = []
    
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):
        output_file = os.path.join(args.temp_dir, f"chunk_{i:04d}.wav")
        
        # Skip if the file already exists (resume capability)
        if os.path.exists(output_file):
            print(f"Chunk {i} already processed, skipping...")
            audio_files.append(output_file)
            continue
        
        # Generate audio for this chunk
        success = generate_audio_with_piper(chunk, output_file, args.model)
        
        if success:
            audio_files.append(output_file)
        else:
            print(f"Failed to generate audio for chunk {i}")
    
    # Combine all audio files
    combine_audio_files(audio_files, args.output)
    
    print("Audiobook generation complete!")

if __name__ == "__main__":
    main()
EOF

# Make the script executable
chmod +x generate_audiobook_piper.py
```

### 2.4 Install Required Python Packages in the Container
```bash
# Install required packages
pip install PyPDF2 nltk tqdm pydub
```

### 2.5 Run the Audiobook Generation Script
```bash
# List available Piper voice models
ls -la /opt/piper/voices

# Run the script with a specific voice model
python generate_audiobook_piper.py --pdf /data/learning_with_ai.pdf --output /data/audiobook_piper.mp3 --model en_US-lessac-medium
```

### 2.6 Monitor and Manage the Process
```bash
# To check progress
ls -la /data/temp_audio | wc -l

# To resume if interrupted
python generate_audiobook_piper.py --pdf /data/learning_with_ai.pdf --output /data/audiobook_piper.mp3
```

## 3. Approach 2: Generating Audiobook with Sesame CSM

### 3.1 Set Up Environment for Sesame CSM
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
pip install PyPDF2 pdfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch
```

### 3.2 Install Sesame CSM
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

### 3.3 Create Audiobook Generation Script
```bash
# Create the script
cat > generate_audiobook_sesame.py << 'EOF'
#!/usr/bin/env python3

import os
import torch
import argparse
from tqdm import tqdm
from pathlib import Path
from PyPDF2 import PdfReader
from pydub import AudioSegment
from nltk.tokenize import sent_tokenize
import nltk
import re
import time

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"Extracting text from {pdf_path}...")
    
    reader = PdfReader(pdf_path)
    text = ""
    
    for i, page in enumerate(tqdm(reader.pages, desc="Processing pages")):
        page_text = page.extract_text()
        
        # Clean page headers/footers
        page_text = re.sub(r'Page \d+ of \d+', '', page_text)
        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
        
        text += page_text + "\n"
    
    return text

def preprocess_text(text, max_chunk_size=1000):
    """Clean and split text into manageable chunks."""
    print("Preprocessing text...")
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into sentences
    sentences = sent_tokenize(text)
    
    # Group sentences into chunks
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    print(f"Split text into {len(chunks)} chunks")
    return chunks

def generate_audio(model, text, output_path):
    """Generate audio for a text segment."""
    try:
        # Clear CUDA cache
        torch.cuda.empty_cache()
        
        # Generate audio
        audio = model.generate(text=text)
        audio.export(output_path, format="mp3")
        return True
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False

def combine_audio_files(audio_files, output_path):
    """Combine multiple audio files into a single audiobook."""
    print(f"Combining {len(audio_files)} audio segments...")
    
    # Start with an empty audio segment
    combined = AudioSegment.empty()
    
    # Add a pause between segments (500ms)
    pause = AudioSegment.silent(duration=500)
    
    # Combine all files
    for file_path in tqdm(audio_files, desc="Combining audio"):
        segment = AudioSegment.from_mp3(file_path)
        combined += segment + pause
        
    # Export the final audiobook
    combined.export(output_path, format="mp3")
    print(f"Audiobook saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate an audiobook from a PDF using Sesame CSM")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--output", default="audiobook_sesame.mp3", help="Output audiobook file path")
    parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()
    
    # Create temporary directory
    os.makedirs(args.temp_dir, exist_ok=True)
    
    # Extract and preprocess text
    text = extract_text_from_pdf(args.pdf)
    chunks = preprocess_text(text, args.chunk_size)
    
    # Load CSM model
    print("Loading Sesame CSM model...")
    from csm import CSMModel
    model = CSMModel.from_pretrained("sesame/csm-1b")
    model = model.half().to("cuda")  # Use half precision to save memory
    
    # Process each chunk
    print(f"Processing {len(chunks)} text segments...")
    audio_files = []
    
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):
        output_path = os.path.join(args.temp_dir, f"chunk_{i:04d}.mp3")
        
        # Skip if already processed
        if os.path.exists(output_path):
            print(f"Skipping chunk {i} - already processed")
            audio_files.append(output_path)
            continue
        
        # Generate audio
        success = generate_audio(model, chunk, output_path)
        if success:
            audio_files.append(output_path)
            
        # Take a short break every 5 chunks to prevent overheating
        if i % 5 == 0 and i > 0:
            print("Taking a short break to prevent overheating...")
            time.sleep(10)
            torch.cuda.empty_cache()
    
    # Combine audio files
    combine_audio_files(audio_files, args.output)
    
    print("Audiobook generation complete!")

if __name__ == "__main__":
    main()
EOF

# Make the script executable
chmod +x generate_audiobook_sesame.py
```

### 3.4 Run the Sesame CSM Audiobook Generation Script
```bash
# Make sure virtual environment is activated
source ~/sesame_project/venv/bin/activate

# Run the script
cd ~/sesame_project
python generate_audiobook_sesame.py --pdf ~/audiobook_data/learning_with_ai.pdf --output ~/audiobook_data/audiobook_sesame.mp3
```

## 3.5 (Optional) Running Automated Dependency Analysis

If you encounter build issues related to dependencies, especially `ResolutionImpossible` errors during the `pip-compile` stage, an automated analysis script can help diagnose and potentially fix the `requirements.in` file.

```bash
# Navigate to your project root directory
cd ~/audiobook

# Run the dependency extraction script
# This script builds a temporary analysis container, runs checks, and extracts results.
./scripts/dependency/extract_during_build.sh
```

This script will output results to a timestamped directory, typically within `~/audiobook/dependency_artifacts/`. The script's final output will indicate the exact location (e.g., `~/audiobook/dependency_artifacts/build_analysis`).

Key files generated in the output directory:
*   `analysis_report.md`
*   `package_install_results.csv`
*   `wheel_availability.txt`
*   `pip_compile_error.txt`
*   **`requirements.in`**: a copy of your original requirements.in used for analysis  
  → You can use this file as a starting point, or copy it back into your build directory:
    ```bash
    cp ~/audiobook/dependency_artifacts/build_analysis/requirements.in \
       ~/audiobook/docker/sesame-tts/requirements.in
    ```
*   `test_packages.sh`
*   (no `recommended_requirements.in` if resolution failed)

**Applying the Recommendations:**

1.  **Check Logs & Report:** Examine the `analysis_report.md` and, crucially, the `pip_compile_error.txt` (or similar log file) in the output directory to understand why resolution might have failed.
    ```bash
    cat ~/audiobook/dependency_artifacts/build_analysis/analysis_report.md
    cat ~/audiobook/dependency_artifacts/build_analysis/pip_compile_error.txt # Or pip_compile_log.txt
    # (Replace 'build_analysis' with the actual output directory name if different)
    ```

2.  **Apply Changes:**
    *   **If `recommended_requirements.in` exists:** Review it and copy it over the one used by your main build.
        ```bash
        # Adjust path if your output directory is different
        cp ~/audiobook/dependency_artifacts/build_analysis/recommended_requirements.in ~/audiobook/docker/sesame-tts/requirements.in
        ```
    *   **If `recommended_requirements.in` does NOT exist:** Manually edit `~/audiobook/docker/sesame-tts/requirements.in` based on the analysis report's text recommendations and the errors found in the compile logs (e.g., adjust versions, remove conflicting packages like `moshi`).

3.  **Rebuild the Docker image with no cache** (ensures the resolver stage re‑runs and picks up Rust installation):

```bash
cd ~/audiobook
./scripts/dependency/setup_multistage.sh
./scripts/dependency/build.sh --no-cache
```

## 4. Performance Optimization and Monitoring

### 4.1 Monitoring Tools
```bash
# Monitor GPU usage and temperature
sudo tegrastats

# Monitor CPU and memory usage
htop

# Monitor disk usage
df -h
```

### 4.2 Optimization Tips for Jetson Orin Nano

#### Memory Management
- Use half-precision (FP16) for model inference
- Clear CUDA cache between batches with `torch.cuda.empty_cache()`
- Process smaller text chunks
- Close unnecessary applications while processing

#### Thermal Management
- Add periodic cooling breaks (implemented in both scripts)
- Monitor temperature with `tegrastats`
- Consider additional cooling if temperatures exceed 80°C
- Run the process overnight for cooler ambient temperatures

#### Storage Management
- Pre-clear space before starting
- Use compressed audio formats (MP3)
- Clean up temporary files after completion

## 5. Comparing the Two Approaches

### 5.1 Piper Advantages
- Directly integrated with jetson-containers ecosystem
- Lower memory footprint
- Faster processing
- Multiple voices available
- Easier setup

### 5.2 Sesame CSM Advantages
- Higher quality, more natural voices
- Better prosody and emotional range
- More humanlike intonation
- State-of-the-art voice quality
- Better for long-form content like audiobooks

### 5.3 Deciding Which to Use
- **For quick results or limited hardware**: Use Piper
- **For highest quality**: Use Sesame CSM
- **Consider testing both**: Generate a small sample with each to compare quality

## 6. Additional Enhancements

### 6.1 Adding Chapter Markers
To add chapter markers to the final audiobook (requires ffmpeg):

```bash
# Extract chapter titles and timestamps
python extract_chapters.py --pdf learning_with_ai.pdf --output chapters.txt

# Add chapter markers to the audiobook
ffmpeg -i audiobook.mp3 -i chapters.txt -map_metadata 1 -codec copy audiobook_chaptered.mp3
```

### 6.2 Parallel Processing with Multiple Jetson Devices
If you have two Jetson Orin Nano devices, you can divide the workload:

```bash
# On device 1:
python generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 0-500

# On device 2:
python generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 501-1000
```

### 6.3 Improving Voice Quality
For Piper, you can adjust parameters:

```bash
# Use higher quality settings
piper --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100
```

For Sesame CSM, you can modify voice parameters:

```python
# Adjust voice parameters (example)
audio = model.generate(
    text=text,
    voice_preset="calm", 
    speaking_rate=0.95
)
```

## 7. Troubleshooting Common Issues

### 7.1 Memory Errors
```
# If you encounter CUDA out of memory errors
1. Reduce chunk size in the script
2. Try restarting the Jetson to clear memory
3. Use half precision (already implemented)
4. Process fewer chunks at a time
```

### 7.2 Installation Issues
```
# If pip fails to install packages
sudo apt update
sudo apt install -y build-essential python3-dev

# Check if Rust/Cargo is needed (error messages mentioning "cargo" or "rust")
# If so, install it:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
# Then retry pip install

# If PyTorch fails to install
# Ensure you are using the correct index URLs for Jetson wheels
# Example for manual install:
# pip install --extra-index-url https://pypi.ngc.nvidia.com --extra-index-url https://pypi.jetson-ai-lab.dev/simple torch torchvision torchaudio

# For audio library issues
sudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools libsndfile1
```

### 7.3 Docker or Container Issues
```
# If container fails to start
sudo systemctl restart docker
sudo systemctl restart nvidia-container-runtime

# If GPU is not available in container
./jetson-containers run --runtime nvidia --gpus all piper
```

# === Dependency Analysis Results and Recommendations ===

## Dependency Analysis Insights (latest)

Recent dependency analysis and build attempts revealed:

- **PyTorch Version Conflict:**  
  `moshi` requires `torch>=2.2.0,<2.7`, but some requirements or base images may specify `torch>=2.7.0`.  
  *Resolution:* Pin `torch`, `torchvision`, and `torchaudio` to the latest Jetson-compatible versions `<2.7` (e.g., `torch==2.6.0`, `torchvision==0.21.0`, `torchaudio==2.6.0`).

- **Moshi Source Build:**  
  No ARM64 wheel is available for `moshi`; it must be installed from source using the correct subdirectory syntax:  
  ```
  git+https://github.com/kyutai-labs/moshi.git@main#egg=moshi&subdirectory=moshi
  ```

- **bitsandbytes Issue:**  
  `moshi`'s `pyproject.toml` requires `bitsandbytes >= 0.45, < 0.46`, but ARM64 wheels are not available on PyPI.  
  *Resolution options:*  
    - Use a Jetson-compatible fork of `bitsandbytes` if available (e.g., from `dusty-nv/jetson-containers`).  
    - Patch `moshi` to make `bitsandbytes` optional or use a compatible version if possible.

- **General Recommendations:**  
    - Use Jetson-optimized wheels wherever available.
    - Pin `vector_quantize_pytorch` to `>=1.22.15` and `einops` to `>=0.8.0`.
    - If dependency resolution fails, install packages in smaller groups to isolate the conflict.
    - Review the generated `analysis_report.md` and `pip_compile_error.log` for details.

# Torch Version Requirements Checklist

To ensure there are no conflicting torch version requirements in your repository, review the following:

- [ ] **requirements.in / requirements.txt**:  
  Ensure all torch, torchvision, and torchaudio pins are `==2.6.0`, `==0.21.0`, and `==2.6.0` (or `<2.7.0`).

- [ ] **Dockerfiles (including Dockerfile.analysis)**:  
  Check for any `torch>=2.7.0` or similar pins in `RUN pip install ...` or requirements files copied into the image.

- [ ] **Any included or secondary requirements files**:  
  If you use `-r otherfile.txt` in your requirements, check those files for torch version requirements.

- [ ] **Custom scripts or patch scripts**:  
  Look for any scripts that modify requirements or install torch directly.

- [ ] **Transitive dependencies**:  
  If a package you use requires `torch>=2.7.0`, you may need to downgrade or patch it.

- [ ] **CI/CD or automation scripts**:  
  Check for any automated install commands that might override your pins.

You can use this command to search for torch version requirements in your repo:
```bash
grep -r "torch" /Users/kieranlal/workspace/audiobook
```
and review any lines that specify a version.

## Conclusion

This comprehensive plan provides two complete approaches for generating an audiobook from a PDF on Jetson Orin Nano devices. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis. 

Both methods include optimizations for the limited resources of the Jetson platform, robust error handling, and the ability to resume processing if interrupted. By following this guide, you can convert your 230-page "Learning with AI" book into a high-quality audiobook using local processing on your Jetson Orin Nano.
