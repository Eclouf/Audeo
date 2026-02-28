# <p align="center">![image](https://github.com/Eclouf/Audeo/blob/5335686113f9325f0d3bd00a0bb15b22a8c5f716/src/audeo2/ressources/audeo.png)</p>

# <p align="center">Audeo</p>



A modern desktop application for downloading and managing audio and video content from online platforms.

## Overview

Audeo is a user-friendly application built with Python and Toga that enables users to download audio and video content from various online sources. The application provides a queue-based management system, download tracking, and a clean graphical interface for managing your media library.

**Version:** 0.6.0  
**Python:** >= 3.10

## Features

- 🎵 **Audio Downloads**: Download audio tracks from multiple online platforms
- 🎬 **Video Downloads**: Download videos with support for various formats
- 📋 **Video Information Explorer**: Analyze videos without downloading - view metadata, available formats, and technical details
- 🔍 **Metadata Extraction**: Extract comprehensive video information including title, duration, uploader, views, and description
- 📊 **Format Analysis**: Interactive table showing all available formats with resolution, codec, file size, and FPS
- ⚡ **Direct Download**: Launch downloads directly from the information view after analysis
- ✅ **Download History**: Track completed downloads with a finished items view
- ⚙️ **Configurable Settings**: Customize download options, proxy settings, and application preferences
- 🔄 **Auto-Update System**: Automatic update checking and installation with multi-platform support
- � **Multi-language Support**: Full internationalization with support for 8 languages (English, French, Spanish, Italian, Portuguese, Polish, Russian, German)
- � **Modern UI**: Clean and intuitive user interface built with Toga
- 📊 **Download Management**: Monitor active downloads in real-time

## Project Structure

```
audeo/
├── src/audeo2/                      # Main package
│   ├── __init__.py                  # Package initialization
│   ├── app.py                       # Application entry point and main window
│   ├── constants.py                  # Application constants and enums
│   ├── download_models.py            # Data classes for download management
│   ├── options_formatter.py         # yt-dlp options generation logic
│   ├── download_manager.py          # Core download management logic
│   ├── settings.py                  # Application configuration and constants
│   ├── update.py                    # Auto-update system with GitHub API integration
│   ├── widgets.py                   # Reusable UI components
│   ├── ressources/                  # Asset files
│   │   └── pictures/
│   │       ├── audio/               # Audio-related icons and images
│   │       ├── settings/            # Settings-related icons
│   │       └── video/               # Video-related icons
│   ├── locales/                     # Translation files
│   │   ├── de/LC_MESSAGES/        # German translations
│   │   ├── en/LC_MESSAGES/        # English translations
│   │   ├── es/LC_MESSAGES/        # Spanish translations
│   │   ├── fr/LC_MESSAGES/        # French translations
│   │   ├── it/LC_MESSAGES/        # Italian translations
│   │   ├── pl/LC_MESSAGES/        # Polish translations
│   │   ├── pt/LC_MESSAGES/        # Portuguese translations
│   │   └── ru/LC_MESSAGES/        # Russian translations
│   └── views/                       # Application views/screens
│       ├── __init__.py              # Views package initialization
│       ├── downloads.py             # Active downloads view
│       ├── finished.py              # Completed downloads history
│       ├── info.py                  # Video information and analysis view
│       └── settings.py              # Settings/preferences view
├── pyproject.toml                   # Project metadata and dependencies
├── README.md                        # This file
├── CHANGELOG                        # Version history
├── LICENSE                          # License information
├── convert_cli_to_ytdlp.py         # Utility script for conversion
└── installer/                       # Installation packages
    └── windows/
        └── Audeo.iss               # Windows Inno Setup installer script
```

## Core Components

### app.py
The main entry point of the application. This module initializes the Toga application, creates the main window, and orchestrates the different views. It manages the overall application lifecycle and navigation between different screens.

**Key Functions:**
- Application initialization
- Main window setup
- View management
- Event handling

