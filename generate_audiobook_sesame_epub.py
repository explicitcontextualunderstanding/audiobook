#!/usr/bin/env python3

import os
import torch
import argparse
from tqdm import tqdm
from pathlib import Path
from pydub import AudioSegment
from nltk.tokenize import sent_tokenize
import nltk
import re
import time
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_text_from_epub(epub_path):
    """Extract text from an ePub file."""
    print(f"Extracting text from {epub_path}...")
    
    book = epub.read_epub(epub_path)
    text = ""
    
    for item in tqdm(book.get_items_of_type(ebooklib.ITEM_DOCUMENT), desc="Processing chapters"):
        content = item.get_content()
        soup = BeautifulSoup(content, 'html.parser')
        chapter_text = soup.get_text()
        text += chapter_text + "\n\n"
    
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
    parser = argparse.ArgumentParser(description="Generate an audiobook from an ePub using Sesame CSM")
    parser.add_argument("--epub", required=True, help="Path to the ePub file")
    parser.add_argument("--output", default="audiobook_sesame.mp3", help="Output audiobook file path")
    parser.add_argument("--temp_dir", default="temp_audio_sesame", help="Directory for temporary audio files")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Maximum characters per chunk")
    args = parser.parse_args()
    
    # Create temporary directory
    os.makedirs(args.temp_dir, exist_ok=True)
    
    # Extract and preprocess text
    text = extract_text_from_epub(args.epub)
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
