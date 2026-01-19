#!/usr/bin/env python3
"""
Build script for Audeo - Creates standalone executable using PyInstaller
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

def get_project_root():
    """Get the root directory of the project"""
    return Path(__file__).parent.parent

def get_resource_path():
    """Get the path to resource files"""
    return get_project_root() / "src" / "audeo2" / "ressources"

def build_executable(optimize=False, one_file=True, debug=False):
    """Build the executable using PyInstaller"""
    root = get_project_root()
    
    print("=" * 60)
    print("Audeo Build Script")
    print("=" * 60)
    
    # Check dependencies
    print("\n[1/5] Checking dependencies...")
    try:
        import PyInstaller
        print(f"  + PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("  - PyInstaller not found. Installing...")
        os.system(f"{sys.executable} -m pip install pyinstaller")
    
    # Prepare build directory
    print("\n[2/5] Preparing build directories...")
    dist_dir = root / "dist"
    build_dir = root / "build"
    
    # Kill any existing Audeo processes
    if sys.platform == "win32":
        print("  * Checking for running Audeo processes...")
        os.system("taskkill /F /IM Audeo.exe 2>nul")
    
    # Clean dist directory
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir)
            print(f"  + Cleaned {dist_dir}")
        except PermissionError as e:
            print(f"  ! Could not clean {dist_dir}: {e}")
            print("  ! Make sure Audeo.exe is not running")
            return False
    
    # Clean build directory
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print(f"  + Cleaned {build_dir}")
        except Exception as e:
            print(f"  ! Warning: Could not clean {build_dir}: {e}")
    
    # Prepare icon
    print("\n[2.5/5] Preparing icon...")
    icon_path = root / "src" / "audeo2" / "ressources" / "pictures" / "audio" / "audeo-icon.ico"
    icon_png = root / "src" / "audeo2" / "ressources" / "pictures" / "audio" / "audeo-icon.png"
    
    if not icon_path.exists() and icon_png.exists():
        print(f"  * Converting PNG to ICO...")
        try:
            from PIL import Image
            img = Image.open(icon_png)
            # Resize to 256x256 for better icon quality
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            img.save(icon_path, "ICO")
            print(f"  + Icon created: {icon_path}")
        except Exception as e:
            print(f"  ! Could not convert icon: {e}")
    elif icon_path.exists():
        print(f"  + Icon found: {icon_path}")
    else:
        print(f"  ! No icon found (optional)")
    
    # Build PyInstaller command
    print("\n[3/5] Building PyInstaller command...")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "Audeo",
        "--windowed",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        "--clean",
    ]
    
    # Add icon if it exists
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print(f"  Using icon: {icon_path}")
    
    # Add optional flags
    if one_file:
        cmd.append("--onefile")
    
    if optimize:
        cmd.extend(["--optimize", "2"])
    
    if not debug:
        cmd.append("--noconfirm")
    
    # Add hidden imports for Toga and dependencies
    hidden_imports = [
        "toga",
        "toga.style",
        "yt_dlp",
        "pillow",
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Add data files (resources)
    resources = get_resource_path()
    if resources.exists():
        cmd.extend(["--add-data", f"{resources}{os.pathsep}audeo2/ressources"])
    
    # Use the wrapper as entry point (fixes relative imports)
    entry_point = root / "audeo_runner.py"
    cmd.append(str(entry_point))
    
    print(f"  Command: {' '.join(cmd[:5])} ... {cmd[-1]}")
    
    # Run PyInstaller
    print("\n[4/5] Running PyInstaller...")
    result = os.system(" ".join(cmd))
    
    if result != 0:
        print("  - Build failed!")
        return False
    
    print("  + Build completed successfully")
    
    # Print summary
    print("\n[5/5] Build Summary")
    print("=" * 60)
    
    exe_path = dist_dir / "Audeo.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  + Executable created: {exe_path}")
        print(f"  + Size: {size_mb:.2f} MB")
    else:
        print(f"  - Executable not found at {exe_path}")
        return False
    
    print("\n" + "=" * 60)
    print("Build completed! Run the executable with:")
    print(f"  {exe_path}")
    print("=" * 60)
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Build Audeo executable"
    )
    
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create a directory instead of a single file"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize Python bytecode (slower build, faster runtime)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug output"
    )
    
    args = parser.parse_args()
    
    success = build_executable(
        optimize=args.optimize,
        one_file=not args.onedir,
        debug=args.debug
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
