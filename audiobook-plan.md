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
# Create directories for your data and ePub files
mkdir -p ~/audiobook_data
mkdir -p ~/audiobook

# Copy your ePub file to the books directory
cp ~/learning_ai.epub ~/audiobook/
```

## 2. Approach 1: Generating Audiobook with Piper (via jetson-containers)

### 2.1 Check Available Piper Models
```bash
# Show details about the piper-tts container (note the correct package name)
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

### 2.3 Create ePub Processing Script and Test Piper

Inside the container, first test Piper with the included test voice model:

```bash
# Test Piper with a simple sentence (note: Piper reads from stdin)
echo "This is a test of the Piper text to speech system." > test.txt
cat test.txt | piper -m /opt/piper/etc/test_voice.onnx -f /audiobook_data/test.wav

# Install ffmpeg and convert to MP3 format
apt-get update && apt-get install -y ffmpeg
ffmpeg -i /audiobook_data/test.wav -y -codec:a libmp3lame -qscale:a 2 /audiobook_data/test.mp3

# Now create the ePub processing script

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
    chapter_titles = []
    combined = AudioSegment.empty()
    # Common chapter heading patterns
    # Add a short pause between segments
    pause = AudioSegment.silent(duration=500)  # 500ms pause
        r'^CHAPTER\s+\d+',  # "CHAPTER 1", "CHAPTER 2", etc.
    for audio_file in tqdm(audio_files, desc="Combining audio"):tle"
        segment = AudioSegment.from_file(audio_file)
        combined += segment + pauseendix sections
    ]
    # Export the combined audio
    combined.export(output_file, format="mp3")
    print(f"Combined audiobook saved to {output_file}")ing
        first_line = chunk.split('\n')[0] if '\n' in chunk else chunk[:100]
def main():
    parser = argparse.ArgumentParser(description="Generate an audiobook from a PDF using Piper TTS")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--output", default="audiobook.mp3", help="Output audiobook file path")
    parser.add_argument("--model", default="en_US-lessac-medium", help="Piper voice model to use")
    parser.add_argument("--temp_dir", default="temp_audio", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()cted or the first chunk isn't a chapter,
    # treat the beginning as chapter 1
    # Create temporary directory chapter_boundaries[0] != 0:
    os.makedirs(args.temp_dir, exist_ok=True)
        chapter_titles.insert(0, "Chapter 1")
    # Extract text from PDF
    text = extract_text_from_pdf(args.pdf)les
    
    # Split text into chunkso_files, output_dir, chapter_boundaries=None, chapter_titles=None):
    chunks = split_text_into_chunks(text, args.chunk_size)
    print(f"Organizing {len(audio_files)} audio segments into chapters...")
    # Generate audio for each chunk
    audio_files = []ut_dir, exist_ok=True)
    
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):
        output_file = os.path.join(args.temp_dir, f"chunk_{i:04d}.wav")
        chapter_boundaries = [0]
        # Skip if the file already exists (resume capability)
        if os.path.exists(output_file):
            print(f"Chunk {i} already processed, skipping...")
            audio_files.append(output_file):
            continuechapter_boundaries[i]
        end_idx = chapter_boundaries[i+1] if i+1 < len(chapter_boundaries) else len(audio_files)
        # Generate audio for this chunk
        success = generate_audio_with_piper(chunk, output_file, args.model)
        chapter_title = chapter_titles[i]
        if success:= re.sub(r'[^\w\s-]', '', chapter_title).strip().replace(' ', '_')
            audio_files.append(output_file)e_title}.mp3"
        else:t_file = os.path.join(output_dir, chapter_filename)
            print(f"Failed to generate audio for chunk {i}")
        print(f"Creating chapter file: {chapter_filename}")
    # Combine all audio files
    combine_audio_files(audio_files, args.output)pter
        chapter_segments = audio_files[start_idx:end_idx]
    print("Audiobook generation complete!")
        # Skip if no segments for this chapter
if __name__ == "__main__":ments:
    main()  print(f"No audio segments for chapter {i+1} - skipping")
EOF         continue
            
# Make the script executableent.empty()
chmod +x generate_audiobook_piper.pyduration=500)  # 500ms pause
```     
        for audio_file in tqdm(chapter_segments, desc=f"Combining audio for chapter {i+1}"):
