# Comprehensive Plan for Generating an Audiobook on Jetson Orin Nano

This document outlines a comprehensive plan for converting a book into an audiobook using two different approaches on the Jetson Orin Nano:
1. Piper TTS using jetson-containers (recommended first approach)
2. Sesame CSM for higher quality voice synthesis (alternative approach)

The plan supports both ePub and PDF formats, with ePub being the recommended format due to its better structure for chapter detection and text extraction.

## 1. Setup and Environment Preparation

### 1.1 System Requirementsrate Audiobook with Piper (Basic)
- Jetson Orin Nano with JetPack/L4T
- At least 5GB of available RAMok
- At least 20GB of free storage space
- Internet connection for downloading models

### 1.2 Clone the jetson-containers Repository
```bashne https://github.com/dusty-nv/jetson-containers
# Clone the repository
git clone https://github.com/dusty-nv/jetson-containersobook_data --volume ~/audiobook:/books $(./autotag piper-tts)
cd jetson-containers
```. Inside container: Generate the audiobook
python generate_audiobook_piper.py --input /books/your_book.epub --output /audiobook_data/audiobook_piper.mp3 --model /opt/piper/voices/en/en_US-lessac-medium.onnx
### 1.3 Prepare Data Directory
```bash
# Create directories for your data and book files
mkdir -p ~/audiobook_dataommand Option |
mkdir -p ~/audiobook--|---------------|
| Lessac (Medium) | Professional female voice | `--model /opt/piper/voices/en/en_US-lessac-medium.onnx` |
# Copy your book file to the books directoryl /opt/piper/voices/en/en_US-ryan-medium.onnx` |
cp ~/your_book.epub ~/audiobook/e voice | `--model /opt/piper/voices/en/en_GB-jenny-medium.onnx` |
# or
cp ~/your_book.pdf ~/audiobook/instructions below for complete setup and advanced options.
```
## 1. Setup and Environment Preparation
## 2. Approach 1: Generating Audiobook with Piper (via jetson-containers)
### 1.1 System Requirements
### 2.1 Check Available Piper Models
```bashast 5GB of available RAM
# Show details about the piper-tts container (note the correct package name)
./jetson-containers show piper-ttsing models
```
### 1.2 Clone the jetson-containers Repository
### 2.2 Run the Piper Containerection Guide
```bashpository
# Run the piper-tts container with correct volume mountsty | File Path | Good For |
# IMPORTANT: Volume arguments must come BEFORE the container name------|----------|
./jetson-containers run --volume ~/audiobook_data:/audiobook_data \/opt/piper/voices/en/en_US-lessac-medium.onnx` | Audiobooks, narration |
  --volume ~/audiobook:/books \Clear | Medium | High | `/opt/piper/voices/en/en_US-ryan-medium.onnx` | Technical content |
  --workdir /audiobook_data $(./autotag piper-tts) | High | `/opt/piper/voices/en/en_GB-jenny-medium.onnx` | Storytelling |
```athleen | English (US) | Female | Warm | Medium | High | `/opt/piper/voices/en/en_US-kathleen-medium.onnx` | Children's books |bash
| Alan | English (UK) | Male | Formal | Medium | High | `/opt/piper/voices/en/en_GB-alan-medium.onnx` | Academic content |# Create directories for your data and book files
### 2.3 Create Book Processing Script and Test Piper
**Note:** For smaller memory footprint but lower quality, you can use the `-low.onnx` versions instead of `-medium.onnx`.mkdir -p ~/audiobook
Inside the container, first test Piper with the included test voice model:
### 2.2 Run the Piper Container# Copy your book file to the books directory
```bashur_book.epub ~/audiobook/
# Test Piper with a simple sentence (note: Piper reads from stdin)
echo "This is a test of the Piper text to speech system." > test.txt
cat test.txt | piper -m /opt/piper/etc/test_voice.onnx -f /audiobook_data/test.wav
  --volume ~/audiobook:/books \
# Install ffmpeg and convert to MP3 formatper-tts)h Piper (via jetson-containers)
apt-get update && apt-get install -y ffmpeg
ffmpeg -i /audiobook_data/test.wav -y -codec:a libmp3lame -qscale:a 2 /audiobook_data/test.mp3
``` 2.3 Create Book Processing Script and Test Piperbash
# Show details about the piper-tts container (note the correct package name)
Now create the book processing script: with the included test voice model:
```
```bash
# Create the script simple sentence (note: Piper reads from stdin)er Container
cat > generate_audiobook_piper.py << 'EOF'speech system." > test.txt
#!/usr/bin/env python3m /opt/piper/etc/test_voice.onnx -f /audiobook_data/test.wavntainer with correct volume mounts
# IMPORTANT: Volume arguments must come BEFORE the container name
import os ffmpeg and convert to MP3 formatcontainers run --volume ~/audiobook_data:/audiobook_data \
import sysdate && apt-get install -y ffmpeg ~/audiobook:/books \
import argparseobook_data/test.wav -y -codec:a libmp3lame -qscale:a 2 /audiobook_data/test.mp3diobook_data $(./autotag piper-tts)
import subprocess
import re
from tqdm import tqdmrocessing script:rocessing Script and Test Piper
import nltk
from nltk.tokenize import sent_tokenizeel:
from pydub import AudioSegment
import ebooklibaudiobook_piper.py << 'EOF'
from ebooklib import epubentence (note: Piper reads from stdin)
from bs4 import BeautifulSoup> test.txt
from PyPDF2 import PdfReaderce.onnx -f /audiobook_data/test.wav
import timeimport sys
# Download NLTK datao MP3 format
nltk.download('punkt', quiet=True)
import shutilimport reffmpeg -i /audiobook_data/test.wav -y -codec:a libmp3lame -qscale:a 2 /audiobook_data/test.mp3
def html_to_text(html_content):
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()et=True)ment
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip() format
    return textput_file(file_path): BeautifulSoupaudiobook_piper.py << 'EOF'
    """Validate that the input file exists and has the correct format."""from PyPDF2 import PdfReader#!/usr/bin/env python3
def extract_text_from_epub(epub_path):
    """Extract text and chapters from an ePub file."""ot exist.")
    print(f"Extracting text from ePub: {epub_path}...")
        rgparse
    book = epub.read_epub(epub_path)th('.epub') or file_path.lower().endswith('.pdf')):
    chapters = []rror: Input file format not supported. Only .epub and .pdf files are supported.")ML content to plain text."""
    chapter_titles = []tml_content, 'html.parser')
        text = soup.get_text()rt nltk
    # Get the spine (reading order)
    spine = [item.get_id() for item in book.spine]
    html_to_text(html_content):return textrt ebooklib
    # Process items in reading order text."""
    for item_id in tqdm(spine, desc="Processing ePub items"):
        # Get the itemxt()d chapters from an ePub file."""Reader
        item = book.get_item_with_id(item_id)
         = re.sub(r'\s+', ' ', text).strip()LTK data
        # Skip if not a document
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continuem_epub(epub_path): []l_content):
            ct text and chapters from an ePub file."""content to plain text."""
        # Get contentg text from ePub: {epub_path}...")reading order)oup(html_content, 'html.parser')
        content = item.get_content().decode('utf-8')
         = epub.read_epub(epub_path)up extra whitespace
        # Find title if possible)
        soup = BeautifulSoup(content, 'html.parser')
        title_tag = soup.find(['h1', 'h2', 'h3', 'h4'])
        title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapter_titles) + 1}"
        e = [item.get_id() for item in book.spine]xtract text and chapters from an ePub file."""
        # Extract textom ePub: {epub_path}...")
        text = html_to_text(content)() != ebooklib.ITEM_DOCUMENT:
        item_id in tqdm(spine, desc="Processing ePub items"):    continue = epub.read_epub(epub_path)
        # Skip if no meaningful content
        if len(text.strip()) < 50:id(item_id)
            continuent().decode('utf-8')
            ip if not a documentine (reading order)
        chapters.append(text)et_type() != ebooklib.ITEM_DOCUMENT:bler item in book.spine]
        chapter_titles.append(title)
                title_tag = soup.find(['h1', 'h2', 'h3', 'h4'])# Process items in reading order
    print(f"Extracted {len(chapters)} chapters from ePub") 1}""):
    return chapters, chapter_titles).decode('utf-8')
                # Extract text        item = book.get_item_with_id(item_id)
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file and attempt to detect chapters."""
    print(f"Extracting text from PDF: {pdf_path}...")])
        title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapter_titles) + 1}"    if len(text.strip()) < 50:        continue
    reader = PdfReader(pdf_path)
    full_text = ""text
        text = html_to_text(content)    chapters.append(text)    content = item.get_content().decode('utf-8')
    for i, page in enumerate(tqdm(reader.pages, desc="Processing PDF pages")):
        page_text = page.extract_text()
        if len(text.strip()) < 50:t(f"Extracted {len(chapters)} chapters from ePub")soup = BeautifulSoup(content, 'html.parser')
        # Clean up page headers, footers, page numbers, etc.
        page_text = re.sub(r'Page \d+ of \d+', '', page_text)
        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
        chapter_titles.append(title)xtract text from a PDF file and attempt to detect chapters."""# Extract text
        full_text += page_text + "\n"
    print(f"Extracted {len(chapters)} chapters from ePub")    
    # Detect chapters in the PDF text
    chapters, chapter_titles = detect_chapters_in_text(full_text)
    print(f"Detected {len(chapters)} chapters from PDF")
    """Extract text from a PDF file and attempt to detect chapters."""for i, page in enumerate(tqdm(reader.pages, desc="Processing PDF pages")):        
    return chapters, chapter_titlesF: {pdf_path}...")xt()
                    chapter_titles.append(title)
def detect_chapters_in_text(text):ters, page numbers, etc.
    """Attempt to detect chapters in plain text."""
    # Common chapter heading patternsTILINE)
    chapter_patterns = [rate(tqdm(reader.pages, desc="Processing PDF pages")):
        r'^CHAPTER\s+\d+',          # "CHAPTER 1", "CHAPTER 2", etc.
        r'^Chapter\s+\d+',          # "Chapter 1", "Chapter 2", etc.
        r'^\d+\.\s+[A-Z]',          # "1. CHAPTER TITLE", "2. CHAPTER TITLE"
        r'^PART\s+\d+',             # "PART 1", "PART 2", etc.t)
        r'^Part\s+\d+',             # "Part 1", "Part 2", etc.s=re.MULTILINE)
        r'^SECTION\s+\d+',          # "SECTION 1", "SECTION 2", etc.
        r'^Section\s+\d+',          # "Section 1", "Section 2", etc.
        r'^INTRODUCTION',           # "INTRODUCTION"
        r'^Introduction',           # "Introduction"
        r'^APPENDIX\s+\d*',         # "APPENDIX", "APPENDIX A", etc.
        r'^Appendix\s+\d*',         # "Appendix", "Appendix A", etc.
    ]apter_patterns = [   page_text = re.sub(r'Page \d+ of \d+', '', page_text)
    return chapters, chapter_titles    r'^CHAPTER\s+\d+',          # "CHAPTER 1", "CHAPTER 2", etc.    page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
    # Split text into linesapter 2", etc.
    lines = text.split('\n')text):        # "1. CHAPTER TITLE", "2. CHAPTER TITLE"xt + "\n"
    """Attempt to detect chapters in plain text."""    r'^PART\s+\d+',             # "PART 1", "PART 2", etc.
    # Find potential chapter boundariesrt 1", "Part 2", etc.
    chapter_starts = [][+',          # "SECTION 1", "SECTION 2", etc.itles = detect_chapters_in_text(full_text)
    chapter_titles = []+',          # "CHAPTER 1", "CHAPTER 2", etc.+',          # "Section 1", "Section 2", etc.en(chapters)} chapters from PDF")
        r'^Chapter\s+\d+',          # "Chapter 1", "Chapter 2", etc.    r'^INTRODUCTION',           # "INTRODUCTION"
    for i, line in enumerate(lines):# "1. CHAPTER TITLE", "2. CHAPTER TITLE"# "Introduction"
        line = line.strip()         # "PART 1", "PART 2", etc.         # "APPENDIX", "APPENDIX A", etc.
        if not line:+',             # "Part 1", "Part 2", etc.s+\d*',         # "Appendix", "Appendix A", etc.in_text(text):
            continue+\d+',          # "SECTION 1", "SECTION 2", etc.n plain text."""
            ection\s+\d+',          # "Section 1", "Section 2", etc. heading patterns
        # Check if line matches a chapter patternON"
        for pattern in chapter_patterns:ntroduction"CHAPTER 2", etc.
            if re.match(pattern, line):APPENDIX", "APPENDIX A", etc.
                chapter_starts.append(i)ppendix", "Appendix A", etc. CHAPTER TITLE", "2. CHAPTER TITLE"
                chapter_titles.append(line)
                break# "Part 1", "Part 2", etc.
    # Split text into lines    r'^SECTION\s+\d+',          # "SECTION 1", "SECTION 2", etc.
    # If no chapters detected, treat as a single chapter
    if not chapter_starts:TION"
        return [text], ["Chapter 1"]ies
    chapter_starts = []        continue    r'^APPENDIX\s+\d*',         # "APPENDIX", "APPENDIX A", etc.
    # Extract chapter textndix", "Appendix A", etc.
    chapters = []s a chapter pattern
    for i in range(len(chapter_starts)):
        start = chapter_starts[i]
        end = chapter_starts[i+1] if i+1 < len(chapter_starts) else len(lines)
        chapter_text = '\n'.join(lines[start:end]).strip()
        chapters.append(chapter_text)
        # Check if line matches a chapter patternchapter_starts = []
    return chapters, chapter_titleserns:t as a single chapter
            if re.match(pattern, line):    if not chapter_starts:    
