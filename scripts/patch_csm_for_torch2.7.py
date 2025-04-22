#!/usr/bin/env python3
"""
Script to patch the Sesame CSM repository to work without moshi dependency.
This is required if using torch 2.7.0 and newer, as moshi requires torch<2.7.

Usage:
  1. Clone the CSM repository: git clone https://github.com/SesameAILabs/csm.git
  2. Run this script: python patch_csm_for_torch2.7.py /path/to/csm
"""

import os
import sys
import re
import shutil
from pathlib import Path

def patch_csm_repo(csm_path):
    """
    Patch the Sesame CSM repository to work without moshi dependency.
    
    Args:
        csm_path: Path to the cloned CSM repository
    """
    csm_path = Path(csm_path)
    
    if not csm_path.exists():
        print(f"Error: Path {csm_path} does not exist")
        return False
        
    # Backup important files before modifying
    files_to_patch = [
        csm_path / "generator.py",  # Likely contains moshi imports
        csm_path / "models.py",     # Likely contains moshi imports
        csm_path / "setup.py"       # Contains dependency list
    ]
    
    # Create backups
    for file_path in files_to_patch:
        if file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            print(f"Created backup: {backup_path}")
    
    # Patch setup.py to remove moshi dependency
    setup_path = csm_path / "setup.py"
    if setup_path.exists():
        with open(setup_path, 'r') as f:
            setup_content = f.read()
        
        # Remove moshi from install_requires
        modified_content = re.sub(
            r"(['\"]\s*moshi[^'\"]*['\"])\s*,", 
            r"# \1,  # Removed due to torch 2.7 compatibility", 
            setup_content
        )
        
        with open(setup_path, 'w') as f:
            f.write(modified_content)
        print(f"Patched {setup_path} to remove moshi dependency")
    
    # Attempt to patch Python files with moshi imports
    for file_path in [f for f in files_to_patch if f.suffix == '.py']:
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Pattern 1: Comment out import moshi statements
            modified_content = re.sub(
                r'^(\s*import\s+moshi\s*)', 
                r'# \1  # Commented out for torch 2.7 compatibility', 
                content, 
                flags=re.MULTILINE
            )
            
            # Pattern 2: Comment out from moshi import ... statements
            modified_content = re.sub(
                r'^(\s*from\s+moshi\s+import\s+.*)', 
                r'# \1  # Commented out for torch 2.7 compatibility', 
                modified_content, 
                flags=re.MULTILINE
            )
            
            # Pattern 3: Replace moshi function calls with dummy alternatives
            # This is a simplified example - may need manual adjustments
            if 'moshi' in modified_content:
                print(f"WARNING: {file_path} still contains moshi references that may need manual editing")
                print("         Search for 'moshi.' in the file and adjust as needed")
            
            with open(file_path, 'w') as f:
                f.write(modified_content)
            print(f"Patched {file_path} to comment out moshi imports")
    
    print("\nPatching complete! Note that manual editing might still be required.")
    print("Test the patched code thoroughly before using in production.")
    print("You may need to implement alternative functionality for removed moshi features.")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/csm")
        sys.exit(1)
    
    success = patch_csm_repo(sys.argv[1])
    sys.exit(0 if success else 1)
