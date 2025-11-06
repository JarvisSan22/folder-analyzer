# Folder Analyzer - Multi-Media Analysis Tool

A comprehensive media analysis tool that processes videos, images, and entire folders using vision models like Llama3.2 Vision and OpenAI's Whisper. Originally forked from [video-analyzer](https://github.com/byjlw/video-analyzer), this repository has been enhanced with image processing and batch folder processing capabilities.

## Table of Contents
- [Features](#features)
- [What's New](#whats-new)
- [Requirements](#requirements)
  - [System Requirements](#system-requirements)
  - [Installation](#installation)
  - [Ollama Setup](#ollama-setup)
  - [OpenAI-compatible API Setup](#openai-compatible-api-setup-optional)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Video Analysis](#video-analysis)
  - [Image Analysis](#image-analysis)
  - [Folder Processing](#folder-processing)
  - [Sample Output](#sample-output)
- [Design](#design)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Output](#output)
- [Roadmap](#roadmap)
- [Uninstallation](#uninstallation)
- [License](#license)
- [Contributing](#contributing)
- [Credits](#credits)

## Features

### Core Features
- 💻 **Run completely locally** - no cloud services or API keys needed
- ☁️ **Or leverage cloud APIs** - use any OpenAI-compatible LLM service (OpenRouter, OpenAI, etc) for speed and scale
- 🎬 **Video Analysis** - intelligent key frame extraction and analysis
- 🖼️ **Image Analysis** - analyze individual images or entire directories
- 📁 **Batch Processing** - process folders containing mixed media (videos and images)
- 📊 **High-quality transcription** - using OpenAI's Whisper for video audio
- 👁️ **Vision analysis** - using Ollama/Llama3.2 11B Vision or cloud models
- 📝 **Natural language descriptions** - of video and image content
- 📄 **Automatic handling** - of poor quality audio in videos
- 📊 **Detailed JSON output** - of all analysis results
- ⚙️ **Highly configurable** - through command line arguments or config file
- 📋 **Comprehensive logging** - with 5 configurable log levels for debugging and monitoring

### Advanced Features
- ⏱️ **Performance tracking** - processing time for each file
- 🔒 **API key masking** - automatic security in logs
- 🎯 **Custom prompts** - tailor analysis to your needs
- 🔄 **Resume capability** - skip already processed files
- 📈 **Progress tracking** - real-time status updates

## What's New

This fork extends the original video-analyzer with:

### ✨ Image Analysis (`image_analyzer/`)
- Standalone image analysis using the same vision models
- Support for multiple image formats (JPG, PNG, GIF, WEBP, BMP)
- Reuses video-analyzer's client infrastructure and prompts
- Command-line interface matching video-analyzer patterns
- Batch processing for image directories

### ✨ Folder Processing (`process_folder/`)
- Unified processing for folders containing both videos and images
- Automatic file type detection and routing
- Individual output directories for each processed file
- Comprehensive results aggregation
- Processing time tracking per file
- Consolidated JSON output with all results

### ✨ Enhanced Logging
- Comprehensive logging across all modules
- 5 configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Consistent log format: `timestamp - level - message`
- Performance tracking and timing information
- Full exception stack traces for debugging
- API key masking for security

## Requirements

### System Requirements
- Python 3.11 or higher
- FFmpeg (required for audio processing)
- When running LLMs locally (not necessary when using cloud APIs):
  - At least 16GB RAM (32GB recommended)
  - GPU with at least 12GB VRAM or Apple M Series with at least 32GB

### Installation

1. Clone the repository:
```bash
git clone https://github.com/JarvisSan22/folder-analyzer.git
cd folder-analyzer
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:
```bash
pip install .  # For regular installation
# OR
pip install -e .  # For development installation
```

4. Install FFmpeg:
- Ubuntu/Debian:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```
- macOS:
  ```bash
  brew install ffmpeg
  ```
- Windows:
  ```bash
  choco install ffmpeg
  ```

### Ollama Setup

1. Install Ollama following the instructions at [ollama.ai](https://ollama.ai)

2. Pull the default vision model:
```bash
ollama pull llama3.2-vision
```

3. Start the Ollama service:
```bash
ollama serve
```

### OpenAI-compatible API Setup (Optional)

If you want to use OpenAI-compatible APIs (like OpenRouter or OpenAI) instead of Ollama:

1. Get an API key from your provider:
   - [OpenRouter](https://openrouter.ai)
   - [OpenAI](https://platform.openai.com)

2. Configure via command line or environment variables:
   ```bash
   # Set environment variable
   export OPENAI_API_KEY="your-api-key"
   
   # Or pass directly via command line
   video-analyzer video.mp4 --client openai_api --api-key your-key --api-url https://openrouter.ai/api/v1 --model gpt-4o
   ```

   Or add to config/config.json:
   ```json
   {
     "clients": {
       "default": "openai_api",
       "openai_api": {
         "api_key": "your-api-key",
         "api_url": "https://openrouter.ai/api/v1"
       }
     }
   }
   ```

**Note:** With OpenRouter, you can use Llama 3.2 11B Vision for free by adding `:free` to the model name.

## Usage

### Quick Start

```bash
# Video analysis (local with Ollama)
video-analyzer video.mp4

# Image analysis (local with Ollama)
image-analyzer photo.jpg

# Folder processing (mixed videos and images)
python -m process_folder.folder_processor /path/to/media/folder
```

### Video Analysis

```bash
# Basic video analysis
video-analyzer video.mp4

# With cloud API (OpenRouter)
video-analyzer video.mp4 \
    --client openai_api \
    --api-key your-key \
    --api-url https://openrouter.ai/api/v1 \
    --model meta-llama/llama-3.2-11b-vision-instruct:free

# With custom prompt and specific Whisper model
video-analyzer video.mp4 \
    --prompt "What activities are happening in this video?" \
    --whisper-model large

# With debug logging
video-analyzer video.mp4 --log-level DEBUG

# Process only first 30 seconds
video-analyzer video.mp4 --duration 30
```

### Image Analysis

```bash
# Basic image analysis
image-analyzer photo.jpg

# With custom prompt
image-analyzer photo.jpg --prompt "What objects are in this image?"

# With cloud API
image-analyzer photo.jpg \
    --client openai_api \
    --api-key your-key \
    --model gpt-4o

# With debug logging
image-analyzer photo.jpg --log-level DEBUG

# Custom output directory
image-analyzer photo.jpg --output-dir ./my-results
```

### Folder Processing

```bash
# Process entire folder (videos and images)
python -m process_folder.folder_processor /path/to/media

# With specific output directory
python -m process_folder.folder_processor /path/to/media --output-dir ./results

# With cloud API
python -m process_folder.folder_processor /path/to/media --model gpt-4o

# With custom prompt for all files
python -m process_folder.folder_processor /path/to/media \
    --prompt "Describe the main subjects in this media"

# With debug logging
LOG_LEVEL=DEBUG python -m process_folder.folder_processor /path/to/media
```

### Logging Control

All tools support configurable logging:

```bash
# Image/Video analyzer
video-analyzer video.mp4 --log-level DEBUG    # Maximum detail
video-analyzer video.mp4 --log-level INFO     # Normal (default)
video-analyzer video.mp4 --log-level ERROR    # Errors only

# Folder processor
LOG_LEVEL=DEBUG python -m process_folder.folder_processor /path/to/media
LOG_LEVEL=INFO python -m process_folder.folder_processor /path/to/media
```

## Design

The system operates in three main modes:

### 1. Video Analysis
Three-stage pipeline:
1. **Frame Extraction & Audio Processing**
   - Uses OpenCV to extract key frames
   - Processes audio using Whisper for transcription
   - Handles poor quality audio with confidence checks

2. **Frame Analysis**
   - Analyzes each frame using vision LLM
   - Each analysis includes context from previous frames
   - Maintains chronological progression

3. **Video Reconstruction**
   - Combines frame analyses chronologically
   - Integrates audio transcript
   - Creates comprehensive video description

### 2. Image Analysis
Single-stage pipeline:
1. **Image Analysis**
   - Loads image and converts to appropriate format
   - Sends to vision LLM with custom prompt
   - Returns detailed description

### 3. Folder Processing
Batch processing pipeline:
1. **File Discovery**
   - Scans folder for videos and images
   - Categorizes by file type

2. **Batch Processing**
   - Routes videos to video-analyzer
   - Routes images to image-analyzer
   - Tracks progress and timing

3. **Results Aggregation**
   - Combines all results into single JSON
   - Includes processing times
   - Generates summary statistics

![Design](docs/design.png)

## Project Structure

```
folder-analyzer/
├── video_analyzer/          # Original video analysis (core)
│   ├── __init__.py
│   ├── cli.py              # Video CLI interface
│   ├── core.py             # Video processing logic
│   ├── frame.py            # Frame extraction
│   ├── audio_processor.py  # Audio/Whisper handling
│   ├── analyzer.py         # Frame analysis
│   └── clients/            # LLM client implementations
│       ├── ollama.py
│       └── generic_openai_api.py
│
├── image_analyzer/          # NEW: Image analysis module
│   ├── __init__.py
│   ├── cli.py              # Image CLI interface
│   └── core.py             # Image processing logic
│
├── process_folder/          # NEW: Batch folder processing
│   ├── __init__.py
│   └── folder_processor.py # Batch processing logic
│
├── prompts/                 # Prompt templates
│   ├── frame_analysis.txt  # For video frames
│   ├── video_reconstruction.txt
│   └── image.txt           # NEW: For images
│
├── config/                  # Configuration files
│   └── config.json
│
├── docs/                    # Documentation
│   ├── DESIGN.md
│   ├── USAGES.md
│   └── sample_analysis.json
│
├── setup.py                 # Installation configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

The tool uses a cascading configuration system with command line arguments taking highest priority, followed by user config (config/config.json), and finally the default config.

### Example config.json
```json
{
  "clients": {
    "default": "ollama",
    "ollama": {
      "url": "http://localhost:11434",
      "model": "llama3.2-vision"
    },
    "openai_api": {
      "api_key": "your-api-key",
      "api_url": "https://openrouter.ai/api/v1",
      "model": "meta-llama/llama-3.2-11b-vision-instruct:free"
    }
  },
  "audio": {
    "whisper_model": "medium",
    "device": "cpu",
    "language": null
  },
  "frames": {
    "per_minute": 60
  },
  "output_dir": "output"
}
```

## Output

### Video Analysis
Generates `output/analysis.json` containing:
- Metadata (model, whisper version, frame count, etc.)
- Audio transcript with segments
- Frame-by-frame analysis
- Final video description

### Image Analysis
Generates `output/image_analysis.json` containing:
- Image metadata (path, size, MIME type)
- Analysis details (client, model, prompt)
- Detailed description

### Folder Processing
Generates `output/media_descriptions.json` containing:
- Results for all processed files
- Processing time per file
- Success/failure status
- Descriptions or error messages
- File paths and types

### Sample Output
```
The video begins with a person with long blonde hair, wearing a pink t-shirt and yellow shorts, standing in front of a black plastic tub or container on wheels. The ground appears to be covered in wood chips.

As the video progresses, the person remains facing away from the camera, looking down at something inside the tub...
```

Full sample output available in `docs/sample_analysis.json`

## Roadmap

### Planned Features

#### 📄 PDF Processing (To-Do)
- Extract text from PDF documents
- Analyze PDF images and diagrams
- Generate summaries of PDF content
- Support for multi-page PDFs
- Integration with folder processing

#### 📝 Text File Processing (To-Do)
- Process plain text files (.txt, .md)
- Generate summaries of text content
- Extract key information
- Support for multiple text encodings
- Batch processing for text documents

#### 🎯 Future Enhancements
- Support for audio-only files (MP3, WAV, etc.)
- Multi-language support for transcription
- Custom model fine-tuning support
- Web interface for easier access
- Real-time processing capabilities
- Parallel processing for faster batch operations

### Contributions Welcome!
We're actively looking for contributions to implement PDF and text processing. See [Contributing](#contributing) section below.

## Uninstallation

To uninstall the package:
```bash
pip uninstall folder-analyzer
# or if installed as video-analyzer
pip uninstall video-analyzer
```

## License

Apache License 2.0

## Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues**: Use GitHub Issues to report bugs or suggest features
2. **Submit Pull Requests**: 
   - Fork the repository
   - Create a feature branch
   - Make your changes with tests
   - Submit a PR with a clear description
3. **Improve Documentation**: Help us improve docs and examples
4. **Add Features**: Especially interested in PDF and text processing implementations

### Development Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/folder-analyzer.git
cd folder-analyzer

# Install in development mode
pip install -e .

# Make changes and test
python -m pytest  # If you add tests
```

## Credits

### Original Project
This project is forked from [video-analyzer](https://github.com/byjlw/video-analyzer) by [@byjlw](https://github.com/byjlw). The core video analysis functionality and design patterns are from the original project.

### Enhancements by [@JarvisSan22](https://github.com/JarvisSan22)
- Image analysis module (`image_analyzer/`)
- Folder processing module (`process_folder/`)
- Enhanced logging across all modules
- Batch processing capabilities
- Additional documentation and examples

### Technologies Used
- [Ollama](https://ollama.ai) - Local LLM inference
- [OpenAI Whisper](https://github.com/openai/whisper) - Audio transcription
- [Llama 3.2 Vision](https://huggingface.co/meta-llama/Llama-3.2-11B-Vision) - Vision language model
- [OpenCV](https://opencv.org/) - Video frame extraction
- [FFmpeg](https://ffmpeg.org/) - Audio processing

## Acknowledgments

Special thanks to:
- [@byjlw](https://github.com/byjlw) for creating the original video-analyzer
- The Ollama team for making local LLM inference accessible
- The OpenAI team for the Whisper model
- Meta for the Llama 3.2 Vision model
- All contributors and users of this project

---

## Quick Links

- [Original Video Analyzer](https://github.com/byjlw/video-analyzer)
- [Folder Analyzer (This Fork)](https://github.com/JarvisSan22/folder-analyzer)
- [Report Issues](https://github.com/JarvisSan22/folder-analyzer/issues)
- [Documentation](docs/)

---

