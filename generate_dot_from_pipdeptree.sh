#!/bin/bash
# Generate a Graphviz DOT file from the current Python environment's dependencies

# Activate your environment if needed
# source /path/to/venv/bin/activate

# Generate the DOT file
pipdeptree --graph-output dot > dependency_graph.dot

echo "DOT file generated: dependency_graph.dot"
echo "You can now run: dot -Tpng dependency_graph.dot -o dependency_graph.png"

# If dependency_graph.dot exists but dependency_graph.png does not,
# check if the DOT file is empty or invalid.
if [ ! -s dependency_graph.dot ]; then
  echo "dependency_graph.dot is empty or missing. Regenerate it with:"
  echo "  pipdeptree --graph-output dot > dependency_graph.dot"
  exit 1
fi

# Try rendering again and check for errors
dot -Tpng dependency_graph.dot -o dependency_graph.png

if [ -f dependency_graph.png ]; then
  echo "dependency_graph.png generated successfully."
else
  echo "Failed to generate dependency_graph.png. Check dependency_graph.dot for errors."
  echo "You can validate the DOT file with:"
  echo "  dot -Tpng dependency_graph.dot -o /dev/null"
fi
