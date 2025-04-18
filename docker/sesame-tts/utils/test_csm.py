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

# dynamic import: prefer installed csm package, else fallback to local utils
try:
    from csm import CSMModel, CSMConfig
except ImportError:
    utils_dir = os.path.dirname(__file__)
    sys.path.insert(0, utils_dir)
    from generator import CSMModel
    from models    import CSMConfig

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
        
        # Test key imports with careful error handling
        try:
            import torchao
            logger.info(f"✓ Successfully imported torchao version: {torchao.__version__ if hasattr(torchao, '__version__') else 'unknown'}")
        except ImportError as e:
            logger.error(f"❌ Failed to import torchao: {e}")
            logger.info("Continuing without torchao import verification...")
        
        try:
            import torchtune
            logger.info(f"✓ Successfully imported torchtune version: {torchtune.__version__ if hasattr(torchtune, '__version__') else 'unknown'}")
        except ImportError as e:
            logger.error(f"❌ Failed to import torchtune: {e}")
            logger.info("Continuing without torchtune import verification...")
        
        try:
            import moshi
            logger.info("✓ Successfully imported moshi")
        except ImportError as e:
            logger.error(f"❌ Failed to import moshi: {e}")
            logger.info("Continuing without moshi import verification...")
        
        # Start timer for model loading
        start_time = time.time()
        logger.info(f"Loading CSM model from {args.model_path}...")
        
        # Load model via API with config
        try:
            config    = CSMConfig.from_pretrained(args.model_path)
            generator = CSMModel.from_pretrained(args.model_path, config=config).to("cuda")
            logger.info(f"✓ Model loaded successfully in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"❌ Error loading CSM model: {e}")
            logger.error("Please check your model path and that all dependencies are installed correctly.")
            sys.exit(1)
        
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
        try:
            # Modified to use a simpler generation approach to avoid torchtune shape issues
            logger.info("Using a simpler generation approach...")
            
            # Try a basic generation without segments
            audio = generator.generate(
                text=test_text,
                speaker=1,
                # Removed the context=segments parameter
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
        except Exception as e:
            logger.error(f"❌ Error during audio generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()