#!/usr/bin/env python3
"""
Simulates Python dependency resolution to identify potential circular dependencies
and find compatible version sets without actually installing packages.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Output directory
REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "dependency_artifacts"
OUTPUT_DIR.mkdir(exist_ok=True)

# Maximum recursion depth for dependency resolution
MAX_DEPTH = 10

class DependencyResolver:
    """Class to simulate Python dependency resolution"""
    
    def __init__(self):
        self.cache = {}  # Cache for package metadata
        self.resolution_path = []  # Track resolution path for cycle detection
        self.visited = set()  # Track visited packages to prevent infinite loops
    
    def get_package_metadata(self, package_name, index_url=None):
        """Get metadata for a package from PyPI"""
        cache_key = f"{package_name}:{index_url or 'default'}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        cmd = [sys.executable, "-m", "pip", "show", package_name]
        if index_url:
            cmd.extend(["--index-url", index_url])
            
        try:
            output = subprocess.check_output(cmd, text=True)
            metadata = {}
            for line in output.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            # Parse requires
            requires = []
            requires_dist = metadata.get('Requires', '')
            if requires_dist:
                requires = [r.strip() for r in requires_dist.split(',')]
            metadata['requires'] = requires
            
            self.cache[cache_key] = metadata
            return metadata
        except Exception as e:
            print(f"Error getting metadata for {package_name}: {e}")
            empty_metadata = {'Name': package_name, 'Version': 'unknown', 'requires': []}
            self.cache[cache_key] = empty_metadata
            return empty_metadata
    
    def parse_requirement(self, req_string):
        """Parse a requirement string into package name and version specifier"""
        # Handle complex requirements with extras and version specs
        match = re.match(r'([a-zA-Z0-9_\-\.]+)(\[[^\]]+\])?([<>=~!]+.*)?', req_string)
        if match:
            package_name = match.group(1)
            extras = match.group(2) or ""
            version_spec = match.group(3) or ""
            return package_name, extras, version_spec
        return req_string, "", ""
    
    def resolve_dependencies(self, package_name, version_spec="", depth=0, path=None):
        """Recursively resolve dependencies for a package"""
        if path is None:
            path = []
        
        # Check for max recursion depth
        if depth > MAX_DEPTH:
            return {'name': package_name, 'version_spec': version_spec, 'dependencies': [], 
                    'error': f"Max recursion depth ({MAX_DEPTH}) exceeded"}
        
        # Check for cycles
        package_key = f"{package_name}{version_spec}"
        if package_key in path:
            cycle_index = path.index(package_key)
            cycle_path = path[cycle_index:] + [package_key]
            return {'name': package_name, 'version_spec': version_spec, 'dependencies': [],
                    'error': f"Circular dependency detected: {' -> '.join(cycle_path)}"}
        
        # Add to path
        new_path = path + [package_key]
        
        # Check if we've already visited this exact package+version
        if package_key in self.visited:
            return {'name': package_name, 'version_spec': version_spec, 'dependencies': [], 
                    'already_visited': True}
        
        self.visited.add(package_key)
        
        # Get metadata
        metadata = self.get_package_metadata(package_name)
        
        # Resolve dependencies
        dependencies = []
        for req in metadata.get('requires', []):
            req_name, req_extras, req_version = self.parse_requirement(req)
            # Skip if it's an optional dependency
            if req_extras and 'extra' in req_extras.lower():
                continue
            
            dep_result = self.resolve_dependencies(req_name, req_version, depth + 1, new_path)
            dependencies.append(dep_result)
        
        return {
            'name': package_name,
            'version': metadata.get('Version', 'unknown'),
            'version_spec': version_spec,
            'dependencies': dependencies
        }
    
    def simulate_installation(self, requirements_file):
        """Simulate package installation from a requirements file"""
        packages = []
        
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Remove any comments from the line
                    line = line.split('#')[0].strip()
                    
                    # Skip git/url requirements for this check
                    if 'git+' in line or '://' in line:
                        continue
                    
                    # Parse the requirement
                    package_name, extras, version_spec = self.parse_requirement(line)
                    packages.append((package_name, version_spec))
        except Exception as e:
            print(f"Error reading requirements file: {e}")
            return []
        
        # Resolve all top-level dependencies
        results = []
        for package_name, version_spec in packages:
            print(f"Simulating resolution for {package_name}{version_spec}...")
            result = self.resolve_dependencies(package_name, version_spec)
            results.append(result)
        
        return results

def check_for_cycles(dependency_tree, path=None):
    """Recursive function to check for cycles in the dependency tree"""
    if path is None:
        path = []
    
    cycles = []
    
    # Get package key
    pkg_key = f"{dependency_tree['name']}{dependency_tree.get('version_spec', '')}"
    
    # Check if this package is already in our path (cycle)
    if pkg_key in path:
        cycle_index = path.index(pkg_key)
        cycle = path[cycle_index:] + [pkg_key]
        return [{'cycle': cycle, 'cycle_str': ' -> '.join(cycle)}]
    
    # Check explicit error
    if 'error' in dependency_tree and 'Circular dependency' in dependency_tree['error']:
        return [{'cycle': dependency_tree['error'].split(': ')[1].split(' -> '), 
                 'cycle_str': dependency_tree['error'].split(': ')[1]}]
    
    # Skip if already visited
    if dependency_tree.get('already_visited', False):
        return []
    
    # Add to path and recurse
    new_path = path + [pkg_key]
    
    # Check dependencies
    for dependency in dependency_tree.get('dependencies', []):
        cycles.extend(check_for_cycles(dependency, new_path))
    
    return cycles

def generate_report(resolution_results, output_dir):
    """Generate a human-readable report from resolution results"""
    # Find all cycles
    all_cycles = []
    for result in resolution_results:
        all_cycles.extend(check_for_cycles(result))
    
    # Create report
    report_path = output_dir / "dependency_resolution_report.txt"
    json_path = output_dir / "dependency_resolution.json"
    
    with open(report_path, 'w') as f:
        f.write("# Dependency Resolution Simulation Report\n\n")
        
        # Write cycles summary
        f.write("## Detected Circular Dependencies\n\n")
        if all_cycles:
            for i, cycle in enumerate(all_cycles):
                f.write(f"{i+1}. {cycle['cycle_str']}\n")
        else:
            f.write("No circular dependencies detected.\n")
        
        f.write("\n## Package Resolution Details\n\n")
        
        # Write details for each package
        for result in resolution_results:
            write_package_details(f, result, 0)
    
    # Save the JSON for machine processing
    with open(json_path, 'w') as f:
        json.dump(resolution_results, f, indent=2)
    
    return report_path, json_path, all_cycles

def write_package_details(file, package, level):
    """Write details for a package (recursive helper)"""
    indent = "  " * level
    pkg_name = package['name']
    pkg_version = package.get('version', 'unknown')
    pkg_version_spec = package.get('version_spec', '')
    
    file.write(f"{indent}- {pkg_name}{pkg_version_spec} (resolved: {pkg_version})")
    
    if 'error' in package:
        file.write(f" [ERROR: {package['error']}]\n")
    elif package.get('already_visited', False):
        file.write(" [already visited]\n")
    else:
        file.write("\n")
        
        for dependency in package.get('dependencies', []):
            write_package_details(file, dependency, level + 1)

def main():
    # Check requirements.in file
    requirements_in_path = REPO_ROOT / "docker" / "sesame-tts" / "requirements.in"
    if not requirements_in_path.exists():
        print(f"Error: requirements.in not found at {requirements_in_path}")
        return
    
    print(f"Simulating dependency resolution from {requirements_in_path}...")
    
    # Create resolver and simulate installation
    resolver = DependencyResolver()
    resolution_results = resolver.simulate_installation(requirements_in_path)
    
    # Generate report
    report_path, json_path, cycles = generate_report(resolution_results, OUTPUT_DIR)
    
    print(f"\nDependency resolution simulation complete.")
    print(f"Report available at: {report_path}")
    print(f"JSON data available at: {json_path}")
    
    if cycles:
        print(f"\nWARNING: {len(cycles)} circular dependencies detected:")
        for i, cycle in enumerate(cycles):
            print(f"  {i+1}. {cycle['cycle_str']}")

if __name__ == "__main__":
    main()
