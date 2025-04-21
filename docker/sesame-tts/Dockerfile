ARG BASE_IMAGE=dustynv/pytorch:2.6-r36.4.0-cu128-24.04

# ============================================================================
# BUILDER STAGE: Install dependencies and prepare the environment
# ============================================================================
FROM ${BASE_IMAGE} AS builder

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# Set up working directory for the build process
WORKDIR /opt/build

# Environment variables for the build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_TORCH_COMPILE=1 \
    DEBIAN_FRONTEND=noninteractive \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    CONDA_DIR=/opt/conda \
    PATH="/root/.cargo/bin:${PATH}" \
    # Performance optimizations
    PYTHONHASHSEED=0 \
    PIP_DEFAULT_TIMEOUT=100 \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1

# Create necessary directories first for better layering
RUN mkdir -p ${MODELS_DIR} ${AUDIOBOOK_DATA} ${BOOKS_DIR} /segments /opt/csm /opt/tritonserver \
    && mkdir -p ~/.config/pip

# Copy build resources with proper .dockerignore handling
COPY docker/sesame-tts/requirements.txt ./requirements.txt
COPY docker/sesame-tts/build.sh ./build.sh
COPY docker/sesame-tts/utils/ ./utils/

# Run the optimized build script
RUN chmod +x build.sh && \
    /bin/bash -c "set -e && ./build.sh"

# Download and install Triton Inference Server as a separate layer
RUN echo "Installing Triton Inference Server..." && \
    wget --quiet https://github.com/triton-inference-server/server/releases/download/v2.55.0/tritonserver2.55.0-igpu.tar \
    -O triton.tar && \
    tar -xf triton.tar -C /opt/tritonserver --strip-components=1 && \
    rm triton.tar

# Set up CSM package (doing this as a separate step for better caching)
RUN echo "Setting up CSM package..." && \
    git clone --depth 1 https://github.com/SesameAILabs/csm.git /tmp/csm && \
    cp /tmp/csm/generator.py /opt/csm/ && \
    cp /tmp/csm/models.py /opt/csm/ && \
    cp ./utils/audiobook_generator.py /opt/csm/ && \
    cp ./utils/watermarking.py /opt/csm/ && \
    chmod +x /opt/csm/watermarking.py && \
    rm -rf /tmp/csm

# Install Python Triton package for torchao kernels (separated for better caching)
RUN echo "Installing Triton for torchao..." && \
    /opt/conda/bin/conda run -n tts pip install --no-cache-dir \
    --index-url https://pypi.jetson-ai-lab.dev/simple \
    --extra-index-url https://pypi.org/simple \
    triton
    
# Final cleanup to reduce image size
RUN echo "Final cleanup..." && \
    find /opt/conda -name "*.a" -delete && \
    find /opt/conda -name "*.js.map" -delete && \
    rm -rf /opt/conda/pkgs && \
    rm -rf /root/.cache /tmp/* /var/tmp/*

# ============================================================================
# RUNTIME STAGE: Create the minimal runtime image
# ============================================================================
FROM ${BASE_IMAGE} AS runtime

# Add container metadata
LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

# Copy only what's needed from the builder stage
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /opt/csm /opt/csm
COPY --from=builder /opt/tritonserver /opt/tritonserver
COPY --from=builder /opt/build/utils /opt/utils
COPY --from=builder /models /models
COPY --from=builder /audiobook_data /audiobook_data
COPY --from=builder /books /books
COPY --from=builder /segments /segments

# Runtime environment variables
ENV PATH="/opt/tritonserver/bin:/opt/conda/bin:${PATH}" \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    CUDA_MODULE_LOADING=LAZY \
    TORCH_USE_CUDA_DSA=1

# Copy entrypoint and utility scripts
COPY docker/sesame-tts/entrypoint.sh /entrypoint.sh
COPY docker/sesame-tts/utils/force_cuda_test.sh /usr/local/bin/force_cuda_test.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/force_cuda_test.sh

# Add CSM to Python path
RUN echo 'import sys; sys.path.append("/opt/csm")' \
    > $(python3 -c 'import site; print(site.getsitepackages()[0])')/csm_path.pth

# Set working directory
WORKDIR /workspace

# Health check with all critical imports
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD /opt/conda/bin/conda run -n tts python -c "import torch, moshi, torchao, os; print(f'Health check passed. CUDA available: {torch.cuda.is_available()}'); exit(0 if torch.cuda.is_available() else 1)" || exit 1

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["/opt/conda/bin/conda", "run", "-n", "tts", "--no-capture-output", "bash"]