### 2.4 Install Required Python Packages in the Container
```bash     combined += segment + pause
# Install required packages
pip install PyPDF2 nltk tqdm pydub
```     combined.export(output_file, format="mp3")
        print(f"Chapter {i+1} saved to {output_file}")
### 2.5 Run the Audiobook Generation Script
```bashnt(f"All chapter audio files saved to {output_dir}")
# Create necessary directories
mkdir -p /audiobook_data/temp_audio_piper
# Run the script with the test voice models_pipeription="Generate an audiobook from a PDF using Piper TTS")
python /books/generate_audiobook_piper_epub.py \
  --epub /books/learning_ai.epub \ce modeldir", default="audiobook_chapters", help="Output directory for chapter files")
  --output /audiobook_data/audiobook_piper.mp3 \S-lessac-medium", help="Piper voice model to use")
  --model /opt/piper/etc/test_voice.onnx \p_audio", help="Directory for temporary audio files")
  --temp_dir /audiobook_data/temp_audio_piperters_piper \int, default=1000, help="Maximum characters per chunk")
```-model /opt/piper/etc/test_voice.onnx \ args = parser.parse_args()
  --temp_dir /audiobook_data/temp_audio_piper    
### 2.6 Monitor and Manage the Process
```bashs(args.temp_dir, exist_ok=True)
# To check progress Manage the Processs.output_dir, exist_ok=True)
ls -la /audiobook_data/temp_audio_piper | wc -l
# To resume if interrupted, just run the same command again
python /books/generate_audiobook_piper_epub.py \
  --epub /books/learning_ai.epub \un the same command again
  --output /audiobook_data/audiobook_piper.mp3 \
  --model /opt/piper/etc/test_voice.onnx \nk_size)
  --temp_dir /audiobook_data/temp_audio_piper_piper \
```-model /opt/piper/etc/test_voice.onnx \ # Detect chapter boundaries
  --temp_dir /audiobook_data/temp_audio_piper    chapter_boundaries, chapter_titles = detect_chapter_boundaries(chunks)
## 3. Understanding Container and Host File Locations
    
Important path mappings:ainer and Host File Locations each chunk
    audio_files = []
| Inside Container | On Jetson Host |
|-----------------|----------------|
| `/audiobook_data` | `~/audiobook_data` |r, f"chunk_{i:04d}.wav")
| `/books` | `~/audiobook` |-------|
| `/data` | `~/jetson-containers/data` (default mapping) |
| `/books` | `~/audiobook` |        if os.path.exists(output_file):
When running commands:containers/data` (default mapping) |unk {i} already processed, skipping...")
- Use container paths (like `/audiobook_data`) when inside the container
- Use host paths (like `~/audiobook_data`) when on the Jetson host
- Use container paths (like `/audiobook_data`) when inside the container        
Note: Files saved to `/data` inside the container will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`.
        success = generate_audio_with_piper(chunk, output_file, args.model)
