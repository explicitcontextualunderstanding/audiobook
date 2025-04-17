#!/usr/bin/env python3
"""
Enhanced wrapper for the CSM generator with additional error handling
and features for audiobook generation.

This file extends the functionality of the original CSM generator
without modifying the upstream code directly. It uses inheritance rather
than patching to maintain a cleaner separation between our code and the
upstream implementation.
"""

import traceback
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Conditionally import torch - makes the code more robust across environments
try:
    import torch
except ImportError:
    logger.warning("Could not import torch. This module is designed to run within the container environment.")
    # Create a placeholder for development environments
    class PlaceholderTorch:
        def zeros(self, *args, **kwargs):
            return None
    torch = PlaceholderTorch()

# Ensure the CSM module is in the path
if os.path.exists("/opt/csm"):
    sys.path.append("/opt/csm")

# Set up placeholders for development environments
class PlaceholderGenerator:
    """Placeholder for development environments that don't have the CSM generator."""
    def __init__(self, *args, **kwargs):
        pass

    def generate(self, *args, **kwargs):
        return None

Segment = None
original_load_csm_1b = None
OriginalGenerator = PlaceholderGenerator

# Try to import the real components when running in the container
try:
    # Add current path to sys.path for direct imports
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, current_dir)
    
    # Try different import strategies
    try:
        from generator import load_csm_1b as original_load_csm_1b
        from generator import Segment, Generator as OriginalGenerator
        logger.info("Successfully imported CSM generator components from direct import")
    except ImportError:
        # Alternative: Try importing from /opt/csm with absolute path
        sys.path.insert(0, "/opt/csm")
        from generator import load_csm_1b as original_load_csm_1b
        from generator import Segment, Generator as OriginalGenerator
        logger.info("Successfully imported CSM generator components from /opt/csm")
        
except ImportError as e:
    logger.warning(f"Could not import CSM generator: {e}")
    logger.warning("This is expected during development but should work in the container")

class AudiobookGenerator(OriginalGenerator):
    """
    Enhanced version of the CSM Generator with additional error handling
    and features specifically for audiobook generation.
    """
    
    def generate(self, text, speaker, context=None, max_audio_length_ms=30000, temperature=0.8, topk=50):
        """
        Wrapper around the original generate method with additional error handling
        to ensure robustness during audiobook generation.
        
        Args:
            text (str): Text to generate audio for
            speaker (str): Speaker voice to use
            context (list): Context for the generation
            max_audio_length_ms (int): Maximum audio length in milliseconds
            temperature (float): Generation temperature
            topk (int): Top-k for sampling
            
        Returns:
            torch.Tensor: Audio tensor (silent audio on error)
        """
        # Safely handle the case when no context is provided
        if context is None:
            context = []
            
        # Validate all inputs
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string")
            
        try:
            # Call the original generate method
            return super().generate(text, speaker, context, max_audio_length_ms, temperature, topk)
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            traceback.print_exc()
            # Return silent audio instead of failing
            return torch.zeros(int(self.sample_rate * (max_audio_length_ms / 1000))).to("cuda")

def load_csm_1b(*args, **kwargs):
    """
    Drop-in replacement for the original load_csm_1b function that returns
    our enhanced AudiobookGenerator.
    
    Based on examining the original CSM repository, the original load_csm_1b
    returns a Generator instance directly, not a tuple of (model, params).
    
    All arguments are passed through to the original function.
    """
    # The original CSM implementation returns a Generator object directly
    original_generator = original_load_csm_1b(*args, **kwargs)
    
    # Extract the model from the original generator
    model = original_generator._model
    
    # Create our enhanced generator with the model
    enhanced_generator = AudiobookGenerator(model)
    
    # Copy any other important attributes
    if hasattr(original_generator, 'sample_rate'):
        enhanced_generator.sample_rate = original_generator.sample_rate
    if hasattr(original_generator, 'device'):
        enhanced_generator.device = original_generator.device
    if hasattr(original_generator, '_watermarker'):
        enhanced_generator._watermarker = original_generator._watermarker
    if hasattr(original_generator, '_text_tokenizer'):
        enhanced_generator._text_tokenizer = original_generator._text_tokenizer
    if hasattr(original_generator, '_audio_tokenizer'):
        enhanced_generator._audio_tokenizer = original_generator._audio_tokenizer
    
    # Return our enhanced generator
    return enhanced_generator

# Re-export necessary components to maintain the same interface
__all__ = ["load_csm_1b", "Segment", "AudiobookGenerator"]
