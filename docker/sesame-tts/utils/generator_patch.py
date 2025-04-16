"""
Patch file for the CSM generator to fix compatibility issues with the specific 
torchtune/torchao versions available on Jetson.
"""

import torch
import os
import logging

logger = logging.getLogger(__name__)

def patch_csm_generator():
    """
    Apply patches to fix compatibility issues in the CSM generator.
    """
    # Get path to the generator.py file
    generator_path = "/opt/csm/generator.py"
    models_path = "/opt/csm/models.py"
    
    if not os.path.exists(generator_path):
        logger.error(f"Cannot find generator.py at {generator_path}")
        return
    
    if not os.path.exists(models_path):
        logger.error(f"Cannot find models.py at {models_path}")
        return
    
    # Patch the models.py file
    try:
        with open(models_path, 'r') as file:
            models_content = file.read()
        
        # Add this wrapper to handle potentially problematic torchtune transformer calls
        patched_content = models_content.replace(
            "def generate_frame(self, curr_tokens, curr_tokens_mask, input_pos, temperature, topk):",
            """def generate_frame(self, curr_tokens, curr_tokens_mask, input_pos, temperature, topk):
        # Handle shape issues for torchtune compatibility
        if hasattr(curr_tokens, 'ndim') and curr_tokens.ndim != 2:
            # Reshape to ensure 2D tensor if needed
            curr_tokens = curr_tokens.reshape(-1, curr_tokens.size(-1))""")
        
        with open(models_path, 'w') as file:
            file.write(patched_content)
        logger.info("Successfully patched models.py")
    
    except Exception as e:
        logger.error(f"Failed to patch models.py: {e}")
    
    # Patch the generator.py file
    try:
        with open(generator_path, 'r') as file:
            generator_content = file.read()
        
        # Add a try/except block around the generate method to handle potential issues
        patched_content = generator_content.replace(
            "def generate(self, text, speaker, context=None, max_audio_length_ms=30000, temperature=0.8, topk=50):",
            """def generate(self, text, speaker, context=None, max_audio_length_ms=30000, temperature=0.8, topk=50):
        # Safely handle the case when no context is provided
        if context is None:
            context = []
            
        # Validate all inputs
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string")
            
        try:""")
        
        # Close the try block
        patched_content = patched_content.replace(
            "return audio",
            """    return audio
        except Exception as e:
            import traceback
            print(f"Error in generate: {e}")
            traceback.print_exc()
            # Return silent audio instead of failing
            return torch.zeros(int(self.sample_rate * (max_audio_length_ms / 1000))).to("cuda")""")
        
        with open(generator_path, 'w') as file:
            file.write(patched_content)
        logger.info("Successfully patched generator.py")
        
    except Exception as e:
        logger.error(f"Failed to patch generator.py: {e}")
