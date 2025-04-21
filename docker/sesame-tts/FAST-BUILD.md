# Fast Build for Sesame TTS Container

This directory contains optimized files for faster Docker builds of the Sesame TTS container.

## Fast Build Files

- `Dockerfile.fast` - Optimized Dockerfile with multi-stage builds and better caching
- `requirements.fast.txt` - Reorganized requirements for better layer caching
- `.dockerignore.fast` - Comprehensive ignore file to reduce build context size
- `fast-build.sh` - BuildKit-enabled build script with progress indicators

## How to Use

### Basic Usage

```bash
# Make the script executable (first time only)
chmod +x scripts/fast-build.sh

# Run a fast build
./scripts/fast-build.sh
```

### Advanced Usage

```bash
# Build with verbose output
./scripts/fast-build.sh --verbose

# Force a clean build with no cache
./scripts/fast-build.sh --no-cache

# Specify a custom tag for the image
./scripts/fast-build.sh --tag=my-custom-tag

# Use a previous build as cache source
./scripts/fast-build.sh --cache-from=sesame-tts-jetson:fast
```

## Optimization Details

1. **BuildKit Integration**
   - Parallel downloading and building
   - Enhanced caching

2. **Multi-stage Build**
   - `dependencies` stage for installing Python packages
   - `builder` stage for configuration and setup
   - `runtime` stage for the final image

3. **Layer Optimization**
   - Frequently changing files are copied last
   - Dependencies are installed in logical groups

4. **Reduced Image Size**
   - Only necessary files are copied to the runtime image
   - Cleanup of build artifacts and cache

## Troubleshooting

Build logs are saved to `build-logs/` directory with timestamps.

If you encounter issues:
1. Check the logs for specific error messages
2. Try running with `--verbose` for more detailed output
3. Use `--no-cache` to start a fresh build if caching is causing problems
