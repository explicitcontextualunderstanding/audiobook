#!/usr/bin/env python3
"""
Fix script for CSM model loading issues
This script directly modifies the Python path to ensure proper CSM model loading
"""
import os
import sys
import logging
import importlib.util
import traceback
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_csm')

# Ensure the CSM module path is at the beginning of sys.path
CSM_PATH = "/opt/csm"
if CSM_PATH not in sys.path:
    sys.path.insert(0, CSM_PATH)

# Define helper function to import modules directly from file path
def import_module_from_file(file_path, module_name):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logger.error(f"Could not load spec for {file_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error importing {module_name} from {file_path}: {e}")
        traceback.print_exc()
        return None

# Load the generator module directly from file
generator_module = import_module_from_file(os.path.join(CSM_PATH, "generator.py"), "generator")
if generator_module is not None:
    logger.info("✓ Successfully loaded generator.py")
    
    # Make the key components available globally
    sys.modules['generator'] = generator_module
    
    # Extract key components to be used directly
    load_csm_1b = generator_module.load_csm_1b
    Segment = generator_module.Segment
    Generator = generator_module.Generator
    
    logger.info("✓ Fixed generator module imports")
else:
    logger.error("❌ Failed to load generator.py")
    sys.exit(1)

# Check if the model directory exists
if len(sys.argv) > 1:
    model_path = sys.argv[1]
    if not os.path.exists(model_path):
        logger.error(f"❌ Model path does not exist: {model_path}")
        sys.exit(1)
    
    logger.info(f"✓ Model path exists: {model_path}")
    
    # Test loading the model
    try:
        # Import torch and torchaudio here to ensure they're available
        try:
            import torch
            import torchaudio
        except ImportError as e:
            logger.error(f"❌ Error importing torch/torchaudio: {e}")
            logger.error("Make sure PyTorch and torchaudio are installed correctly for your system")
            sys.exit(1)
        
        logger.info("Loading CSM model...")
        start = time.time()
        
        # Check if CUDA is available and use it if possible, otherwise fall back to CPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # For Jetson devices, verify CUDA is working correctly
        if device == "cuda":
            logger.info(f"CUDA devices available: {torch.cuda.device_count()}")
            logger.info(f"Current CUDA device: {torch.cuda.current_device()}")
            logger.info(f"CUDA device name: {torch.cuda.get_device_name(0)}")
        
        generator = load_csm_1b(model_path=model_path, device=device)
        
        logger.info(f"✓ Model loaded successfully in {time.time() - start:.2f} seconds")
            
        # Generate a simple test
        text = "This is a test of the Sesame CSM text to speech system."
        logger.info(f"Generating audio for: '{text}'")
        
        # Use default settings for simplicity
        audio = generator.generate(text, speaker=1)
        
        # Save the audio to a file
        output_file = sys.argv[2] if len(sys.argv) > 2 else "test_output.wav"
        torchaudio.save(output_file, audio.cpu().unsqueeze(0), generator.sample_rate)
        logger.info(f"✓ Audio saved to {output_file}")
        
    except Exception as e:
        logger.error(f"❌ Error testing model: {e}")
        traceback.print_exc()
        sys.exit(1)
else:
    logger.info("No model path specified, skipping model test")

logger.info("✓ CSM import fix script completed successfully")
