# Audiobook Generation on Jetson Orin Nano

This repository contains scripts and documentation for generating audiobooks on a Jetson Orin Nano using either Piper TTS or Sesame CSM.

## Quick Start

The fastest way to get started is to use the quickstart script:

```bash
# Make the script executable
chmod +x quickstart.sh

# Run with an EPUB or PDF file
./quickstart.sh --input /path/to/your/book.epub --method piper  # For Piper TTS (faster)
# or
./quickstart.sh --input /path/to/your/book.epub --method sesame # For Sesame CSM (higher quality)
```

## Usage Options

```
Usage: ./quickstart.sh [options]

Required options:
  --input FILE               Path to input book file (EPUB or PDF)

Optional options:
  --method METHOD            TTS method to use: 'piper' (faster) or 'sesame' (higher quality)
                             Default: piper
  --voice VOICE              Voice preset to use
                             For piper: lessac (default), ryan, jenny, kathleen, alan
                             For sesame: calm (default), excited, authoritative, gentle, narrative
  --chapter-range RANGE      Range of chapters to process (e.g., '1-5')
  --memory-per-chunk SIZE    Memory usage per chunk in MB
  --max-batch-size SIZE      Maximum batch size for processing
  --output-format FORMAT     Output format: mp3 (default), wav, flac
  --help                     Show this help message
```

## Available Scripts

- `build_container.sh` – Build the Docker container image for Sesame TTS.
- `quickstart.sh` – Helper script to set up the environment and start generation.
- `generate_audiobook_piper.py` – Script for generating audiobooks using Piper TTS
- `generate_audiobook_sesame.py` – Script for generating audiobooks using Sesame CSM
- `extract_chapters.py` - Utility script to extract chapters from EPUB/PDF files

## Comprehensive Documentation

For complete instructions, options, and troubleshooting, see the full documentation:

- [Comprehensive Audiobook Generation Plan](audiobook-plan.md)

## Features

- Support for both ePub and PDF formats (ePub recommended)
- Chapter detection and organization
- Progress reporting with time estimates
- Memory usage optimization
- Resume capability for interrupted processes
- Voice model selection
- Process specific chapter ranges
- Batch processing to manage memory usage
- Automatic voice preset discovery

## Example Usage

### Piper TTS (in jetson-containers)

```bash
python generate_audiobook_piper.py \
  --input /books/your_book.epub \
  --output /audiobook_data/audiobook_piper.mp3 \
  --model /opt/piper/voices/en/en_US-lessac-medium.onnx \
  --temp_dir /audiobook_data/temp_audio_piper \
  --max_batch_size 15 \
  --memory_per_chunk 50
```

### Sesame CSM

```bash
python generate_audiobook_sesame.py \
  --input ~/audiobook/your_book.epub \
  --output ~/audiobook_data/audiobook_sesame.mp3 \
  --model_path ~/huggingface_models/sesame-csm-1b \
  --voice_preset "calm" \
  --max_batch_size 8 \
  --memory_per_chunk 150 \
  --chapter_range "1-5"
```

## Requirements

- Jetson Orin Nano with JetPack/L4T
- At least 5GB of available RAM
- At least 20GB of free storage space
- Internet connection for downloading models
- Docker installed for container-based execution

## License

This project is open source and available under the MIT License.
