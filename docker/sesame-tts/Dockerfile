ARG BASE_IMAGE=dustynv/pytorch:2.6-r36.4.0-cu128-24.04

FROM ${BASE_IMAGE}

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# Set up working directory for the build process
WORKDIR /opt/build

# Copy build resources
COPY docker/sesame-tts/requirements.txt ./
COPY docker/sesame-tts/build.sh ./
COPY docker/sesame-tts/utils/ ./utils/

# Make build script executable and run it
RUN chmod +x ./build.sh && /bin/bash -c "set -e && ./build.sh"

# Add final workdir, health check and default command
WORKDIR /workspace

# Health check - runs inside the container to verify it's functioning properly
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD conda run -n tts python -c "import torch, moshi, torchao; print('Health check passed.')" || exit 1

# Default command - uses conda environment
CMD ["conda", "run", "-n", "tts", "--no-capture-output", "bash"]