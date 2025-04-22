#!/usr/bin/env python3
"""
Compares dependency analysis from build-time with runtime container extraction
to identify differences and potential issues.
"""

import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

# Output directory
REPO_ROOT = Path(__file__).parent.parent.parent
BUILD_ANALYSIS_DIR = REPO_ROOT / "dependency_artifacts"
CONTAINER_ANALYSIS_DIR = REPO_ROOT / "dependency_artifacts" / "container_extracted"
OUTPUT_DIR = REPO_ROOT / "dependency_artifacts" / "comparison"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Key packages to focus on
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

def parse_pip_freeze(filepath):
    """Parse pip freeze output into a dictionary of package:version"""
    packages = {}
    
    if not Path(filepath).exists():
        return packages
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-e '):
                continue
                
            if '==' in line:
                name, version = line.split('==', 1)
                packages[name.lower()] = version
    
    return packages

def parse_dependency_tree(filepath):
    """Parse dependency tree output into a structured dictionary"""
    dependencies = {}
    
    if not Path(filepath).exists():
        return dependencies
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Parse the tree structure
    current_pkg = None
    
    for line in content.split('\n'):
        if not line.strip():
            continue
            
        # Check if this is a top-level package
        if not line.startswith(' '):
            match = re.match(r'([a-zA-Z0-9_\-\.]+)==([^ ]+)', line)
            if match:
                pkg_name = match.group(1).lower()
                version = match.group(2)
                current_pkg = pkg_name
                dependencies[current_pkg] = {
                    'version': version,
                    'dependencies': []
                }
        # This is a dependency of the current package
        elif current_pkg and line.startswith('  '):
            match = re.match(r'\s+[\\|\-]+ ([a-zA-Z0-9_\-\.]+)([<>=~!]+[^ ]+)?', line)
            if match:
                dep_name = match.group(1).lower()
                dep_req = match.group(2) if match.group(2) else ''
                dependencies[current_pkg]['dependencies'].append({
                    'name': dep_name,
                    'requirement': dep_req
                })
    
    return dependencies

def parse_conflicts(filepath):
    """Parse dependency conflicts from pipdeptree --warn output"""
    conflicts = []
    
    if not Path(filepath).exists():
        return conflicts
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract conflict sections
    conflict_sections = re.findall(r'(.*?!\s+.*?)(?=\n\n|\Z)', content, re.DOTALL)
    
    for section in conflict_sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Extract the conflict information
        pkg_line = lines[0]
        match = re.match(r'([a-zA-Z0-9_\-\.]+).*?!', pkg_line)
        if match:
            pkg_name = match.group(1).lower()
            conflicts.append({
                'package': pkg_name,
                'description': pkg_line,
                'details': lines[1:] if len(lines) > 1 else []
            })
    
    return conflicts

