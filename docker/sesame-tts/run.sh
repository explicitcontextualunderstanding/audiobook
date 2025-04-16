#!/bin/bash

# Activate conda environment
source /opt/conda/bin/activate tts

# If entrypoint.sh exists, use it
if [ -f /usr/local/bin/entrypoint.sh ]; then
    echo "Starting Sesame TTS service via entrypoint script..."
    exec /usr/local/bin/entrypoint.sh "$@"
else
    echo "Welcome to Sesame TTS container!"
    echo ""
    echo "Available commands:"
    echo "  - Generate audiobook from text file:"
    echo "    python ${BOOKS_DIR}/generate_audiobook_sesame.py /path/to/input.txt /path/to/output.wav"
    echo ""
    echo "  - Generate audiobook from EPUB:"
    echo "    python ${BOOKS_DIR}/generate_audiobook_sesame_epub.py /path/to/book.epub /path/to/output.wav"
    echo ""
    echo "  - Extract chapters:"
    echo "    python ${BOOKS_DIR}/extract_chapters.py /path/to/book.epub"
    echo ""
    echo "  - Test CSM TTS:"
    echo "    python /usr/local/bin/utils/test_csm.py"
    echo ""
    
    # Launch interactive bash shell with conda environment activated
    exec bash
fi
