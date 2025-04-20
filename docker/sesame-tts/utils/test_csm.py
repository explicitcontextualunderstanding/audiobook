#!/usr/bin/env python3
"""
Test script for the CSM text-to-speech system.

This script loads the CSM model and generates a test audio sample
to verify that the installation is working correctly.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_csm")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test CSM text-to-speech system")
    parser.add_argument("model_path", nargs="?", default="/models/sesame-csm-1b",
                        help="Path to the CSM model (default: /models/sesame-csm-1b)")
    parser.add_argument("--output", "-o", default="/audiobook_data/test_sample.wav",
                        help="Output WAV file path (default: /audiobook_data/test_sample.wav)")
    parser.add_argument("--text", "-t", default="This is a test of the Sesame CSM text to speech system.",
                        help="Text to synthesize (default: 'This is a test of the Sesame CSM text to speech system.')")
    parser.add_argument("--device", "-d", choices=["cuda", "cpu"], default="cuda",
                        help="Device to use for inference (default: cuda)")
    return parser.parse_args()

def main():
    """Run the CSM test."""
    args = parse_args()
    
    try:
        # Import torch first to check CUDA
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        logger.info(f"Using device: {args.device}")
        
        # Try multiple import paths for flexibility
        try:
            # Try to import from csm_utils (preferred)
            sys.path.append('/opt/utils')
            from csm_utils import load_audiobook_model
            generator = load_audiobook_model(args.model_path, device=args.device)
            logger.info("Successfully imported from csm_utils")
        except ImportError:
            try:
                # Try to import from csm package
                from csm import load_csm_1b
                generator = load_csm_1b(model_path=args.model_path, device=args.device)
                logger.info("Successfully imported from csm package")
            except ImportError:
                # Direct import from module path
                sys.path.insert(0, "/opt/csm")
                from generator import load_csm_1b
                generator = load_csm_1b(model_path=args.model_path, device=args.device)
                logger.info("Successfully imported directly from generator.py")
        
        logger.info("CSM imports successful")
        
        # Verify model path exists
        if not os.path.exists(args.model_path):
            logger.error(f"Model path does not exist: {args.model_path}")
            sys.exit(1)
        
        # Generate test audio
        logger.info(f"Generating speech for: \"{args.text}\"")
        
        # Time the generation
        import time
        start_time = time.time()
        
        # Generate audio
        import torchaudio
        audio = generator.generate(text=args.text)
        
        # Report generation time
        elapsed_time = time.time() - start_time
        logger.info(f"Generation took {elapsed_time:.2f} seconds")
        
        # Save the audio
        output_file = Path(args.output)
        os.makedirs(output_file.parent, exist_ok=True)
        torchaudio.save(output_file, audio.unsqueeze(0).cpu(), generator.sample_rate)
        logger.info(f"Test audio saved to {output_file}")
        
        logger.info("✅ Test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
