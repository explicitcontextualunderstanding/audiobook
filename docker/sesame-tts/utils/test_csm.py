#!/usr/bin/env python3
"""
Test script for Sesame CSM
This script tests if the CSM model can be loaded and used for generation.
"""

import os
import sys
import torch
import torchaudio
import time
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_csm')

def main():
    parser = argparse.ArgumentParser(description='Test CSM installation')
    parser.add_argument('model_path', type=str, help='Path to the CSM model directory')
    parser.add_argument('--output', type=str, default='test_output.wav', help='Output file for test generation')
    args = parser.parse_args()
    
    try:
        # Test CUDA availability
        if not torch.cuda.is_available():
            logger.error("❌ Error: CUDA is not available. This application requires a CUDA-enabled GPU.")
            sys.exit(1)
        
        logger.info(f"✓ Using device: {torch.cuda.get_device_name(0)}")
        logger.info(f"✓ CUDA Version: {torch.version.cuda}")
        
        # Test imports
        import torchao  # Re-enable import
        logger.info(f"✓ Successfully imported torchao version: {torchao.__version__ if hasattr(torchao, '__version__') else 'unknown'}")
        
        import moshi
        logger.info("✓ Successfully imported moshi")
        
        # Start timer for model loading
        start_time = time.time()
        logger.info(f"Loading CSM model from {args.model_path}...")
        
        # Import and load CSM
        from generator import load_csm_1b
        generator = load_csm_1b(device="cuda")
        logger.info(f"✓ Model loaded successfully in {time.time() - start_time:.2f} seconds")
        
        # Create a test segment
        from generator import Segment
        
        # Generate a small test audio
        logger.info("Generating test audio...")
        start_time = time.time()
        test_text = "This is a test of the Sesame CSM text to speech system."
        
        # Create a simple segment to use as context
        segments = [Segment(
            speaker=1,
            text="Hello, world.",
            audio=torch.zeros(generator.sample_rate).to("cuda")
        )]
        
        # Generate audio
        audio = generator.generate(
            text=test_text,
            speaker=1,
            context=segments,
            max_audio_length_ms=5000,  # 5 seconds max
            temperature=0.9,
            topk=50
        )
        
        # Save output
        output_path = os.path.join(os.getcwd(), args.output)
        torchaudio.save(output_path, audio.unsqueeze(0).cpu(), generator.sample_rate)
        
        logger.info(f"✓ Audio generation completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"✓ Saved test audio to {output_path}")
        logger.info("✓ CSM is installed and working correctly!")

        # Note: The Docker build process seems to be failing because
        # 'docker/sesame-tts/utils/watermarking.py' is missing.
        # Please ensure this file exists in your project directory
        # relative to where you run 'docker build'. This script itself
        # does not use watermarking, but the Dockerfile requires it.

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()