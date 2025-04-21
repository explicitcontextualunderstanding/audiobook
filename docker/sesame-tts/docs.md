# Sesame CSM Text-to-Speech for Audiobooks

This container provides the Sesame CSM text-to-speech model optimized for audiobook generation on Jetson platforms. It is part of a larger audiobook generation project described in the [Audiobook Project Plan](../../audiobook-plan.md).

## Features

- High-quality neural text-to-speech with natural prosody
- Optimized for Jetson devices with CUDA acceleration
- Support for long-form content like books and articles
- Text segmentation with appropriate pauses and intonation
- Audio watermarking capability

## Hardware Requirements

- NVIDIA Jetson device with JetPack 6.0+
- Recommended: at least 8GB RAM
- Recommended: NVMe storage for model files and audio output
- CUDA 11.8 or higher

## Usage Examples

### Basic TTS Generation

```bash
# Run the container with interactive shell
./jetson-containers run sesame-tts

# Inside the container
python3 -c "
import sys
sys.path.append('/opt/csm')
from generator import load_csm_1b, Generator

# Load model
model = load_csm_1b(device='cuda')
generator = Generator(model)

# Generate speech
audio = generator.generate_audio('Hello, this is a test of the Sesame text to speech system.')

# Save to file
generator.save_audio(audio, '/audiobook_data/test.wav')
"
```

### Processing an Ebook

```bash
# Mount your books directory and output directory
./jetson-containers run \
  -v /path/to/your/books:/books \
  -v /path/to/output:/audiobook_data \
  sesame-tts

# Inside the container
python3 -c "
import sys
sys.path.append('/opt/csm')
from audiobook_generator import AudiobookGenerator

# Initialize the generator
generator = AudiobookGenerator(
    model_device='cuda',
    segment_length=1000,  # characters per segment
    add_watermark=True
)

# Process a book
generator.process_book(
    book_path='/books/my_book.epub',
    output_dir='/audiobook_data/my_book',
    chapters=[1, 2, 3]  # optional: process specific chapters only
)
"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODELS_DIR` | Directory for storing model files | `/models` |
| `AUDIOBOOK_DATA` | Directory for output audio files | `/audiobook_data` |
| `BOOKS_DIR` | Directory for input books | `/books` |
| `CUDA_MODULE_LOADING` | CUDA module loading mode | `LAZY` |
| `TORCH_USE_CUDA_DSA` | Enable CUDA Direct System Access | `1` |

## Performance Tips

1. **Memory Management**: CSM models require significant GPU memory. If you experience out-of-memory errors:
   - Reduce batch size
   - Process shorter text segments
   - Use a swap file on NVMe for additional memory

2. **Storage Performance**: For processing long books:
   - Use NVMe storage for both input and output to avoid SD card wear
   - Pre-segment long texts into smaller chunks

3. **Temperature and Throttling**: TTS generation is computationally intensive:
   - Ensure adequate cooling for your Jetson device
   - Consider adding a fan if running extended generation jobs
   - Monitor thermal throttling with `tegrastats`

4. **Throughput Optimization**:
   - Process multiple short segments in parallel rather than sequential long segments
   - Use the `--runtime nvidia` flag with Docker for best GPU performance

## Troubleshooting

### Common Issues

- **Model Loading Fails**: Verify CUDA is available and check your device has sufficient memory
- **Slow Generation**: Check for thermal throttling using `tegrastats`
- **Audio Quality Issues**: Try different sampling rates (22050Hz or 44100Hz)
- **Book Format Problems**: The container supports EPUB, PDF, and TXT formats. Convert other formats first

### Logs and Debugging

Enable verbose logging by setting the environment variable:
```bash
export CSM_DEBUG=1
```

## Resources

- [Sesame CSM GitHub Repository](https://github.com/SesameAILabs/csm)
- [Jetson Containers Documentation](https://github.com/dusty-nv/jetson-containers)
