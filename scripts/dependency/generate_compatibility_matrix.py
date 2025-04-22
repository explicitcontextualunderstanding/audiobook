#!/usr/bin/env python3
"""
Generates a version compatibility matrix to visualize how different package versions work together.
This helps identify problematic version combinations and avoid circular dependency resolution.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Key packages to analyze
KEY_PACKAGES = [
    "torch",
    "torchvision", 
    "torchaudio",
    "vector_quantize_pytorch",
    "torchao",
    "moshi",
    "einops",
    "triton",
    "transformers",
    "librosa"
]

# Output directory
REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "dependency_artifacts"
OUTPUT_DIR.mkdir(exist_ok=True)

def get_available_versions(package_name):
    """Get available versions for a package from PyPI and Jetson index"""
    result = {}
    
    # Check PyPI
    try:
        cmd = f"pip index versions {package_name} --index-url=https://pypi.org/simple"
        output = subprocess.check_output(cmd, shell=True, text=True)
        versions = output.strip().split("\n")
        if len(versions) > 1:
            versions_list = versions[1].split("Available versions: ")[1].split(", ")
            result["pypi"] = versions_list[:5]  # Just take the 5 most recent
    except Exception as e:
        result["pypi"] = [f"Error: {str(e)}"]
    
    # Check Jetson PyPI
    try:
        cmd = f"pip index versions {package_name} --index-url=https://pypi.jetson-ai-lab.dev/simple"
        output = subprocess.check_output(cmd, shell=True, text=True)
        versions = output.strip().split("\n")
        if len(versions) > 1:
            versions_list = versions[1].split("Available versions: ")[1].split(", ")
            result["jetson"] = versions_list[:5]  # Just take the 5 most recent
    except Exception as e:
        result["jetson"] = [f"Error: {str(e)}"]
        
    return result

def get_installed_version(package_name):
    """Get currently installed version of a package"""
    try:
        cmd = f"pip show {package_name} | grep Version"
        output = subprocess.check_output(cmd, shell=True, text=True)
        return output.strip().split("Version: ")[1]
    except Exception:
        return "Not installed"

def check_dependency_constraints(package_name):
    """Find what other packages depend on this package and their version constraints"""
    constraints = {}
    try:
        cmd = "pipdeptree --reverse --json"
        output = subprocess.check_output(cmd, shell=True, text=True)
        data = json.loads(output)
        
        for pkg in data:
            if pkg["package"]["key"].lower() == package_name.lower():
                for dep in pkg.get("dependencies", []):
                    pkg_name = dep["package"]
                    required_version = dep.get("required_version", "Any")
                    constraints[pkg_name] = required_version
                break
    except Exception as e:
        constraints["Error"] = str(e)
    
    return constraints

def main():
    """Main function to generate the compatibility matrix"""
    # Ensure pipdeptree is installed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipdeptree"])
    except Exception as e:
        print(f"Error installing pipdeptree: {e}")
        return
    
    matrix = {}
    
    print("Generating version compatibility matrix...")
    
    # For each key package
    for package in KEY_PACKAGES:
        print(f"Analyzing {package}...")
        matrix[package] = {
            "installed_version": get_installed_version(package),
            "available_versions": get_available_versions(package),
            "required_by": check_dependency_constraints(package)
        }
    
    # Write JSON output
    with open(OUTPUT_DIR / "compatibility_matrix.json", "w") as f:
        json.dump(matrix, f, indent=2)
    
    # Write human-readable output
    with open(OUTPUT_DIR / "compatibility_matrix.txt", "w") as f:
        f.write("# Package Version Compatibility Matrix\n\n")
        f.write("This file shows compatibility relationships between key packages.\n\n")
        
        for package, info in matrix.items():
            f.write(f"## {package}\n\n")
            f.write(f"Currently installed: {info['installed_version']}\n\n")
            
            f.write("Available versions:\n")
            f.write("- PyPI: " + ", ".join(info['available_versions'].get('pypi', ['None'])) + "\n")
            f.write("- Jetson: " + ", ".join(info['available_versions'].get('jetson', ['None'])) + "\n\n")
            
            f.write("Required by:\n")
            if info['required_by']:
                for dep, ver in info['required_by'].items():
                    f.write(f"- {dep}: {ver}\n")
            else:
                f.write("- No packages directly depend on this\n")
            f.write("\n")
    
    print(f"Compatibility matrix generated at {OUTPUT_DIR}/compatibility_matrix.txt")
    print(f"JSON data available at {OUTPUT_DIR}/compatibility_matrix.json")

if __name__ == "__main__":
    main()
