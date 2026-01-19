# Build Audeo executable

Builds a standalone Windows executable using PyInstaller.

## Requirements

- Python 3.10+
- PyInstaller (installed automatically if missing)

## Quick Start

### Windows (PowerShell)
```powershell
.\build.ps1
```

### Windows (Command Line)
```cmd
python devscripts/build.py
```

### Linux/macOS
```bash
python devscripts/build.py
```

## Options

### Create directory instead of single file
```powershell
python devscripts/build.py --onedir
```

### Optimize for runtime (slower build)
```powershell
python devscripts/build.py --optimize
```

### Show debug output
```powershell
python devscripts/build.py --debug
```

## Output

- **Executable**: `dist/Audeo.exe` (Windows)
- **Build files**: `build/` (temporary, safe to delete)

## Distribution

To distribute Audeo:

1. **Single file (recommended)**:
   - Use `dist/Audeo.exe` directly
   - File size: ~150-200 MB

2. **Directory**:
   - Use entire `dist/Audeo/` folder
   - Better for updates, but requires folder structure

## Dependencies Included

The executable includes:
- Python runtime
- Toga (GUI framework)
- yt-dlp (downloader)
- Pillow (image processing)
- All project resources (images, configs)

## Troubleshooting

### "PyInstaller not found"
```powershell
pip install pyinstaller
```

### Icon not showing
Ensure `src/audeo2/ressources/pictures/audio/audeo-icon.png` exists

### Executable too large
Use `--optimize` flag to reduce size (~10-20% smaller)

### Missing modules
Add to `--hidden-import` in `devscripts/build.py`
