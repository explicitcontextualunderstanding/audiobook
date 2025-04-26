import sys
import json
import os

def node_id(pkg):
    # Use both name and version for uniqueness
    return f'"{pkg["package_name"]}=={pkg.get("installed_version", "unknown")}"'

def walk(pkg, edges, seen, nodes):
    src = node_id(pkg)
    nodes.add(src)
    # Only walk if not seen, but always add node
    if src in seen:
        return
    seen.add(src)
    for dep in pkg.get("dependencies", []):
        dst = node_id(dep)
        nodes.add(dst)
        edges.add((src, dst))
        walk(dep, edges, seen, nodes)

def main():
    # Adding debug info
    print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
    print(f"Python version: {sys.version}", file=sys.stderr)
    
    json_path = "dependency_tree.json"
    abs_path = os.path.abspath(json_path)
    print(f"Absolute path to JSON: {abs_path}", file=sys.stderr)
    
    if not os.path.isfile(json_path) or os.path.getsize(json_path) == 0:
        print(f"Error: {json_path} does not exist or is empty.", file=sys.stderr)
        sys.exit(1)
    
    print(f"File exists and has size: {os.path.getsize(json_path)} bytes", file=sys.stderr)
    
    with open(json_path, 'rb') as f:  # Opening in binary mode for diagnosis
        first_bytes = f.read(20)
        print(f"First 20 bytes: {first_bytes}", file=sys.stderr)
        f.seek(0)  # Reset file pointer
        
        try:
            data = json.load(f)
            print(f"Successfully loaded JSON with {len(data)} top-level items", file=sys.stderr)
        except Exception as e:
            print(f"Error loading {json_path}: {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(1)

    edges = set()
    seen = set()
    nodes = set()
    for pkg in data:
        walk(pkg, edges, seen, nodes)

    # If no edges, still output all nodes
    print("digraph dependencies {")
    for n in nodes:
        print(f"    {n};")
    for src, dst in edges:
        print(f"    {src} -> {dst};")
    print("}")

    print(f"// {len(edges)} edges, {len(nodes)} nodes found", file=sys.stderr)

if __name__ == "__main__":
    main()
