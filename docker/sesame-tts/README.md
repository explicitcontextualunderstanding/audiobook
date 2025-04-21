# Sesame TTS Container for Jetson

This container provides the Sesame CSM text-to-speech model optimized for audiobook generation on Jetson platforms.

## Overview

The container is built on top of the `dustynv/pytorch` image and adds:

- Sesame CSM 1B text-to-speech model
- Audiobook generation utilities
- Triton Inference Server for optimized inference
- CUDA-accelerated audio processing

## Usage

Detailed usage instructions are available in [docs.md](./docs.md).

### Quick Start

```bash
# Build the container
./jetson-containers build sesame-tts

# Run with interactive shell
./jetson-containers run sesame-tts

# Mount volumes for books and output
./jetson-containers run \
  -v /path/to/your/books:/books \
  -v /path/to/output:/audiobook_data \
  sesame-tts
```

## Hardware Requirements

- NVIDIA Jetson device with JetPack 6.0+
- Recommended: at least 8GB RAM
- Recommended: NVMe storage for model files and audio output
- CUDA 11.8 or higher

## Project Context

This container is part of a larger audiobook generation project. For the comprehensive project overview, including both Piper TTS and Sesame CSM approaches, see the [Audiobook Project Plan](../../audiobook-plan.md) in the root directory.
