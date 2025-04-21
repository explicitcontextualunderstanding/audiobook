#!/usr/bin/env bash
# Default run script for sesame-tts container
set -e

# Check if we have an argument
if [ "$#" -gt 0 ]; then
    # If we have arguments, run them directly
    exec "$@"
else
    # Default behavior: launch an interactive environment
    echo "=== Sesame TTS Container ==="
    echo "TTS model is available in the Python environment."
    echo "You can load it with:"
    echo ""
    echo "  import sys"
    echo "  sys.path.append('/opt/csm')"
    echo "  from generator import load_csm_1b, Generator"
    echo ""
    echo "Starting interactive shell..."
    echo "================================"
    exec /bin/bash
fi
