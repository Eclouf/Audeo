#!/usr/bin/env python3
"""
Script de build multi-plateformes pour Audeo-2
Utilise les fichiers de version spécifiques à chaque plateforme
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def get_version_info():
    """Retourne les informations de version communes"""
    return {
        'version': '0.1.0',
        'name': 'Audeo-2',
        'company': 'Eclouf',
        'description': 'Audeo is a user-friendly application for downloading audio and video content from various online sources',
        'copyright': 'Copyright © 2026 Eclouf',
        'homepage': 'https://github.com/Eclouf/Audeo'
    }

def build_executable(optimize=False, one_file=True, debug=False):
    """Build principal utilisant build.py"""
    root = Path(__file__).parent
    build_script = root / "devscripts" / "build.py"
    
    if build_script.exists():
        cmd = [sys.executable, str(build_script)]
        
        if optimize:
            cmd.append("--optimize")
        if not one_file:
            cmd.append("--onedir")
        if debug:
            cmd.append("--debug")
            
        print("Using main build script...")
        subprocess.run(cmd, check=True)
    else:
        print("Main build script not found!")
        return False
    
    return True

def build_windows():
    """Build pour Windows avec version.txt"""
    root = Path(__file__).parent
    version_file = root / "version.txt"
    
    if version_file.exists():
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name", "Audeo",
            "--windowed",
            "--version-file", str(version_file),
            "--onefile",
            "audeo_runner.py"
        ]
        print("Building Windows executable with version info...")
        subprocess.run(cmd, check=True)
    else:
        print("Windows version file not found!")

def build_macos():
    """Build pour macOS avec support natif"""
    root = Path(__file__).parent
    
    # Nettoyer les anciens builds
    dist_dir = root / "dist"
    build_dir = root / "build"
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"Cleaned {dist_dir}")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"Cleaned {build_dir}")
    
    # Commande PyInstaller optimisée pour macOS
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "Audeo",
        "--windowed",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        "--clean",
        "--onefile",
        "--hidden-import", "toga_cocoa",
        "--hidden-import", "cocoa",
        "--hidden-import", "objc",
        "--hidden-import", "Foundation",
        "--hidden-import", "AppKit",
        "--exclude-module", "toga_winforms",
        "--exclude-module", "toga_gtk",
        "--exclude-module", "toga_android",
        "--exclude-module", "toga_iOS",
        "--exclude-module", "toga_web",
        "--add-data", f"{root}/src/audeo2/ressources{os.pathsep}audeo2/ressources",
        "audeo_runner.py"
    ]
    
    print("Building macOS executable with Cocoa support...")
    print(f"Command: {' '.join(cmd[:8])} ...")
    
    try:
        subprocess.run(cmd, check=True)
        print("macOS build completed successfully!")
        
        # Vérifier l'exécutable
        exe_path = dist_dir / "Audeo"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
            
            # Créer les fichiers de version macOS
            create_macos_version_files()
            
            return True
        else:
            print("Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def create_macos_version_files():
    """Crée les fichiers de version pour macOS"""
    print("Creating macOS version files...")
    
    version_info = "0.1.0"
    bundle_id = "com.eclouf.audeo2"
    
    # Créer le bundle structure
    dist_dir = Path(__file__).parent / "dist"
    app_path = dist_dir / "Audeo.app"
    
    if app_path.exists():
        # Créer l'Info.plist
        info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Audeo-2</string>
    <key>CFBundleDisplayName</key>
    <string>Audeo-2</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleVersion</key>
    <string>{version_info}</string>
    <key>CFBundleShortVersionString</key>
    <string>{version_info}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>Audeo</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleSupportedPlatforms</key>
    <array>
        <string>MacOSX</string>
    </array>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>CFBundleCopyright</key>
    <string>Copyright © 2026 Eclouf</string>
    <key>CFBundleGetInfoString</key>
    <string>Audeo-2 {version_info}, Video Information and Download Tool</string>
    <key>CFBundleLongVersionString</key>
    <string>Audeo-2 version {version_info}, (c) 2026 Eclouf</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.video</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 Eclouf</string>
</dict>
</plist>
"""
        
        # Écrire l'Info.plist
        contents_dir = app_path / "Contents"
        info_plist_path = contents_dir / "Info.plist"
        
        with open(info_plist_path, "w") as f:
            f.write(info_plist_content)
        
        print(f"Created Info.plist: {info_plist_path}")
    
    print("All macOS version files created successfully!")

