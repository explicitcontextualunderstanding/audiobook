import json
import sys

def main():
    filename = "dependency_tree.json"
    print(f"Attempting to open {filename}...", file=sys.stderr)
    try:
        with open(filename, 'rb') as f:
            # Try reading the first few bytes
            first_bytes = f.read(10)
            print(f"First 10 bytes: {first_bytes}", file=sys.stderr)
            # Rewind to start
            f.seek(0)
            # Try parsing as JSON
            data = json.load(f)
            print(f"Successfully loaded JSON with {len(data)} top-level items", file=sys.stderr)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
