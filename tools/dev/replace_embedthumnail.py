import os
import sys
import shutil
import site
import subprocess
from pathlib import Path

def get_yt_dlp_path():
    """Trouve le chemin d'installation de yt-dlp"""
    try:
        # Obtenir le chemin du package yt-dlp
        import yt_dlp
        return os.path.dirname(yt_dlp.__file__)
    except ImportError:
        return None

def backup_original_file(file_path):
    """Crée une sauvegarde du fichier original"""
    backup_path = file_path + '.backup'
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
    return backup_path

def get_embedthumbnail_path():
    """Trouve le chemin du fichier postprocessor/embedthumbnail.py"""
    yt_dlp_path = get_yt_dlp_path()
    if not yt_dlp_path:
        return None
    
    return os.path.join(yt_dlp_path, 'postprocessor', 'embedthumbnail.py')

def has_write_permission(path):
    """Vérifie si nous avons les permissions d'écriture"""
    return os.access(os.path.dirname(path), os.W_OK)

def run_as_admin():
    """Relance le script avec des privilèges administrateur"""
    if sys.platform.startswith('win'):
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            script = os.path.abspath(sys.argv[0])
            params = ' '.join(sys.argv[1:])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            if ret > 32:
                sys.exit(0)
            else:
                raise PermissionError("Impossible d'obtenir les privilèges administrateur")
    else:
        if os.geteuid() != 0:
            args = ['sudo', sys.executable] + sys.argv
            os.execvp('sudo', args)

def install_custom_embedthumbnail():
    """Installe le fichier embedthumbnail.py personnalisé"""
    try:
        # Trouver le fichier embedthumbnail.py
        target_path = get_embedthumbnail_path()
        if not target_path:
            print("Impossible de trouver l'installation de yt-dlp")
            return False

        # Vérifier les permissions
        if not has_write_permission(target_path):
            print("Permissions insuffisantes. Tentative d'exécution en tant qu'administrateur...")
            run_as_admin()
            return True

        # Créer une sauvegarde
        backup_path = backup_original_file(target_path)
        print(f"Sauvegarde créée : {backup_path}")

        # Copier le nouveau fichier
        source_path = os.path.join(os.path.dirname(__file__), 'embedthumbnail_custom.py')
        shutil.copy2(source_path, target_path)
        print(f"Fichier personnalisé installé avec succès dans : {target_path}")

        return True

    except Exception as e:
        print(f"Erreur lors de l'installation : {e}")
        return False

def restore_original_file():
    """Restaure le fichier original depuis la sauvegarde"""
    try:
        target_path = get_embedthumbnail_path()
        backup_path = target_path + '.backup'
        
        if os.path.exists(backup_path):
            if not has_write_permission(target_path):
                print("Permissions insuffisantes. Tentative d'exécution en tant qu'administrateur...")
                run_as_admin()
                return True

            shutil.copy2(backup_path, target_path)
            os.remove(backup_path)
            print("Fichier original restauré avec succès")
            return True
        else:
            print("Aucune sauvegarde trouvée")
            return False

    except Exception as e:
        print(f"Erreur lors de la restauration : {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        restore_original_file()
    else:
        install_custom_embedthumbnail()
