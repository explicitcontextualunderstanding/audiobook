# Sesame TTS

A high-quality text-to-speech (TTS) container for NVIDIA Jetson platforms using the Sesame Conditional Speech Model (CSM).

## Overview

This package provides a TTS system based on Sesame AI Labs' CSM model, optimized for Jetson platforms running JetPack 6.1 or newer. It includes tools for generating audiobooks from text files and EPUB documents.

## Key Features

- High-quality neural text-to-speech synthesis
- Support for processing EPUB books
- Audio watermarking capabilities
- Complete audiobook pipeline with chapter extraction

## Model Information

This container requires the CSM-1B model to be downloaded separately. The model will be automatically loaded from the `/models/csm-1b-v1.0` directory if available.

## Usage

### Basic TTS Test

To test that the TTS system is working:

```bash
python /usr/local/bin/utils/test_csm.py
```

This will generate a short audio sample using the CSM model.

### Generating Audiobooks

Generate an audiobook from a text file:

```bash
python /books/generate_audiobook_sesame.py /path/to/input.txt /path/to/output.wav
```

Generate an audiobook from an EPUB file:

```bash
python /books/generate_audiobook_sesame_epub.py /path/to/book.epub /path/to/output.wav
```

Extract chapters from an EPUB book:

```bash
python /books/extract_chapters.py /path/to/book.epub
```

### Volume Mounting

When running the container, you'll typically want to mount three directories:

- `/models` - For storing the CSM model files
- `/books` - For input books (text/EPUB)
- `/audiobook_data` - For output audio files

Example:

```bash
jetson-containers run \
  --volume /path/to/models:/models \
  --volume /path/to/books:/books \
  --volume /path/to/output:/audiobook_data \
  sesame-tts
```

## Resource Considerations

- **Memory Usage**: The CSM model requires at least 4GB of RAM to run efficiently
- **Storage**: Ensure sufficient space for model files (~1GB) and generated audio
- **Processing Speed**: TTS generation can be relatively slow on Jetson devices; expect around 3-5x realtime for audio generation

## Troubleshooting

### Common Issues

1. **Model Not Found**: Ensure the CSM model is downloaded and placed in `/models/csm-1b-v1.0`
2. **CUDA Out of Memory**: Try reducing batch sizes or processing smaller text chunks
3. **Audio Quality Issues**: Check your input text formatting; poor punctuation can affect speech quality

### Log Location

Log files are written to `/audiobook_data/logs/` when generating audio.

## Further Reading

- [Sesame AI Labs CSM Repository](https://github.com/SesameAILabs/csm)
- [NVIDIA Jetson Documentation](https://docs.nvidia.com/jetson/)