def generate_comparison_report():
    """Generate a comparison report between build-time and runtime analysis"""
    
    # Check if both directories exist
    if not BUILD_ANALYSIS_DIR.exists():
        print(f"Error: Build analysis directory {BUILD_ANALYSIS_DIR} does not exist.")
        print("Run ./scripts/dependency/analyze_all.sh first.")
        return False
        
    if not CONTAINER_ANALYSIS_DIR.exists():
        print(f"Error: Container analysis directory {CONTAINER_ANALYSIS_DIR} does not exist.")
        print("Run ./scripts/dependency/extract_from_container.sh first.")
        return False
    
    # Get package versions from both analyses
    build_packages = parse_pip_freeze(BUILD_ANALYSIS_DIR / "frozen_deps.txt")
    container_packages = parse_pip_freeze(CONTAINER_ANALYSIS_DIR / "pip_freeze.txt")
    
    # Get dependency trees
    build_deps = parse_dependency_tree(BUILD_ANALYSIS_DIR / "dependency_tree.txt")
    container_deps = parse_dependency_tree(CONTAINER_ANALYSIS_DIR / "dependency_tree.txt")
    
    # Get conflicts
    build_conflicts = parse_conflicts(BUILD_ANALYSIS_DIR / "dependency_conflicts.txt")
    container_conflicts = parse_conflicts(CONTAINER_ANALYSIS_DIR / "dependency_conflicts.txt")
    
    # Compare package versions
    version_diffs = {}
    missing_in_build = []
    missing_in_container = []
    
    all_packages = set(list(build_packages.keys()) + list(container_packages.keys()))
    
    for pkg in all_packages:
        build_ver = build_packages.get(pkg)
        container_ver = container_packages.get(pkg)
        
        if build_ver and not container_ver:
            missing_in_container.append((pkg, build_ver))
        elif container_ver and not build_ver:
            missing_in_build.append((pkg, container_ver))
        elif build_ver != container_ver:
            version_diffs[pkg] = {
                'build': build_ver,
                'container': container_ver
            }
    
    # Create the comparison report
    report_path = OUTPUT_DIR / "comparison_report.md"
    
    with open(report_path, 'w') as f:
        f.write("# Dependency Analysis Comparison Report\n\n")
        f.write("This report compares dependency analysis results from build-time with runtime container extraction.\n\n")
        
        # System information
        f.write("## System Information\n\n")
        
        if (CONTAINER_ANALYSIS_DIR / "system_info.txt").exists():
            with open(CONTAINER_ANALYSIS_DIR / "system_info.txt", 'r') as sys_info:
                f.write("```\n")
                f.write(sys_info.read())
                f.write("```\n\n")
        
        # Summary section
        f.write("## Summary\n\n")
        f.write(f"- Total packages in build analysis: {len(build_packages)}\n")
        f.write(f"- Total packages in container: {len(container_packages)}\n")
        f.write(f"- Packages with version differences: {len(version_diffs)}\n")
        f.write(f"- Packages missing in container: {len(missing_in_build)}\n")
        f.write(f"- Packages missing in build analysis: {len(missing_in_container)}\n")
        f.write(f"- Conflicts detected in build analysis: {len(build_conflicts)}\n")
        f.write(f"- Conflicts detected in container: {len(container_conflicts)}\n")
        f.write("\n")
        
        # Key packages comparison
        f.write("## Key Packages Comparison\n\n")
        f.write("| Package | Build Version | Container Version | Match | Notes |\n")
        f.write("|---------|---------------|-------------------|-------|-------|\n")
        
        for pkg in KEY_PACKAGES:
            build_ver = build_packages.get(pkg, "Not found")
            container_ver = container_packages.get(pkg, "Not found")
            
            match = "✅" if build_ver == container_ver else "❌"
            notes = ""
            
            if pkg in version_diffs:
                notes = "Version mismatch"
            elif pkg in [p for p, _ in missing_in_container]:
                notes = "Missing in container"
            elif pkg in [p for p, _ in missing_in_build]:
                notes = "Missing in build analysis"
            
            f.write(f"| {pkg} | {build_ver} | {container_ver} | {match} | {notes} |\n")
        
        f.write("\n")
        
        # Version differences section
        if version_diffs:
            f.write("## Version Differences\n\n")
            f.write("| Package | Build Version | Container Version |\n")
            f.write("|---------|---------------|-------------------|\n")
            
            for pkg, versions in sorted(version_diffs.items()):
                f.write(f"| {pkg} | {versions['build']} | {versions['container']} |\n")
            
            f.write("\n")
        
        # Missing packages sections
        if missing_in_container:
            f.write("## Packages Missing in Container\n\n")
            f.write("| Package | Build Version |\n")
            f.write("|---------|---------------|\n")
            
            for pkg, version in sorted(missing_in_container):
                f.write(f"| {pkg} | {version} |\n")
            
            f.write("\n")
        
        if missing_in_build:
            f.write("## Packages Missing in Build Analysis\n\n")
            f.write("| Package | Container Version |\n")
            f.write("|---------|-------------------|\n")
            
            for pkg, version in sorted(missing_in_build):
                f.write(f"| {pkg} | {version} |\n")
            
            f.write("\n")
        
        # Dependency conflicts section
        f.write("## Dependency Conflicts\n\n")
        
        f.write("### Build Analysis Conflicts\n\n")
        if build_conflicts:
            for i, conflict in enumerate(build_conflicts):
                f.write(f"{i+1}. **{conflict['package']}**: {conflict['description']}\n")
                for detail in conflict['details']:
                    f.write(f"   - {detail}\n")
                f.write("\n")
        else:
            f.write("No conflicts detected in build analysis.\n\n")
        
        f.write("### Container Conflicts\n\n")
        if container_conflicts:
            for i, conflict in enumerate(container_conflicts):
                f.write(f"{i+1}. **{conflict['package']}**: {conflict['description']}\n")
                for detail in conflict['details']:
                    f.write(f"   - {detail}\n")
                f.write("\n")
        else:
            f.write("No conflicts detected in container.\n\n")
        
        # Recommendations section
        f.write("## Recommendations\n\n")
        
        if version_diffs:
            f.write("### Version Differences\n\n")
            f.write("Consider updating your requirements.in file to match the versions actually used in the container:\n\n")
            
            for pkg, versions in sorted(version_diffs.items()):
                if pkg in KEY_PACKAGES:
                    f.write(f"- Change `{pkg}{build_packages.get(pkg, '')}` to `{pkg}>={versions['container']}`\n")
            
            f.write("\n")
        
        if build_conflicts or container_conflicts:
            f.write("### Dependency Conflicts\n\n")
            f.write("Review and resolve the dependency conflicts identified above. Consider:\n\n")
            f.write("1. Updating packages with conflicts to newer versions\n")
            f.write("2. Adding more specific version constraints to resolve conflicts\n")
            f.write("3. Separating conflicting package installations into separate steps\n\n")
        
        # Final advice
        f.write("## Next Steps\n\n")
        f.write("1. Review the full dependency tree files for more details\n")
        f.write("2. Update your requirements.in file with the recommended changes\n")
        f.write("3. Rebuild the Docker container to verify the changes\n")
        f.write("4. Run the extraction and comparison again to confirm resolution\n\n")
        
        f.write("## Files to Review\n\n")
        f.write(f"- Build dependency tree: {BUILD_ANALYSIS_DIR}/dependency_tree.txt\n")
        f.write(f"- Container dependency tree: {CONTAINER_ANALYSIS_DIR}/dependency_tree.txt\n")
        f.write(f"- Build conflicts: {BUILD_ANALYSIS_DIR}/dependency_conflicts.txt\n")
        f.write(f"- Container conflicts: {CONTAINER_ANALYSIS_DIR}/dependency_conflicts.txt\n")
    
    # Create JSON data for machine processing
    json_path = OUTPUT_DIR / "comparison_data.json"
    
    json_data = {
        'summary': {
            'build_package_count': len(build_packages),
            'container_package_count': len(container_packages),
            'version_diff_count': len(version_diffs),
            'missing_in_container_count': len(missing_in_container),
            'missing_in_build_count': len(missing_in_build),
            'build_conflict_count': len(build_conflicts),
            'container_conflict_count': len(container_conflicts)
        },
        'key_packages': {pkg: {
            'build_version': build_packages.get(pkg, "Not found"),
            'container_version': container_packages.get(pkg, "Not found"),
            'match': build_packages.get(pkg) == container_packages.get(pkg)
        } for pkg in KEY_PACKAGES},
        'version_diffs': version_diffs,
        'missing_in_container': missing_in_container,
        'missing_in_build': missing_in_build,
        'build_conflicts': build_conflicts,
        'container_conflicts': container_conflicts
    }
    
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"Comparison report generated at {report_path}")
    print(f"JSON data available at {json_path}")
    
    return True

