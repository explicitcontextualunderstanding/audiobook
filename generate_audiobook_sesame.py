#!/usr/bin/env python3

import argparse
import os
import sys
import re
import shutil
import time
import datetime
import psutil
from tqdm import tqdm
from pydub import AudioSegment
import torch
import torchaudio

# Add paths to help find the audiobook_generator module
sys.path.insert(0, '/opt/csm')
# Also add the docker utils path which contains our custom modules
if os.path.exists('/opt/utils'):
    sys.path.insert(0, '/opt/utils')
elif os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docker/sesame-tts/utils')):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docker/sesame-tts/utils'))

try:
    # Import from our custom audiobook_generator module
    from audiobook_generator import load_csm_1b, Segment
    print("Successfully imported audiobook_generator module")
except ModuleNotFoundError as e:
    print(f"Error importing audiobook_generator: {e}")
    print("Attempting fallback import path...")
    try:
        # Fallback to direct import from generator if running in original container
        from generator import load_csm_1b, Segment
        print("Successfully imported from generator module")
    except ModuleNotFoundError as e2:
        print(f"Failed fallback import: {e2}")
        print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
        print("sys.path:", sys.path)
        print("Current directory:", os.getcwd())
        print("Directory contents:", os.listdir())
        sys.exit(1)

# --- Helper Functions ---
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except (nltk.downloader.DownloadError, LookupError):
    print("NLTK 'punkt' tokenizer not found. Attempting to download...")
    try:
        nltk.download('punkt')
        print("Successfully downloaded NLTK punkt tokenizer")
    except Exception as e:
        print(f"Error downloading NLTK punkt: {e}")
        sys.exit("Error: NLTK 'punkt' not available.")
from nltk.tokenize import sent_tokenize

def html_to_text(html_content):
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Get text and remove extra whitespace
    text = ' '.join(soup.stripped_strings)
    return text

def extract_text_from_epub(epub_path):
    """Extract text from an ePub file, chapter by chapter."""
    print("Extracting text from ePub: {}...".format(epub_path))
    try:
        book = epub.read_epub(epub_path)
        chapters_text = []
        # Process items in reading order (spine)
        for item in tqdm(book.get_items_of_type(ebooklib.ITEM_DOCUMENT), desc="Processing ePub items"):
            content = item.get_content().decode('utf-8', errors='ignore')
            text = html_to_text(content)
            if text: # Only add if text is not empty
                chapters_text.append(text)
        full_text = "\n\n".join(chapters_text) # Join chapters
        print("Extracted text from {} items.".format(len(chapters_text)))
        return full_text
    except Exception as e:
        print("Error reading EPUB file {}: {}".format(epub_path, e))
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print("Extracting text from PDF: {}...".format(pdf_path))
    full_text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in tqdm(reader.pages, desc="Processing PDF pages"):
            try:
                page_text = page.extract_text()
                if page_text:
                    # Basic cleaning (remove excessive newlines)
                    page_text = re.sub(r'\n\s*\n', '\n', page_text)
                    full_text += page_text + "\n"
            except Exception as page_e:
                print("Warning: Could not extract text from a PDF page: {}".format(page_e))
        print("Extracted text from {} pages.".format(len(reader.pages)))
        return full_text.strip()
    except Exception as e:
        print("Error reading PDF file {}: {}".format(pdf_path, e))
        return None

def split_text(text, max_length=500, sentence_boundary=True):
    """Split text into chunks, respecting sentence boundaries if possible."""
    print("Splitting text...")
    if not text:
        return []
    
    chunks = []
    if sentence_boundary:
        sentences = sent_tokenize(text)
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + " "
            else:
                # Add the current chunk if it's not empty
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # Start new chunk, handle sentence longer than max_length
                if len(sentence) > max_length:
                    # Force split long sentence
                    for i in range(0, len(sentence), max_length):
                         chunks.append(sentence[i:i+max_length])
                    current_chunk = "" # Reset chunk
                else:
                    current_chunk = sentence + " "
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
    else:
        # Simple character split if sentence boundary is false
        for i in range(0, len(text), max_length):
            chunks.append(text[i:i+max_length])

    print("Split into {} chunks.".format(len(chunks)))
    return chunks