### 3.1 Set Up Environment for Sesame CSMontainer will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`.
```bashcess:
# Install system dependenciesr Sesame CSMd(output_file)
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg libsndfile1
sudo apt update    
# Create project directory3-venv python3-pip ffmpeg libsndfile1by chapter
mkdir -p ~/sesame_projectir, chapter_boundaries, chapter_titles)
cd ~/sesame_projectrectory
mkdir -p ~/sesame_project    print("Audiobook chapter generation complete!")
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activatertual environment
python3 -m venv venvEOF
# Install Python dependencies
pip install --upgrade pip
pip install PyPDF2 pdfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch
``` install --upgrade pip
pip install PyPDF2 pdfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch
### 3.2 Install Sesame CSMontainer
```bash
# Clone the repository CSMkages
git clone https://github.com/SesameAILabs/csm.git
cd csme the repository
git clone https://github.com/SesameAILabs/csm.git
# Install in development mode
pip install -e .
# Install in development mode# Create necessary directories
# Download the model/temp_audio_piper
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"
# Download the modelpython /books/generate_audiobook_piper_epub.py \
# Go back to project directoryb import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"ub \
cd .. /audiobook_data/audiobook_piper.mp3 \
```o back to project directory-model /opt/piper/etc/test_voice.onnx \
cd ..  --temp_dir /audiobook_data/temp_audio_piper
### 3.3 Create Audiobook Generation Script
```bash
# Create the scriptobook Generation Script Manage the Process
cat > generate_audiobook_sesame.py << 'EOF'
#!/usr/bin/env python3
cat > generate_audiobook_sesame.py << 'EOF'ls -la /audiobook_data/temp_audio_piper | wc -l
import osn/env python3me if interrupted, just run the same command again
import torchudiobook_piper_epub.py \
import argparseing_ai.epub \
from tqdm import tqdmiobook_piper.mp3 \
from pathlib import Pathce.onnx \
from PyPDF2 import PdfReaderudio_piper
from pydub import AudioSegment
from nltk.tokenize import sent_tokenize
import nltkimport AudioSegmentstanding Container and Host File Locations
import re.tokenize import sent_tokenize
import timeath mappings:
import re
# Download NLTK resources if not already downloaded
try:----------|----------------|
    nltk.data.find('tokenizers/punkt')dy downloadeda` |
except LookupError:
    nltk.download('punkt')zers/punkt')ainers/data` (default mapping) |
except LookupError:
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"Extracting text from {pdf_path}...")n host
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path) {pdf_path}...")ide the container will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`.
    text = ""
    reader = PdfReader(pdf_path)3.1 Set Up Environment for Sesame CSM
    for i, page in enumerate(tqdm(reader.pages, desc="Processing pages")):
        page_text = page.extract_text()
        i, page in enumerate(tqdm(reader.pages, desc="Processing pages")): update
        # Clean page headers/footerst()hon3-pip ffmpeg libsndfile1
        page_text = re.sub(r'Page \d+ of \d+', '', page_text)
        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
        page_text = re.sub(r'Page \d+ of \d+', '', page_text) ~/sesame_project
        text += page_text + "\n"*\d+\s*$', '', page_text, flags=re.MULTILINE)
        
    return text page_text + "\n"tivate virtual environment
    python3 -m venv venv
def preprocess_text(text, max_chunk_size=1000):
    """Clean and split text into manageable chunks."""
    print("Preprocessing text...")k_size=1000):
    """Clean and split text into manageable chunks."""install --upgrade pip
    # Remove extra whitespace...")ix nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove extra whitespace
    # Split into sentences' ', text).strip()
    sentences = sent_tokenize(text)
    # Split into sentencesone the repository
    # Group sentences into chunkst)meAILabs/csm.git
    chunks = []
    current_chunk = ""into chunks
    chunks = []stall in development mode
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + " "
        else:n(current_chunk) + len(sentence) < max_chunk_size:om huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            chunks.append(current_chunk.strip())
    if current_chunk:hunk = sentence + " "
        chunks.append(current_chunk.strip())
        urrent_chunk:Create Audiobook Generation Script
    print(f"Split text into {len(chunks)} chunks")
    return chunks
    print(f"Split text into {len(chunks)} chunks")cat > generate_audiobook_sesame.py << 'EOF'
def generate_audio(model, text, output_path):
    """Generate audio for a text segment."""
    try:rate_audio(model, text, output_path):s
        # Clear CUDA cachea text segment."""
        torch.cuda.empty_cache()
        # Clear CUDA cachem import tqdm
        # Generate audio_cache()
        audio = model.generate(text=text)
        audio.export(output_path, format="mp3")
        return Trueel.generate(text=text)import sent_tokenize
    except Exception as e:t_path, format="mp3")
        print(f"Error generating audio: {e}")
        return False as e:
        print(f"Error generating audio: {e}")
