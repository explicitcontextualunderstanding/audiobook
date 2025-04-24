#!/usr/bin/env python3
# Copyright (c) 2024 SesameAI. All rights reserved.

"""
Configuration script for Sesame CSM TTS model for audiobook generation.
This follows the jetson-containers framework architecture.
"""

import os

# Try to import package and requires functions (will be available in the jetson-containers environment)
try:
    from jetson_containers import package, requires
except ImportError:
    # Provide mock implementations for standalone testing
    def package(name, **kwargs):
        kwargs['name'] = name
        return kwargs
        
    def requires(*args, **kwargs):
        return args

# Get environment variables
CUDA_VERSION = os.environ.get('CUDA_VERSION', 'cu128')
L4T_VERSION = os.environ.get('L4T_VERSION', 'r36.4.0')
LSB_RELEASE = os.environ.get('LSB_RELEASE', '24.04')

# Define base package configuration
sesame_tts = package(
    name='sesame-tts',
    license='https://github.com/SesameAILabs/csm',
    depends=[
        'python:3.12',
        'pytorch:2.6',
        'cuda',
        'ffmpeg',
        'torchaudio',
    ],
    requires=[
        '>=cu118',  # Requires at least CUDA 11.8
        'jp6',      # Requires JetPack 6.x
        '==aarch64' # Only for ARM64 architecture
    ],
    build_args={
        'BASE_IMAGE': f'dustynv/pytorch:2.6-{L4T_VERSION}-{CUDA_VERSION}-{LSB_RELEASE}',
    }
)

# Variant with minimum dependencies (for testing)
sesame_tts_minimal = package(
    name='sesame-tts:minimal',
    license='https://github.com/SesameAILabs/csm',
    depends=[
        'python:3.12',
        'pytorch:2.6',
        'cuda'
    ],
    requires=[
        '>=cu118',
        'jp6',
        '==aarch64'
    ],
    build_args={
        'BASE_IMAGE': f'dustynv/pytorch:2.6-{L4T_VERSION}-{CUDA_VERSION}-{LSB_RELEASE}',
        'MINIMAL_BUILD': 'ON'
    }
)

# Default package selection based on environment
DEFAULT_PACKAGE = sesame_tts

# If we're running standalone, print package info
if __name__ == '__main__':
    import json
    print(json.dumps(DEFAULT_PACKAGE, indent=2))