def split_text_into_chunks(text, max_chars=1000):
    """Split text into manageable chunks for TTS processing."""
    # Split text into sentences
    sentences = sent_tokenize(text)
    # If no chapters detected, treat as a single chapterfor i in range(len(chapter_starts)):        
    # Group sentences into chunksr pattern
    chunks = [][text], ["Chapter 1"]hapter_starts[i+1] if i+1 < len(chapter_starts) else len(lines)tern in chapter_patterns:
    current_chunk = ""tart:end]).strip()h(pattern, line):
    # Extract chapter text    chapters.append(chapter_text)            chapter_starts.append(i)
    for sentence in sentences:
        # Clean the sentenceer_starts)):_titles
        sentence = sentence.strip()
        if not sentence:arts[i+1] if i+1 < len(chapter_starts) else len(lines)ks(text, max_chars=1000):ected, treat as a single chapter
            continue = '\n'.join(lines[start:end]).strip()to manageable chunks for TTS processing."""tarts:
            ters.append(chapter_text)text into sentencesrn [text], ["Chapter 1"]
        # If adding this sentence doesn't exceed max_chars, add it to the current chunk
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:t_into_chunks(text, max_chars=1000):[]range(len(chapter_starts)):
            # Save the current chunk if it's not emptyssing."""
            if current_chunk:es_starts) else len(lines)
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    # Group sentences into chunks    sentence = sentence.strip()
    # Add the last chunk if not empty
    if current_chunk:"
        chunks.append(current_chunk.strip())
    for sentence in sentences:    # If adding this sentence doesn't exceed max_chars, add it to the current chunk"""Split text into manageable chunks for TTS processing."""
    return chunkshe sentencerrent_chunk) + len(sentence) + 1 <= max_chars:into sentences
        sentence = sentence.strip()            current_chunk += sentence + " "    sentences = sent_tokenize(text)
def generate_audio_with_piper(text, output_file, model_path):
    """Generate audio for a chunk of text using Piper."""
    # Save text to a temporary file
    temp_text_file = "/tmp/piper_input.txt"xceed max_chars, add it to the current chunk.strip())
    with open(temp_text_file, "w") as f:ence) + 1 <= max_chars: "
        f.write(text)hunk += sentence + " "
        else:# Add the last chunk if not empty    # Clean the sentence
    # Call Piper to generate audionk if it's not empty
    cmd = [ if current_chunk:nks.append(current_chunk.strip())not sentence:
        "piper",chunks.append(current_chunk.strip())
        "--model", model_path,ntence + " "
        "--output_file", output_file,
        "--file", temp_text_fileemptyxt, output_file, model_path):len(sentence) + 1 <= max_chars:
    ]f current_chunk:""Generate audio for a chunk of text using Piper."""       current_chunk += sentence + " "
        chunks.append(current_chunk.strip())# Save text to a temporary file    else:
    try:t_file = "/tmp/piper_input.txt"    # Save the current chunk if it's not empty
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return Truet_chunk.strip())
    except subprocess.CalledProcessError as e:ime_per_chunk=5):
        print(f"Error generating audio: {e}")ed on number of chunks."""
        print(f"stderr: {e.stderr.decode()}")_chunk
        return Falseime.timedelta(seconds=total_seconds))
        "--model", model_path,        chunks.append(current_chunk.strip())
