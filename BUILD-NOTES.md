# Build System for Audiobook TTS

This document explains the optimized build system used in this project to reduce Docker build times for the TTS containers.

## Overview

The build system has been optimized to address the long build times previously experienced. It uses several techniques:

1. **BuildKit and Caching**: Utilizing Docker BuildKit for parallel operations and better caching
2. **Multi-stage Builds**: Separating dependencies, build, and runtime stages
3. **Layer Optimization**: Strategic ordering of commands to maximize cache hits
4. **Dependency Management**: Intelligent grouping of dependencies for better caching

## Components

### Dockerfile

The Dockerfile (`docker/sesame-tts/Dockerfile`) has been optimized with:

- **Three-stage build**:
  - `dependencies` stage: Installs all Python packages
  - `builder` stage: Sets up the environment and configuration
  - `runtime` stage: Creates the minimal final image

- **Strategic layering**:
  - Infrequently changing operations first
  - Library/framework installations before application code
  - Separate layers for specialized dependencies

### Requirements File

The requirements.txt file has been reorganized:

- PyTorch stack is commented out and installed separately in the Dockerfile
- Dependencies are grouped by purpose
- Specialized packages with potential compilation needs are handled separately

### .dockerignore

The .dockerignore file provides comprehensive exclusions to reduce the build context size, leading to faster builds.

### Build Script

The `build.sh` script provides a user-friendly way to build the container with:

- BuildKit enabled by default
- Progress indicators during builds
- Cache utilization options
- Build timing and logging

## Usage

```bash
# Make the script executable (first time only)
chmod +x build.sh

# Basic build
./build.sh

# Build with detailed output
./build.sh --verbose

# Force a clean build (ignoring cache)
./build.sh --no-cache

# Use a previous build as cache source
./build.sh --cache-from=sesame-tts-jetson:latest

# Specify a custom tag for the image
./build.sh --tag=my-custom-tag
```

## Performance Notes

For best performance:

1. **Initial Build**: The first build will still take time to download and install all dependencies

2. **Subsequent Builds**: Will be significantly faster when using the `--cache-from` option

3. **Dependency Changes**: If you modify requirements.txt, the cache will be partially invalidated

4. **Code Changes**: Changes to application code will only trigger rebuilds of the affected layers

## Troubleshooting

Build logs are saved to the `build-logs/` directory with timestamps. If you encounter issues:

1. Check the logs for specific error messages
2. Try running with `--verbose` for more detailed output
3. Use `--no-cache` to start a fresh build if caching is causing problems

## Background

This build system was implemented to address the issue of long build times for the Sesame CSM container. The key improvements are:

1. **Eliminated redundant work**: Using multi-stage builds to avoid repeating steps
2. **Improved caching**: Better layer organization to maximize cache usage
3. **Reduced context size**: Comprehensive .dockerignore to speed up initial transfer
4. **Parallel processing**: BuildKit enables concurrent operations where possible
