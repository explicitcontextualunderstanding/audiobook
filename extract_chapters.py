#!/usr/bin/env python3

import os
import re
import argparse
from PyPDF2 import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_chapters_from_pdf(pdf_path):
    """Extract potential chapter titles from a PDF file."""
    print(f"Extracting chapter information from {pdf_path}...")
    
    reader = PdfReader(pdf_path)
    chapters = []
    
    # Try to extract from outlines/bookmarks
    if hasattr(reader, 'outline') and reader.outline:
        print("Found PDF outlines/bookmarks")
        # Process the outline entries
        def process_outline(outline, level=0):
            if isinstance(outline, list):
                for item in outline:
                    process_outline(item, level)
            elif isinstance(outline, dict):
                title = outline.get('/Title', '')
                if title:
                    page_num = reader.get_destination_page_number(outline)
                    chapters.append((title, page_num))
                if '/Kids' in outline:
                    process_outline(outline['/Kids'], level + 1)
        
        process_outline(reader.outline)
    else:
        # No outlines, try to detect chapters from text
        print("No PDF outlines found, detecting chapters from text...")
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Check for lines that look like chapter headings
            for line in lines:
                line = line.strip()
                # Look for chapter patterns, e.g., "Chapter 1: Introduction"
                if re.match(r'^(Chapter|Section)\s+\d+', line, re.IGNORECASE):
                    chapters.append((line, i))
    
    return chapters

def extract_chapters_from_epub(epub_path):
    """Extract chapter titles and positions from an EPUB file."""
    print(f"Extracting chapter information from {epub_path}...")
    
    book = epub.read_epub(epub_path)
    chapters = []
    
    # Get the table of contents
    toc = book.toc
    
    # If TOC is available, use it
    if toc:
        print("Using EPUB table of contents")
        
        def process_toc(toc_items, level=0):
            for item in toc_items:
                if isinstance(item, tuple):
                    title, href = item[0], item[1]
                    # Extract position from href if possible
                    chapters.append((title, href))
                elif isinstance(item, list):
                    process_toc(item, level + 1)
        
        process_toc(toc)
    else:
        # No TOC, try to detect chapters from content
        print("No TOC found, detecting chapters from content...")
        
        # Process each document item in the EPUB
        estimated_position = 0
        for i, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
            content = item.get_content().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for headings
            headings = soup.find_all(['h1', 'h2', 'h3'])
            for heading in headings:
                if heading.get_text().strip():
                    # Use a position estimate based on document order and position within document
                    chapters.append((heading.get_text().strip(), f"position_{estimated_position}"))
                    estimated_position += 1
    
    return chapters

def generate_chapter_markers(chapters, duration, output_file):
    """Generate chapter markers file for ffmpeg."""
    print(f"Generating chapter markers for {len(chapters)} chapters...")
    
    # Calculate approximate time for each chapter (very simple approach)
    time_per_position = duration / (max(1, len(chapters)))
    
    with open(output_file, 'w') as f:
        f.write(";FFMETADATA1\n")
        
        for i, (title, position) in enumerate(chapters):
            # For PDF
            if isinstance(position, int):
                start_time = int(position * time_per_position * 1000)  # ms
            # For EPUB
            else:
                # Extract position number or use index
                if isinstance(position, str) and position.startswith("position_"):
                    pos_num = int(position.split("_")[1])
                else:
                    pos_num = i
                start_time = int(pos_num * time_per_position * 1000)  # ms
            
            # Calculate end time (next chapter's start or end of audio)
            if i < len(chapters) - 1:
                end_time = int(start_time + time_per_position * 1000)
            else:
                end_time = int(duration * 1000)  # ms
            
            # Convert to seconds
            start_sec = start_time / 1000
            end_sec = end_time / 1000
            
            # Format as HH:MM:SS
            start_formatted = f"{int(start_sec // 3600):02d}:{int((start_sec % 3600) // 60):02d}:{int(start_sec % 60):02d}"
            end_formatted = f"{int(end_sec // 3600):02d}:{int((end_sec % 3600) // 60):02d}:{int(end_sec % 60):02d}"
            
            f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={start_time}\nEND={end_time}\ntitle={title}\n\n")
    
    print(f"Chapter markers written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Extract chapter information from a book file")
    parser.add_argument("--file", required=True, help="Path to the PDF or EPUB file")
    parser.add_argument("--output", default="chapters.txt", help="Output chapter metadata file")
    parser.add_argument("--duration", type=float, default=3600, help="Duration of the audiobook in seconds")
    parser.add_argument("--format", choices=["pdf", "epub", "auto"], default="auto", 
                         help="Format of the input file (pdf, epub, or auto-detect)")
    args = parser.parse_args()
    
    file_path = args.file
    file_format = args.format
    
    # Auto-detect format if not specified
    if file_format == "auto":
        if file_path.lower().endswith(".pdf"):
            file_format = "pdf"
        elif file_path.lower().endswith((".epub", ".epb")):
            file_format = "epub"
        else:
            print("Could not determine file format. Please specify with --format.")
            return
    
    # Extract chapters based on format
    if file_format == "pdf":
        chapters = extract_chapters_from_pdf(file_path)
    else:  # epub
        chapters = extract_chapters_from_epub(file_path)
    
    if not chapters:
        print("No chapters found in the file")
        return
    
    print(f"Found {len(chapters)} chapters:")
    for i, (title, position) in enumerate(chapters):
        print(f"{i+1}. {title} (Position: {position})")
    
    # Generate chapter markers file
    generate_chapter_markers(chapters, args.duration, args.output)

if __name__ == "__main__":
    main()
