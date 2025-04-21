# Audiobook Generation Project Documentation

This repository contains tools and containers for generating audiobooks from ePub and PDF files using different TTS engines on Jetson platforms.

## Core Documentation

- [**Audiobook Project Plan**](./audiobook-plan.md) - Comprehensive overview of the entire audiobook generation system
- [**Quickstart Guide**](./quickstart.sh) - Script for quickly generating audiobooks

## Container Documentation

### Sesame CSM TTS

- [**Sesame TTS Container Overview**](./docker/sesame-tts/README.md) - Basic information about the Sesame TTS container
- [**Sesame TTS Usage Documentation**](./docker/sesame-tts/docs.md) - Detailed usage instructions for the Sesame TTS container

### Piper TTS

- Uses jetson-containers framework's piper-tts container
- See the [Audiobook Project Plan](./audiobook-plan.md) for usage instructions

## Scripts

- [**generate_audiobook_sesame.py**](./generate_audiobook_sesame.py) - Script for generating audiobooks using Sesame CSM
- [**generate_audiobook_piper.py**](./generate_audiobook_piper.py) - Script for generating audiobooks using Piper TTS

## File Organization

```
audiobook/
├── audiobook-plan.md           # Comprehensive project plan
├── quickstart.sh               # Quick start script for audiobook generation
├── generate_audiobook_piper.py # Script for Piper TTS audiobook generation
├── generate_audiobook_sesame.py # Script for Sesame CSM audiobook generation
├── docker/
│   └── sesame-tts/             # Sesame TTS container files
│       ├── README.md           # Container overview
│       ├── docs.md             # Detailed usage instructions
│       ├── Dockerfile          # Container definition
│       ├── build.sh            # Build script
│       ├── pkg_install.sh      # Package installation script
│       ├── run.sh              # Container runtime script
│       ├── test.sh             # Test script
│       └── config.py           # jetson-containers configuration
```