def process_range(range_str, max_val):
    """Process a range string like '1-5' and return a list of indices."""
    if not range_str:
        return list(range(max_val))  # All chunks
    
    try:
        # Parse the range string (e.g., "1-5")
        parts = range_str.split('-')
        if len(parts) == 1:
            # Single value
            start = int(parts[0]) - 1  # Convert to 0-based index
            end = start + 1
        else:
            # Range
            start = int(parts[0]) - 1  # Convert to 0-based index
            end = int(parts[1])
        
        # Validate range
        if start < 0 or end > max_val or start >= end:
            print(f"Warning: Invalid range {range_str} for {max_val} chunks. Using all chunks.")
            return list(range(max_val))
        
        return list(range(start, end))
    except ValueError:
        print(f"Warning: Could not parse range string '{range_str}'. Using all chunks.")
        return list(range(max_val))

def find_voice_preset_file(model_path, voice_preset):
    """Find the voice preset file in various possible locations."""
    if not voice_preset:
        return None
    
    # Define possible preset locations and extensions
    extensions = ['.wav', '.mp3']
    locations = [
        model_path,
        os.path.join(model_path, 'prompts'),
        os.path.join(model_path, 'presets'),
        os.path.join(model_path, 'voices'),
    ]
    
    # Try with and without extension
    preset_names = [voice_preset]
    for ext in extensions:
        preset_names.append(f"{voice_preset}{ext}")
    
    # Search all combinations
    for location in locations:
        if os.path.exists(location) and os.path.isdir(location):
            for name in preset_names:
                path = os.path.join(location, name)
                if os.path.exists(path) and os.path.isfile(path):
                    return path
    
    return None

def synthesize_chunk(generator, text, voice_preset_wav, output_path, device):
    """Synthesizes audio for a text chunk using the generator."""
    try:
        context = []
        speaker_id = 0 # Default speaker ID

        # Use voice_preset_wav as context
        if voice_preset_wav and os.path.exists(voice_preset_wav):
            try:
                ref_wav, ref_sr = torchaudio.load(voice_preset_wav)
                # Resample if necessary
                if ref_sr != generator.sample_rate:
                    ref_wav = torchaudio.functional.resample(ref_wav.squeeze(0), orig_freq=ref_sr, new_freq=generator.sample_rate)
                else:
                    ref_wav = ref_wav.squeeze(0)
                # Create a Segment for context
                # Use a placeholder text for the context segment
                context = [Segment(text="Voice prompt.", speaker=speaker_id, audio=ref_wav.to(device))]
                print(f"Using voice preset as context: {voice_preset_wav}")
            except Exception as load_e:
                print("Warning: Could not load or process voice preset {}: {}".format(voice_preset_wav, load_e))
                context = [] # Fallback to no context
        
        # Generate audio using the new method
        audio = generator.generate(
            text=text,
            speaker=speaker_id,
            context=context,
            max_audio_length_ms=60_000, # Allow longer chunks (60s)
        )

        # Save generated audio
        torchaudio.save(output_path, audio.unsqueeze(0).cpu(), generator.sample_rate)
        return True
    except Exception as e:
        print("Error during synthesis for chunk: {}".format(e))
        # print("Chunk text: {}".format(text[:100])) # Optional debug
        return False