def combine_audio_files(audio_files, output_path):
    """Combine multiple audio files into a single audiobook."""
    print(f"Combining {len(audio_files)} audio segments...")
    chapter_titles = []"""Combine multiple audio files into a single audiobook."""pt LookupError:
    # Start with an empty audio segment
    combined = AudioSegment.empty()ns
    chapter_patterns = [# Start with an empty audio segmentextract_text_from_pdf(pdf_path):
    # Add a pause between segments (500ms) "Chapter 2", etc.
    pause = AudioSegment.silent(duration=500)HAPTER 2", etc.
        r'^\d+\.\s+',       # "1. Chapter Title", "2. Chapter Title"# Add a pause between segments (500ms)
    # Combine all files',   # Introduction chaptert.silent(duration=500)pdf_path)
    for file_path in tqdm(audio_files, desc="Combining audio"):
        segment = AudioSegment.from_mp3(file_path)
        combined += segment + pauseer.pages, desc="Processing pages")):
        i, chunk in enumerate(chunks):segment = AudioSegment.from_mp3(file_path)page_text = page.extract_text()
    # Export the final audiobookrts with a chapter headinguse
    combined.export(output_path, format="mp3")\n' in chunk else chunk[:100]
    print(f"Audiobook saved to {output_path}")
        for pattern in chapter_patterns:    combined.export(output_path, format="mp3")        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