def build_linux():
    """Build pour Linux avec corrections GTK"""
    root = Path(__file__).parent
    
    # Nettoyer les anciens builds
    dist_dir = root / "dist"
    build_dir = root / "build"
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"Cleaned {dist_dir}")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"Cleaned {build_dir}")
    
    # Commande PyInstaller optimisée pour Linux/GTK
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "Audeo",
        "--windowed",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        "--clean",
        "--onefile",
        "--hidden-import", "toga_gtk",
        "--hidden-import", "gi",
        "--hidden-import", "gi.repository.Gtk",
        "--hidden-import", "gi.repository.Gdk",
        "--hidden-import", "gi.repository.GObject",
        "--hidden-import", "gi.repository.Gio",
        "--hidden-import", "gi.repository.GdkPixbuf",
        "--hidden-import", "cairo",
        "--exclude-module", "toga_winforms",
        "--exclude-module", "toga_cocoa", 
        "--exclude-module", "toga_android",
        "--exclude-module", "toga_iOS",
        "--exclude-module", "toga_web",
        "--add-data", f"{root}/src/audeo2/ressources{os.pathsep}audeo2/ressources",
        "audeo_runner.py"
    ]
    
    print("Building Linux executable with GTK3 support...")
    print(f"Command: {' '.join(cmd[:8])} ...")
    
    try:
        subprocess.run(cmd, check=True)
        print("Linux build completed successfully!")
        
        # Vérifier l'exécutable
        exe_path = dist_dir / "Audeo"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
            
            # Rendre exécutable
            os.chmod(exe_path, 0o755)
            print("Made executable")
            
            # Créer les fichiers de version Linux
            create_linux_version_files()
            
            return True
        else:
            print("Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def create_linux_version_files():
    """Crée les fichiers de version pour Linux"""
    print("Creating Linux version files...")
    
    version_info = "0.1.0"
    package_name = "audeo2"
    maintainer = "Eclouf <contact@eclouf.com>"
    description = "Audeo is a user-friendly application for downloading audio and video content from various online sources"
    homepage = "https://github.com/Eclouf/Audeo"
    
    # Fichier .desktop
    desktop_content = f"""[Desktop Entry]
Version={version_info}
Type=Application
Name=Audeo-2
Name[fr]=Audeo-2
Comment=A user-friendly application for downloading audio and video content
Comment[fr]=Application conviviale pour télécharger du contenu audio et vidéo
Exec=Audeo
Icon=audeo2
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=video;audio;download;youtube;media;
StartupNotify=true
"""
    
    with open("audeo2.desktop", "w") as f:
        f.write(desktop_content)
    print("Created desktop file: audeo2.desktop")
    
    # Fichier AppStream
    appstream_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.eclouf.audeo2</id>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <name>Audeo-2</name>
  <summary>User-friendly audio and video downloader</summary>
  <summary xml:lang="fr">Application conviviale de téléchargement audio et vidéo</summary>
  
  <description>
    <p>Audeo-2 is a modern desktop application for downloading and managing audio and video content from various online platforms.</p>
    <p xml:lang="fr">Audeo-2 est une application de bureau moderne pour télécharger et gérer du contenu audio et vidéo depuis diverses plateformes en ligne.</p>
  </description>
  
  <launchable type="desktop-id">audeo2.desktop</launchable>
  <provides>
    <binary>Audeo</binary>
  </provides>
  
  <url type="homepage">{homepage}</url>
  
  <developer_name>Eclouf</developer_name>
  
  <categories>
    <category>AudioVideo</category>
    <category>Audio</category>
    <category>Video</category>
    <category>Network</category>
  </categories>
  
  <releases>
    <release version="{version_info}" date="2026-01-20">
      <description>
        <p>Initial release with video information analysis and download capabilities</p>
        <p xml:lang="fr">Version initiale avec analyse d'information vidéo et capacités de téléchargement</p>
      </description>
    </release>
  </releases>
</component>
"""
    
    with open("com.eclouf.audeo2.metainfo.xml", "w") as f:
        f.write(appstream_content)
    print("Created AppStream file: com.eclouf.audeo2.metainfo.xml")
    
    print("All Linux version files created successfully!")

def main():
    """Fonction principale de build multi-plateformes"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build Audeo-2 for multiple platforms"
    )
    
    parser.add_argument(
        "--platform", "-p",
        choices=["windows", "macos", "linux", "auto"],
        default="auto",
        help="Target platform (default: auto-detect)"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize Python bytecode"
    )
    
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create directory instead of single file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode"
    )
    
    args = parser.parse_args()
    
    # Déterminer la plateforme
    if args.platform == "auto":
        system = platform.system().lower()
    else:
        system = args.platform.lower()
    
    print("=" * 60)
    print(f"Building Audeo-2 for {system}...")
    print("=" * 60)
    
    try:
        if system == "windows":
            build_windows()
        elif system == "darwin":
            build_macos()
        elif system == "linux":
            build_linux()
        else:
            print(f"Unsupported platform: {system}")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
