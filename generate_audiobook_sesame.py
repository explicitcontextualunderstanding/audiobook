#!/usr/bin/env python3

import argparse
import os
import sys # Import sys module
import re
import shutil
import time
import datetime
import psutil
from tqdm import tqdm
from pydub import AudioSegment
import torch
import torchaudio

# Add /opt/csm to the Python path
sys.path.insert(0, '/opt/csm')

# Now try importing CSM
try:
    from csm.model.model import CSM
    from csm.utils.spec_utils import wav_to_fbank
    from csm.utils.tokenizer import Tokenizer
except ImportError as e:
    print("Failed to import CSM module even after adding /opt/csm to path.")
    print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
    print("sys.path:", sys.path)
    raise e

# --- Helper Functions (assuming extract_text_from_epub, extract_text_from_pdf, split_text exist) ---

def html_to_text(html_content):
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_epub(epub_path):
    """Extract text and chapters from an ePub file."""
    print("Extracting text from ePub: {}...".format(epub_path))
    
    book = epub.read_epub(epub_path)
    chapters = []
    chapter_titles = []
    
    # Get the spine (reading order)
    spine = [item.get_id() for item in book.spine]
    
    # Process items in reading order
    for item_id in tqdm(spine, desc="Processing ePub items"):
        # Get the item
        item = book.get_item_with_id(item_id)
        
        # Skip if not a document
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
            
        # Get content
        content = item.get_content().decode('utf-8')
        
        # Find title if possible
        soup = BeautifulSoup(content, 'html.parser')
        title_tag = soup.find(['h1', 'h2', 'h3', 'h4'])
        title = title_tag.get_text().strip() if title_tag else "Chapter {}".format(len(chapter_titles) + 1)
        
        # Extract text
        text = html_to_text(content)
        
        # Skip if no meaningful content
        if len(text.strip()) < 50:
            continue
            
        chapters.append(text)
        chapter_titles.append(title)
    
    print("Extracted {} chapters from ePub".format(len(chapters)))
    return chapters, chapter_titles

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file and attempt to detect chapters."""
    print("Extracting text from PDF: {}...".format(pdf_path))
    
    reader = PdfReader(pdf_path)
    full_text = ""
    
    for i, page in enumerate(tqdm(reader.pages, desc="Processing PDF pages")):
        page_text = page.extract_text()
        
        # Clean up page headers, footers, page numbers, etc.
        page_text = re.sub(r'Page \d+ of \d+', '', page_text)
        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)
        
        full_text += page_text + "\n"
    
    # Detect chapters in the PDF text
    chapters, chapter_titles = detect_chapters_in_text(full_text)
    print("Detected {} chapters from PDF".format(len(chapters)))
    
    return chapters, chapter_titles

def detect_chapters_in_text(text):
    """Attempt to detect chapters in plain text."""
    # Common chapter heading patterns
    chapter_patterns = [
        r'^CHAPTER\s+\d+',          # "CHAPTER 1", "CHAPTER 2", etc.
        r'^Chapter\s+\d+',          # "Chapter 1", "Chapter 2", etc.
        r'^\d+\.\s+[A-Z]',          # "1. CHAPTER TITLE", "2. CHAPTER TITLE"
        r'^PART\s+\d+',             # "PART 1", "PART 2", etc.
        r'^Part\s+\d+',             # "Part 1", "Part 2", etc.
        r'^SECTION\s+\d+',          # "SECTION 1", "SECTION 2", etc.
        r'^Section\s+\d+',          # "Section 1", "Section 2", etc.
        r'^INTRODUCTION',           # "INTRODUCTION"
        r'^Introduction',           # "Introduction"
        r'^APPENDIX\s+\d*',         # "APPENDIX", "APPENDIX A", etc.
        r'^Appendix\s+\d*',         # "Appendix", "Appendix A", etc.
    ]
    
    # Split text into lines
    lines = text.split('\n')
    
    # Find potential chapter boundaries
    chapter_starts = []
    chapter_titles = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line matches a chapter pattern
        for pattern in chapter_patterns:
            if re.match(pattern, line):
                chapter_starts.append(i)
                chapter_titles.append(line)
                break
    
    # If no chapters detected, treat as a single chapter
    if not chapter_starts:
        return [text], ["Chapter 1"]
    
    # Extract chapter text
    chapters = []
    for i in range(len(chapter_starts)):
        start = chapter_starts[i]
        end = chapter_starts[i+1] if i+1 < len(chapter_starts) else len(lines)
        chapter_text = '\n'.join(lines[start:end]).strip()
        chapters.append(chapter_text)
    
    return chapters, chapter_titles

def preprocess_text(text, max_chunk_size=1000):
    """Clean and split text into manageable chunks."""
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
    
    return chunks

def estimate_processing_time(num_chunks, avg_time_per_chunk=10):
    """Estimate the total processing time based on number of chunks."""
    total_seconds = num_chunks * avg_time_per_chunk
    return str(datetime.timedelta(seconds=total_seconds))

def synthesize_chunk(model, tokenizer, text, voice_preset_wav, output_path, device):
    """Synthesizes audio for a text chunk using Sesame CSM."""
    try:
        # Ensure voice preset audio is loaded correctly
        if not os.path.exists(voice_preset_wav):
            print("Error: Voice preset file not found: {}".format(voice_preset_wav))
            return False
        
        # Load voice preset and convert to fbank
        ref_wav, ref_sr = torchaudio.load(voice_preset_wav)
        ref_fbank = wav_to_fbank(ref_wav, ref_sr, device=device)

        # Tokenize text
        text_tokens = torch.IntTensor(tokenizer.encode(text, lang='en')).unsqueeze(0).to(device)

        # Generate audio
        with torch.no_grad():
            gen_wav, gen_sr = model.generate(ref_fbank, text_tokens)

        # Save generated audio
        torchaudio.save(output_path, gen_wav.cpu(), gen_sr)
        return True
    except Exception as e:
        print("Error during synthesis for chunk: {}".format(e))
        # print("Chunk text: {}".format(text[:100])) # Optional: print problematic chunk start
        return False

def main(args):
    # Validate input file path
    if not os.path.exists(args.input):
        # Replace f-string on (originally) line 31
        print("Error: Input file '{}' does not exist.".format(args.input))
        return

    # Validate model path
    if not os.path.exists(args.model_path) or not os.path.isdir(args.model_path):
        print("Error: Model path '{}' does not exist or is not a directory.".format(args.model_path))
        return

    # Determine voice preset path
    # Assuming presets are within the model directory structure
    voice_preset_filename = "{}.wav".format(args.voice_preset) # Example: calm.wav
    # Look in common locations within the model dir
    potential_paths = [
        os.path.join(args.model_path, voice_preset_filename),
        os.path.join(args.model_path, "prompts", voice_preset_filename)
    ]
    voice_preset_path = None
    for path in potential_paths:
        if os.path.exists(path):
            voice_preset_path = path
            break
            
    if not voice_preset_path:
        print("Error: Could not find voice preset '{}' in model path '{}' or its 'prompts' subdirectory.".format(args.voice_preset, args.model_path))
        return
    print("Using voice preset: {}".format(voice_preset_path))


    # Create output directories if they don't exist
    temp_dir = args.temp_dir or os.path.join(os.path.dirname(args.output), "temp_audio_sesame")
    os.makedirs(temp_dir, exist_ok=True)

    # --- Text Extraction ---
    print("Extracting text from '{}'...".format(args.input))
    file_extension = os.path.splitext(args.input)[1].lower()
    if file_extension == '.epub':
        full_text = extract_text_from_epub(args.input)
    elif file_extension == '.pdf':
        full_text = extract_text_from_pdf(args.input)
    else:
        print("Error: Unsupported file format '{}'. Please use EPUB or PDF.".format(file_extension))
        return

    if not full_text:
        print("Error: Could not extract text from the input file.")
        return
    print("Text extracted successfully.")

    # --- Text Splitting ---
    print("Splitting text into manageable chunks...")
    text_chunks = split_text(full_text, max_length=args.chunk_length) # Use args.chunk_length
    print("Text split into {} chunks.".format(len(text_chunks)))

    # --- Model Loading ---
    print("Loading Sesame CSM model from '{}'...".format(args.model_path))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device: {}".format(device))

    try:
        # Assuming model files (config.json, ckpt.pt/model.safetensors) are in model_path
        config_path = os.path.join(args.model_path, 'config.json')
        
        # Find checkpoint file
        ckpt_path = None
        if os.path.exists(os.path.join(args.model_path, 'ckpt.pt')):
            ckpt_path = os.path.join(args.model_path, 'ckpt.pt')
        elif os.path.exists(os.path.join(args.model_path, 'model.safetensors')):
             ckpt_path = os.path.join(args.model_path, 'model.safetensors') # CSM might need specific loading for safetensors

        if not ckpt_path:
             print("Error: Could not find 'ckpt.pt' or 'model.safetensors' in model path '{}'".format(args.model_path))
             return

        model = CSM.from_pretrained(config_path=config_path, ckpt_path=ckpt_path)
        model.eval()
        model.to(device)
        tokenizer = Tokenizer() # Assuming Tokenizer doesn't need model path
        print("Model loaded successfully.")
    except Exception as e:
        print("Error loading model: {}".format(e))
        return

    # --- Audio Synthesis ---
    print("Starting audio synthesis...")
    audio_files = []
    synthesis_failed = False
    for i, chunk in enumerate(tqdm(text_chunks, desc="Synthesizing Chunks")):
        chunk_filename = os.path.join(temp_dir, "chunk_{:04d}.wav".format(i))
        
        # Resume capability: Skip if chunk already exists
        if os.path.exists(chunk_filename) and os.path.getsize(chunk_filename) > 0:
            # print(f"Skipping existing chunk {i}") # Use .format() if needed
            audio_files.append(chunk_filename)
            continue

        if not synthesize_chunk(model, tokenizer, chunk, voice_preset_path, chunk_filename, device):
            print("Warning: Failed to synthesize chunk {}. Skipping.".format(i))
            # Decide if you want to stop on failure or just skip
            # synthesis_failed = True
            # break 
            continue # Skip this chunk

        audio_files.append(chunk_filename)
        
    if synthesis_failed:
         print("Audio synthesis aborted due to errors.")
         # Optional: Clean up temp files?
         return

    if not audio_files:
        print("Error: No audio chunks were successfully synthesized.")
        return

    print("Audio synthesis complete.")

    # --- Audio Concatenation ---
    print("Combining audio chunks...")
    combined_audio = AudioSegment.empty()
    try:
        for audio_file in tqdm(audio_files, desc="Combining Audio"):
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                segment = AudioSegment.from_wav(audio_file)
                combined_audio += segment
            else:
                print("Warning: Skipping missing or empty audio file: {}".format(audio_file))

        # Export final audio file
        output_format = os.path.splitext(args.output)[1].lower().strip('.') or 'mp3'
        print("Exporting final audiobook to '{}' (format: {})...".format(args.output, output_format))
        combined_audio.export(args.output, format=output_format)
        print("Audiobook generation complete!")

    except Exception as e:
        print("Error during audio concatenation or export: {}".format(e))

    # --- Cleanup (Optional) ---
    if not args.keep_temp:
        print("Cleaning up temporary files...")
        for audio_file in audio_files:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception as e:
                print("Warning: Could not remove temp file {}: {}".format(audio_file, e))
        try:
            # Attempt to remove the temp directory if it's empty
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                 os.rmdir(temp_dir)
        except Exception as e:
            print("Warning: Could not remove temp directory {}: {}".format(temp_dir, e))
        print("Cleanup complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an audiobook using Sesame CSM.")
    parser.add_argument("--input", required=True, help="Path to the input EPUB or PDF file.")
    parser.add_argument("--output", required=True, help="Path to the output audio file (e.g., audiobook.mp3).")
    parser.add_argument("--model_path", required=True, help="Path to the directory containing the downloaded Sesame model files (config.json, ckpt.pt/model.safetensors).")
    parser.add_argument("--voice_preset", default="calm", help="Name of the voice preset WAV file (without extension, e.g., 'calm', 'read_speech_a') located in the model directory or its 'prompts' subdirectory.")
    parser.add_argument("--chunk_length", type=int, default=500, help="Maximum character length for text chunks.")
    parser.add_argument("--temp_dir", default=None, help="Directory to store temporary audio chunks. Defaults to 'temp_audio_sesame' next to the output file.")
    parser.add_argument("--keep_temp", action='store_true', help="Keep temporary audio chunk files after generation.")

    # Placeholder for potentially missing helper functions if they weren't included
    def extract_text_from_epub(file_path):
        print("Placeholder: extract_text_from_epub called for {}".format(file_path))
        # Implement actual EPUB extraction using ebooklib/BeautifulSoup
        return "This is placeholder text from EPUB."

    def extract_text_from_pdf(file_path):
        print("Placeholder: extract_text_from_pdf called for {}".format(file_path))
        # Implement actual PDF extraction using PyPDF2 or pdfminer.six
        return "This is placeholder text from PDF."

    def split_text(text, max_length):
        print("Placeholder: split_text called")
        # Implement actual text splitting logic (e.g., using nltk sentence tokenizer)
        # Simple split for placeholder:
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    args = parser.parse_args()
    main(args)