def combine_audio_files(audio_files, output_file):odel_path):
    """Combine multiple audio files into a single audio file."""
    print(f"Combining {len(audio_files)} audio segments...")
    temp_text_file = "/tmp/piper_input.txt"generate_audio_with_piper(text, output_file, model_path):
    combined = AudioSegment.empty()as f:
        f.write(text)    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)# Save text to a temporary file
    # Add a short pause between segments
    pause = AudioSegment.silent(duration=500)  # 500ms pause
    cmd = [    print(f"Error generating audio: {e}")    f.write(text)
    for audio_file in tqdm(audio_files, desc="Combining audio"):
        segment = AudioSegment.from_file(audio_file)
        combined += segment + pausee,
        "--file", temp_text_filecombine_audio_files(audio_files, output_file):    "piper",
    # Export the combined audioile."""
    combined.export(output_file, format="mp3")
    print(f"Combined audio saved to {output_file}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)    combined = AudioSegment.empty()    ]
def process_chapter(chapter_text, chapter_title, chapter_num, args):
    """Process a single chapter and generate audio."""
    print(f"Processing chapter {chapter_num}: {chapter_title}")PE)
        print(f"stderr: {e.stderr.decode()}")    return True
    # Create chapter directorydesc="Combining audio"):ocessError as e:
    chapter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")
    os.makedirs(chapter_dir, exist_ok=True)_file):
    """Combine multiple audio files into a single audio file."""    return False
    # Split chapter text into chunkses)} audio segments...")
    chunks = split_text_into_chunks(chapter_text, args.chunk_size)
    print(f"Chapter split into {len(chunks)} chunks")
    t(f"Combining {len(audio_files)} audio segments...")
    # Generate audio for each chunkmentshapter_title, chapter_num, args):
    audio_files = []ment.silent(duration=500)  # 500ms pausegle chapter and generate audio."""Segment.empty()
    print(f"Processing chapter {chapter_num}: {chapter_title}")
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):
        output_file = os.path.join(chapter_dir, f"chunk_{i:04d}.wav")
        combined += segment + pauseter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")
        # Skip if the file already exists (resume capability)
        if os.path.exists(output_file):
            print(f"Chunk {i} already processed, skipping...")
            audio_files.append(output_file)_file}")_text, args.chunk_size)
            continueks)} chunks")bined audio
            chapter(chapter_text, chapter_title, chapter_num, args):output_file, format="mp3")
        # Generate audio for this chunkerate audio."""_file}")
        success = generate_audio_with_piper(chunk, output_file, args.model)
        ter(chapter_text, chapter_title, chapter_num, args):
        if success:r directory enumerate(tqdm(chunks, desc="Generating audio")):ngle chapter and generate audio."""
            audio_files.append(output_file)r, f"chapter_{chapter_num:02d}")dir, f"chunk_{i:04d}.wav")}: {chapter_title}")
        else:rs(chapter_dir, exist_ok=True)
            print(f"Failed to generate audio for chunk {i}")
    # Split chapter text into chunks    if os.path.exists(output_file):chapter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")
    # Combine all audio files for this chapterxt, args.chunk_size)d, skipping...")
    if audio_files: split into {len(chunks)} chunks")iles.append(output_file)
        safe_title = re.sub(r'[^\w\s-]', '', chapter_title).strip().replace(' ', '_')
        chapter_output = os.path.join(args.output_dir, f"chapter_{chapter_num:02d}_{safe_title}.mp3")
        combine_audio_files(audio_files, chapter_output)))
        print(f"Chapter audio saved to {chapter_output}")estimated_time}")_file, args.model)
        return chapter_output
    else:erate audio for each chunkf success:_files = []
        print(f"No audio generated for chapter {chapter_num}")
        return Noneme.time()rate(tqdm(chunks, desc="Generating audio")):
                print(f"Failed to generate audio for chunk {i}")        output_file = os.path.join(chapter_dir, f"chunk_{i:04d}.wav")
def main():late chunks per batch based on memory limit
    parser = argparse.ArgumentParser(description="Generate an audiobook using Piper TTS")
    parser.add_argument("--input", required=True, help="Path to the input book file (ePub or PDF)")
    parser.add_argument("--output", default="audiobook.mp3", help="Output combined audiobook file path")
    parser.add_argument("--output_dir", default="audiobook_chapters", help="Output directory for chapter files")
    parser.add_argument("--model", default="/opt/piper/etc/test_voice.onnx", help="Piper voice model to use")
    parser.add_argument("--temp_dir", default="temp_audio", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):    print(f"No audio generated for chapter {chapter_num}")    
    # Create directories.path.join(chapter_dir, f"chunk_{i:04d}.wav")
    os.makedirs(args.temp_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)me capability)
        if os.path.exists(output_file):parser = argparse.ArgumentParser(description="Generate an audiobook using Piper TTS")        print(f"Failed to generate audio for chunk {i}")
    # Determine file type and extract textessed, skipping...")d=True, help="Path to the input book file (ePub or PDF)")
    input_path = args.inputend(output_file)output", default="audiobook.mp3", help="Output combined audiobook file path")es for this chapter
            continueparser.add_argument("--output_dir", default="audiobook_chapters", help="Output directory for chapter files")if audio_files:
    if input_path.lower().endswith('.epub'): help="Piper voice model to use") chapter_title).strip().replace(' ', '_')
        chapters, chapter_titles = extract_text_from_epub(input_path)es")pter_num:02d}_{safe_title}.mp3")
    elif input_path.lower().endswith('.pdf'):hunk, output_file, args.model)int, default=1000, help="Maximum characters per chunk")ter_output)
        chapters, chapter_titles = extract_text_from_pdf(input_path)
    else:f success: chapter_output
        print(f"Unsupported file format: {input_path}")
        print("Supported formats: .epub, .pdf")
        return 1t(f"Failed to generate audio for chunk {i}")args.output_dir, exist_ok=True)one
        
    # Process each chaptersplay progressand extract text
    chapter_audio_files = []= 0:tParser(description="Generate an audiobook using Piper TTS")
            elapsed_time = time.time() - start_timeparser.add_argument("--input", required=True, help="Path to the input book file (ePub or PDF)")
    for i, (chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):
        chapter_audio = process_chapter(chapter_text, chapter_title, i+1, args)
        if chapter_audio:aining = remaining_chunks * avg_time_per_chunk().endswith('.pdf'):--model", default="/opt/piper/etc/test_voice.onnx", help="Piper voice model to use")
            chapter_audio_files.append(chapter_audio)estimated_remaining)))pdf(input_path)udio", help="Directory for temporary audio files")
            print(f"Progress: {i}/{len(chunks)} chunks ({i/len(chunks)*100:.1f}%) - ETA: {eta}")else:parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    # Combine all chapters into a single audiobook if requested
    if args.output and chapter_audio_files:break after each batchdf")
        print(f"Combining {len(chapter_audio_files)} chapters into final audiobook...")
        combine_audio_files(chapter_audio_files, args.output)
        print(f"Audiobook saved to {args.output}")stem recover
    chapter_audio_files = []
    print("Audiobook generation complete!")ter
    return 0_files:chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):th = args.input
        safe_title = re.sub(r'[^\w\s-]', '', chapter_title).strip().replace(' ', '_')        chapter_audio = process_chapter(chapter_text, chapter_title, i+1, args)    
if __name__ == "__main__":s.path.join(args.output_dir, f"chapter_{chapter_num:02d}_{safe_title}.mp3")ndswith('.epub'):
    sys.exit(main())o_files(audio_files, chapter_output)audio_files.append(chapter_audio)apter_titles = extract_text_from_epub(input_path)
EOF     print(f"Chapter audio saved to {chapter_output}")  elif input_path.lower().endswith('.pdf'):
        return chapter_output    # Combine all chapters into a single audiobook if requested        chapters, chapter_titles = extract_text_from_pdf(input_path)
# Make the script executable
chmod +x generate_audiobook_piper.pyor chapter {chapter_num}")er_audio_files)} chapters into final audiobook...")mat: {input_path}")
```     return None     combine_audio_files(chapter_audio_files, args.output)     print("Supported formats: .epub, .pdf")
        print(f"Audiobook saved to {args.output}")        return 1
### 2.4 Install Required Python Packages in the Container
```bashser = argparse.ArgumentParser(description="Generate an audiobook using Piper TTS")nt("Audiobook generation complete!")rocess each chapter
# Install required packagesinput", required=True, help="Path to the input book file (ePub or PDF)")
pip install PyPDF2 nltk tqdm pydub ebooklib beautifulsoup4", help="Output combined audiobook file path")
``` parser.add_argument("--output_dir", default="audiobook_chapters", help="Output directory for chapter files")__name__ == "__main__": for i, (chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):
    parser.add_argument("--model", default="/opt/piper/etc/test_voice.onnx", help="Piper voice model to use")    sys.exit(main())        chapter_audio = process_chapter(chapter_text, chapter_title, i+1, args)
### 2.5 Run the Audiobook Generation Script with Enhanced Optionslt="temp_audio", help="Directory for temporary audio files")
```bashser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")apter_audio_files.append(chapter_audio)
# Create necessary directories_batch_size", type=int, default=20, help="Maximum chunks to process before pausing")
mkdir -p /audiobook_data/temp_audio_pipernk", type=int, default=50, help="Estimated memory usage per chunk in MB")book if requested
mkdir -p /audiobook_data/audiobook_chapters_piperRange of chapters to process (e.g., '1-5')")
    args = parser.parse_args()        print(f"Combining {len(chapter_audio_files)} chapters into final audiobook...")
# For ePub format with a specific voice model and memory optimization settingster_audio_files, args.output)
python generate_audiobook_piper.py \
  --input /books/your_book.epub \gs.input):
  --output /audiobook_data/audiobook_piper.mp3 \
  --output_dir /audiobook_data/audiobook_chapters_piper \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --temp_dir /audiobook_data/temp_audio_piper \
  --max_batch_size 15 \    os.makedirs(args.output_dir, exist_ok=True)```bash    sys.exit(main())
  --memory_per_chunk 50es
t textpiper
# For large books, process specific chapter rangesapters_piper
python generate_audiobook_piper.py \
  --input /books/your_large_book.epub \
  --output /audiobook_data/audiobook_piper_part1.mp3 \_text_from_epub(input_path)
  --output_dir /audiobook_data/audiobook_chapters_piper \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \     chapters, chapter_titles = extract_text_from_pdf(input_path)-output /audiobook_data/audiobook_piper.mp3 \bash
  --temp_dir /audiobook_data/temp_audio_piper \    else:  --output_dir /audiobook_data/audiobook_chapters_piper \# Install required packages
  --chapter_range 1-10t: {input_path}")nx \oklib beautifulsoup4
``` print("Supported formats: .epub, .pdf")p_dir /audiobook_data/temp_audio_piper

## 3. Understanding Container and Host File Locations
        # Process only specified chapter range if providedpython generate_audiobook_piper.py \```bash
Important path mappings:
    
| Inside Container | On Jetson Host | args.chapter_range.split('-'))diobook_chapters_piper \k_chapters_piper
|-----------------|----------------|nd, len(chapters)))
| `/audiobook_data` | `~/audiobook_data` |pter_range]
| `/books` | `~/audiobook` |les[i] for i in chapter_range]
| `/data` | `~/jetson-containers/data` (default mapping) |
             chapter_titles = selected_titles 2.6 Monitor and Manage the Process-output /audiobook_data/audiobook_piper.mp3 \
When running commands:            print(f"Processing chapters {start} to {min(end, len(selected_chapters)+start-1)}")```bash  --output_dir /audiobook_data/audiobook_chapters_piper \
- Use container paths (like `/audiobook_data`) when inside the container
- Use host paths (like `~/audiobook_data`) when on the Jetson host        print(f"Invalid chapter range format: {args.chapter_range}. Expected format: '1-5'")la /audiobook_data/audiobook_chapters_piper | wc -ltemp_dir /audiobook_data/temp_audio_piper
        
Note: Files saved to `/data` inside the container will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`. resume if interrupted, just run the same command againr PDF format

## 4. Approach 2: Using Sesame CSM for Higher Quality Voiceter) for chapter in chapters)
 args.chunk_size.mp3 \.mp3 \
### 4.1 Set Up Environment for Sesame CSMe_processing_time(estimated_chunks)ta/audiobook_chapters_piper \ta/audiobook_chapters_piper \
```bashme}")
# Install system dependenciestemp_dir /audiobook_data/temp_audio_pipertemp_dir /audiobook_data/temp_audio_piper
sudo apt updatepter
sudo apt install -y python3-venv python3-pip ffmpeg libsndfile1
    
# Create project directoryi, (chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):
mkdir -p ~/sesame_project
cd ~/sesame_project        if chapter_audio:    ls -la /audiobook_data/audiobook_chapters_piper | wc -l
    
# Create and activate virtual environment    |-----------------|----------------|# To resume if interrupted, just run the same command again
python3 -m venv venvaudiobook if requested|
source venv/bin/activateargs.output and chapter_audio_files:ks` | `~/audiobook` |ut /books/your_book.epub \
    n(chapter_audio_files)} chapters into final audiobook...")ers/data` (default mapping) |diobook_piper.mp3 \
# Install Python dependencies_audio_files(chapter_audio_files, args.output)data/audiobook_chapters_piper \
pip install --upgrade pip
pip install PyPDF2 pdfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch ebooklib beautifulsoup4e container paths (like `/audiobook_data`) when inside the containertemp_dir /audiobook_data/temp_audio_piper
```iles if successfulaudiobook_data`) when on the Jetson host
os.path.exists(args.temp_dir) and chapter_audio_files:
### 4.2 Install Sesame CSM= input("Processing complete! Would you like to remove temporary files to save space? (y/n): ")o `/data` inside the container will be available at `~/jetson-containers/data` on the host, not at `~/audiobook_data`. Container and Host File Locations
```bash    if user_input.lower() == 'y':
# Clone the repositoryles in {args.temp_dir}...")gher Quality Voice
git clone https://github.com/SesameAILabs/csm.gitmtree(args.temp_dir)
cd csmrary files removed.")nt for Sesame CSMJetson Host |
    ash--------------|----------------|
# Install in development modeon complete!")obook_data` |
pip install -e .
    
# Download the model__name__ == "__main__":  
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"    sys.exit(main())# Create project directoryWhen running commands:
    n inside the container
# Go back to project directoryojectost paths (like `~/audiobook_data`) when on the Jetson host
cd ..utable
``` `~/jetson-containers/data` on the host, not at `~/audiobook_data`.
m venv venv
### 4.3 Create Audiobook Generation Scriptenv/bin/activate. Approach 2: Using Sesame CSM for Higher Quality Voice
```bashon Packages in the Container
# Create the scriptciesnvironment for Sesame CSM
cat > generate_audiobook_sesame.py << 'EOF'stall required packagesinstall --upgrade pipash
#!/usr/bin/env python3ltk tqdm pydub ebooklib beautifulsoup4 psutildfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch ebooklib beautifulsoup4endencies

import ostall -y python3-venv python3-pip ffmpeg libsndfile1
import torchration Script
import argparseshshate project directory
from tqdm import tqdmreate necessary directorieslone the repositoryir -p ~/sesame_project
from pathlib import Pathmkdir -p /audiobook_data/temp_audio_pipergit clone https://github.com/SesameAILabs/csm.gitcd ~/sesame_project
from PyPDF2 import PdfReaders_piper
from pydub import AudioSegmentvate virtual environment
from nltk.tokenize import sent_tokenizerecommended)pment modev
import nltk
import timebook.epub \
import re  --output /audiobook_data/audiobook_piper.mp3 \# Download the model# Install Python dependencies
import ebooklibt_dir /audiobook_data/audiobook_chapters_piper \ "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"ll --upgrade pip
from ebooklib import epubpt/piper/etc/test_voice.onnx \dfminer.six nltk tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch ebooklib beautifulsoup4
from bs4 import BeautifulSoupudiobook_data/temp_audio_piperoject directory

# Download NLTK resources if not already downloaded
try:per.py \
    nltk.data.find('tokenizers/punkt') \ation Script
except LookupError:per.mp3 \
    nltk.download('punkt')dir /audiobook_data/audiobook_chapters_piper \e script
opt/piper/etc/test_voice.onnx \ate_audiobook_sesame.py << 'EOF'
def html_to_text(html_content):dir /audiobook_data/temp_audio_pipern/env python3 in development mode
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()e Process
    # Clean up extra whitespaceimport datetime```bashimport argparsepython -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"
    text = re.sub(r'\s+', ' ', text).strip()
    return textrt shutilla /audiobook_data/audiobook_chapters_piper | wc -l pathlib import Path back to project directory

def extract_text_from_epub(epub_path):ources if not already downloadedrrupted, just run the same command againudioSegment
    """Extract text and chapters from an ePub file."""e
    print(f"Extracting text from ePub: {epub_path}...")    nltk.data.find('tokenizers/punkt')  --input /books/your_book.epub \import nltk### 4.3 Create Audiobook Generation Script
    mp3 \
    book = epub.read_epub(epub_path)
    chapters = []
    chapter_titles = []ts and has correct formatta/temp_audio_piper
    th):
    # Get the spine (reading order)nd has the correct format."""
    spine = [item.get_id() for item in book.spine]ath.exists(file_path):ding Container and Host File Locations resources if not already downloaded
            print(f"Error: Input file '{file_path}' does not exist.")    try:import argparse
    # Process items in reading order
    for item_id in tqdm(spine, desc="Processing ePub items"):
        # Get the item_path.lower().endswith('.pdf')):
        item = book.get_item_with_id(item_id)    print(f"Error: Input file format not supported. Only .epub and .pdf files are supported.")--------------|----------------|ub import AudioSegment
        
        # Skip if not a document |ML content to plain text."""
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:s/data` (default mapping) |p(html_content, 'html.parser')
            continue = soup.get_text()rt re
            
        # Get contentide the container
        content = item.get_content().decode('utf-8')soup = BeautifulSoup(html_content, 'html.parser')e host paths (like `~/audiobook_data`) when on the Jetson hostreturn text bs4 import BeautifulSoup
        
        # Find title if possible/data` on the host, not at `~/audiobook_data`.
        soup = BeautifulSoup(content, 'html.parser')+', ' ', text).strip()b file."""
        title_tag = soup.find(['h1', 'h2', 'h3', 'h4'])
        title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapter_titles) + 1}"
        path):esame CSMath)
        # Extract text
        text = html_to_text(content)ng text from ePub: {epub_path}...")endencies []l_content):
        nt to plain text."""
        # Skip if no meaningful contentepub(epub_path)ython3-venv python3-pip ffmpeg libsndfile1reading order)oup(html_content, 'html.parser')
        if len(text.strip()) < 50:
            continueter_titles = [] project directoryup extra whitespace
            
        chapters.append(text)
        chapter_titles.append(title)
    
    print(f"Extracted {len(chapters)} chapters from ePub")ocess items in reading order-m venv venvxtract text and chapters from an ePub file."""
    return chapters, chapter_titlesm(spine, desc="Processing ePub items"):tea document text from ePub: {epub_path}...")

