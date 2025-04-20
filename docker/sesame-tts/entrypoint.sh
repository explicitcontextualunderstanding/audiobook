#!/usr/bin/env bash
set -euo pipefail

# Delegate to conda-run inside the tts environment
exec /opt/conda/bin/conda run -n tts --no-capture-output "$@"