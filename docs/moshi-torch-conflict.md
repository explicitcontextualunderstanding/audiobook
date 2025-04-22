# Resolving the Moshi vs. PyTorch 2.7 Conflict

## The Problem

The Sesame CSM (Conditional Speech Model) has a dependency on `moshi==0.2.2`, which requires `torch<2.7`. However, the latest Jetson-optimized PyTorch wheels available on the PyPI index (`pypi.jetson-ai-lab.dev`) are for PyTorch 2.7.0.

This creates a dependency conflict where you must choose between:

1. Using the latest Jetson-optimized PyTorch 2.7.0 wheels (better performance) but losing `moshi` functionality
2. Using older PyTorch versions compatible with `moshi` but potentially missing optimizations for Jetson

## Option 1: Use PyTorch 2.7.0 Without Moshi (Recommended for Performance)

This approach prioritizes using the Jetson-optimized PyTorch wheels for best performance, but will require modifying the CSM code to work without `moshi`.

1. In `requirements.in`, uncomment the PyTorch 2.7.0 section and keep `moshi` commented out
2. Run the patching script to modify the CSM code:
   ```bash
   python scripts/patch_csm_for_torch2.7.py /path/to/cloned/csm
   ```
3. Rebuild the Docker container

Note that this approach may break some functionality in CSM that depends on `moshi`. The patching script attempts to comment out `moshi` imports but may not handle all cases perfectly.

## Option 2: Use Older PyTorch Compatible with Moshi

This approach prioritizes keeping the original CSM code intact but may result in slower performance:

1. In `requirements.in`, comment out the PyTorch 2.7.0 section and uncomment the PyTorch 2.2.0 section with `moshi`
2. Rebuild the Docker container

This approach will likely require PyTorch to be built from source or downloaded from a different source, as the Jetson-optimized repository primarily focuses on the latest version (2.7.0).

## Understanding the Impact

The `moshi` package appears to be used by CSM for model serialization. Without it, features related to model saving, loading specific weights, or certain model transformations might be affected.

For generating an audiobook, the core text-to-speech functionality may still work without `moshi`, especially if you're just performing inference with pre-trained models rather than fine-tuning or modifying models.

## Long-term Solutions

1. **Wait for updates**: The `moshi` package might eventually be updated to support PyTorch 2.7+
2. **Fork and patch**: Create a forked version of `moshi` with updated PyTorch compatibility
3. **Alternative workflows**: Explore using PyTorch 2.7 and alternative serialization methods to replace `moshi`