def extract_text_from_pdf(pdf_path):item = book.get_item_with_id(item_id)l Python dependencies    continue = epub.read_epub(epub_path)
    """Extract text from a PDF file and attempt to detect chapters."""
    print(f"Extracting text from PDF: {pdf_path}...") tqdm pydub transformers huggingface_hub numpy scipy librosa soundfile psutil torch ebooklib beautifulsoup4
    or item.get_type() != ebooklib.ITEM_DOCUMENT:decode('utf-8')
    reader = PdfReader(pdf_path)continue order)
    full_text = ""ine]
    
    for i, page in enumerate(tqdm(reader.pages, desc="Processing PDF pages")):    content = item.get_content().decode('utf-8')one the repository    title_tag = soup.find(['h1', 'h2', 'h3', 'h4'])# Process items in reading order
        page_text = page.extract_text()
        
        # Clean up page headers, footers, page numbers, etc.        soup = BeautifulSoup(content, 'html.parser')            # Extract text        item = book.get_item_with_id(item_id)
        page_text = re.sub(r'Page \d+ of \d+', '', page_text) 'h2', 'h3', 'h4'])
        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)er {len(chapter_titles) + 1}"
        
        full_text += page_text + "\n"    # Extract textwnload the model    if len(text.strip()) < 50:        continue
    ent)import snapshot_download; snapshot_download(repo_id='sesame/csm-1b')"
    # Detect chapters in the PDF text
    chapters, chapter_titles = detect_chapters_in_text(full_text)    # Skip if no meaningful content back to project directory    chapters.append(text)    content = item.get_content().decode('utf-8')
    print(f"Detected {len(chapters)} chapters from PDF")
    
    return chapters, chapter_titles    acted {len(chapters)} chapters from ePub")soup = BeautifulSoup(content, 'html.parser')

def detect_chapters_in_text(text):
    """Attempt to detect chapters in plain text."""
    # Common chapter heading patternst(f"Extracted {len(chapters)} chapters from ePub")nerate_audiobook_sesame.py << 'EOF'xtract text from a PDF file and attempt to detect chapters."""# Extract text
    chapter_patterns = [
        r'^CHAPTER\s+\d+',          # "CHAPTER 1", "CHAPTER 2", etc.
        r'^Chapter\s+\d+',          # "Chapter 1", "Chapter 2", etc.
        r'^\d+\.\s+[A-Z]',          # "1. CHAPTER TITLE", "2. CHAPTER TITLE"s."""
        r'^PART\s+\d+',             # "PART 1", "PART 2", etc.
        r'^Part\s+\d+',             # "Part 1", "Part 2", etc. tqdm import tqdmfor i, page in enumerate(tqdm(reader.pages, desc="Processing PDF pages")):        
        r'^SECTION\s+\d+',          # "SECTION 1", "SECTION 2", etc.
        r'^Section\s+\d+',          # "Section 1", "Section 2", etc.    full_text = ""from PyPDF2 import PdfReader                chapter_titles.append(title)
        r'^INTRODUCTION',           # "INTRODUCTION"
        r'^Introduction',           # "Introduction"c="Processing PDF pages")):Pub")
        r'^APPENDIX\s+\d*',         # "APPENDIX", "APPENDIX A", etc.()=re.MULTILINE)
        r'^Appendix\s+\d*',         # "Appendix", "Appendix A", etc.
    ]
    
    # Split text into lines)
    lines = text.split('\n')
    
    # Find potential chapter boundaries
    chapter_starts = []
    chapter_titles = []xt(full_text)
    DF")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:o_text(html_content):hapter_patterns = [   page_text = re.sub(r'Page \d+ of \d+', '', page_text)
            continuedetect_chapters_in_text(text):"""Convert HTML content to plain text."""    r'^CHAPTER\s+\d+',          # "CHAPTER 1", "CHAPTER 2", etc.    page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
            apters in plain text."""ml_content, 'html.parser')         # "Chapter 1", "Chapter 2", etc.
        # Check if line matches a chapter pattern patterns      # "1. CHAPTER TITLE", "2. CHAPTER TITLE"xt + "\n"
        for pattern in chapter_patterns:chapter_patterns = [# Clean up extra whitespace    r'^PART\s+\d+',             # "PART 1", "PART 2", etc.
            if re.match(pattern, line):CHAPTER 1", "CHAPTER 2", etc.rip()Part 1", "Part 2", etc.
                chapter_starts.append(i)+',          # "Chapter 1", "Chapter 2", etc.     # "SECTION 1", "SECTION 2", etc.itles = detect_chapters_in_text(full_text)
                chapter_titles.append(line)]',          # "1. CHAPTER TITLE", "2. CHAPTER TITLE" 1", "Section 2", etc.en(chapters)} chapters from PDF")
                break    r'^PART\s+\d+',             # "PART 1", "PART 2", etc.extract_text_from_epub(epub_path):    r'^INTRODUCTION',           # "INTRODUCTION"
    # "Part 1", "Part 2", etc.m an ePub file."""# "Introduction"
    # If no chapters detected, treat as a single chapter         # "SECTION 1", "SECTION 2", etc. from ePub: {epub_path}...")         # "APPENDIX", "APPENDIX A", etc.
    if not chapter_starts:+\d+',          # "Section 1", "Section 2", etc.# "Appendix", "Appendix A", etc.in_text(text):
        return [text], ["Chapter 1"]ION',           # "INTRODUCTION"_epub(epub_path)n plain text."""
    ntroduction',           # "Introduction" = [] heading patterns
    # Extract chapter text "APPENDIX A", etc.
    chapters = []ppendix", "Appendix A", etc.
    for i in range(len(chapter_starts)):
        start = chapter_starts[i]ER TITLE"
        end = chapter_starts[i+1] if i+1 < len(chapter_starts) else len(lines)
        chapter_text = '\n'.join(lines[start:end]).strip()t('\n')n reading order[]',             # "Part 1", "Part 2", etc.
        chapters.append(chapter_text)for item_id in tqdm(spine, desc="Processing ePub items"):    r'^SECTION\s+\d+',          # "SECTION 1", "SECTION 2", etc.
    
    return chapters, chapter_titleswith_id(item_id))          # "INTRODUCTION"

