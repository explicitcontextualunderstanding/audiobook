# Audiobook Generation on Jetson Orin Nano

This repository contains scripts and documentation for generating audiobooks on a Jetson Orin Nano using either Piper TTS or Sesame CSM.

## Quick Start

The fastest way to get started is to use the quickstart script:

```bash
# Make the script executable
chmod +x scripts/quickstart.sh

# Run with your book file (ePub recommended)
./scripts/quickstart.sh /path/to/your/book.epub piper  # For Piper TTS (faster)
# or
./scripts/quickstart.sh /path/to/your/book.epub sesame # For Sesame CSM (higher quality)
```

## Available Scripts

- `generate_audiobook_piper.py` - Script for generating audiobooks using Piper TTS
- `generate_audiobook_sesame.py` - Script for generating audiobooks using Sesame CSM
- `quickstart.sh` - Helper script to set up the environment and start the generation process

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
  --output_dir ~/audiobook_data/audiobook_chapters_sesame \
  --voice_preset "calm" \
  --max_batch_size 8 \
  --memory_per_chunk 150
```

## Requirements

- Jetson Orin Nano with JetPack/L4T
- At least 5GB of available RAM
- At least 20GB of free storage space
- Internet connection for downloading models

## License

This project is open source and available under the MIT License.
