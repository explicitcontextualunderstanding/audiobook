#!/usr/bin/env python3
"""
Determines the best package versions to use by analyzing:
1. Jetson PyPI index availability
2. Dependency compatibility
3. Wheel availability for ARM64
4. Circular dependency avoidance

This script produces a recommended requirements.in file.
"""

import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Output directory
REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "dependency_artifacts"
OUTPUT_DIR.mkdir(exist_ok=True)

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

class VersionResolver:
    """Class to determine the best versions of packages to use"""
    
    def __init__(self):
        self.jetson_versions = {}  # Latest versions available on Jetson index
        self.pypi_versions = {}    # Latest versions available on PyPI
        self.wheel_availability = {}  # Whether wheels are available for ARM64
        self.dependency_constraints = defaultdict(list)  # Version constraints from dependencies
        self.current_versions = {}  # Versions from current requirements.in
        
    def get_jetson_versions(self):
        """Get latest versions available on Jetson PyPI index"""
        print("Checking latest versions on Jetson PyPI index...")
        
        for package in KEY_PACKAGES:
            try:
                cmd = f"pip index versions {package} --index-url=https://pypi.jetson-ai-lab.dev/simple"
                output = subprocess.check_output(cmd, shell=True, text=True)
                versions = output.strip().split("\n")
                if len(versions) > 1:
                    versions_list = versions[1].split("Available versions: ")[1].split(", ")
                    if versions_list:
                        self.jetson_versions[package] = versions_list[0]  # Take the first (latest)
            except Exception as e:
                print(f"  Error checking Jetson version for {package}: {e}")
        
        return self.jetson_versions
    
    def get_pypi_versions(self):
        """Get latest versions available on PyPI"""
        print("Checking latest versions on PyPI...")
        
        for package in KEY_PACKAGES:
            try:
                cmd = f"pip index versions {package}"
                output = subprocess.check_output(cmd, shell=True, text=True)
                versions = output.strip().split("\n")
                if len(versions) > 1:
                    versions_list = versions[1].split("Available versions: ")[1].split(", ")
                    if versions_list:
                        self.pypi_versions[package] = versions_list[0]  # Take the first (latest)
            except Exception as e:
                print(f"  Error checking PyPI version for {package}: {e}")
        
        return self.pypi_versions
    
    def check_wheel_availability(self):
        """Check whether ARM64 wheels are available for packages"""
        print("Checking wheel availability for ARM64...")
        
        for package in KEY_PACKAGES:
            try:
                # Check if ARM64 wheel is available on Jetson index
                jetson_cmd = [
                    sys.executable, "-m", "pip", "download",
                    "--no-deps",
                    "--only-binary=:all:",
                    f"--python-version=3.10",
                    f"--platform=linux_aarch64",
                    f"--index-url=https://pypi.jetson-ai-lab.dev/simple",
                    package
                ]
                
                jetson_result = subprocess.run(jetson_cmd, capture_output=True, text=True, timeout=30)
                jetson_available = jetson_result.returncode == 0
                
                # Check if ARM64 wheel is available on PyPI
                pypi_cmd = [
                    sys.executable, "-m", "pip", "download",
                    "--no-deps",
                    "--only-binary=:all:",
                    f"--python-version=3.10",
                    f"--platform=linux_aarch64",
                    package
                ]
                
                pypi_result = subprocess.run(pypi_cmd, capture_output=True, text=True, timeout=30)
                pypi_available = pypi_result.returncode == 0
                
                self.wheel_availability[package] = {
                    'jetson': jetson_available,
                    'pypi': pypi_available
                }
                
                # Clean up downloaded wheels
                for file in os.listdir():
                    if file.endswith('.whl'):
                        try:
                            os.remove(file)
                        except:
                            pass
                
            except Exception as e:
                print(f"  Error checking wheel availability for {package}: {e}")
                self.wheel_availability[package] = {'jetson': False, 'pypi': False}
        
        return self.wheel_availability
    
    def get_current_versions(self, requirements_in_path):
        """Get versions from current requirements.in file"""
        print(f"Reading current versions from {requirements_in_path}...")
        
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
                        
                        if package_name in KEY_PACKAGES:
                            self.current_versions[package_name] = version_spec
        except Exception as e:
            print(f"  Error reading requirements.in: {e}")
        
        return self.current_versions
    
    def get_dependency_constraints(self):
        """Get version constraints from dependencies using pipdeptree"""
        print("Analyzing dependency constraints...")
        
        try:
            # Install pipdeptree if not already installed
            subprocess.run([sys.executable, "-m", "pip", "install", "pipdeptree"], check=True)
            
            # Get reverse dependencies
            cmd = "pipdeptree --reverse --json"
            output = subprocess.check_output(cmd, shell=True, text=True)
            data = json.loads(output)
            
            # Process each package
            for key_package in KEY_PACKAGES:
                constraints = []
                
                # Find the package in the data
                for pkg in data:
                    if pkg["package"]["key"].lower() == key_package.lower():
                        # Get packages that depend on this one
                        for dep in pkg.get("dependencies", []):
                            pkg_name = dep["package"]
                            required_version = dep.get("required_version", "Any")
                            
                            if required_version and required_version != "Any":
                                constraints.append({
                                    'package': pkg_name,
                                    'version_spec': required_version
                                })
                        
                        break
                
                self.dependency_constraints[key_package] = constraints
        except Exception as e:
            print(f"  Error analyzing dependency constraints: {e}")
        
        return self.dependency_constraints
    
    def analyze_conflicts(self):
        """Analyze version conflicts using pip-compile dry run"""
        print("Analyzing potential version conflicts...")
        
        conflicts = []
        
        try:
            # Create a temporary requirements file
            temp_req_path = OUTPUT_DIR / "temp_requirements.in"
            with open(temp_req_path, 'w') as f:
                for package in KEY_PACKAGES:
                    # Use Jetson version if available, otherwise PyPI
                    version = ""
                    if package in self.jetson_versions:
                        version = f"=={self.jetson_versions[package]}"
                    elif package in self.pypi_versions:
                        version = f"=={self.pypi_versions[package]}"
                    
                    f.write(f"{package}{version}\n")
            
            # Try to compile with pip-compile
            cmd = f"pip-compile --dry-run {temp_req_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Check for conflicts in the output
            if result.returncode != 0:
                output = result.stderr or result.stdout
                lines = output.strip().split('\n')
                
                for i, line in enumerate(lines):
                    if "Could not find a version that satisfies the requirement" in line:
                        if i+1 < len(lines) and "caused by" in lines[i+1]:
                            conflicts.append({
                                'description': line.strip(),
                                'cause': lines[i+1].strip()
                            })
            
            # Clean up temp file
            if temp_req_path.exists():
                temp_req_path.unlink()
                
        except Exception as e:
            print(f"  Error analyzing conflicts: {e}")
        
        return conflicts
    
    def determine_best_versions(self):
        """Determine the best versions to use based on all data collected"""
        print("Determining best versions to use...")
        
        best_versions = {}
        recommendations = {}
        
        for package in KEY_PACKAGES:
            jetson_version = self.jetson_versions.get(package)
            pypi_version = self.pypi_versions.get(package)
            wheel_avail = self.wheel_availability.get(package, {'jetson': False, 'pypi': False})
            constraints = self.dependency_constraints.get(package, [])
            current_version = self.current_versions.get(package)
            
            # Start with current version as baseline
            best_spec = current_version
            
            # Logic for determining best version
            if wheel_avail['jetson'] and jetson_version:
                # Jetson wheel available - use the Jetson version
                recommendation = f">={jetson_version}"
                reason = f"Jetson-optimized wheel available ({jetson_version})"
            elif wheel_avail['pypi'] and pypi_version:
                # PyPI wheel available - use PyPI version
                recommendation = f">={pypi_version}"
                reason = f"ARM64 wheel available on PyPI ({pypi_version})"
            elif jetson_version:
                # No wheel but Jetson version exists - use minimum version
                recommendation = f">={jetson_version}"
                reason = f"No ARM64 wheel, but version exists on Jetson index ({jetson_version})"
            elif pypi_version:
                # Fallback to PyPI version
                recommendation = f">={pypi_version}"
                reason = f"Fallback to PyPI version ({pypi_version}), will build from source"
            else:
                # Keep current or use unpinned
                recommendation = current_version or ""
                reason = "Keeping current version (no better alternative found)"
            
            # Consider dependency constraints
            if constraints:
                constraint_specs = [c['version_spec'] for c in constraints if c.get('version_spec')]
                if constraint_specs:
                    note = f"Has {len(constraint_specs)} dependency constraints: {', '.join(constraint_specs)}"
                    reason += f". {note}"
            
            # Save recommendation
            best_versions[package] = recommendation
            recommendations[package] = {
                'recommendation': recommendation,
                'reason': reason,
                'jetson_version': jetson_version,
                'pypi_version': pypi_version,
                'wheel_available_jetson': wheel_avail.get('jetson', False),
                'wheel_available_pypi': wheel_avail.get('pypi', False),
                'current_version': current_version,
                'dependency_constraints': constraints
            }
        
        return best_versions, recommendations
    
    def generate_recommended_requirements(self, output_path, recommendations):
        """Generate a recommended requirements.in file"""
        print(f"Generating recommended requirements.in at {output_path}...")
        
        with open(output_path, 'w') as f:
            f.write("# Recommended requirements.in generated by resolve_best_versions.py\n")
            f.write("# Generated on: " + subprocess.check_output("date", shell=True, text=True).strip() + "\n\n")
            
            # Core PyTorch packages
            f.write("# Core PyTorch - using Jetson-optimized versions\n")
            for pkg in ['torch', 'torchvision', 'torchaudio']:
                if pkg in recommendations:
                    rec = recommendations[pkg]
                    f.write(f"{pkg}{rec['recommendation']}  # {rec['reason']}\n")
            f.write("\n")
            
            # Libraries with specific version requirements
            f.write("# Libraries with specific version requirements - using Jetson-optimized where available\n")
            for pkg in ['vector_quantize_pytorch', 'torchtune', 'torchao', 'moshi', 'triton']:
                if pkg in recommendations:
                    rec = recommendations[pkg]
                    f.write(f"{pkg}{rec['recommendation']}  # {rec['reason']}\n")
            f.write("\n")
            
            # Updated other critical dependencies
            f.write("# Updated other critical dependencies for better compatibility\n")
            for pkg in ['einops', 'silentcipher', 'librosa']:
                if pkg in recommendations:
                    rec = recommendations[pkg]
                    f.write(f"{pkg}{rec['recommendation']}  # {rec['reason']}\n")
            f.write("\n")
            
            # Add remaining packages from original requirements.in
            original_req_path = REPO_ROOT / "docker" / "sesame-tts" / "requirements.in"
            if original_req_path.exists():
                with open(original_req_path, 'r') as orig:
                    in_key_section = False
                    
                    for line in orig:
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Skip packages already handled
                        package_name = line.split('=')[0].split('>')[0].split('<')[0].strip()
                        if package_name in recommendations:
                            continue
                        
                        # Add other packages as-is
                        match = re.match(r'([a-zA-Z0-9_\-\.]+)([<>=~!]+.*)?', line)
                        if match:
                            pkg_name = match.group(1)
                            pkg_version = match.group(2) or ""
                            f.write(f"{pkg_name}{pkg_version}\n")
            
            f.write("\n# End of recommended requirements.in\n")
        
        return output_path
    
    def generate_report(self, recommendations, conflicts, output_dir):
        """Generate a human-readable report of version analysis"""
        report_path = output_dir / "version_analysis_report.txt"
        json_path = output_dir / "version_analysis.json"
        
        with open(report_path, 'w') as f:
            f.write("# Package Version Analysis Report\n\n")
            
            # Write conflicts section
            f.write("## Potential Version Conflicts\n\n")
            if conflicts:
                for i, conflict in enumerate(conflicts):
                    f.write(f"{i+1}. {conflict['description']}\n")
                    f.write(f"   Cause: {conflict['cause']}\n\n")
            else:
                f.write("No version conflicts detected with recommended versions.\n\n")
            
            # Write package recommendations
            f.write("## Package Recommendations\n\n")
            
            for package, rec in sorted(recommendations.items()):
                f.write(f"### {package}\n\n")
                f.write(f"**Recommendation:** {package}{rec['recommendation']}\n\n")
                f.write(f"**Reason:** {rec['reason']}\n\n")
                
                f.write("**Details:**\n")
                f.write(f"- Current version: {rec['current_version'] or 'Not specified'}\n")
                f.write(f"- Latest on Jetson index: {rec['jetson_version'] or 'Not found'}\n")
                f.write(f"- Latest on PyPI: {rec['pypi_version'] or 'Not found'}\n")
                f.write(f"- ARM64 wheel on Jetson: {'Yes' if rec['wheel_available_jetson'] else 'No'}\n")
                f.write(f"- ARM64 wheel on PyPI: {'Yes' if rec['wheel_available_pypi'] else 'No'}\n")
                
                if rec['dependency_constraints']:
                    f.write("\n**Dependency constraints:**\n")
                    for constraint in rec['dependency_constraints']:
                        f.write(f"- Required by {constraint['package']}: {constraint['version_spec']}\n")
                
                f.write("\n")
        
        # Write JSON data
        with open(json_path, 'w') as f:
            json.dump({
                'recommendations': recommendations,
                'conflicts': conflicts
            }, f, indent=2)
        
        return report_path, json_path
    
    def run_analysis(self, requirements_in_path):
        """Run the full analysis pipeline"""
        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Gather data
        self.get_current_versions(requirements_in_path)
        self.get_jetson_versions()
        self.get_pypi_versions()
        self.check_wheel_availability()
        self.get_dependency_constraints()
        
        # Analyze conflicts
        conflicts = self.analyze_conflicts()
        
        # Determine best versions
        best_versions, recommendations = self.determine_best_versions()
        
        # Generate outputs
        recommended_req_path = OUTPUT_DIR / "recommended_requirements.in"
        self.generate_recommended_requirements(recommended_req_path, recommendations)
        
        report_path, json_path = self.generate_report(recommendations, conflicts, OUTPUT_DIR)
        
        return {
            'recommended_requirements': recommended_req_path,
            'report': report_path,
            'json_data': json_path,
            'best_versions': best_versions,
            'conflicts': conflicts
        }

