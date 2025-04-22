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
