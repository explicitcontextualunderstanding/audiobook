#!/bin/bash
# Cleanup script to remove temporary files
# Make this executable with: chmod +x cleanup.sh

# Remove .bak files
rm -f .dockerignore.bak
rm -f docker/sesame-tts/Dockerfile.bak
rm -f scripts/fast-build.sh.bak

# Remove other temporary files
rm -f docker/sesame-tts/Dockerfile.test-wheels
rm -f docker/sesame-tts/requirements.fast.txt
rm -f docker/sesame-tts/FAST-BUILD.md
rm -f build-validation.md

echo "Cleanup complete. All temporary files have been removed."