def main():
    # Check requirements.in file
    requirements_in_path = REPO_ROOT / "docker" / "sesame-tts" / "requirements.in"
    if not requirements_in_path.exists():
        print(f"Error: requirements.in not found at {requirements_in_path}")
        return
    
    print(f"Starting version resolution analysis for {requirements_in_path}...")
    
    # Create resolver and run analysis
    resolver = VersionResolver()
    results = resolver.run_analysis(requirements_in_path)
    
    print(f"\nAnalysis complete. Outputs:")
    print(f"- Recommended requirements: {results['recommended_requirements']}")
    print(f"- Analysis report: {results['report']}")
    print(f"- JSON data: {results['json_data']}")
    
    if results['conflicts']:
        print(f"\nWARNING: {len(results['conflicts'])} potential version conflicts detected.")
        print(f"Review the analysis report for details.")
    else:
        print(f"\nNo version conflicts detected with the recommended versions.")
    
    print(f"\nRecommended actions:")
    print(f"1. Review the analysis report in {results['report']}")
    print(f"2. Compare the recommended requirements with your current requirements")
    print(f"3. If satisfied, replace your requirements.in with the recommended one:")
    print(f"   cp {results['recommended_requirements']} {requirements_in_path}")
    print(f"4. Build the Docker container with the updated requirements.in")

if __name__ == "__main__":
    main()