def main(args):
    # Validate input file path
    if not os.path.exists(args.input):
        print("Error: Input file '{}' does not exist.".format(args.input))
        return

    # Validate model path (still needed for load_csm_1b)
    if not os.path.exists(args.model_path) or not os.path.isdir(args.model_path):
        print("Error: Model path '{}' does not exist or is not a directory.".format(args.model_path))
        return

    # Determine voice preset path (used for context)
    voice_preset_path = None
    if args.voice_preset:
        voice_preset_path = find_voice_preset_file(args.model_path, args.voice_preset)
        if not voice_preset_path:
            print("Warning: Could not find voice preset '{}' in model path or its subdirectories. Proceeding without voice preset context.".format(args.voice_preset))
        else:
             print("Using voice preset for context: {}".format(voice_preset_path))
    else:
        print("No voice preset specified, using default voice.")

    # Create output directories
    temp_dir = args.temp_dir or os.path.join(os.path.dirname(args.output), "temp_audio_sesame")
    os.makedirs(temp_dir, exist_ok=True)

    # --- Model Loading ---
    print("Loading Sesame CSM model from '{}'...".format(args.model_path))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device: {}".format(device))
    try:
        # Load using the new function, passing the model path
        generator = load_csm_1b(args.model_path, device=device)
        print("Model loaded successfully. Sample rate: {}".format(generator.sample_rate))
    except Exception as e:
        print("Error loading model: {}".format(e))
        # Check if it's related to Llama-3.2-1B access
        if "meta-llama/Llama-3.2-1B" in str(e):
             print("Ensure you are logged into Hugging Face CLI and have accepted terms for meta-llama/Llama-3.2-1B.")
        return

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
    text_chunks = split_text(full_text, max_length=args.chunk_length, sentence_boundary=True)
    
    # --- Process Chapter Range ---
    if args.chapter_range:
        chunk_indices = process_range(args.chapter_range, len(text_chunks))
        selected_chunks = [text_chunks[i] for i in chunk_indices]
        print(f"Processing {len(selected_chunks)} chunks from specified range: {args.chapter_range}")
        text_chunks = selected_chunks

    # --- Apply Memory Constraints ---
    if args.memory_per_chunk > 0 and args.max_batch_size > 0:
        # Split into batches to manage memory
        max_chunks = args.max_batch_size
        print(f"Processing in batches of maximum {max_chunks} chunks (memory per chunk: {args.memory_per_chunk}MB)")
        batches = [text_chunks[i:i+max_chunks] for i in range(0, len(text_chunks), max_chunks)]
    else:
        # Process all at once
        batches = [text_chunks]
        
    # --- Audio Synthesis ---
    print("Starting audio synthesis...")
    audio_files = []
    start_time = time.time()
    
    batch_count = len(batches)
    for batch_idx, batch in enumerate(batches):
        print(f"Processing batch {batch_idx+1}/{batch_count} ({len(batch)} chunks)")
        
        for i, chunk in enumerate(tqdm(batch, desc=f"Synthesizing Batch {batch_idx+1}")):
            overall_idx = batch_idx * args.max_batch_size + i if args.max_batch_size > 0 else i
            chunk_filename = os.path.join(temp_dir, "chunk_{:04d}.wav".format(overall_idx))
            
            if os.path.exists(chunk_filename) and os.path.getsize(chunk_filename) > 0:
                print(f"Chunk {overall_idx} already exists, skipping synthesis")
                audio_files.append(chunk_filename)
                continue

            if not synthesize_chunk(generator, chunk, voice_preset_path, chunk_filename, device):
                print("Warning: Failed to synthesize chunk {}. Skipping.".format(overall_idx))
                continue # Skip this chunk

            audio_files.append(chunk_filename)
        
        # Clean up GPU memory between batches
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not audio_files:
        print("Error: No audio chunks were successfully synthesized.")
        return

    end_time = time.time()
    print("Audio synthesis complete in {:.2f} seconds.".format(end_time - start_time))

    # --- Audio Concatenation ---
    print("Combining audio chunks...")
    combined_audio = AudioSegment.empty()
    try:
        for audio_file in tqdm(audio_files, desc="Combining Audio"):
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                try:
                    segment = AudioSegment.from_wav(audio_file)
                    combined_audio += segment
                except Exception as combine_e:
                     print("Warning: Could not process audio file {}: {}".format(audio_file, combine_e))
            else:
                print("Warning: Skipping missing or empty audio file: {}".format(audio_file))

        if len(combined_audio) == 0:
            print("Error: Combined audio is empty. Cannot export.")
            return

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
    parser.add_argument("--model_path", required=True, help="Path to the directory containing the downloaded Sesame model files (used by load_csm_1b).")
    parser.add_argument("--voice_preset", default=None, help="Name of the voice preset to use (without extension, e.g., 'calm'). If omitted, uses default voice.")
    parser.add_argument("--chunk_length", type=int, default=500, help="Approximate maximum character length for text chunks (respects sentence boundaries).")
    parser.add_argument("--temp_dir", default=None, help="Directory to store temporary audio chunks. Defaults to 'temp_audio_sesame' next to the output file.")
    parser.add_argument("--keep_temp", action='store_true', help="Keep temporary audio chunk files after generation.")
    parser.add_argument("--chapter_range", default=None, help="Range of chapters to process (e.g., '1-5')")
    parser.add_argument("--memory_per_chunk", type=int, default=150, help="Estimated memory usage per chunk in MB.")
    parser.add_argument("--max_batch_size", type=int, default=8, help="Maximum number of chunks to process in a single batch.")

    args = parser.parse_args()
    main(args)
