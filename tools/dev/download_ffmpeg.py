#!/usr/bin/env python3
import os
import sys
import requests
import zipfile
import tarfile
import shutil
from pathlib import Path

def download_file(url, target_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def main():
    # Create temporary directory
    temp_dir = Path('temp_ffmpeg')
    temp_dir.mkdir(exist_ok=True)
    
    # Destination folder
    dest_dir = Path('src/audeo/resources/ffmpeg')
    
    try:
        # Windows x64
        print("Downloading FFmpeg for Windows x64...")
        win_x64_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        win_zip = temp_dir / "ffmpeg-win64.zip"
        download_file(win_x64_url, win_zip)
        with zipfile.ZipFile(win_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir / "win64")
        (dest_dir / "windows-x64").mkdir(parents=True, exist_ok=True)
        shutil.copy(
            temp_dir / "win64" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe",
            dest_dir / "windows-x64" / "ffmpeg.exe"
        )
        
        # Linux x64
        print("Downloading FFmpeg for Linux x64...")
        linux_x64_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        linux_tar = temp_dir / "ffmpeg-linux64.tar.xz"
        download_file(linux_x64_url, linux_tar)
        with tarfile.open(linux_tar, 'r:xz') as tar_ref:
            tar_ref.extractall(temp_dir / "linux64")
        # Create the destination folder
        (dest_dir / "linux-x64").mkdir(parents=True, exist_ok=True)
        for file in (temp_dir / "linux64").glob("ffmpeg-*-amd64-static/ffmpeg"):
            shutil.copy(file, dest_dir / "linux-x64" / "ffmpeg")
        
        # Linux ARM64
        print("Downloading FFmpeg for Linux ARM64...")
        linux_arm_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
        linux_arm_tar = temp_dir / "ffmpeg-linux-arm64.tar.xz"
        download_file(linux_arm_url, linux_arm_tar)
        with tarfile.open(linux_arm_tar, 'r:xz') as tar_ref:
            tar_ref.extractall(temp_dir / "linux-arm64")
        (dest_dir / "linux-arm64").mkdir(parents=True, exist_ok=True)
        for file in (temp_dir / "linux-arm64").glob("ffmpeg-*-arm64-static/ffmpeg"):
            shutil.copy(file, dest_dir / "linux-arm64" / "ffmpeg")
        
        # The binaries for macOS x64 and ARM64 must be downloaded manually
        print("\nNOTE: For macOS, please download the binaries manually from:")
        print("https://osxexperts.net/")
        print("And place them in:")
        (dest_dir / "macos-x64").mkdir(parents=True, exist_ok=True)
        (dest_dir / "macos-arm64").mkdir(parents=True, exist_ok=True)
        print(f"- {dest_dir}/macos-x64/ffmpeg")
        print(f"- {dest_dir}/macos-arm64/ffmpeg")
        
        # Make Unix binaries executable
        if sys.platform != "win32":
            for platform_dir in ["linux-x64", "linux-arm64", "macos-x64", "macos-arm64"]:
                ffmpeg_path = dest_dir / platform_dir / "ffmpeg"
                if ffmpeg_path.exists():
                    os.chmod(ffmpeg_path, 0o755)
        
        print("\nDownload complete!")
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
