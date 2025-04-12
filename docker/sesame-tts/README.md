# Sesame CSM Text-to-Speech

This container provides the Sesame CSM text-to-speech engine for high-quality audiobook generation.

## Model Information

Sesame CSM is a controllable speech model for high-quality text-to-speech synthesis, 
offering several voice presets and speaking styles.

## Usage

```bash
# Run the container with volume mounts
./jetson-containers run --volume ~/audiobook_data:/audiobook_data \
  --volume ~/audiobook:/books \
  --workdir /audiobook_data $(./autotag sesame-tts)