### download_models.py
**New in v0.6.0** - Data classes for download management. This module defines the core data structures used throughout the application for managing downloads and tracking progress.

**Key Classes:**
- `DownloadProgress`: Tracks real-time download status, progress, and metadata
- `DownloadTask`: Represents download jobs with configuration and state management

**Key Features:**
- Progress tracking with detailed metrics (speed, ETA, file size)
- Playlist support with item numbering
- Task state management (cancelled, paused)
- Metadata extraction and thumbnail support

### options_formatter.py
**New in v0.6.0** - Dedicated module for yt-dlp options generation and configuration. This module handles the complex logic of creating yt-dlp command-line options based on user settings and download requirements.

**Key Responsibilities:**
- Format-specific option generation
- Proxy configuration integration
- Metadata and thumbnail options
- Playlist handling settings
- Custom parameter processing

### download_manager.py
Handles all download operations and management logic. This module integrates with yt-dlp to fetch content from online sources. It manages the download queue, tracks progress, handles errors, and stores download history.

**Key Responsibilities:**
- Download initiation and execution
- Queue management
- Progress tracking
- Error handling and logging
- Download history maintenance
- Integration with yt-dlp and OptionsFormatter

### settings.py
Manages application configuration, including default paths, API endpoints, user preferences, and global constants. This module centralizes all configuration settings to ensure consistency across the application.

**Key Settings:**
- Download directories
- Application preferences
- Format preferences
- Logging configuration
- API configurations

### i18n.py
Handles internationalization and localization for the application. This module provides translation services using gettext and supports multiple languages with automatic language detection.

**Key Features:**
- Multi-language support (8 languages)
- Automatic system language detection
- Translation file management
- Language switching capabilities

### widgets.py
Contains reusable UI components that are used throughout the application. This module promotes code reusability and maintains a consistent visual style across different views.

**Common Widgets:**
- Custom buttons
- Progress indicators
- List components
- Input fields
- Status displays

### Views

#### views/downloads.py
Displays the currently active downloads with real-time progress information. Users can view:
- Download progress percentage
- Current download speed
- Estimated time remaining
- File being downloaded

#### views/finished.py
Shows the history of all completed downloads. Users can:
- View previously downloaded files
- Access download dates and times
- Redownload items if needed
- Clear download history

#### views/info.py
**New in v0.1.0** - Comprehensive video information and analysis interface where users can:
- Enter video URLs for analysis without downloading
- View detailed metadata (title, duration, uploader, views, date, description)
- Browse available formats in an interactive table
- See format details (resolution, codec, file size, FPS)
- Launch downloads directly from the analysis results
- Filter and sort formats by quality or type

#### views/queue.py (deprecated in v0.1.0)
*This view has been replaced by the Video Information Explorer (views/info.py)*

#### views/settings.py
Provides an interface for configuring application settings:
- Download location preferences
- Default audio/video formats
- Language selection (8 supported languages)
- Proxy configuration (URL, username, password)
- Metadata and thumbnail options
- Playlist handling settings
- Advanced options and custom parameters

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Audeo
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Windows:
   ```bash
   .\venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install the package in development mode**
   ```bash
   pip install -e .
   ```

## Building an Executable

You can create a standalone Windows executable using PyInstaller. This allows users to run Audeo without needing Python installed.

### Quick Build

**Windows (PowerShell):**
```powershell
.\build.ps1
```

**Windows (Command Line):**
```cmd
python devscripts/build.py
```

**Linux/macOS:**
```bash
bash build.sh
```

### Build Options

```bash
# Single file (default, ~150-200 MB)
python devscripts/build.py

# Directory (better for updates)
python devscripts/build.py --onedir

# Optimized (slower build, smaller size)
python devscripts/build.py --optimize

