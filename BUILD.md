# Build Audeo-2 Executable

Builds standalone executables for Windows, macOS, and Linux using PyInstaller.

## Requirements

- Python 3.10+
- PyInstaller (installed automatically if missing)

## Platform-Specific Requirements

### Linux Dependencies

For Linux builds, you need to install GTK development libraries:

```bash
# Update package manager
sudo apt update

# Install required GTK and GI libraries
sudo apt install libgirepository-2.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-4.0 gir1.2-girepository-3.0

# Install Python GTK bindings
pip install pycairo  # Use --break-system-packages if not in virtual environment
pip install PyGObject
```

### Windows
- No additional system dependencies required

### macOS
- Xcode Command Line Tools (install with `xcode-select --install`)

## Quick Start

### Multi-Platform Build (Recommended)
```bash
# Auto-detect platform and build
python build_multiplatform.py

# Specific platform
python build_multiplatform.py --platform linux
python build_multiplatform.py --platform windows
python build_multiplatform.py --platform macos
```

### Traditional Build Script
```bash
# Use the original build script
python devscripts/build.py
```

### Linux Distribution Script
```bash
# Create Linux distribution packages only
python devscripts/linux_dist.py
```

## Build Options

### Multi-Platform Build Options
```bash
# Create directory instead of single file
python build_multiplatform.py --onedir

# Optimize for runtime (slower build, smaller size)
python build_multiplatform.py --optimize

# Show debug output
python build_multiplatform.py --debug
```

### Traditional Build Options
```bash
# Create directory instead of single file
python devscripts/build.py --onedir

# Optimize for runtime (slower build)
python devscripts/build.py --optimize

# Show debug output
python devscripts/build.py --debug
```

## Output

### Multi-Platform Build
- **Windows**: `dist/Audeo.exe`
- **Linux**: `dist/Audeo` + `audeo-linux-launcher.sh`
- **macOS**: `dist/Audeo.app`

### Traditional Build
- **Windows**: `dist/Audeo.exe`
- **Linux/macOS**: `dist/Audeo`

## Version Files

The build process automatically creates platform-specific version files:

- **Windows**: `version.txt` (VSVersionInfo)
- **Linux**: `audeo2.desktop` + `com.eclouf.audeo2.metainfo.xml`
- **macOS**: `Info.plist` in app bundle

## Distribution

### Windows
1. **Single file (recommended)**:
   - Use `dist/Audeo.exe` directly
   - File size: ~150-200 MB

2. **Directory**:
   - Use entire `dist/Audeo/` folder
   - Better for updates, but requires folder structure

### Linux
1. **AppImage (Recommended)**:
   - Use `dist/Audeo-0.1.0-x86_64.AppImage` directly
   - Portable, no installation required
   - Run with: `./Audeo-0.1.0-x86_64.AppImage`

2. **Manual Installation**:
   - Use `dist/audeo2-0.1.0-linux-x86_64.tar.gz`
   - Extract and run with launcher script
   - Run with: `./audeo-linux-launcher.sh`

3. **Directory**:
   - Use entire `dist/Audeo/` folder
   - Install with: `sudo cp -r dist/Audeo /opt/`

### macOS
1. **App bundle**:
   - Use `dist/Audeo.app`
   - Drag to Applications folder

## Dependencies Included

The executable includes:
- Python runtime
- Toga (GUI framework) with platform-specific backend
- yt-dlp (downloader)
- Pillow (image processing)
- All project resources (images, configs)

## Troubleshooting

### Linux GTK Issues

**Problem**: `gi.RepositoryError: Namespace GIRepository not available`

**Solution**: Install the required GTK development libraries:
```bash
sudo apt update
sudo apt install libgirepository-2.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-4.0 gir1.2-girepository-3.0
pip install pycairo PyGObject
```

**Problem**: `ImportError: Requiring namespace 'Gdk' version '4.0', but '3.0' is already loaded`

**Solution**: This is resolved by installing the correct GTK4 bindings:
```bash
sudo apt install gir1.2-gtk-4.0
```

### General Issues

#### "PyInstaller not found"
```bash
pip install pyinstaller
```

#### Icon not showing
Ensure `src/audeo2/ressources/pictures/audio/audeo-icon.png` exists

#### Executable too large
Use `--optimize` flag to reduce size (~10-20% smaller)

#### Missing modules
Add to `--hidden-import` in build script or use `build_multiplatform.py`

### Platform-Specific Issues

#### Windows
- Ensure Windows Defender is not blocking the executable
- Run as Administrator if permission issues occur

#### macOS
- If app doesn't open, check Gatekeeper settings:
  ```bash
  xattr -d com.apple.quarantine dist/Audeo.app
  ```

#### Linux
- Make executable: `chmod +x dist/Audeo`
- Use launcher script for proper GTK environment
