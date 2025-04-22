#!/usr/bin/env python3
"""
Test script for bitsandbytes on Jetson.

This script verifies that bitsandbytes is properly installed and
functional on Jetson devices.
"""

import os
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_bitsandbytes")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test bitsandbytes on Jetson")
    parser.add_argument("--device", "-d", choices=["cuda", "cpu"], default="cuda",
                        help="Device to use for testing (default: cuda)")
    return parser.parse_args()

def main():
    """Run the bitsandbytes test."""
    args = parse_args()

    try:
        # Import torch first to check CUDA
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        logger.info(f"Using device: {args.device}")

        # Import bitsandbytes
        import bitsandbytes as bnb
        logger.info(f"Bitsandbytes version: {bnb.__version__}")
        logger.info(f"Compiled with CUDA: {bnb.COMPILED_WITH_CUDA}")
        logger.info(f"CUDA compute capabilities: {bnb.COMPILED_WITH_CUDA_COMPUTE_CAPABILITY}")

        # Try to use 8-bit linear layer
        in_features = 1024
        out_features = 1024

        # Create a Linear8bitLt layer
        linear = bnb.nn.Linear8bitLt(in_features, out_features)
        logger.info("Created Linear8bitLt layer")

        # Test with some data
        if args.device == "cuda" and torch.cuda.is_available():
            logger.info("Testing on CUDA...")
            x = torch.randn(1, in_features).cuda()
            linear = linear.cuda()
            y = linear(x)
            logger.info(f"Output shape: {y.shape}")
            logger.info("CUDA forward pass successful")
        else:
            logger.info("Testing on CPU...")
            x = torch.randn(1, in_features)
            y = linear(x)
            logger.info(f"Output shape: {y.shape}")
            logger.info("CPU forward pass successful")

        logger.info("✅ Bitsandbytes test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
