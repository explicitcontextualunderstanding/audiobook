#!/bin/bash
# Remove all dangling (untagged) Docker images to free up disk space

echo "Removing all dangling Docker images..."
docker image prune -f

echo "Removing all <none> (untagged) images..."
docker images --filter "dangling=true" -q | xargs -r docker rmi

# Optionally, remove old sesame-tts-analysis images except the latest
echo "Removing old sesame-tts-analysis images except the latest..."
docker images | grep 'sesame-tts-analysis' | awk 'NR>1 {print $3}' | xargs -r docker rmi

echo "Docker image cleanup complete."
