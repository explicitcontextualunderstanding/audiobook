#!/usr/bin/env python3
"""
Checks the availability of pre-built wheels for different Python packages
on various platforms and Python versions, with special focus on Jetson/ARM64.
"""

import concurrent.futures
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

# Output directory
REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "dependency_artifacts"
OUTPUT_DIR.mkdir(exist_ok=True)

# Package sources to check
SOURCES = [
    {"name": "PyPI", "index": "https://pypi.org/simple"},
    {"name": "Jetson", "index": "https://pypi.jetson-ai-lab.dev/simple"},
    {"name": "NGC", "index": "https://pypi.ngc.nvidia.com"}
]

# Platforms to check
PLATFORMS = [
    {"name": "linux_x86_64", "alias": "Linux x86_64"},
    {"name": "linux_aarch64", "alias": "Linux ARM64 (Jetson)"},
    {"name": "manylinux2014_aarch64", "alias": "Manylinux ARM64"},
    {"name": "manylinux_2_17_aarch64", "alias": "Manylinux 2.17 ARM64"}
]

# Python versions to check
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11"]

def get_packages_from_requirements(requirements_in_path):
    """Extract package names and versions from requirements.in file"""
    packages = []
    
    try:
        with open(requirements_in_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Remove any comments from the line
                line = line.split('#')[0].strip()
                
                # Skip git/url requirements for this check
                if 'git+' in line or '://' in line:
                    continue
                    
                # Parse package name and version specifier
                match = re.match(r'([a-zA-Z0-9_\-\.]+)([<>=~!]+.*)?', line)
                if match:
                    package_name = match.group(1)
                    version_spec = match.group(2) if match.group(2) else None
                    packages.append({"name": package_name, "version": version_spec})
    except Exception as e:
        print(f"Error reading requirements file: {e}")
    
    return packages

def check_wheel_availability(package, python_version, platform, index_url):
    """Check if a pre-built wheel is available for a specific package/platform/Python version"""
    try:
        cmd = [
            sys.executable, "-m", "pip", "download",
            "--no-deps",
            "--only-binary=:all:",
            f"--python-version={python_version}",
            f"--platform={platform}",
            f"--index-url={index_url}",
            package["name"] + (package["version"] or "")
        ]
        
        # Run with subprocess and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Check if the command was successful
        if result.returncode == 0:
            # Extract the actual wheel filename from the output if possible
            match = re.search(r'Saved (.*\.whl)', result.stdout)
            wheel_name = match.group(1) if match else "Available"
            return True, wheel_name
        else:
            # No wheel available
            return False, None
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    # Get packages from requirements.in
    requirements_in_path = REPO_ROOT / "docker" / "sesame-tts" / "requirements.in"
    if not requirements_in_path.exists():
        print(f"Error: requirements.in not found at {requirements_in_path}")
        return
        
    packages = get_packages_from_requirements(requirements_in_path)
    if not packages:
        print("No packages found in requirements.in")
        return
        
    print(f"Found {len(packages)} packages in requirements.in")
    
    # Create CSV file for results
    csv_path = OUTPUT_DIR / "wheel_availability.csv"
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Package', 'Version Spec', 'Python Version', 'Platform', 'Source', 'Available', 'Wheel Name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Create a text summary file
        txt_path = OUTPUT_DIR / "wheel_availability_summary.txt"
        with open(txt_path, 'w') as txtfile:
            txtfile.write("# Wheel Availability Summary\n\n")
            txtfile.write("This file shows which packages have pre-built wheels available for different platforms.\n\n")
            
            # Process packages in groups to avoid overwhelming PyPI
            for i, package in enumerate(packages):
                pkg_name = package["name"]
                pkg_ver = package["version"] or "latest"
                print(f"Checking wheel availability for {pkg_name} ({pkg_ver}) [{i+1}/{len(packages)}]")
                
                txtfile.write(f"## {pkg_name} {pkg_ver}\n\n")
                
                # Check each combination of Python version, platform, and source
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_params = {}
                    for python_version in PYTHON_VERSIONS:
                        for platform_info in PLATFORMS:
                            for source in SOURCES:
                                future = executor.submit(
                                    check_wheel_availability,
                                    package,
                                    python_version,
                                    platform_info["name"],
                                    source["index"]
                                )
                                future_to_params[future] = {
                                    "python_version": python_version,
                                    "platform": platform_info["name"],
                                    "platform_alias": platform_info["alias"],
                                    "source": source["name"]
                                }
                    
                    for future in concurrent.futures.as_completed(future_to_params):
                        params = future_to_params[future]
                        available, wheel_name = future.result()
                        
                        # Write to CSV
                        writer.writerow({
                            'Package': pkg_name,
                            'Version Spec': pkg_ver,
                            'Python Version': params["python_version"],
                            'Platform': params["platform"],
                            'Source': params["source"],
                            'Available': 'Yes' if available else 'No',
                            'Wheel Name': wheel_name if available else 'N/A'
                        })
                        
                        # Store result for text summary
                        results.append({
                            **params,
                            'available': available,
                            'wheel_name': wheel_name
                        })
                
                # Write text summary for this package
                txtfile.write("| Platform | Python | Source | Available | Wheel |\n")
                txtfile.write("|----------|--------|--------|-----------|-------|\n")
                
                # Sort by platform, Python version, and source
                results.sort(key=lambda x: (x["platform"], x["python_version"], x["source"]))
                
                for result in results:
                    if result["platform"] == "linux_aarch64":  # Highlight Jetson results
                        availability = "✅ Yes" if result["available"] else "❌ No"
                    else:
                        availability = "Yes" if result["available"] else "No"
                        
                    wheel_info = result["wheel_name"] if result["available"] else "N/A"
                    # Truncate wheel name if too long
                    if isinstance(wheel_info, str) and len(wheel_info) > 30:
                        wheel_info = wheel_info[:27] + "..."
                        
                    txtfile.write(f"| {result['platform_alias']} | {result['python_version']} | {result['source']} | {availability} | {wheel_info} |\n")
                
                txtfile.write("\n")
                txtfile.flush()  # Force write to disk
                
                # Cleanup any downloaded wheels
                for file in os.listdir():
                    if file.endswith('.whl'):
                        try:
                            os.remove(file)
                        except:
                            pass
    
    print(f"Wheel availability check complete.")
    print(f"CSV results available at: {csv_path}")
    print(f"Summary report available at: {txt_path}")

if __name__ == "__main__":
    main()
