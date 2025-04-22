# Sesame TTS Docker Container for Jetson

This directory contains the Docker build files for Sesame CSM text-to-speech optimized for Jetson devices.

## Optimized Dependency Management

The Docker build process has been optimized to use Jetson-specific wheels from the Jetson PyPI index, ensuring better compatibility and performance on Jetson hardware.

### Key Features

- **Jetson-Optimized Packages**: Uses packages from `pypi.jetson-ai-lab.dev` that are pre-built for ARM64 architecture
- **Dependency Locking**: Generates a deterministic lock file for reproducible builds
- **Multi-Stage Build**: Optimizes Docker layer caching and reduces final image size
- **BuildKit Integration**: Uses advanced Docker BuildKit features for faster builds
- **Dependency Documentation**: Generates comprehensive dependency information for debugging

## Building the Container

To build the container, run:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with detailed output
docker build -t sesame-tts-jetson --progress=plain -f docker/sesame-tts/Dockerfile .
```

Or use the provided build script:

```bash
# Make the script executable if needed
chmod +x scripts/dependency/build.sh

# Build with verbose output
./scripts/dependency/build.sh --verbose
```

## Running the Container

```bash
docker run --runtime nvidia -it --rm \
  --name sesame-tts \
  --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --volume ~/huggingface_models/sesame-csm-1b:/models/sesame-csm-1b \
  --volume ${HOME}/.cache/huggingface:/root/.cache/huggingface \
  --workdir /audiobook_data \
  sesame-tts-jetson
```

## Key Dependency Changes

The container now uses Jetson-optimized versions of key packages:

| Package | Previous Version | Current Version |
|---------|-----------------|-----------------|
| torch | 2.2.0 | 2.7.0+ |
| torchvision | 0.17.0 | 0.22.0+ |
| torchaudio | 2.2.0 | 2.7.0+ |
| torchao | 0.1.0 | 0.11.0+ |
| triton | 2.1.0 | 3.3.0+ |
| vector_quantize_pytorch | 1.8.6 | 1.22.15+ |
| einops | 0.7.0 | 0.8.0+ |

## Troubleshooting

If you encounter build issues:

1. **Check Docker BuildKit**: Ensure BuildKit is enabled with `export DOCKER_BUILDKIT=1`

2. **Check Network Access**: Ensure your system can access the Jetson PyPI index at `https://pypi.jetson-ai-lab.dev/simple`

3. **View Dependency Documentation**: After building, you can check `/opt/dependency_docs` inside the container to see the complete dependency tree:
   ```bash
   docker run --rm -it sesame-tts-jetson cat /opt/dependency_docs/frozen_deps.txt
   ```

4. **Build Information**: Check the build info file:
   ```bash
   docker run --rm -it sesame-tts-jetson cat /opt/build_info.txt
   ```

5. **Build with More Verbose Output**:
   ```bash
   BUILDKIT_PROGRESS=plain docker build -t sesame-tts-jetson --progress=plain -f docker/sesame-tts/Dockerfile .
   ```

## License

This project is open source and available under the MIT License.
