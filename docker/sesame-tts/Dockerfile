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
COPY docker/sesame-tts/utils/ /opt/utils/
COPY docker/sesame-tts/entrypoint.sh ./

# Make scripts executable and run build
RUN chmod +x ./build.sh ./entrypoint.sh && /bin/bash -c "set -e && ./build.sh"

# Add final workdir, health check and default command
WORKDIR /workspace

# Copy entrypoint script to final location
COPY docker/sesame-tts/entrypoint.sh /entrypoint.sh
COPY docker/sesame-tts/utils/force_cuda_test.sh /usr/local/bin/force_cuda_test.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/force_cuda_test.sh

# Health check - runs inside the container to verify it's functioning properly
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD /opt/conda/bin/conda run -n tts python -c "import torch, moshi, torchao; print('Health check passed.')" || exit 1

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command - uses conda environment with full path
CMD ["/opt/conda/bin/conda", "run", "-n", "tts", "--no-capture-output", "bash"]

# Install Triton Inference Server for JetPack 6.2/Orin
RUN wget https://github.com/triton-inference-server/server/releases/download/v2.55.0/tritonserver2.55.0-igpu.tar.gz \
      -O tritonserver2.55.0-igpu.tar.gz && \
    mkdir -p /opt/tritonserver && \
    tar -xzf tritonserver2.55.0-igpu.tar.gz -C /opt/tritonserver --strip-components=1 && \
    rm tritonserver2.55.0-igpu.tar.gz

ENV PATH="/opt/tritonserver/bin:${PATH}"

# Shallow‑clone Sesame CSM repo, copy only the two utils, then drop the git data
RUN rm -rf /opt/utils/csm && \
    git clone --depth 1 https://github.com/SesameAILabs/csm.git /opt/utils/csm && \
    cp /opt/utils/csm/generator.py /opt/utils/ && \
    cp /opt/utils/csm/models.py    /opt/utils/ && \
    rm -rf /opt/utils/csm/.git

# Install Python Triton package so torchao kernels are available
RUN /opt/conda/bin/conda run -n tts pip install triton