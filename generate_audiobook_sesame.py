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
import time
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import datetime
import psutil
import shutil

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Validate input file exists and has correct format
def validate_input_file(file_path):
    """Validate that the input file exists and has the correct format."""
    if not os.path.exists(file_path):
        print(f"Error: Input file '{file_path}' does not exist.")
        return False
        
    if not (file_path.lower().endswith('.epub') or file_path.lower().endswith('.pdf')):
        print(f"Error: Input file format not supported. Only .epub and .pdf files are supported.")
        return False
        
    return True

def html_to_text(html_content):
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_epub(epub_path):
    """Extract text and chapters from an ePub file."""
    print(f"Extracting text from ePub: {epub_path}...")
    
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
        title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapter_titles) + 1}"
        
        # Extract text
        text = html_to_text(content)
        
        # Skip if no meaningful content
        if len(text.strip()) < 50:
            continue
            
        chapters.append(text)
        chapter_titles.append(title)
    
    print(f"Extracted {len(chapters)} chapters from ePub")
    return chapters, chapter_titles

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file and attempt to detect chapters."""
    print(f"Extracting text from PDF: {pdf_path}...")
    
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
    print(f"Detected {len(chapters)} chapters from PDF")
    
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

def generate_audio(model, text, output_path, voice_preset="default", speaking_rate=1.0):
    """Generate audio for a text segment."""
    try:
        # Clear CUDA cache
        torch.cuda.empty_cache()
        
        # Generate audio
        audio = model.generate(
            text=text,
            voice_preset=voice_preset,
            speaking_rate=speaking_rate
        )
        
        audio.export(output_path, format="mp3")
        return True
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False

def combine_audio_files(audio_files, output_path):
    """Combine multiple audio files into a single audiobook."""
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

def process_chapter(model, chapter_text, chapter_title, chapter_num, args):
    """Process a single chapter and generate audio."""
    print(f"Processing chapter {chapter_num}: {chapter_title}")
    
    # Create chapter directory
    chapter_dir = os.path.join(args.temp_dir, f"chapter_{chapter_num:02d}")
    os.makedirs(chapter_dir, exist_ok=True)
    
    # Split chapter text into chunks
    chunks = preprocess_text(chapter_text, args.chunk_size)
    print(f"Chapter split into {len(chunks)} chunks")
    
    # Estimate processing time
    estimated_time = estimate_processing_time(len(chunks))
    print(f"Estimated processing time for this chapter: {estimated_time}")
    
    # Generate audio for each chunk
    audio_files = []
    start_time = time.time()
    
    # Calculate chunks per batch based on memory limit
    available_memory = psutil.virtual_memory().available
    memory_per_chunk = args.memory_per_chunk  # MB per chunk (estimated)
    chunks_per_batch = min(
        args.max_batch_size,
        max(1, int(available_memory / (memory_per_chunk * 1024 * 1024)))
    )
    print(f"Processing up to {chunks_per_batch} chunks at a time based on available memory")
    
    for i, chunk in enumerate(tqdm(chunks, desc="Generating audio")):
        output_path = os.path.join(chapter_dir, f"chunk_{i:04d}.mp3")
        
        # Skip if already processed
        if os.path.exists(output_path):
            print(f"Skipping chunk {i} - already processed")
            audio_files.append(output_path)
            continue
            
        # Generate audio
        success = generate_audio(model, chunk, output_path, args.voice_preset, args.speaking_rate)
        
        if success:
            audio_files.append(output_path)
            
        # Calculate and display progress
        if i > 0 and i % 5 == 0:
            elapsed_time = time.time() - start_time
            avg_time_per_chunk = elapsed_time / i
            remaining_chunks = len(chunks) - i
            estimated_remaining = remaining_chunks * avg_time_per_chunk
            eta = str(datetime.timedelta(seconds=int(estimated_remaining)))
            print(f"Progress: {i}/{len(chunks)} chunks ({i/len(chunks)*100:.1f}%) - ETA: {eta}")
        
        # Take a short break every few chunks to prevent overheating and clear memory
        if i > 0 and i % chunks_per_batch == 0:
            print("Taking a break to free up memory and prevent overheating...")
            torch.cuda.empty_cache()
            time.sleep(10)
    
    # Combine audio files for this chapter
    if audio_files:
        safe_title = re.sub(r'[^\w\s-]', '', chapter_title).strip().replace(' ', '_')
        chapter_output = os.path.join(args.output_dir, f"chapter_{chapter_num:02d}_{safe_title}.mp3")
        combine_audio_files(audio_files, chapter_output)
        print(f"Chapter audio saved to {chapter_output}")
        return chapter_output
    else:
        print(f"No audio generated for chapter {chapter_num}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate an audiobook using Sesame CSM")
    parser.add_argument("--input", required=True, help="Path to the input book file (ePub or PDF)")
    parser.add_argument("--output", default="audiobook_sesame.mp3", help="Output combined audiobook file path")
    parser.add_argument("--output_dir", default="audiobook_chapters_sesame", help="Output directory for chapter files")
    parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    parser.add_argument("--voice_preset", default="default", help="Voice preset (default, calm, excited, serious)")
    parser.add_argument("--speaking_rate", type=float, default=1.0, help="Speaking rate (1.0 is normal)")
    parser.add_argument("--max_batch_size", type=int, default=10, help="Maximum chunks to process before pausing")
    parser.add_argument("--memory_per_chunk", type=int, default=150, help="Estimated memory usage per chunk in MB")
    parser.add_argument("--chapter_range", help="Range of chapters to process (e.g., '1-5')")
    args = parser.parse_args()
    
    # Validate input file
    if not validate_input_file(args.input):
        return 1
    
    # Create directories
    os.makedirs(args.temp_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load CSM model
    print("Loading Sesame CSM model...")
    from csm import CSMModel
    model = CSMModel.from_pretrained("sesame/csm-1b")
    model = model.half().to("cuda")  # Use half precision to save memory
    
    # Determine file type and extract text
    input_path = args.input
    
    if input_path.lower().endswith('.epub'):
        chapters, chapter_titles = extract_text_from_epub(input_path)
    elif input_path.lower().endswith('.pdf'):
        chapters, chapter_titles = extract_text_from_pdf(input_path)
    else:
        print(f"Unsupported file format: {input_path}")
        print("Supported formats: .epub, .pdf")
        return 1
    
    # Process only specified chapter range if provided
    if args.chapter_range:
        try:
            start, end = map(int, args.chapter_range.split('-'))
            chapter_range = range(start-1, min(end, len(chapters)))
            selected_chapters = [chapters[i] for i in chapter_range]
            selected_titles = [chapter_titles[i] for i in chapter_range]
            chapters = selected_chapters
            chapter_titles = selected_titles
            print(f"Processing chapters {start} to {min(end, len(selected_chapters)+start-1)}")
        except ValueError:
            print(f"Invalid chapter range format: {args.chapter_range}. Expected format: '1-5'")
            return 1
    
    # Estimate total processing time
    total_text_length = sum(len(chapter) for chapter in chapters)
    estimated_chunks = total_text_length / args.chunk_size
    estimated_time = estimate_processing_time(estimated_chunks)
    print(f"Total estimated processing time: {estimated_time}")
    
    # Process each chapter
    chapter_audio_files = []
    
    for i, (chapter_text, chapter_title) in enumerate(zip(chapters, chapter_titles)):
        chapter_audio = process_chapter(model, chapter_text, chapter_title, i+1, args)
        if chapter_audio:
            chapter_audio_files.append(chapter_audio)
    
    # Combine all chapters into a single audiobook if requested
    if args.output and chapter_audio_files:
        print(f"Combining {len(chapter_audio_files)} chapters into final audiobook...")
        combine_audio_files(chapter_audio_files, args.output)
        print(f"Audiobook saved to {args.output}")
    
    # Clean up temporary files if successful
    if args.temp_dir and os.path.exists(args.temp_dir) and chapter_audio_files:
        user_input = input("Processing complete! Would you like to remove temporary files to save space? (y/n): ")
        if user_input.lower() == 'y':
            print(f"Removing temporary files in {args.temp_dir}...")
            shutil.rmtree(args.temp_dir)
            print("Temporary files removed.")
    
    print("Audiobook generation complete!")
    return 0

if __name__ == "__main__":
    main()
