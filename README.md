# EchoShift

EchoShift is a multimedia processing pipeline designed to handle the end-to-end transformation of video content through downloading, audio extraction, transcription, translation, and speech synthesis.

## Core Features
- **YouTube Downloader:** Download high-quality video content directly from YouTube URLs.
- **Audio Extraction:** Isolate audio tracks from video files (e.g., MP4 to MP3/WAV).
- **Speech-to-Text (STT):** High-accuracy transcription of audio content.
- **Translation:** Translate transcribed text into multiple target languages.
- **Text-to-Speech (TTS):** Generate natural-sounding voiceovers from translated text.

## Pipeline Overview
1.  **Download:** Fetch source video from YouTube.
2.  **Extract:** Pull the audio stream from the downloaded video file.
3.  **Transcribe:** Convert the extracted audio into a text script.
4.  **Translate:** Process the script into the desired language.
5.  **Synthesize:** Create a new audio file using AI-driven voice generation.

## Current Progress
- [x] Initial Project Setup
- [x] Secure API Key Management (OpenRouter Integration)
- [ ] YouTube Downloader Module
- [ ] Video-to-Audio Extraction Module
- [ ] Transcription Module
- [ ] Translation Module
- [ ] TTS Generation Module

## Prerequisites
- Python 3.x
- FFmpeg (for media processing)
- OpenRouter API Key (for LLM-based tasks)

## Setup

1. **Environment Preparation:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   ```bash
   cp .env.example .env
   ```
   Add your `OPENROUTER_API_KEY` to the `.env` file to enable translation and advanced processing features.

## Usage
*(Modules are currently under development. Detailed usage instructions for each pipeline stage will be added as they are implemented.)*

Check your API status:
```bash
./venv/bin/python3 check_openrouter.py
```

## License
MIT
