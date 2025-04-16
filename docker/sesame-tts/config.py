#!/usr/bin/env python3
from jetson_containers import L4T_VERSION, CUDA_VERSION, package

# Define the package with configuration and build arguments
sesame_tts = package(
    name='sesame-tts',
    category='audio',
    license='MIT',
    requires=[
        '>=jp6.1',  # Requires Jetpack 6.1 or newer
        '==aarch64'  # Only for ARM64 architecture
    ],
    depends=[
        'python',
        'pytorch'
    ],
    arch=['aarch64'],
    description='Sesame CSM text-to-speech for Jetson',
    
    # Build arguments passed to Dockerfile
    build_args={
        'PYTORCH_IMAGE': 'dustynv/pytorch:2.6-r36.4.0-cu128-24.04',
        'JETPACK_VERSION': '6.1',
        'CUDA_VERSION': '12.8',
    },
    
    # These paths are automatically used by the framework
    test_script='test.sh',
    run_script='run.sh',
    docs='docs.md',
)

# Set as default package for this directory
package = sesame_tts
