ARG BASE_IMAGE=dustynv/pytorch:2.6-r36.4.0-cu128-24.04
FROM ${BASE_IMAGE} AS builder

LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

WORKDIR /opt/build
COPY docker/sesame-tts/requirements.txt ./requirements.txt
COPY docker/sesame-tts/build.sh ./build.sh
COPY docker/sesame-tts/utils/ ./utils/

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
    PATH="/root/.cargo/bin:${PATH}"

RUN chmod +x build.sh && ./build.sh && \
    wget https://github.com/triton-inference-server/server/releases/download/v2.55.0/tritonserver2.55.0-igpu.tar \
      -O triton.tar && \
    mkdir -p /opt/tritonserver && \
    tar -xvf triton.tar -C /opt/tritonserver --strip-components=1 && rm triton.tar

FROM ${BASE_IMAGE} AS runtime

LABEL org.opencontainers.image.description="Sesame CSM text-to-speech for Jetson"
LABEL org.opencontainers.image.source="https://github.com/SesameAILabs/csm"
LABEL com.nvidia.jetpack.version="6.1"
LABEL com.nvidia.cuda.version="12.8"

COPY --from=builder /opt/conda        /opt/conda
COPY --from=builder /opt/tritonserver /opt/tritonserver
COPY --from=builder /opt/build/utils  /opt/utils

ENV PATH="/opt/tritonserver/bin:/opt/conda/bin:${PATH}" \
    MODELS_DIR=/models \
    AUDIOBOOK_DATA=/audiobook_data \
    BOOKS_DIR=/books \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all

COPY docker/sesame-tts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /workspace

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD /opt/conda/bin/conda run -n tts python -c "import torch, moshi, torchao" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/opt/conda/bin/conda", "run", "-n", "tts", "--no-capture-output", "bash"]