# Debug mode
python devscripts/build.py --debug
```

### Output

- **Single file**: `dist/Audeo.exe`
- **Directory**: `dist/Audeo/`

See [BUILD.md](BUILD.md) for detailed build instructions and troubleshooting.

## Dependencies

The application relies on the following key packages:

- **toga** (>= 0.4.5): Modern GUI toolkit for building native applications
- **yt-dlp** (>= 2024.1.1): Feature-rich command-line audio/video downloader
- **pillow** (>= 10.0.0): Python imaging library for image processing
- **imageio-ffmpeg** (>= 0.5.0): FFmpeg bindings for video processing

## Usage

### Running the Application

```bash
python -m audeo2.app
```

Or using the console script:
```bash
audeo-2
```

### Basic Workflow

1. **Analyze Videos**: Navigate to the Information tab and enter video URLs to analyze without downloading
2. **View Details**: Examine metadata, available formats, and technical specifications
3. **Select Format**: Choose the desired format from the interactive formats table
4. **Download**: Launch downloads directly from the information view
5. **Monitor Progress**: Switch to the downloads view to track active downloads
6. **View History**: Check the finished view to see completed downloads
7. **Configure Settings**: Adjust preferences, proxy settings, and other options as needed

## Development

### Project Setup for Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint code
pylint src/
```

### File Structure for Development

- All source code is located in `src/audeo2/`
- Views are organized in the `views/` subdirectory
- Assets are stored in `ressources/`
- Tests should be placed in a `tests/` directory

## Configuration

Application settings can be configured through:

1. **GUI Settings View**: User-friendly interface for common settings
2. **Proxy Configuration**: Complete proxy support with authentication
   - HTTP/HTTPS proxy URLs
   - Username and password support
   - Automatic proxy detection for video analysis and downloads
3. **settings.py**: Programmatic configuration for advanced users
4. **Environment Variables**: System-level configuration options

### Proxy Setup

To configure proxy settings:

1. Open the Settings view
2. Navigate to the General tab
3. Enter your proxy URL (e.g., `http://proxy.example.com:8080`)
4. Add username and password if required
5. Proxy will be automatically used for both video analysis and downloads

## Troubleshooting

### Video Analysis Fails
- Verify the URL is valid and accessible
- Check your internet connection
- If using a proxy, verify proxy settings are correct
- Some platforms may restrict metadata access
- Check logs for detailed error messages

### Download Fails
- Verify the URL is valid and accessible
- Check your internet connection
- Ensure the output directory has write permissions
- If using a proxy, verify proxy authentication
- Check logs for detailed error messages

### Application Won't Start
- Verify Python version is 3.10 or higher
- Ensure all dependencies are installed: `pip install -e .`
- Check for any error messages in the console

### Performance Issues
- Close other applications to free up system resources
- Reduce the number of concurrent downloads
- Check available disk space

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Version History

See [CHANGELOG](CHANGELOG) for detailed version history and release notes.

## Support

For issues, questions, or suggestions, please open an issue on the project repository.

## Disclaimer

### Legal Notice

**Audeo is provided "as-is" for personal and lawful use only.** Users are solely responsible for ensuring their use of this application complies with applicable laws and regulations in their jurisdiction.

### Intellectual Property

- Users must respect copyright laws and the intellectual property rights of content creators
- This application should only be used to download content you have the legal right to download
- Downloading copyrighted material without permission may violate applicable laws
- The developers of Audeo are not responsible for any misuse of this application

### Liability Limitation

The developers and contributors of Audeo assume no liability for:
- Unauthorized downloading of copyrighted material
- Loss of data or corruption
- System damage or performance issues
- Legal consequences resulting from misuse of this application
- Illegal use of downloaded content

### Third-Party Services

- Audeo relies on third-party services and platforms for content retrieval
- These services may change, restrict, or prohibit access at any time
- The developers are not responsible for changes in third-party service availability or policies

### Responsible Use

Users are encouraged to:
- Only download content they have explicit permission to download
- Respect content creators' rights and terms of service
- Use this application in compliance with local laws and regulations
- Support creators by purchasing or subscribing to their official content

---

**Project Home:** Audeo - Audio and Video Downloader  
**Last Updated:** February 28, 2026  
**Version:** 0.6.0
