#!/usr/bin/env python3

import os
import sys
import torch
import argparse
from tqdm import tqdm
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pydub import AudioSegment
from nltk.tokenize import sent_tokenize
import nltk
import re
import time

# Add /opt/csm to path to help find generator modules
sys.path.insert(0, '/opt/csm')

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_chapters_from_epub(epub_path):
    """Extract chapters from an EPUB file as a list of (title, text) tuples."""
    print(f"Extracting chapters from {epub_path}...")
    book = epub.read_epub(epub_path)
    chapters = []
    for i, item in enumerate(tqdm(list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)), desc="Processing chapters")):
        content = item.get_content().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        # Try to find a chapter title
        title_tag = soup.find(['h1', 'h2', 'h3', 'h4'])
        title = title_tag.get_text().strip() if title_tag else f"Chapter {i+1}"
        chapter_text = soup.get_text()
        chapter_text = re.sub(r'\s+', ' ', chapter_text).strip()
        # Only add chapters with meaningful content
        if len(chapter_text) > 50:
            chapters.append((title, chapter_text))
    print(f"Extracted {len(chapters)} chapters from EPUB.")
    return chapters

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
    parser = argparse.ArgumentParser(description="Generate per-chapter audio from an EPUB using Sesame CSM")
    parser.add_argument("--epub", required=True, help="Path to the EPUB file")
    parser.add_argument("--output_dir", default="audiobook_chapters_sesame", help="Output directory for chapter audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Extract chapters
    chapters = extract_chapters_from_epub(args.epub)

    # Load CSM model
    print("Loading Sesame CSM model...")
    try:
        try:
            from audiobook_generator import load_csm_1b, Segment
            print("Using enhanced audiobook generator with error handling")
        except ImportError:
            from generator import load_csm_1b, Segment
            print("Using original CSM generator")
        model = load_csm_1b("/models/sesame-csm-1b", device="cuda")
        model = model.half()
    except Exception as e:
        print(f"Error loading CSM model: {e}")
        sys.exit(1)

    # Generate audio for each chapter
    for idx, (title, chapter_text) in enumerate(chapters, 1):
        print(f"Processing chapter {idx}: {title}")
        # Split chapter into chunks
        chunks = preprocess_text(chapter_text, args.chunk_size)
        audio_files = []
        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(args.output_dir, f"chapter_{idx:02d}_chunk_{i:03d}.mp3")
            if os.path.exists(chunk_path):
                print(f"Skipping chunk {i} of chapter {idx} - already processed")
                audio_files.append(chunk_path)
                continue
            success = generate_audio(model, chunk, chunk_path)
            if success:
                audio_files.append(chunk_path)
        # Combine all chunk files for this chapter
        chapter_output = os.path.join(args.output_dir, f"chapter_{idx:02d}_{re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')}.mp3")
        combine_audio_files(audio_files, chapter_output)
        print(f"Chapter {idx} audio saved to {chapter_output}")

    print("Per-chapter audiobook generation complete!")

if __name__ == "__main__":
    main()
