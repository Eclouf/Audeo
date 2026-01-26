#!/usr/bin/env python3
"""
Build script for Audeo - Linux distribution package
"""
from pathlib import Path
import shutil
import os
import subprocess
import urllib.request

def create_appimage():
    """Crée un package AppImage pour Linux"""
    print("Creating AppImage package...")
    
    root = Path(__file__).parent.parent  # Remonter au répertoire racine du projet
    dist_dir = root / "dist"
    appimage_dir = root / "AppImage"
    
    # Nettoyer l'ancien répertoire AppImage
    if appimage_dir.exists():
        shutil.rmtree(appimage_dir)
    
    appimage_dir.mkdir()
    
    # Variables
    app_name = "Audeo"
    version = "0.1.0"
    arch = "x86_64"
    
    # Structure AppImage
    appdir = appimage_dir / f"{app_name}.AppDir"
    appdir.mkdir()
    
    # Copier l'exécutable
    exe_path = dist_dir / "Audeo"
    if exe_path.exists():
        shutil.copy2(exe_path, appdir / "AppRun")
        os.chmod(appdir / "AppRun", 0o755)
        print(f"Copied executable to {appdir / 'AppRun'}")
    else:
        print("Executable not found!")
        return False
    
    # Créer le fichier .desktop
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=Audeo-2
Comment=Video Information and Download Tool
Exec=AppRun
Icon={app_name.lower()}
Categories=AudioVideo;Audio;Video;
Terminal=false
StartupWMClass=Audeo
"""
    
    with open(appdir / f"{app_name.lower()}.desktop", "w") as f:
        f.write(desktop_content)
    
    # Créer l'icône (utiliser une icône par défaut si nécessaire)
    icon_source = root / "src" / "audeo2" / "ressources" / "pictures" / "audio" / "audeo-icon.png"
    icon_target = appdir / f"{app_name.lower()}.png"
    
    if icon_source.exists():
        shutil.copy2(icon_source, icon_target)
    else:
        # Créer une icône simple si l'original n'existe pas
        print("Warning: Icon not found, creating simple icon")
        # Vous pourriez ajouter du code pour créer une icône SVG ici
    
    # Créer le fichier AppRun
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export PATH="${HERE}/usr/bin:$PATH"
export GTK_PATH="${HERE}/usr/lib/x86_64-linux-gnu/gtk-3.0:$GTK_PATH"
export GDK_BACKEND=x11
export NO_AT_BRIDGE=1
export GTK_MODULES=""

exec "${HERE}/AppRun" "$@"
"""
    
    with open(appdir / "AppRun", "w") as f:
        f.write(apprun_content)
    os.chmod(appdir / "AppRun", 0o755)
    
    # Créer la structure usr/lib pour les dépendances
    usr_lib = appdir / "usr" / "lib"
    usr_lib.mkdir(parents=True)
    
    # Copier les bibliothèques GTK nécessaires (optionnel)
    # Vous pouvez copier les bibliothèques requises pour rendre l'AppImage plus portable
    
    # Télécharger appimagetool si nécessaire
    appimagetool = root / "appimagetool-x86_64.AppImage"
    if not appimagetool.exists():
        print("Downloading appimagetool...")
        import urllib.request
        appimagetool_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        urllib.request.urlretrieve(appimagetool_url, appimagetool)
        os.chmod(appimagetool, 0o755)
    
    # Créer l'AppImage
    appimage_name = f"{app_name}-{version}-{arch}.AppImage"
    appimage_path = dist_dir / appimage_name
    
    try:
        # Vérifier si appimagetool est exécutable
        if not appimagetool.exists():
            print(f"appimagetool not found at: {appimagetool}")
            return False
            
        # Tester si appimagetool peut s'exécuter
        test_result = subprocess.run([str(appimagetool), "--help"], 
                                   capture_output=True, text=True, timeout=10)
        if test_result.returncode != 0:
            print(f"appimagetool is not executable in this environment")
            print(f"Error: {test_result.stderr}")
            print("This is normal in WSL/VM environments")
            return False
        
        cmd = [str(appimagetool), str(appdir), str(appimage_path)]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if appimage_path.exists():
            size_mb = appimage_path.stat().st_size / (1024 * 1024)
            print(f"AppImage created: {appimage_path}")
            print(f"Size: {size_mb:.2f} MB")
            
            # Rendre exécutable
            os.chmod(appimage_path, 0o755)
            
            return True
        else:
            print("AppImage creation failed - no output file created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"AppImage creation failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        print("This is expected in WSL/VM environments")
        return False
    except Exception as e:
        print(f"AppImage creation failed: {e}")
        return False

def linux_dist(bin: Path, desktop: Path, metainfo: Path):
    """Crée un package de distribution Linux complet"""
    print("Creating Linux distribution package...")
    
    root = Path(__file__).parent.parent  # Remonter au répertoire racine du projet
    dist_dir = root / "dist"
    
    # Créer le package AppImage
    if create_appimage():
        print("AppImage package created successfully!")
    
    # Créer un tar.gz avec les fichiers essentiels
    tar_name = f"audeo2-0.1.0-linux-x86_64.tar.gz"
    tar_path = dist_dir / tar_name
    
    import tarfile
    
    with tarfile.open(tar_path, "w:gz") as tar:
        # Ajouter l'exécutable
        exe_path = dist_dir / "Audeo"
        if exe_path.exists():
            tar.add(exe_path, arcname="audeo2/Audeo")
        
        # Ajouter le launcher
        launcher_path = root / "audeo-linux-launcher.sh"
        if launcher_path.exists():
            tar.add(launcher_path, arcname="audeo2/audeo-linux-launcher.sh")
        
        # Ajouter les fichiers .desktop et .metainfo.xml
        desktop_path = root / "audeo2.desktop"
        if desktop_path.exists():
            tar.add(desktop_path, arcname="audeo2/audeo2.desktop")
        
        metainfo_path = root / "com.eclouf.audeo2.metainfo.xml"
        if metainfo_path.exists():
            tar.add(metainfo_path, arcname="audeo2/com.eclouf.audeo2.metainfo.xml")
        
        # Ajouter un README d'installation
        readme_content = """# Audeo-2 Linux Installation

## Quick Start

### Option 1: AppImage (Recommended)
```bash
chmod +x Audeo-0.1.0-x86_64.AppImage
./Audeo-0.1.0-x86_64.AppImage
```

### Option 2: Manual Installation
```bash
tar -xzf audeo2-0.1.0-linux-x86_64.tar.gz
cd audeo2
chmod +x Audeo audeo-linux-launcher.sh
./audeo-linux-launcher.sh
```

## System Integration

### Desktop Entry
```bash
# Copy desktop file
cp audeo2.desktop ~/.local/share/applications/

# Copy metainfo
sudo cp com.eclouf.audeo2.metainfo.xml /usr/share/metainfo/
```

### Manual Installation
```bash
# Copy to /opt
sudo cp -r audeo2 /opt/audeo2
sudo ln -s /opt/audeo2/audeo-linux-launcher.sh /usr/local/bin/audeo2
```

## Requirements

- GTK 3.0 development libraries
- Python 3.10+ (for AppImage: bundled)
- PyGObject, pycairo (for AppImage: bundled)

## Troubleshooting

See BUILD.md for detailed troubleshooting information.
"""
        
        readme_path = dist_dir / "INSTALL_LINUX.md"
        with open(readme_path, "w") as f:
            f.write(readme_content)
        
        tar.add(readme_path, arcname="audeo2/INSTALL_LINUX.md")
    
    if tar_path.exists():
        size_mb = tar_path.stat().st_size / (1024 * 1024)
        print(f"Linux distribution package created: {tar_path}")
        print(f"Size: {size_mb:.2f} MB")
        return True
    
    return False

if __name__ == "__main__":
    """Point d'entrée principal pour le script de distribution Linux"""
    print("Audeo-2 Linux Distribution Builder")
    print("=" * 40)
    
    # Lancer la création des packages
    if linux_dist(None, None, None):
        print("\n Linux distribution packages created successfully!")
        print("\n Generated files:")
        print("   - AppImage: dist/Audeo-0.1.0-x86_64.AppImage")
        print("   - Archive:  dist/audeo2-0.1.0-linux-x86_64.tar.gz")
        print("   - Install:  dist/INSTALL_LINUX.md")
    else:
        print("\n Failed to create Linux distribution packages!")