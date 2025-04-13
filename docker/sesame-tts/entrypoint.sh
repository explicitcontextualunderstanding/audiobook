#!/bin/bash

echo "=================================================="
echo "Sesame CSM Audiobook Generator for Jetson"
echo "=================================================="
echo ""
echo "Available commands:"
echo ""
echo "  • Test CSM installation:"
echo "    python /usr/local/bin/utils/test_csm.py /models/sesame-csm-1b"
echo ""
echo "  • Generate audiobook:"
echo "    python /books/generate_audiobook_sesame.py \
      --input /books/your_book.epub \
      --output /audiobook_data/audiobook.mp3 \
      --model_path /models/sesame-csm-1b"
echo ""
echo "Volume mounts:"
echo "  • /models/sesame-csm-1b: Model files"
echo "  • /books: Source books"
echo "  • /audiobook_data: Output directory"
echo ""
echo "=================================================="

exec "$@"