#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_csm")

try:
    import torch
    import torchaudio
    # import torchao # No longer needed/present in the environment
    
    # Try multiple import paths for flexibility
    try:
        from csm import load_csm_1b, Segment
        logger.info("Successfully imported from csm package")
    except ImportError:
        # Direct import from module path
        sys.path.insert(0, "/opt/csm")
        from generator import load_csm_1b, Segment
        logger.info("Successfully imported directly from generator.py")
    
    logger.info("CSM imports successful")
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    # Get model path from argument or use default
    model_path = sys.argv[1] if len(sys.argv) > 1 else "/models/sesame-csm-1b"
    
    # Verify model path exists
    if not os.path.exists(model_path):
        logger.error(f"Model path does not exist: {model_path}")
        sys.exit(1)
    
    # Load the model
    logger.info(f"Loading CSM model from {model_path}...")
    generator = load_csm_1b(model_path=model_path, device=device)
    
    # Generate test audio
    text = "This is a test of the CSM text to speech system."
    logger.info(f"Generating speech for: \"{text}\"")
    audio = generator.generate(text=text)
    
    # Save the audio
    output_file = Path("/audiobook_data/test_sample.wav")
    torchaudio.save(output_file, audio.unsqueeze(0).cpu(), generator.sample_rate)
    logger.info(f"Test audio saved to {output_file}")
    
    logger.info("✅ Test completed successfully!")

except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)