def main(): if re.match(pattern, first_line.strip()):"Audiobook saved to {output_path}")
    parser = argparse.ArgumentParser(description="Generate an audiobook from a PDF using Sesame CSM")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--output", default="audiobook_sesame.mp3", help="Output audiobook file path")
    parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()hapter 1p_dir", default="temp_audio_sesame", help="Directory for temporary audio files")to manageable chunks."""
    if not chapter_boundaries or chapter_boundaries[0] != 0:parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")print("Preprocessing text...")
    # Create temporary directoryt(0, 0)
    os.makedirs(args.temp_dir, exist_ok=True)
        # Create temporary directorytext = re.sub(r'\s+', ' ', text).strip()
    # Extract and preprocess textapter_titlesist_ok=True)
    text = extract_text_from_pdf(args.pdf)
    chunks = preprocess_text(text, args.chunk_size)apter_boundaries=None, chapter_titles=None):
    """Combine audio files by chapter."""text = extract_text_from_pdf(args.pdf)
    # Load CSM modelng {len(audio_files)} audio segments into chapters...")ess_text(text, args.chunk_size)s into chunks
    print("Loading Sesame CSM model...")
    from csm import CSMModelexist_ok=True)
    model = CSMModel.from_pretrained("sesame/csm-1b")
    model = model.half().to("cuda")  # Use half precision to save memory
    if not chapter_boundaries or not chapter_titles:model = CSMModel.from_pretrained("sesame/csm-1b")    if len(current_chunk) + len(sentence) < max_chunk_size:
    # Process each chunkes = [0].to("cuda")  # Use half precision to save memoryk += sentence + " "
    print(f"Processing {len(chunks)} text segments...")
    audio_files = []t_chunk.strip())
    # Create a chapter audio file for each chapterprint(f"Processing {len(chunks)} text segments...")        current_chunk = sentence + " "
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):
        output_path = os.path.join(args.temp_dir, f"chunk_{i:04d}.mp3")
        end_idx = chapter_boundaries[i+1] if i+1 < len(chapter_boundaries) else len(audio_files)i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):chunks.append(current_chunk.strip())
        # Skip if already processed4d}.mp3")
        if os.path.exists(output_path):itize for filename
            print(f"Skipping chunk {i} - already processed")
            audio_files.append(output_path), chapter_title).strip().replace(' ', '_')
            continuename = f"{i+1:02d}_{safe_title}.mp3"Skipping chunk {i} - already processed")odel, text, output_path):
        output_file = os.path.join(output_dir, chapter_filename)    audio_files.append(output_path)enerate audio for a text segment."""
        # Generate audio
        success = generate_audio(model, chunk, output_path)
        if success:cache()
            audio_files.append(output_path)is chapternk, output_path)
            ter_segments = audio_files[start_idx:end_idx]uccess:nerate audio
        # Take a short break every 5 chunks to prevent overheating
        if i % 5 == 0 and i > 0:r this chapter
            print("Taking a short break to prevent overheating...")
            time.sleep(10)io segments for chapter {i+1} - skipping")i > 0:
            torch.cuda.empty_cache()verheating...")io: {e}")
                    time.sleep(10)    return False
    # Combine audio filesegment.empty()pty_cache()
    combine_audio_files(audio_files, args.output)  # 500ms pause
        # Combine audio files"""Combine multiple audio files into a single audiobook."""
    print("Audiobook generation complete!")ents, desc=f"Combining audio for chapter {i+1}"):utput)dio segments...")
            segment = AudioSegment.from_mp3(audio_file)        
if __name__ == "__main__":gment + pauseation complete!")audio segment
    main()gment.empty()
EOF     # Export the chapter audio__name__ == "__main__": 
        combined.export(output_file, format="mp3")    main()    # Add a pause between segments (500ms)
# Make the script executable} saved to {output_file}")
chmod +x generate_audiobook_sesame.py
``` print(f"All chapter audio files saved to {output_dir}")ake the script executable # Combine all files
chmod +x generate_audiobook_sesame.py    for file_path in tqdm(audio_files, desc="Combining audio"):
### 3.4 Run the Sesame CSM Audiobook Generation Script
```bashser = argparse.ArgumentParser(description="Generate an audiobook from a PDF using Sesame CSM")ed += segment + pause
# Make sure virtual environment is activatedue, help="Path to the PDF file")ion Script
source ~/sesame_project/venv/bin/activateefault="audiobook_chapters_sesame", help="Output directory for chapter files")
    parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")# Make sure virtual environment is activated    combined.export(output_path, format="mp3")
# Run the scriptrgument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")project/venv/bin/activateobook saved to {output_path}")
cd ~/sesame_projectarse_args()
mkdir -p ~/audiobook_data/audiobook_chapters_sesame
python generate_audiobook_sesame_epub.py --epub ~/audiobook/learning_ai.epub --output_dir ~/audiobook_data/audiobook_chapters_sesame # Create temporary directory~/sesame_project parser = argparse.ArgumentParser(description="Generate an audiobook from a PDF using Sesame CSM")
```    os.makedirs(args.temp_dir, exist_ok=True)python generate_audiobook_sesame_epub.py --epub ~/audiobook/learning_ai.epub --output ~/audiobook_data/audiobook_sesame.mp3    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
e)ook file path")
## 4. Performance Optimization and Monitoring        parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
cess textzation and Monitoring"--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
### 4.1 Monitoring Toolst = extract_text_from_pdf(args.pdf)ser.parse_args()
```bashargs.chunk_size)
# Monitor GPU usage and temperature
sudo tegrastats    # Detect chapter boundaries# Monitor GPU usage and temperature    os.makedirs(args.temp_dir, exist_ok=True)
r_titles = detect_chapter_boundaries(chunks)
# Monitor CPU and memory usageprint(f"Detected {len(chapter_boundaries)} chapters")tract and preprocess text
htop    # Monitor CPU and memory usage    text = extract_text_from_pdf(args.pdf)
rgs.chunk_size)
# Monitor disk usagerint("Loading Sesame CSM model...")
df -h from csm import CSMModelonitor disk usage # Load CSM model
```    model = CSMModel.from_pretrained("sesame/csm-1b")df -h    print("Loading Sesame CSM model...")
f precision to save memory
### 4.2 Optimization Tips for Jetson Orin Nano        model = CSMModel.from_pretrained("sesame/csm-1b")
nkips for Jetson Orin Nano().to("cuda")  # Use half precision to save memory
#### Memory Managementnts...")
- Use half-precision (FP16) for model inference
- Clear CUDA cache between batches with `torch.cuda.empty_cache()` text segments...")
- Process smaller text chunksGenerating audio")):da.empty_cache()`
- Close unnecessary applications while processing        output_path = os.path.join(args.temp_dir, f"chunk_{i:04d}.mp3")- Process smaller text chunks    
 processingmerate(tqdm(chunks, desc="Generating audio")):
#### Thermal Management
- Add periodic cooling breaks (implemented in both scripts)
- Monitor temperature with `tegrastats`d")s)
- Consider additional cooling if temperatures exceed 80°C
- Run the process overnight for cooler ambient temperatures            continue- Consider additional cooling if temperatures exceed 80°C            print(f"Skipping chunk {i} - already processed")
 ambient temperatures.append(output_path)
#### Storage Management
- Pre-clear space before startingel, chunk, output_path)
- Use compressed audio formats (MP3)
- Clean up temporary files after completion            audio_files.append(output_path)- Use compressed audio formats (MP3)        success = generate_audio(model, chunk, output_path)

## 5. Comparing the Two Approaches        # Take a short break every 5 chunks to prevent overheating            audio_files.append(output_path)
d i > 0:Approaches
### 5.1 Piper Advantagesrheating...")
- Directly integrated with jetson-containers ecosystem0)d i > 0:
- Lower memory footprintuda.empty_cache()ed with jetson-containers ecosystemTaking a short break to prevent overheating...")
- Faster processing
- Multiple voices availableaudio filesssingrch.cuda.empty_cache()
- Easier setup    combine_audio_files(audio_files, args.output_dir, chapter_boundaries, chapter_titles)- Multiple voices available    

### 5.2 Sesame CSM Advantagesete!")
- Higher quality, more natural voices
- Better prosody and emotional rangeal voicestion complete!")
- More humanlike intonation
- State-of-the-art voice quality
- Better for long-form content like audiobooks- State-of-the-art voice quality    main()
 like audiobooks
### 5.3 Deciding Which to Use
- **For quick results or limited hardware**: Use Piper
- **For highest quality**: Use Sesame CSM
- **Consider testing both**: Generate a small sample with each to compare quality### 3.4 Run the Sesame CSM Audiobook Generation Script- **For highest quality**: Use Sesame CSM```
e with each to compare quality
## 6. Additional Enhancements# Make sure virtual environment is activated### 3.4 Run the Sesame CSM Audiobook Generation Script
in/activate
### 6.1 Adding Chapter Markers
To add chapter markers to the final audiobook (requires ffmpeg):# Run the script### 6.1 Adding Chapter Markerssource ~/sesame_project/venv/bin/activate
same_projectchapter markers to the final audiobook (requires ffmpeg):
```bashy --epub ~/audiobook/learning_ai.epub --output ~/audiobook_data/audiobook_sesame.mp3
# Extract chapter titles and timestamps
python extract_chapters.py --pdf learning_with_ai.pdf --output chapters.txt# Extract chapter titles and timestampspython generate_audiobook_sesame_epub.py --epub ~/audiobook/learning_ai.epub --output ~/audiobook_data/audiobook_sesame.mp3
itoringing_with_ai.pdf --output chapters.txt
# Add chapter markers to the audiobook
ffmpeg -i audiobook.mp3 -i chapters.txt -map_metadata 1 -codec copy audiobook_chaptered.mp3 4.1 Monitoring Toolsdd chapter markers to the audiobook4. Performance Optimization and Monitoring
``````bashffmpeg -i audiobook.mp3 -i chapters.txt -map_metadata 1 -codec copy audiobook_chaptered.mp3

### 6.2 Parallel Processing with Multiple Jetson Devices
If you have two Jetson Orin Nano devices, you can divide the workload:### 6.2 Parallel Processing with Multiple Jetson Devices# Monitor GPU usage and temperature
or CPU and memory usagehave two Jetson Orin Nano devices, you can divide the workload:grastats
```bash
# On device 1:
python generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 0-500# Monitor disk usage# On device 1:htop
ok.py --pdf learning_with_ai.pdf --chunk_range 0-500
# On device 2:
python generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 501-1000evice 2:-h
```### 4.2 Optimization Tips for Jetson Orin Nanopython generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 501-1000```

### 6.3 Improving Voice Quality
For Piper, you can adjust parameters:- Use half-precision (FP16) for model inference### 6.3 Improving Voice Quality
 CUDA cache between batches with `torch.cuda.empty_cache()`er, you can adjust parameters:mory Management
```bash
# Use higher quality settings
piper --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100higher quality settingsrocess smaller text chunks
```#### Thermal Managementpiper --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100- Close unnecessary applications while processing
th scripts)
For Sesame CSM, you can modify voice parameters:- Monitor temperature with `tegrastats`#### Thermal Management
r additional cooling if temperatures exceed 80°Ce CSM, you can modify voice parameters:iodic cooling breaks (implemented in both scripts)
```pythonler ambient temperatures
# Adjust voice parameters (example)
audio = model.generate(anagement parameters (example)ess overnight for cooler ambient temperatures
    text=text,
    voice_preset="calm",  # Options: "default", "calm", "excited", "serious"
    speaking_rate=0.95,   # 1.0 is normal speed, lower is slower
    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustment
    energy_shift=0.0      # Values between -1.0 and 1.0 for volume/energy# 5. Comparing the Two Approaches   pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustment Clean up temporary files after completion
)ergy_shift=0.0      # Values between -1.0 and 1.0 for volume/energy
```### 5.1 Piper Advantages)## 5. Comparing the Two Approaches
ontainers ecosystem
## 7. Troubleshooting Common Issues- Lower memory footprint### 5.1 Piper Advantages
ommon Issues with jetson-containers ecosystem
### 7.1 Memory Errorsultiple voices availabler memory footprint
```
# If you encounter CUDA out of memory errors
1. Reduce chunk size in the script
2. Try restarting the Jetson to clear memory
3. Use half precision (already implemented)ngelear memory
4. Process fewer chunks at a timeore humanlike intonationUse half precision (already implemented)igher quality, more natural voices
```- State-of-the-art voice quality4. Process fewer chunks at a time- Better prosody and emotional range
nt like audiobooks
### 7.2 Piper Command Syntaxice quality
```bash
# Using stdin for input (recommended approach)
cat input.txt | piper -m /opt/piper/etc/test_voice.onnx -f output.wav- **For highest quality**: Use Sesame CSM# Using stdin for input (recommended approach)### 5.3 Deciding Which to Use
 both**: Generate a small sample with each to compare qualityr -m /opt/piper/etc/test_voice.onnx -f output.wavs or limited hardware**: Use Piper
# Alternative syntax
piper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt## 6. Additional Enhancements# Alternative syntax- **Consider testing both**: Generate a small sample with each to compare quality
.txt
# Converting to MP3 format afterward
ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3add chapter markers to the final audiobook (requires ffmpeg):onverting to MP3 format afterward
```ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3### 6.1 Adding Chapter Markers

### 7.3 Installation Issuesct chapter titles and timestamps
```bashearning_with_ai.pdf --output chapters.txt
# If pip fails to install packagess
sudo apt updaters.txt
sudo apt install -y python3-dev build-essentialffmpeg -i audiobook.mp3 -i chapters.txt -map_metadata 1 -codec copy audiobook_chaptered.mp3sudo apt update
 audiobook
# For audio library issues
sudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools### 6.2 Parallel Processing with Multiple Jetson Devices# For audio library issues```
oad:ibportaudiocpp0 ffmpeg libav-tools
# If you encounter SSL certificate errors during package downloads
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name>```bash# If you encounter SSL certificate errors during package downloadsIf you have two Jetson Orin Nano devices, you can divide the workload:
iles.pythonhosted.org <package_name>
# For CUDA-related package issuesng_with_ai.pdf --chunk_range 0-500
export TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"
pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.htmln device 2:ort TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"hon generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 0-500
```python generate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 501-1000pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html

### 7.4 Docker or Container Issuesnerate_audiobook.py --pdf learning_with_ai.pdf --chunk_range 501-1000
```tyssues
# If container fails to startameters:
sudo systemctl restart docker
sudo systemctl restart nvidia-container-runtime```bashsudo systemctl restart dockerFor Piper, you can adjust parameters:

# If GPU is not available in containerv --file input.txt --speaker-id 0 --quality 100
./jetson-containers run --runtime nvidia --gpus all piperf GPU is not available in containerse higher quality settings
```./jetson-containers run --runtime nvidia --gpus all piperpiper --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100
M, you can modify voice parameters:
## Conclusion

This comprehensive plan provides two complete approaches for generating an audiobook from a PDF on Jetson Orin Nano devices. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis. # Adjust voice parameters (example)

Both methods include optimizations for the limited resources of the Jetson platform, robust error handling, and the ability to resume processing if interrupted. By following this guide, you can convert your 230-page "Learning with AI" book into a high-quality audiobook using local processing on your Jetson Orin Nano.    text=text,# Adjust voice parameters (example)
































































Both methods include optimizations for the limited resources of the Jetson platform, robust error handling, and the ability to resume processing if interrupted. By following this guide, you can convert your 230-page "Learning with AI" book into a high-quality audiobook using local processing on your Jetson Orin Nano.This comprehensive plan provides two complete approaches for generating an audiobook from a PDF on Jetson Orin Nano devices. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis. ## Conclusion```./jetson-containers run --runtime nvidia --gpus all piper# If GPU is not available in containersudo systemctl restart nvidia-container-runtimesudo systemctl restart docker# If container fails to start```### 7.4 Docker or Container Issues```pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.htmlexport TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"# For CUDA-related package issuespip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name># If you encounter SSL certificate errors during package downloadssudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools# For audio library issuessudo apt install -y python3-dev build-essentialsudo apt update# If pip fails to install packages```bash### 7.3 Installation Issues```ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3# Converting to MP3 format afterwardpiper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt# Alternative syntaxcat input.txt | piper -m /opt/piper/etc/test_voice.onnx -f output.wav# Using stdin for input (recommended approach)```bash### 7.2 Piper Command Syntax```4. Process fewer chunks at a time3. Use half precision (already implemented)2. Try restarting the Jetson to clear memory1. Reduce chunk size in the script# If you encounter CUDA out of memory errors```### 7.1 Memory Errors## 7. Troubleshooting Common Issues```)    energy_shift=0.0      # Values between -1.0 and 1.0 for volume/energy    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustment    speaking_rate=0.95,   # 1.0 is normal speed, lower is slower    voice_preset="calm",  # Options: "default", "calm", "excited", "serious"

Both methods include optimizations for the limited resources of the Jetson platform, robust error handling, and the ability to resume processing if interrupted. By following this guide, you can convert your 230-page "Learning with AI" book into a high-quality audiobook using local processing on your Jetson Orin Nano.audio = model.generate(
    text=text,
    voice_preset="calm",  # Options: "default", "calm", "excited", "serious"
    speaking_rate=0.95,   # 1.0 is normal speed, lower is slower
    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustment
    energy_shift=0.0      # Values between -1.0 and 1.0 for volume/energy
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

### 7.2 Piper Command Syntax
```bash
# Using stdin for input (recommended approach)
cat input.txt | piper -m /opt/piper/etc/test_voice.onnx -f output.wav

# Alternative syntax
piper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt

# Converting to MP3 format afterward
ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3
```

### 7.3 Installation Issues
```bash
# If pip fails to install packages
sudo apt update
sudo apt install -y python3-dev build-essential

# For audio library issues
sudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools

# If you encounter SSL certificate errors during package downloads
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name>

# For CUDA-related package issues
export TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"
pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html
```

### 7.4 Docker or Container Issues
```
# If container fails to start
sudo systemctl restart docker
sudo systemctl restart nvidia-container-runtime

# If GPU is not available in container
./jetson-containers run --runtime nvidia --gpus all piper
```

## Conclusion

This comprehensive plan provides two complete approaches for generating an audiobook from a PDF on Jetson Orin Nano devices. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis. 

Both methods include optimizations for the limited resources of the Jetson platform, robust error handling, and the ability to resume processing if interrupted. By following this guide, you can convert your 230-page "Learning with AI" book into a high-quality audiobook using local processing on your Jetson Orin Nano.
