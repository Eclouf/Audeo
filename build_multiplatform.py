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
        'version': '0.6.0',
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
    """Build pour Windows avec support natif harmonisé"""
    root = Path(__file__).parent
    
    print("============================================================")
    print("                   Audeo Build Script                        ")
    print("============================================================")
    
    # Nettoyer les anciens builds
    dist_dir = root / "dist"
    build_dir = root / "build"
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"Cleaned {dist_dir}")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"Cleaned {build_dir}")
    
    # Préparer l'icône
    icon_path = root / "src" / "audeo2" / "ressources" / "audeo.ico"
    icon_png = root / "src" / "audeo2" / "ressources" / "audeo.png"
    
    if not icon_path.exists() and icon_png.exists():
        print(f"Converting PNG to ICO...")
        try:
            from PIL import Image
            img = Image.open(icon_png)
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            img.save(icon_path, "ICO")
            print(f"Icon created: {icon_path}")
        except Exception as e:
            print(f"Could not convert icon: {e}")
    
    # Commande PyInstaller harmonisée pour Windows
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
        "--hidden-import", "toga_winforms",
        "--hidden-import", "winforms",
        "--hidden-import", "System.Drawing",
        "--hidden-import", "System.Windows.Forms",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "pillow",
        "--exclude-module", "toga_cocoa",
        "--exclude-module", "toga_gtk",
        "--exclude-module", "toga_android",
        "--exclude-module", "toga_iOS",
        "--exclude-module", "toga_web",
        # Exclusions pour réduire la taille
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "jupyter",
        "--exclude-module", "IPython",
        "--exclude-module", "notebook",
        "--exclude-module", "pytest",
        "--exclude-module", "sphinx",
        "--exclude-module", "pip",
        "--exclude-module", "setuptools",
        "--exclude-module", "wheel",
        #"--exclude-module", "distutils",
        "--add-data", f"{root}/src/audeo2/ressources{os.pathsep}audeo2/ressources",
        "--add-data", f"{root}/src/audeo2/locales{os.pathsep}audeo2/locales",
        "audeo_runner.py"
    ]
    
    # Ajouter l'icône si disponible
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Ajouter le fichier de version si disponible
    version_file = root / "version.txt"
    if version_file.exists():
        cmd.extend(["--version-file", str(version_file)])
    
    # Gérer les arguments supplémentaires
    if hasattr(build_windows, 'onedir') and build_windows.onedir:
        cmd.remove("--onefile")
        cmd.append("--onedir")
        print("Mode: Multiple files (onedir)")
    else:
        print("Mode: Single file")
    
    # L'optimisation PyInstaller est désactivée car elle cause plus de problèmes que de bénéfices
    # if hasattr(build_windows, 'optimize') and build_windows.optimize:
    #     cmd.extend(["--optimize", "1"])
    #     print("Optimizing bytecode (level 1)...")
    
    if hasattr(build_windows, 'debug') and build_windows.debug:
        print("Debug mode enabled")
    else:
        cmd.append("--noconfirm")
    
    print("Building Windows executable with WinForms support...")
    print(f"Command: {' '.join(cmd[:8])} ...")
    
    try:
        subprocess.run(cmd, check=True)
        print("Windows build completed successfully!")
        
        # Vérifier l'exécutable
        exe_path = dist_dir / "Audeo.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
            return True
        else:
            print("Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

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
    
    # Commande PyInstaller harmonisée pour macOS
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
        "--hidden-import", "yt_dlp",
        "--hidden-import", "pillow",
        "--exclude-module", "toga_winforms",
        "--exclude-module", "toga_gtk",
        "--exclude-module", "toga_android",
        "--exclude-module", "toga_iOS",
        "--exclude-module", "toga_web",
        # Exclusions pour réduire la taille
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "jupyter",
        "--exclude-module", "IPython",
        "--exclude-module", "notebook",
        "--exclude-module", "pytest",
        "--exclude-module", "sphinx",
        "--exclude-module", "pip",
        "--exclude-module", "setuptools",
        "--exclude-module", "wheel",
        "--exclude-module", "distutils",
        "--add-data", f"{root}/src/audeo2/ressources{os.pathsep}audeo2/ressources",
        "--add-data", f"{root}/src/audeo2/locales{os.pathsep}audeo2/locales",
        "audeo_runner.py"
    ]
    
    # L'optimisation PyInstaller est désactivée car elle cause plus de problèmes que de bénéfices
    # if hasattr(build_macos, 'onedir') and build_macos.onedir:
    #     cmd.remove("--onefile")
    #     cmd.append("--onedir")
    #     print("Mode: Multiple files (onedir)")
    # else:
    #     print("Mode: Single file")
    
    # if hasattr(build_macos, 'optimize') and build_macos.optimize:
    #     cmd.extend(["--optimize", "1"])
    #     print("Optimizing bytecode (level 1)...")
    
    if hasattr(build_macos, 'debug') and build_macos.debug:
        print("Debug mode enabled")
    else:
        cmd.append("--noconfirm")
    
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
    
    version_info = "0.6.0"
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
    import sys  # Import manquant
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
    
    # Commande PyInstaller harmonisée pour Linux/GTK
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
        "--hidden-import", "yt_dlp",
        "--hidden-import", "pillow",
        "--exclude-module", "toga_winforms",
        "--exclude-module", "toga_cocoa", 
        "--exclude-module", "toga_android",
        "--exclude-module", "toga_iOS",
        "--exclude-module", "toga_web",
        "--add-data", f"{root}/src/audeo2/ressources{os.pathsep}audeo2/ressources",
        "--add-data", f"{root}/src/audeo2/locales{os.pathsep}audeo2/locales",
        "audeo_runner.py"
    ]
    
    # L'optimisation PyInstaller est désactivée car elle cause plus de problèmes que de bénéfices
    # if hasattr(build_linux, 'onedir') and build_linux.onedir:
    #     cmd.remove("--onefile")
    #     cmd.append("--onedir")
    #     print("Mode: Multiple files (onedir)")
    # else:
    #     print("Mode: Single file")
    
    # if hasattr(build_linux, 'optimize') and build_linux.optimize:
    #     cmd.extend(["--optimize", "1"])
    #     print("Optimizing bytecode (level 1)...")
    
    if hasattr(build_linux, 'debug') and build_linux.debug:
        print("Debug mode enabled")
    else:
        cmd.append("--noconfirm")
    
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
            
            # Créer les packages de distribution Linux
            try:
                sys.path.insert(0, str(root / "devscripts"))
                from linux_dist import linux_dist
                
                # Chemins des fichiers pour linux_dist
                exe_path = dist_dir / "Audeo"
                desktop_path = root / "audeo2.desktop"
                metainfo_path = root / "com.eclouf.audeo2.metainfo.xml"
                
                if linux_dist(exe_path, desktop_path, metainfo_path):
                    print("Linux distribution packages created successfully!")
                else:
                    print("Warning: Linux distribution packages creation failed")
                    
            except Exception as e:
                print(f"Warning: Could not create Linux distribution packages: {e}")
            
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
    
    version_info = "0.6.0"
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
    <release version="{version_info}" date="2026-02-28">
      <description>
        <p>Major release with comprehensive multi-language support and internationalization</p>
        <p xml:lang="fr">Version majeure avec support multi-langues complet et internationalisation</p>
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
        help="[DÉSACTIVÉ] L'optimisation PyInstaller cause plus de problèmes que de bénéfices"
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
            # Passer les arguments à build_windows
            build_windows.onedir = args.onedir
            build_windows.optimize = args.optimize
            build_windows.debug = args.debug
            success = build_windows()
        elif system == "darwin":
            success = build_macos()
        elif system == "linux":
            success = build_linux()
        else:
            print(f"Unsupported platform: {system}")
            sys.exit(1)
        
        if success:
            print("\n" + "=" * 60)
            print("Build completed successfully!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("Build failed!")
            print("=" * 60)
            sys.exit(1)
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