def main():
    print("Generating comparison report between build-time and runtime analysis...")
    success = generate_comparison_report()
    
    if success:
        print("\nComparison complete!")
        print(f"Report available at: {OUTPUT_DIR}/comparison_report.md")
        print(f"JSON data available at: {OUTPUT_DIR}/comparison_data.json")
        
        print("\nKey findings:")
        
        # Load the JSON data for a quick summary
        with open(OUTPUT_DIR / "comparison_data.json", 'r') as f:
            data = json.load(f)
        
        version_diffs = data['version_diffs']
        key_version_diffs = {k: v for k, v in version_diffs.items() if k in KEY_PACKAGES}
        
        if key_version_diffs:
            print("\nKey package version differences:")
            for pkg, versions in key_version_diffs.items():
                print(f"- {pkg}: {versions['build']} (build) vs {versions['container']} (container)")
        
        build_conflicts = data['build_conflicts']
        container_conflicts = data['container_conflicts']
        
        if build_conflicts and not container_conflicts:
            print("\nGood news! Build-time conflicts were resolved in the container.")
        elif container_conflicts and not build_conflicts:
            print("\nWarning: New conflicts appeared in the container that weren't in the build analysis.")
        elif container_conflicts:
            print(f"\nWarning: {len(container_conflicts)} dependency conflicts still exist in the container.")
    else:
        print("\nFailed to generate comparison report.")
        print("Please run the build analysis and container extraction first:")
        print("1. ./scripts/dependency/analyze_all.sh")
        print("2. ./scripts/dependency/extract_from_container.sh")

if __name__ == "__main__":
    main()
