#!/bin/bash
set -e

echo "====================================================="
echo "Sesame CSM Text-to-Speech for Audiobook Generation"
echo "====================================================="
echo ""
echo "This container provides Sesame CSM Text-to-Speech capabilities"
echo "specifically configured for audiobook generation on Jetson devices."
echo ""
echo "Environment paths:"
echo "  - Books directory: $BOOKS_DIR"
echo "  - Audiobook data directory: $AUDIOBOOK_DATA"
echo "  - Models directory: $MODELS_DIR"
echo ""
echo "Available scripts:"
echo "  - $BOOKS_DIR/generate_audiobook_sesame.py - Main script for both EPUB and PDF"
echo "  - $BOOKS_DIR/generate_audiobook_sesame_epub.py - Optimized for EPUB format"
echo "  - $BOOKS_DIR/extract_chapters.py - Extract chapter information"
echo ""
echo "Example usage:"
echo "  conda run -n tts python $BOOKS_DIR/generate_audiobook_sesame.py \\"
echo "    --input $BOOKS_DIR/your_book.epub \\"
echo "    --output $AUDIOBOOK_DATA/audiobook_sesame.mp3 \\"
echo "    --model_path $MODELS_DIR/sesame-csm-1b \\"
echo "    --voice_preset calm"
echo ""
echo "Test the CSM installation by running:"
echo "  conda run -n tts python /usr/local/bin/utils/test_csm.py $MODELS_DIR/sesame-csm-1b"
echo ""
echo "Note: Remember to use 'conda run -n tts' before any Python commands"
echo "to ensure they run within the conda environment."
echo ""
echo "====================================================="

# Activate the conda environment for interactive sessions
source ~/.bashrc

# Execute the command
if [ "$#" -eq 0 ]; then
    # If no command was provided, start an interactive shell
    /bin/bash
else
    # Otherwise, execute the provided command
    exec "$@"
fi