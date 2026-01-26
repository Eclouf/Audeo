"""
FFmpeg management module for Audeo
Handles downloading, installation, and verification of ffmpeg and ffprobe
"""

import sys
import subprocess
import tempfile
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path
from typing import Optional, Callable


class FFmpegManager:
    """Manages ffmpeg/ffprobe download and installation"""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        Initialize FFmpeg manager
        
        Args:
            ffmpeg_path: Path to existing ffmpeg executable (optional)
        """
        self.ffmpeg_path = ffmpeg_path
        self.install_dir = Path.home() / ".audeo2" / "ffmpeg"
        self._get_platform_info()
    
    def _get_platform_info(self) -> None:
        """Determine platform-specific download URLs and executable names"""
        if sys.platform == "win32":
            self.url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            self.filename = "ffmpeg-master-latest-win64-gpl.zip"
            self.exe_name = "ffmpeg.exe"
            self.ffprobe_name = "ffprobe.exe"
        elif sys.platform == "darwin":
            self.url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-osx64-gpl.zip"
            self.filename = "ffmpeg-master-latest-osx64-gpl.zip"
            self.exe_name = "ffmpeg"
            self.ffprobe_name = "ffprobe"
        else:
            self.url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
            self.filename = "ffmpeg-master-latest-linux64-gpl.tar.xz"
            self.exe_name = "ffmpeg"
            self.ffprobe_name = "ffprobe"
    
    def is_available(self) -> bool:
        """Check if ffmpeg and ffprobe are available"""
        if not self.ffmpeg_path:
            return False
        
        ffmpeg_file = Path(self.ffmpeg_path)
        if not ffmpeg_file.exists():
            print(f"[FFmpeg] ffmpeg file does not exist: {self.ffmpeg_path}")
            return False
        
        return self._check_ffprobe_available(self.ffmpeg_path)
    
    def _check_ffprobe_available(self, ffmpeg_path: str) -> bool:
        """Check if ffprobe is available with the given ffmpeg"""
        try:
            ffmpeg_file = Path(ffmpeg_path)
            if not ffmpeg_file.exists():
                print(f"[FFmpeg] ffmpeg file does not exist: {ffmpeg_path}")
                return False
            
            ffmpeg_dir = ffmpeg_file.parent
            ffprobe_path = ffmpeg_dir / self.ffprobe_name
            
            if ffprobe_path.exists():
                print(f"[FFmpeg] ffprobe found at: {ffprobe_path}")
                return True
            
            print(f"[FFmpeg] ffprobe not found at: {ffprobe_path}")
            
            # Check if ffprobe is in PATH
            try:
                result = subprocess.run(
                    [self.ffprobe_name, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"[FFmpeg] ffprobe found in PATH")
                    return True
            except Exception:
                pass
            
            print(f"[FFmpeg] ffprobe not available")
            return False
            
        except Exception as e:
            print(f"[FFmpeg] Error checking ffprobe: {e}")
            return False
    
    def download_and_install(self, progress_callback: Optional[Callable] = None) -> Optional[Path]:
        """
        Download and install ffmpeg/ffprobe
        
        Args:
            progress_callback: Optional callback function(percent, message) for progress updates
            
        Returns:
            Path to installed ffmpeg executable, or None if failed
        """
        def update_progress(percent: int, message: str):
            """Helper to call progress callback safely"""
            if progress_callback:
                try:
                    progress_callback(percent, message)
                except Exception as e:
                    print(f"[FFmpeg] Progress callback error: {e}")
        
        print("[FFmpeg] Starting download...")
        update_progress(0, "Initialisation...")
        
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            print(f"[FFmpeg] Install dir: {self.install_dir}")
            
            # Check if already installed
            ffmpeg_path = self.install_dir / self.exe_name
            ffprobe_path = self.install_dir / self.ffprobe_name
            if ffmpeg_path.exists() and ffprobe_path.exists():
                print(f"[FFmpeg] Already installed at {ffmpeg_path}")
                update_progress(100, "Déjà installé")
                return ffmpeg_path
            
            # Download the archive
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / self.filename
                
                def progress_hook(block_num, block_size, total_size):
                    """Callback for urllib download progress"""
                    if total_size > 0:
                        current_bytes = block_num * block_size
                        percent = min(100, int((current_bytes * 50) / total_size))
                        downloaded_mb = current_bytes / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        message = f"Téléchargement: {percent}% ({downloaded_mb:.1f}MB / {total_mb:.1f}MB)"
                        update_progress(percent, message)
                        print(f"[FFmpeg] {message}")
                
                print(f"[FFmpeg] Downloading from {self.url}...")
                update_progress(5, "Téléchargement en cours...")
                urllib.request.urlretrieve(self.url, temp_path, progress_hook)
                
                file_size_mb = temp_path.stat().st_size / (1024 * 1024)
                print(f"[FFmpeg] Download complete ({file_size_mb:.1f}MB)")
                update_progress(50, f"Extraction ({file_size_mb:.1f}MB)...")
                
                # Extract archive
                print(f"[FFmpeg] Extracting...")
                if self.filename.endswith('.zip'):
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                else:
                    # .tar.xz for Linux
                    with tarfile.open(temp_path, 'r:xz') as tar_ref:
                        tar_ref.extractall(temp_dir)
                
                print(f"[FFmpeg] Extract complete")
                update_progress(75, "Finalisation...")
                
                # Find extracted ffmpeg directory
                extracted_dirs = [
                    d for d in Path(temp_dir).iterdir()
                    if d.is_dir() and 'ffmpeg' in d.name.lower()
                ]
                if not extracted_dirs:
                    extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
                
                if not extracted_dirs:
                    raise Exception("Impossible de trouver le répertoire ffmpeg extrait")
                
                ffmpeg_source_dir = extracted_dirs[0]
                print(f"[FFmpeg] Found directory: {ffmpeg_source_dir}")
                
                # Copy executables
                ffmpeg_source = ffmpeg_source_dir / "bin" / self.exe_name
                ffprobe_source = ffmpeg_source_dir / "bin" / self.ffprobe_name
                
                if not ffmpeg_source.exists():
                    # Try main directory
                    ffmpeg_source = ffmpeg_source_dir / self.exe_name
                    ffprobe_source = ffmpeg_source_dir / self.ffprobe_name
                
                if ffmpeg_source.exists():
                    print(f"[FFmpeg] Copying ffmpeg from {ffmpeg_source}")
                    shutil.copy2(ffmpeg_source, self.install_dir / self.exe_name)
                else:
                    print(f"[FFmpeg] ffmpeg not found at {ffmpeg_source}")
                
                if ffprobe_source.exists():
                    print(f"[FFmpeg] Copying ffprobe from {ffprobe_source}")
                    shutil.copy2(ffprobe_source, self.install_dir / self.ffprobe_name)
                else:
                    print(f"[FFmpeg] ffprobe not found at {ffprobe_source}")
                
                # Make executables executable (Linux/macOS)
                if sys.platform != "win32":
                    (self.install_dir / self.exe_name).chmod(0o755)
                    (self.install_dir / self.ffprobe_name).chmod(0o755)
            
            # Verify installation
            ffmpeg_path = self.install_dir / self.exe_name
            ffprobe_path = self.install_dir / self.ffprobe_name
            
            if ffmpeg_path.exists() and ffprobe_path.exists():
                print(f"[FFmpeg] Installation successful: {ffmpeg_path}")
                update_progress(100, "Installation réussie!")
                return ffmpeg_path
            else:
                raise Exception(
                    f"ffmpeg ou ffprobe manquant après extraction: "
                    f"ffmpeg={ffmpeg_path.exists()}, ffprobe={ffprobe_path.exists()}"
                )
            
        except Exception as e:
            print(f"[FFmpeg] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            update_progress(0, f"Erreur: {str(e)}")
            return None
