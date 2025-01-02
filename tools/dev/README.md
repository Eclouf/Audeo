# Development Tools

This directory contains tools and scripts used during development and packaging of the Audeo application.

## Scripts

### download_ffmpeg.py

Downloads FFmpeg binaries for different platforms and architectures:

- Windows (x64)
- Linux (x64, ARM64)
- macOS binaries need to be downloaded manually from <https://osxexperts.net/>

Usage:

```bash
python tools/dev/download_ffmpeg.py
```

This script should be run during initial setup, during packaging or when updating FFmpeg binaries. The binaries are placed in the correct locations within the project structure for use by the application.