def preprocess_text(text, max_chunk_size=1000):    # Skip if not a document        continue    r'^APPENDIX\s+\d*',         # "APPENDIX", "APPENDIX A", etc.
    """Clean and split text into manageable chunks."""te(lines):m.get_type() != ebooklib.ITEM_DOCUMENT:ppendix", "Appendix A", etc.
    # Remove extra whitespacene.strip()nuef line matches a chapter pattern
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into sentences
    sentences = sent_tokenize(text)
    ns:
    # Group sentences into chunks        if re.match(pattern, line):    soup = BeautifulSoup(content, 'html.parser')chapter_starts = []
    chunks = []nd(i), 'h2', 'h3', 'h4'])t as a single chapter
    current_chunk = ""                chapter_titles.append(line)        title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapter_titles) + 1}"    if not chapter_starts:    
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chunk_size:, treat as a single chapterontent)
            current_chunk += sentence + " "
        else:    return [text], ["Chapter 1"]    # Skip if no meaningful contentfor i in range(len(chapter_starts)):        
            chunks.append(current_chunk.strip()) chapter pattern
            current_chunk = sentence + " "ts) else len(lines)erns:
    chapters = []            chapter_text = '\n'.join(lines[start:end]).strip()        if re.match(pattern, line):
    if current_chunk:arts)):pend(i)
        chunks.append(current_chunk.strip()) chapter_starts[i]_titles.append(title)tles.append(line)
    starts[i+1] if i+1 < len(chapter_starts) else len(lines)
    return chunks    chapter_text = '\n'.join(lines[start:end]).strip()print(f"Extracted {len(chapters)} chapters from ePub")
r_text)itleschunk_size=1000): treat as a single chapter
def generate_audio(model, text, output_path, voice_preset="default", speaking_rate=1.0):
    """Generate audio for a text segment."""
    try: PDF file and attempt to detect chapters.""".sub(r'\s+', ' ', text).strip()
        # Clear CUDA cache..")
        torch.cuda.empty_cache()e chunks."""
        # Remove extra whitespacereader = PdfReader(pdf_path)sentences = sent_tokenize(text)for i in range(len(chapter_starts)):
        # Generate audios+', ' ', text).strip()
        audio = model.generate(
            text=text,# Split into sentencesfor i, page in enumerate(tqdm(reader.pages, desc="Processing PDF pages")):chunks = []    chapter_text = '\n'.join(lines[start:end]).strip()
            voice_preset=voice_preset,ent_tokenize(text) = page.extract_text() = ""append(chapter_text)
            speaking_rate=speaking_rate                    
        )
        k_size:
        audio.export(output_path, format="mp3")ent_chunk = ""page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)    current_chunk += sentence + " "rocess_text(text, max_chunk_size=1000):
        return True
    except Exception as e:\n"t_chunk.strip())
        print(f"Error generating audio: {e}")# Clean the sentencecurrent_chunk = sentence + " " = re.sub(r'\s+', ' ', text).strip()
        return Falsence.strip() the PDF text
chapters_in_text(full_text)
def combine_audio_files(audio_files, output_path):n(chapters)} chapters from PDF")current_chunk.strip())okenize(text)
    """Combine multiple audio files into a single audiobook."""
    # Start with an empty audio segment't exceed max_chars, add it to the current chunk
    combined = AudioSegment.empty()f len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
        current_chunk += sentence + " "ct_chapters_in_text(text):rate_audio(model, text, output_path, voice_preset="default", speaking_rate=1.0):ent_chunk = ""
    # Add a pause between segments (500ms)
    pause = AudioSegment.silent(duration=500)the current chunk if it's not emptyr heading patterns
    nk:
    # Combine all filestrip())R 1", "CHAPTER 2", etc.
    for file_path in tqdm(audio_files, desc="Combining audio"):chunk = sentence + " "+\d+',          # "Chapter 1", "Chapter 2", etc.
        segment = AudioSegment.from_mp3(file_path)            r'^\d+\.\s+[A-Z]',          # "1. CHAPTER TITLE", "2. CHAPTER TITLE"        # Generate audio            continue
        combined += segment + pause
    
    # Export the final audiobookip())SECTION 1", "SECTION 2", etc.ence) < max_chunk_size:
    combined.export(output_path, format="mp3")c.ratece + " "
    print(f"Audiobook saved to {output_path}")return chunks    r'^INTRODUCTION',           # "INTRODUCTION"    )    else:

def process_chapter(model, chapter_text, chapter_title, chapter_num, args):time_per_chunk=10):IX", "APPENDIX A", etc.")
    """Process a single chapter and generate audio.""""""Estimate the total processing time based on number of chunks."""    r'^Appendix\s+\d*',         # "Appendix", "Appendix A", etc.    return True            chunks.append(current_chunk.strip())
    print(f"Processing chapter {chapter_num}: {chapter_title}")_chunks * avg_time_per_chunk " "
    
    # Create chapter directory
    chapter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")put_path, voice_preset="default", speaking_rate=1.0):
    os.makedirs(chapter_dir, exist_ok=True)"""Generate audio for a text segment."""combine_audio_files(audio_files, output_path):    chunks.append(current_chunk.strip())
     audiobook."""
    # Split chapter text into chunks
    chunks = preprocess_text(chapter_text, args.chunk_size)
    print(f"Chapter split into {len(chunks)} chunks")                def generate_audio(model, text, output_path, voice_preset="default", speaking_rate=1.0):
    
    # Generate audio for each chunk
    audio_files = []
            voice_preset=voice_preset,        continue# Combine all files    torch.cuda.empty_cache()
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):king_ratebining audio"):
        output_path = os.path.join(chapter_dir, f"chunk_{i:04d}.mp3")
        
        # Skip if already processed    audio.export(output_path, format="mp3")        if re.match(pattern, line):        text=text,
        if os.path.exists(output_path):
            print(f"Skipping chunk {i} - already processed")
            audio_files.append(output_path)
            continue    return False
            title, chapter_num, args):ormat="mp3")
        # Generate audioles(audio_files, output_path):tarts:gle chapter and generate audio."""
        success = generate_audio(model, chunk, output_path, args.voice_preset, args.speaking_rate)"""Combine multiple audio files into a single audiobook."""    return [text], ["Chapter 1"]print(f"Processing chapter {chapter_num}: {chapter_title}")except Exception as e:
        
        if success:
            audio_files.append(output_path)ined = AudioSegment.empty()ters = []ter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")
        
        # Take a short break every 5 chunks to prevent overheatings
        if i % 5 == 0 and i > 0:s) else len(lines)
            print("Taking a short break to prevent overheating...")
            time.sleep(10)n tqdm(audio_files, desc="Combining audio"):end(chapter_text)split into {len(chunks)} chunks")
            torch.cuda.empty_cache()ent = AudioSegment.from_file(audio_file)gments (500ms)
    ent + pausepter_titles each chunk.silent(duration=500)
    # Combine audio files for this chapter
    if audio_files:port the combined audiorocess_text(text, max_chunk_size=1000):e all files
        safe_title = re.sub(r'[^\w\s-]', '', chapter_title).strip().replace(' ', '_')(output_path, format="mp3")lit text into manageable chunks.""" enumerate(tqdm(chunks, desc="Generating audio")):n tqdm(audio_files, desc="Combining audio"):
        chapter_output = os.path.join(args.output_dir, f"chapter_{chapter_num:02d}_{safe_title}.mp3")_path}")i:04d}.mp3")e_path)
        combine_audio_files(audio_files, chapter_output)b(r'\s+', ' ', text).strip()combined += segment + pause
        print(f"Chapter audio saved to {chapter_output}")m, args):
        return chapter_outputand generate audio.""":
    else:
        print(f"No audio generated for chapter {chapter_num}")
        return None
chapter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")chunks = []        process_chapter(model, chapter_text, chapter_title, chapter_num, args):
def main():)
    parser = argparse.ArgumentParser(description="Generate an audiobook using Sesame CSM")tput_path, args.voice_preset, args.speaking_rate)ing chapter {chapter_num}: {chapter_title}")
    parser.add_argument("--input", required=True, help="Path to the input book file (ePub or PDF)")
    parser.add_argument("--output", default="audiobook_sesame.mp3", help="Output combined audiobook file path")
    parser.add_argument("--output_dir", default="audiobook_chapters_sesame", help="Output directory for chapter files")
    parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")ehunks to prevent overheating
    parser.add_argument("--voice_preset", default="default", help="Voice preset (default, calm, excited, serious)")ated_time = estimate_processing_time(len(chunks))   f i % 5 == 0 and i > 0:it chapter text into chunks
    parser.add_argument("--speaking_rate", type=float, default=1.0, help="Speaking rate (1.0 is normal)")ated_time}")e, add it to the current chunk...")
    args = parser.parse_args()n(sentence) < max_chunk_size:eep(10) split into {len(chunks)} chunks")
        # Generate audio for each chunk            current_chunk += sentence + " "            torch.cuda.empty_cache()    
    # Create directoriesiles = []e:io for each chunk
    os.makedirs(args.temp_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load CSM model
    print("Loading Sesame CSM model...")
    from csm import CSMModel
    model = CSMModel.from_pretrained("sesame/csm-1b")
    model = model.half().to("cuda")  # Use half precision to save memory
    et="default", speaking_rate=1.0):ated for chapter {chapter_num}")(output_path)
    # Determine file type and extract textprint(f"Processing up to {chunks_per_batch} chunks at a time based on available memory")"""Generate audio for a text segment."""    return None        continue
    input_path = args.input
    sc="Generating audio")):
    if input_path.lower().endswith('.epub'): f"chunk_{i:04d}.mp3")audiobook using Sesame CSM")output_path, args.voice_preset, args.speaking_rate)
        chapters, chapter_titles = extract_text_from_epub(input_path)        parser.add_argument("--input", required=True, help="Path to the input book file (ePub or PDF)")    
    elif input_path.lower().endswith('.pdf'):ready processedudioent("--output", default="audiobook_sesame.mp3", help="Output combined audiobook file path")
        chapters, chapter_titles = extract_text_from_pdf(input_path)udiobook_chapters_sesame", help="Output directory for chapter files")th)
    else: chunk {i} - already processed")r", default="temp_audio_sesame", help="Directory for temporary audio files")
        print(f"Unsupported file format: {input_path}")characters per chunk")t overheating
        print("Supported formats: .epub, .pdf")
        return 1            )parser.add_argument("--speaking_rate", type=float, default=1.0, help="Speaking rate (1.0 is normal)")        print("Taking a short break to prevent overheating...")
    
    # Process each chapteraudio(model, chunk, output_path, args.voice_preset, args.speaking_rate)_path, format="mp3")
    chapter_audio_files = []        return True# Create directories
    
    for i, (chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):
        chapter_audio = process_chapter(model, chapter_text, chapter_title, i+1, args)
        if chapter_audio:
            chapter_audio_files.append(chapter_audio)f i > 0 and i % 5 == 0:ne_audio_files(audio_files, output_path):("Loading Sesame CSM model...")ombine_audio_files(audio_files, chapter_output)
    ."""
    # Combine all chapters into a single audiobook if requested i
    if args.output and chapter_audio_files:ining_chunks = len(chunks) - iudioSegment.empty()l.half().to("cuda")  # Use half precision to save memory
        print(f"Combining {len(chapter_audio_files)} chapters into final audiobook...")        estimated_remaining = remaining_chunks * avg_time_per_chunk    print(f"No audio generated for chapter {chapter_num}")
        combine_audio_files(chapter_audio_files, args.output)time.timedelta(seconds=int(estimated_remaining)))segments (500ms)and extract text
        print(f"Audiobook saved to {args.output}"): {i}/{len(chunks)} chunks ({i/len(chunks)*100:.1f}%) - ETA: {eta}")ent(duration=500)
        main():
    print("Audiobook generation complete!")
    return 0
 a break to free up memory and prevent overheating...")gment.from_mp3(file_path)().endswith('.pdf'):--output", default="audiobook_sesame.mp3", help="Output combined audiobook file path")
if __name__ == "__main__":e", help="Output directory for chapter files")
    main()        time.sleep(10)else:parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
EOF
")df")efault="default", help="Voice preset (default, calm, excited, serious)")
# Make the script executable
chmod +x generate_audiobook_sesame.pytrip().replace(' ', '_')
```dir, f"chapter_{chapter_num:02d}_{safe_title}.mp3")itle, chapter_num, args):
    combine_audio_files(audio_files, chapter_output)"""Process a single chapter and generate audio."""chapter_audio_files = []# Create directories
### 4.4 Run the Sesame CSM Audiobook Generation Script with Enhanced Optionspter_output}")}: {chapter_title}")
```bashrn chapter_outputtext, chapter_title) in enumerate(zip(chapters, chapter_titles)):irs(args.output_dir, exist_ok=True)
# Make sure virtual environment is activated    else:    # Create chapter directory        chapter_audio = process_chapter(model, chapter_text, chapter_title, i+1, args)    
source ~/sesame_project/venv/bin/activateenerated for chapter {chapter_num}")join(args.temp_dir, f"chapter_{chapter_num:02d}")
turn Noneedirs(chapter_dir, exist_ok=True)  chapter_audio_files.append(chapter_audio)"Loading Sesame CSM model...")
# Create output directoriesfrom csm import CSMModel
mkdir -p ~/audiobook_data/audiobook_chapters_sesamedef main():    # Split chapter text into chunks    # Combine all chapters into a single audiobook if requested    model = CSMModel.from_pretrained("sesame/csm-1b")
ntParser(description="Generate an audiobook using Sesame CSM")(chapter_text, args.chunk_size)er_audio_files:"cuda")  # Use half precision to save memory
# For ePub format with memory optimizationquired=True, help="Path to the input book file (ePub or PDF)")hunks)} chunks")r_audio_files)} chapters into final audiobook...")
python generate_audiobook_sesame.py \ parser.add_argument("--output", default="audiobook_sesame.mp3", help="Output combined audiobook file path")      combine_audio_files(chapter_audio_files, args.output) # Determine file type and extract text
  --input ~/audiobook/your_book.epub \    parser.add_argument("--output_dir", default="audiobook_chapters_sesame", help="Output directory for chapter files")    # Generate audio for each chunk        print(f"Audiobook saved to {args.output}")    input_path = args.input
  --output ~/audiobook_data/audiobook_sesame.mp3 \dio_sesame", help="Directory for temporary audio files")
  --output_dir ~/audiobook_data/audiobook_chapters_sesame \ser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")"Audiobook generation complete!")input_path.lower().endswith('.epub'):
  --voice_preset "calm" \fault="default", help="Voice preset (default, calm, excited, serious)")esc="Generating audio")):
  --max_batch_size 8 \, type=float, default=1.0, help="Speaking rate (1.0 is normal)")r_dir, f"chunk_{i:04d}.mp3")
  --memory_per_chunk 150    parser.add_argument("--max_batch_size", type=int, default=10, help="Maximum chunks to process before pausing")        if __name__ == "__main__":        chapters, chapter_titles = extract_text_from_pdf(input_path)
memory_per_chunk", type=int, default=150, help="Estimated memory usage per chunk in MB")rocessed
# For large books, process specific chapter ranges to avoid running out of memorynge of chapters to process (e.g., '1-5')")
python generate_audiobook_sesame.py \    args = parser.parse_args()            print(f"Skipping chunk {i} - already processed")        print("Supported formats: .epub, .pdf")
  --input ~/audiobook/your_large_book.epub \
  --output ~/audiobook_data/audiobook_sesame_part1.mp3 \
  --output_dir ~/audiobook_data/audiobook_chapters_sesame \put):
  --voice_preset "calm" \
  --chapter_range 1-5
szip(chapters, chapter_titles)):
# After completing part 1, run part 2    os.makedirs(args.temp_dir, exist_ok=True)        if success:# Make sure virtual environment is activated        chapter_audio = process_chapter(model, chapter_text, chapter_title, i+1, args)
python generate_audiobook_sesame.py \args.output_dir, exist_ok=True)o_files.append(output_path)project/venv/bin/activateer_audio:
  --input ~/audiobook/your_large_book.epub \
  --output ~/audiobook_data/audiobook_sesame_part2.mp3 \ overheating
  --output_dir ~/audiobook_data/audiobook_chapters_sesame \
  --voice_preset "calm" \
  --chapter_range 6-10om_pretrained("sesame/csm-1b")10)mmended)ng {len(chapter_audio_files)} chapters into final audiobook...")
``` model = model.half().to("cuda")  # Use half precision to save memory         torch.cuda.empty_cache()hon generate_audiobook_sesame.py \     combine_audio_files(chapter_audio_files, args.output)
          --input ~/audiobook/your_book.epub \        print(f"Audiobook saved to {args.output}")
## 5. Performance Optimization and Monitoring
    input_path = args.input    if audio_files:  --output_dir ~/audiobook_data/audiobook_chapters_sesame \    print("Audiobook generation complete!")
### 5.1 Monitoring Tools and Memory Usage chapter_title).strip().replace(' ', '_')
```bashinput_path.lower().endswith('.epub'): chapter_output = os.path.join(args.output_dir, f"chapter_{chapter_num:02d}_{safe_title}.mp3")
# Monitor GPU usage and temperatureextract_text_from_epub(input_path)iles, chapter_output)
sudo tegrastatspath.lower().endswith('.pdf'):"Chapter audio saved to {chapter_output}")_audiobook_sesame.py \
        chapters, chapter_titles = extract_text_from_pdf(input_path)        return chapter_output  --input ~/audiobook/your_book.pdf \EOF
# Monitor CPU and memory usage
htop    print(f"Unsupported file format: {input_path}")    print(f"No audio generated for chapter {chapter_num}")output_dir ~/audiobook_data/audiobook_chapters_sesame \ke the script executable
        print("Supported formats: .epub, .pdf")        return None  --voice_preset "calm"chmod +x generate_audiobook_sesame.py
# Monitor disk usage
df -hin():
 # Process only specified chapter range if provided parser = argparse.ArgumentParser(description="Generate an audiobook using Sesame CSM")5. Performance Optimization and Monitoring 4.4 Run the Sesame CSM Audiobook Generation Script
# Track memory usage of the Python process    if args.chapter_range:    parser.add_argument("--input", required=True, help="Path to the input book file (ePub or PDF)")```bash
watch -n 2 "ps -o pid,user,%mem,%cpu,command -p \$(pgrep -f 'python.*generate_audiobook')" combined audiobook file path")
```            start, end = map(int, args.chapter_range.split('-'))    parser.add_argument("--output_dir", default="audiobook_chapters_sesame", help="Output directory for chapter files")```bashsource ~/sesame_project/venv/bin/activate
nge = range(start-1, min(end, len(chapters)))t("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")d temperature
### 5.2 Optimization Tips for Jetson Orin Nanor i in chapter_range]t, default=1000, help="Maximum characters per chunk")
range]"Voice preset (default, calm, excited, serious)")
#### Memory Managemented_chapterseaking_rate", type=float, default=1.0, help="Speaking rate (1.0 is normal)")e
- Use half-precision (FP16) for model inference
- Clear CUDA cache between batches with `torch.cuda.empty_cache()`        print(f"Processing chapters {start} to {min(end, len(selected_chapters)+start-1)}")enerate_audiobook_sesame.py \
- Process smaller text chunksor:s_book.epub \
- Close unnecessary applications while processingpter_range}. Expected format: '1-5'")
    
#### Thermal Management
- Add periodic cooling breaks (implemented in both scripts)
- Monitor temperature with `tegrastats`total_text_length = sum(len(chapter) for chapter in chapters)print("Loading Sesame CSM model...")F format
- Consider additional cooling if temperatures exceed 80°Ctotal_text_length / args.chunk_sizeModelk_sesame.py \
- Run the process overnight for cooler ambient temperaturescessing_time(estimated_chunks)ned("sesame/csm-1b")odel inferencedf \
    ng time: {estimated_time}") # Use half precision to save memoryith `torch.cuda.empty_cache()`k_sesame.mp3 \
#### Storage Management
- Pre-clear space before starting
- Use compressed audio formats (MP3)    chapter_audio_files = []    input_path = args.input    ```
- Clean up temporary files after completion
- Consider processing only a few chapters at a time if storage is limited    for i, (chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):    if input_path.lower().endswith('.epub'):- Add periodic cooling breaks (implemented in both scripts)## 5. Performance Optimization and Monitoring
process_chapter(model, chapter_text, chapter_title, i+1, args)r_titles = extract_text_from_epub(input_path)th `tegrastats`
## 6. Comparing the Two Approaches
o_files.append(chapter_audio)r_titles = extract_text_from_pdf(input_path)ght for cooler ambient temperatures
### 6.1 Piper Advantages
- Directly integrated with jetson-containers ecosysteminto a single audiobook if requested file format: {input_path}")
- Lower memory footprinttput and chapter_audio_files:"Supported formats: .epub, .pdf")ace before starting
- Faster processing        print(f"Combining {len(chapter_audio_files)} chapters into final audiobook...")        return 1- Use compressed audio formats (MP3)# Monitor CPU and memory usage
- Multiple voices availablehapter_audio_files, args.output)
- Easier setuprgs.output}")ime if storage is limited

### 6.2 Sesame CSM Advantagesles if successful
- Higher quality, more natural voices.exists(args.temp_dir) and chapter_audio_files:r_title) in enumerate(zip(chapters, chapter_titles)):
- Better prosody and emotional rangee! Would you like to remove temporary files to save space? (y/n): ") chapter_text, chapter_title, i+1, args)
- More humanlike intonation        if user_input.lower() == 'y':        if chapter_audio:- Directly integrated with jetson-containers ecosystem### 5.2 Optimization Tips for Jetson Orin Nano
- State-of-the-art voice qualitytemporary files in {args.temp_dir}...")es.append(chapter_audio)
- Better for long-form content like audiobooks
d.")audiobook if requested
### 6.3 Deciding Which to Use
- **For quick results or limited hardware**: Use Piper
- **For highest quality**: Use Sesame CSM    return 0        combine_audio_files(chapter_audio_files, args.output)### 6.2 Sesame CSM Advantages- Close unnecessary applications while processing
- **For large books**: Consider processing chapter-by-chapter with either method
- **Consider testing both**: Generate a sample chapter with each to compare qualityif __name__ == "__main__":    - Better prosody and emotional range#### Thermal Management
ed in both scripts)
## 7. Additional Enhancements
- Better for long-form content like audiobooks- Consider additional cooling if temperatures exceed 80°C
### 7.1 Adding Chapter Markersthe script executableme__ == "__main__":ess overnight for cooler ambient temperatures
To add chapter markers to the final audiobook (requires ffmpeg):
mited hardware**: Use Pipere Management
```bashUse Sesame CSMar space before starting
# Extract chapter metadata from processed chaptersn the Sesame CSM Audiobook Generation Script script executablerge books**: Consider processing chapter-by-chapter with either methodressed audio formats (MP3)
python -c 'te_audiobook_sesame.pyr testing both**: Generate a sample chapter with each to compare qualitytemporary files after completion
import os# Make sure virtual environment is activated```- Consider processing only a few chapters at a time if storage is limited
import sysvate
import json

# Replace with your chapter directorymkdir -p ~/audiobook_data/audiobook_chapters_sesame# Make sure virtual environment is activatedTo add chapter markers to the final audiobook (requires ffmpeg):### 6.1 Piper Advantages
chapter_dir = "~/audiobook_data/audiobook_chapters_piper"nv/bin/activate jetson-containers ecosystem
chapter_files = sorted([f for f in os.listdir(chapter_dir) if f.endswith(".mp3")])(recommended)
python generate_audiobook_sesame.py \# Create output directories# Extract chapter metadata from processed chapters- Faster processing
metadata = []_book.epub \audiobook_chapters_sesame
current_time = 0.0
a/audiobook_chapters_sesame \)
for file in chapter_files:ok_sesame.py \
    # Extract chapter number and title from filename
    parts = file.split("_", 2)
    if len(parts) >= 3:enerate_audiobook_sesame.py \ut_dir ~/audiobook_data/audiobook_chapters_sesame \dir = "~/audiobook_data/audiobook_chapters_piper"umanlike intonation
        chapter_num = parts[1]r_book.pdf \or f in os.listdir(chapter_dir) if f.endswith(".mp3")])quality
        chapter_title = parts[2].replace(".mp3", "").replace("_", " ")ta/audiobook_sesame.mp3 \
        udiobook_chapters_sesame \
        # Add to metadata
        metadata.append({book/your_book.pdf \s or limited hardware**: Use Piper
            "time": current_time,iobook_data/audiobook_sesame.mp3 \ in chapter_files:highest quality**: Use Sesame CSM
            "title": f"Chapter {chapter_num}: {chapter_title}"y-chapter with either method
        })
        
        # Update time for next chapter (approximate)```bash        chapter_num = parts[1]## 7. Additional Enhancements
        # In a real implementation, you would get actual durationtemperaturezation and Monitoringparts[2].replace(".mp3", "").replace("_", " ")
        current_time += 300.0  # Assume 5 minutes per chapter
 ffmpeg):
# Write metadata to file
with open("chapters.txt", "w") as f:htop# Monitor GPU usage and temperature            "time": current_time,```bash
    for entry in metadata:
        f.write(f"{entry['time']:.2f}:{entry['title']}\n") Monitor disk usage      })ython -c '
df -h# Monitor CPU and memory usage        import os
print(f"Generated chapter metadata file with {len(metadata)} chapters")
'
 5.2 Optimization Tips for Jetson Orin Nanoonitor disk usage     current_time += 300.0  # Assume 5 minutes per chapter
# Add chapter markers to the audiobookdf -h# Replace with your chapter directory
ffmpeg -i audiobook.mp3 -i chapters.txt -map_metadata 1 -codec copy audiobook_chaptered.mp3
```
- Clear CUDA cache between batches with `torch.cuda.empty_cache()`### 5.2 Optimization Tips for Jetson Orin Nano    for entry in metadata:
### 7.2 Parallel Processing with Multiple Jetson Devicesss smaller text chunkse(f"{entry['time']:.2f}:{entry['title']}\n")a = []
If you have two Jetson Orin Nano devices, you can divide the workload:ssary applications while processingnagement

```bash#### Thermal Management- Clear CUDA cache between batches with `torch.cuda.empty_cache()`'for file in chapter_files:
# On device 1: cooling breaks (implemented in both scripts)ler text chunks and title from filename
python generate_audiobook_piper.py --input your_book.epub --chapter_range 1-10
onsider additional cooling if temperatures exceed 80°C peg -i audiobook.mp3 -i chapters.txt -map_metadata 1 -codec copy audiobook_chaptered.mp3 if len(parts) >= 3:
# On device 2:- Run the process overnight for cooler ambient temperatures#### Thermal Management```        chapter_num = parts[1]
python generate_audiobook_piper.py --input your_book.epub --chapter_range 11-20)_", " ")
```Devices
- Pre-clear space before starting- Consider additional cooling if temperatures exceed 80°CIf you have two Jetson Orin Nano devices, you can divide the workload:        # Add to metadata
### 7.3 Improving Voice Qualityompressed audio formats (MP3)he process overnight for cooler ambient temperaturesta.append({
For Piper, you can adjust parameters:ter completion

```bashclear space before startinghon generate_audiobook_piper.py --input your_book.epub --chapter_range 1-10     })
# Use higher quality settings## 6. Comparing the Two Approaches- Use compressed audio formats (MP3)        
piper --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100
```### 6.1 Piper Advantages- Consider processing only a few chapters at a time if storage is limitedpython generate_audiobook_piper.py --input your_book.epub --chapter_range 11-20        # In a real implementation, you would get actual duration
y integrated with jetson-containers ecosystem300.0  # Assume 5 minutes per chapter
For Sesame CSM, you can modify voice parameters:

```pythonces availableAdvantages can adjust parameters:pters.txt", "w") as f:
# Adjust voice parameters (example)
audio = model.generate(
    text=text,
    voice_preset="calm",  # Options: "default", "calm", "excited", "serious"
    speaking_rate=0.95,   # 1.0 is normal speed, lower is slower Better prosody and emotional range Easier setup``
    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustmentore humanlike intonation
    energy_shift=0.0      # Values between -1.0 and 1.0 for volume/energy- State-of-the-art voice quality### 6.2 Sesame CSM AdvantagesFor Sesame CSM, you can modify voice parameters:# Add chapter markers to the audiobook
) audiobooksesdiobook_chaptered.mp3
```- Better prosody and emotional range```python```
h to Usenationters (example)
## 8. Troubleshooting Common Issues*For quick results or limited hardware**: Use Pipertate-of-the-art voice qualityio = model.generate( 7.2 Parallel Processing with Multiple Jetson Devices

### 8.1 Memory Errorspter-by-chapter with either method
```ter with each to compare quality
# If you encounter CUDA out of memory errors:
1. Reduce chunk size (try 500 instead of 1000) CSMs between -1.0 and 1.0 for volume/energyy --input your_book.epub --chapter_range 1-10
2. Restart the Jetson to clear memory (sudo reboot)
3. Use half precision (already implemented in both scripts)le chapter with each to compare quality
4. Process fewer chunks at a timeal audiobook (requires ffmpeg):
5. Close background applications (browsers, unnecessary services)
6. Monitor memory usage with: free -h
7. If persistent, try swap space:ta from processed chaptersarkerslity
   sudo fallocate -l 4G /swapfileudiobook (requires ffmpeg):
   sudo chmod 600 /swapfileort osou encounter CUDA out of memory errors:
   sudo mkswap /swapfileimport sys```bash1. Reduce chunk size (try 500 instead of 1000)```bash
   sudo swapon /swapfiles memory (sudo reboot)
``` -c 'Use half precision (already implemented in both scripts)er --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100
tory
### 8.2 Text Extraction Issuesiper"
```_dir) if f.endswith(".mp3")])
# If PDF text extraction is poor:
1. Try OCR-based extraction: pip install pytesseractmetadata = []# Replace with your chapter directory   sudo fallocate -l 4G /swapfile```python
2. Use a different PDF reader: pip install pdfplumber
3. Convert PDF to ePub using tools like Calibre before processing

# If ePub extraction misses content or chapters:me
1. Check ePub validity with: epubcheck your_book.epub parts = file.split("_", 2)rent_time = 0.0eaking_rate=0.95,   # 1.0 is normal speed, lower is slower
2. Try converting with: ebook-convert your_book.epub fixed.epub    if len(parts) >= 3:### 8.2 Text Extraction Issues    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustment
3. Inspect book structure: unzip -l your_book.epub1] for volume/energy
``` chapter_title = parts[2].replace(".mp3", "").replace("_", " ")xtract chapter number and title from filenameF text extraction is poor:

### 8.3 Piper Command Syntax
```bash        metadata.append({        chapter_num = parts[1]3. Convert PDF to ePub using tools like Calibre before processing## 8. Troubleshooting Common Issues
# Using stdin for input (recommended approach)current_time,e = parts[2].replace(".mp3", "").replace("_", " ")
cat input.txt | piper -m /opt/piper/etc/test_voice.onnx -f output.wav
        })        # Add to metadata1. Check ePub validity with: epubcheck your_book.epub```
# Alternative syntax
piper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt
     # In a real implementation, you would get actual duration         "title": f"Chapter {chapter_num}: {chapter_title}"Restart the Jetson to clear memory (sudo reboot)
# Converting to MP3 format afterward        current_time += 300.0  # Assume 5 minutes per chapter        })3. Use half precision (already implemented in both scripts)
ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3
``` metadata to file # Update time for next chapter (approximate)e background applications (browsers, unnecessary services)
f:, you would get actual durationed approach) -h
### 8.4 Dependency Installation Issuesn metadata:_time += 300.0  # Assume 5 minutes per chapter piper -m /opt/piper/etc/test_voice.onnx -f output.wavt, try swap space:
```bashitle']}\n")
# If pip fails to install packages# Write metadata to file# Alternative syntax   sudo chmod 600 /swapfile
sudo apt updatemetadata file with {len(metadata)} chapters")"w") as f:st_voice.onnx --output_file output.wav < input.txt
sudo apt install -y python3-dev build-essential
        f.write(f"{entry['time']:.2f}:{entry['title']}\n")# Converting to MP3 format afterward```
# For audio library issues
sudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-toolsmp3
```'```
# If you encounter SSL certificate errors during package downloads
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name> Jetson Devices

# For CUDA-related package issuespt updateConvert PDF to ePub using tools like Calibre before processing
export TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"```bashsudo apt install -y python3-dev build-essential
pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.htmles
```hon generate_audiobook_piper.py --input your_book.epub --chapter_range 1-10you have two Jetson Orin Nano devices, you can divide the workload:or audio library issuesCheck ePub validity with: epubcheck your_book.epub
g libav-tools-convert your_book.epub fixed.epub
### 8.5 Docker or Container Issues
```_book.epub --chapter_range 11-20
# If container fails to start```python generate_audiobook_piper.py --input your_book.epub --chapter_range 1-10pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name>
sudo systemctl restart docker
sudo systemctl restart nvidia-container-runtime
For Piper, you can adjust parameters:python generate_audiobook_piper.py --input your_book.epub --chapter_range 11-20export TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"# Using stdin for input (recommended approach)
# If GPU is not available in container
./jetson-containers run --runtime nvidia --gpus all piper-tts
se higher quality settings 7.3 Improving Voice Qualityrnative syntax
# If container lacks permission to access mounted volumespiper --model en_US-lessac-medium --output_file output.wav --file input.txt --speaker-id 0 --quality 100For Piper, you can adjust parameters:### 8.5 Docker or Container Issuespiper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt
sudo chown -R 1000:1000 ~/audiobook_data ~/audiobook
```hf container fails to startonverting to MP3 format afterward
fy voice parameters:sra libmp3lame -qscale:a 2 output.mp3
### 8.6 Processing Performance Issues
```
# If processing is too slow:
1. Monitor temperature and throttling: sudo tegrastats
2. Add external cooling fan or heatsink
3. Reduce system load by closing other applicationsious"
4. Consider nighttime processing when ambient temperature is cooler speaking_rate=0.95,   # 1.0 is normal speed, lower is slowerdjust voice parameters (example)o chown -R 1000:1000 ~/audiobook_data ~/audiobooko apt install -y python3-dev build-essential
5. Use jetson_clocks to maximize performance: sudo jetson_clocks    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustmentaudio = model.generate(```
6. If using Docker, ensure nvidia-docker runtime is properly configuredift=0.0      # Values between -1.0 and 1.0 for volume/energy,
```)    voice_preset="calm",  # Options: "default", "calm", "excited", "serious"### 8.6 Processing Performance Issuessudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools

## Conclusion    pitch_shift=0.0,      # Values between -1.0 and 1.0 for pitch adjustment# If processing is too slow:# If you encounter SSL certificate errors during package downloads
 1.0 for volume/energy tegrastatsed-host files.pythonhosted.org <package_name>
This comprehensive plan provides two complete approaches for generating an audiobook from ePub or PDF files on Jetson Orin Nano devices, with ePub being the recommended format for better chapter detection and text extraction. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis.

Both methods now include enhanced features:
- Proper chapter detection and organization for both ePub and PDF formatson_clockswnload.pytorch.org/whl/cu113/torch_stable.html
- Per-chapter audio generation with descriptive filenames 1000)
- Improved text extraction and preprocessing2. Restart the Jetson to clear memory (sudo reboot)### 8.1 Memory Errors```
- Support for resuming interrupted processing
- Comprehensive troubleshooting guidance4. Process fewer chunks at a time# If you encounter CUDA out of memory errors:## Conclusion```



By following this guide, you can convert your book into a high-quality audiobook using local processing on your Jetson Orin Nano, with chapter-based organization that makes the final result more usable and professional.























































































By following this guide, you can convert your book into a high-quality audiobook using local processing on your Jetson Orin Nano, with chapter-based organization that makes the final result more usable and professional.- Comprehensive troubleshooting guidance- Support for resuming interrupted processing- Improved text extraction and preprocessing- Per-chapter audio generation with descriptive filenames- Proper chapter detection and organization for both ePub and PDF formatsBoth methods now include enhanced features:This comprehensive plan provides two complete approaches for generating an audiobook from ePub or PDF files on Jetson Orin Nano devices, with ePub being the recommended format for better chapter detection and text extraction. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis.## Conclusion```6. If using Docker, ensure nvidia-docker runtime is properly configured5. Use jetson_clocks to maximize performance: sudo jetson_clocks4. Consider nighttime processing when ambient temperature is cooler3. Reduce system load by closing other applications2. Add external cooling fan or heatsink1. Monitor temperature and throttling: sudo tegrastats# If processing is too slow:```### 8.6 Processing Performance Issues```sudo chown -R 1000:1000 ~/audiobook_data ~/audiobook# If container lacks permission to access mounted volumes./jetson-containers run --runtime nvidia --gpus all piper-tts# If GPU is not available in containersudo systemctl restart nvidia-container-runtimesudo systemctl restart docker# If container fails to start```### 8.5 Docker or Container Issues```pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.htmlexport TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"# For CUDA-related package issuespip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name># If you encounter SSL certificate errors during package downloadssudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools# For audio library issuessudo apt install -y python3-dev build-essentialsudo apt update# If pip fails to install packages```bash### 8.4 Dependency Installation Issues```ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3# Converting to MP3 format afterwardpiper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt# Alternative syntaxcat input.txt | piper -m /opt/piper/etc/test_voice.onnx -f output.wav# Using stdin for input (recommended approach)```bash### 8.3 Piper Command Syntax```3. Inspect book structure: unzip -l your_book.epub2. Try converting with: ebook-convert your_book.epub fixed.epub1. Check ePub validity with: epubcheck your_book.epub# If ePub extraction misses content or chapters:3. Convert PDF to ePub using tools like Calibre before processing2. Use a different PDF reader: pip install pdfplumber1. Try OCR-based extraction: pip install pytesseract# If PDF text extraction is poor:```### 8.2 Text Extraction Issues```   sudo swapon /swapfile   sudo mkswap /swapfile   sudo chmod 600 /swapfile   sudo fallocate -l 4G /swapfile7. If persistent, try swap space:6. Monitor memory usage with: free -h5. Close background applications (browsers, unnecessary services)



























































































By following this guide, you can convert your book into a high-quality audiobook using local processing on your Jetson Orin Nano, with chapter-based organization that makes the final result more usable and professional.- Comprehensive troubleshooting guidance- Support for resuming interrupted processing- Improved text extraction and preprocessing- Per-chapter audio generation with descriptive filenames- Proper chapter detection and organization for both ePub and PDF formatsBoth methods now include enhanced features:This comprehensive plan provides two complete approaches for generating an audiobook from ePub or PDF files on Jetson Orin Nano devices, with ePub being the recommended format for better chapter detection and text extraction. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis.## Conclusion```6. If using Docker, ensure nvidia-docker runtime is properly configured5. Use jetson_clocks to maximize performance: sudo jetson_clocks4. Consider nighttime processing when ambient temperature is cooler3. Reduce system load by closing other applications2. Add external cooling fan or heatsink1. Monitor temperature and throttling: sudo tegrastats# If processing is too slow:```### 8.6 Processing Performance Issues```sudo chown -R 1000:1000 ~/audiobook_data ~/audiobook# If container lacks permission to access mounted volumes./jetson-containers run --runtime nvidia --gpus all piper-tts# If GPU is not available in containersudo systemctl restart nvidia-container-runtimesudo systemctl restart docker# If container fails to start```### 8.5 Docker or Container Issues```pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.htmlexport TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"# For CUDA-related package issuespip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name># If you encounter SSL certificate errors during package downloadssudo apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools# For audio library issuessudo apt install -y python3-dev build-essentialsudo apt update# If pip fails to install packages```bash### 8.4 Dependency Installation Issues```ffmpeg -i output.wav -codec:a libmp3lame -qscale:a 2 output.mp3# Converting to MP3 format afterwardpiper -m /opt/piper/etc/test_voice.onnx --output_file output.wav < input.txt# Alternative syntaxcat input.txt | piper -m /opt/piper/etc/test_voice.onnx -f output.wav# Using stdin for input (recommended approach)```bash### 8.3 Piper Command Syntax```3. Inspect book structure: unzip -l your_book.epub2. Try converting with: ebook-convert your_book.epub fixed.epub1. Check ePub validity with: epubcheck your_book.epub# If ePub extraction misses content or chapters:3. Convert PDF to ePub using tools like Calibre before processing2. Use a different PDF reader: pip install pdfplumber1. Try OCR-based extraction: pip install pytesseract# If PDF text extraction is poor:```### 8.2 Text Extraction Issues```   sudo swapon /swapfile   sudo mkswap /swapfile   sudo chmod 600 /swapfile   sudo fallocate -l 4G /swapfile7. If persistent, try swap space:6. Monitor memory usage with: free -h5. Close background applications (browsers, unnecessary services)4. Process fewer chunks at a time3. Use half precision (already implemented in both scripts)2. Restart the Jetson to clear memory (sudo reboot)1. Reduce chunk size (try 500 instead of 1000)











By following this guide, you can convert your book into a high-quality audiobook using local processing on your Jetson Orin Nano, with chapter-based organization that makes the final result more usable and professional.- Comprehensive troubleshooting guidance- Support for resuming interrupted processing- Improved text extraction and preprocessing- Per-chapter audio generation with descriptive filenames- Proper chapter detection and organization for both ePub and PDF formatsBoth methods now include enhanced features:This comprehensive plan provides two complete approaches for generating an audiobook from ePub or PDF files on Jetson Orin Nano devices, with ePub being the recommended format for better chapter detection and text extraction. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis.# If container fails to start
sudo systemctl restart docker
sudo systemctl restart nvidia-container-runtime

# If GPU is not available in container
./jetson-containers run --runtime nvidia --gpus all piper-tts

# If container lacks permission to access mounted volumes
sudo chown -R 1000:1000 ~/audiobook_data ~/audiobook
```

### 8.6 Processing Performance Issues
```
# If processing is too slow:
1. Monitor temperature and throttling: sudo tegrastats
2. Add external cooling fan or heatsink
3. Reduce system load by closing other applications
4. Consider nighttime processing when ambient temperature is cooler
5. Use jetson_clocks to maximize performance: sudo jetson_clocks
6. If using Docker, ensure nvidia-docker runtime is properly configured
```

## Conclusion

This comprehensive plan provides two complete approaches for generating an audiobook from ePub or PDF files on Jetson Orin Nano devices, with ePub being the recommended format for better chapter detection and text extraction. The Piper approach using jetson-containers offers simplicity and efficiency, while the Sesame CSM approach provides higher quality voice synthesis.

Both methods now include enhanced features:
- Proper chapter detection and organization for both ePub and PDF formats
- Per-chapter audio generation with descriptive filenames
- Improved text extraction and preprocessing
- Support for resuming interrupted processing
- Comprehensive troubleshooting guidance

By following this guide, you can convert your book into a high-quality audiobook using local processing on your Jetson Orin Nano, with chapter-based organization that makes the final result more usable and professional.
