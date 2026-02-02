from __future__ import annotations

import math
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import toga


def _fmt_bytes(n: Optional[int]) -> str:
    if n is None:
        return "-"
    if n <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = min(int(math.log(n, 1024)), len(units) - 1)
    v = n / (1024**i)
    return f"{v:.1f} {units[i]}"


def _fmt_eta(seconds: Optional[int]) -> str:
    if seconds is None:
        return "-"
    m, s = divmod(max(0, int(seconds)), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _fmt_speed(n: Optional[float]) -> str:
    if n is None:
        return "-"
    if n <= 0:
        return "0 B/s"
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    i = 0
    v = float(n)
    while v >= 1024.0 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.2f} {units[i]}"


@dataclass
class DownloadCardModel:
    task_id: str
    title: str
    url: str
    kind: str


class DownloadCard(toga.Box):
    def __init__(self, model: DownloadCardModel) -> None:
        super().__init__(style=toga.style.Pack(direction="row", margin=2, background_color="#888888"))
        self.model = model

        default_path = Path(__file__).resolve().parent / "ressources"
        self._default_image = toga.Image(str(default_path / "default-200.png"))
        self._play = toga.Icon(str(default_path / "pictures" / "play-24.png"))
        self._pause = toga.Icon(str(default_path / "pictures" / "pause-24.png"))
        self._stop = toga.Icon(str(default_path / "pictures" / "stop-24.png"))

        self.thumb = toga.ImageView(style=toga.style.Pack(width=200, height=120, margin=(5, 5, 5, 5)))
        self.thumb.image = self._default_image

        self.title_label = toga.Label(model.title, style=toga.style.Pack(font_size=12, font_weight="bold"))
        self.meta_label = toga.Label("-", style=toga.style.Pack(margin_top=2))
        self.status_label = toga.Label("En attente", style=toga.style.Pack(margin_top=4))
        self.percent_label = toga.Label("0%", style=toga.style.Pack(margin_top=4))

        self.progress = toga.ProgressBar(max=1.0, style=toga.style.Pack(margin_top=6, flex=1))
        self.progress.value = 0.0
        
        # Conteneur pour les boutons de contrôle
        self.controls_box = toga.Box(style=toga.style.Pack(direction="column", margin_top=4))
        
        self.pause_btn = toga.Button(icon=self._pause, on_press=self.on_pause, style=toga.style.Pack(margin=3))
        self.stop = toga.Button(icon=self._stop, on_press=self.on_stop, style=toga.style.Pack(margin=3))
        
        self.controls_box.add(self.pause_btn)
        self.controls_box.add(self.stop)
        
        self.task_id = model.task_id
        self.app = None  # Sera défini par l'application
        self.is_paused = False

        right = toga.Box(style=toga.style.Pack(direction="column", margin=(5, 5, 5, 5), flex=1))
        right.add(self.title_label)
        right.add(self.meta_label)
        right.add(self.status_label)
        right.add(self.percent_label)
        right.add(self.progress)
        
        r_right = toga.Box(style=toga.style.Pack(direction="column", margin=(5, 5, 5, 5)))
        r_right.add(self.controls_box)

        # Conteneur principal avec cadre
        main_container = toga.Box(
            children=[self.thumb, right, r_right],
            style=toga.style.Pack(
                direction="row", 
                margin=1.5, 
                background_color="#f0f0f0", #couleur de fond
                flex=1
            )
        )
        
        self.add(main_container)

    def update_progress(
        self,
        *,
        percent: float,
        downloaded_bytes: Optional[int],
        total_bytes: Optional[int],
        eta_seconds: Optional[int],
        status: str,
        speed_bytes_s: Optional[float] = None,
        item_number: Optional[int] = None,
        total_items: Optional[int] = None,
        duration: Optional[int] = None,
        uploader: Optional[str] = None,
    ) -> None:
        self.progress.value = max(0.0, min(1.0, percent))
        self.percent_label.text = f"{int (self.progress.value * 100)}%"
        
        # Adapter l'affichage pour les playlists
        if item_number and total_items:
            # Format pour les playlists
            meta_parts = []
            # Ajouter les infos d'item en premier
            meta_parts.append(f"Items: {item_number}/{total_items}")
            if downloaded_bytes is not None and total_bytes is not None:
                meta_parts.append(f"{_fmt_bytes(downloaded_bytes)} / {_fmt_bytes(total_bytes)}")
            if speed_bytes_s is not None:
                meta_parts.append(f"{_fmt_speed(speed_bytes_s)}")
            if eta_seconds is not None:
                meta_parts.append(f"ETA: {_fmt_eta(eta_seconds)}")
            
            self.meta_label.text = " | ".join(meta_parts)
        else:
            # Format standard pour les vidéos simples
            self.meta_label.text = (
                f"{_fmt_bytes(downloaded_bytes)} / {_fmt_bytes(total_bytes)} | "
                f"{_fmt_speed(speed_bytes_s)} | ETA: {_fmt_eta(eta_seconds)}"
            )
        
        if status == "finished":
            self.status_label.text = "Terminé"
        elif status == "downloading":
            self.status_label.text = f"Téléchargement: {int(self.progress.value * 100)}%"
        elif status == "paused":
            self.status_label.text = "En pause"
        elif status == "preparing":
            self.status_label.text = "Préparation..."
        else:
            self.status_label.text = status

    def mark_error(self, message: str) -> None:
        self.status_label.text = f"Erreur: {message}"
        
    def on_pause(self, widget: toga.Button) -> None:
        """Gère le clic sur le bouton pause"""
        if self.app and hasattr(self.app, 'manager'):
            try:
                if self.is_paused:
                    # Reprendre le téléchargement
                    self.app.manager.resume_download(self.task_id)
                    self.pause_btn.icon = self._pause
                    self.status_label.text = "Téléchargement..."
                    self.is_paused = False
                else:
                    # Mettre en pause le téléchargement
                    self.app.manager.pause_download(self.task_id)
                    self.pause_btn.icon = self._play
                    self.status_label.text = "En pause"
                    self.is_paused = True
            except Exception as e:
                self.status_label.text = f"Erreur pause: {str(e)}"
                
    def on_stop(self, widget: toga.Button) -> None:
        """Gère le clic sur le bouton d'arrêt"""
        if self.app and hasattr(self.app, 'manager'):
            try:
                # Désactiver tous les contrôles
                self.pause_btn.enabled = False
                self.stop.enabled = False
                self.status_label.text = "Arrêt en cours..."
                
                # Arrêter le téléchargement via le manager
                self.app.manager.cancel_download(self.task_id)
                
                # Supprimer la carte après un court délai
                import threading
                import time
                
                def remove_card():
                    # Attendre un peu pour que l'annulation prenne effet
                    time.sleep(0.5)
                    
                    # Supprimer la carte de l'interface
                    if self.app and hasattr(self.app, '_cards') and hasattr(self.app, 'cards_box'):
                        try:
                            # Supprimer du dictionnaire des cartes
                            self.app._cards.pop(self.task_id, None)
                            
                            # Supprimer de l'interface
                            self.app.cards_box.remove(self)
                            
                            # Utiliser la bonne référence pour le logging
                            if hasattr(self.app, 'downloads_view') and self.app.downloads_view:
                                self.app.downloads_view.log_info(f"Carte {self.task_id} supprimée")
                        except Exception as e:
                            if hasattr(self.app, 'downloads_view') and self.app.downloads_view:
                                self.app.downloads_view.log_error(f"Erreur suppression carte: {e}")
                
                # Lancer la suppression en arrière-plan
                threading.Thread(target=remove_card, daemon=True).start()
                
            except Exception as e:
                self.status_label.text = f"Erreur arrêt: {str(e)}"
                self.pause_btn.enabled = True
                self.stop.enabled = True
                
    def set_app_reference(self, app) -> None:
        """Définit la référence à l'application principale"""
        self.app = app


class FinishedDownloadCard(toga.Box):
    def __init__(self, *, title: str, size_text: str, file_path: Optional[Path] = None) -> None:
        super().__init__(style=toga.style.Pack(direction="row", margin=2, background_color="#888888"))

        default_path = Path(__file__).resolve().parent / "ressources" / "default-200.png"
        self._default_image = toga.Image(str(default_path))
        self.file_path = file_path  # Stocker le chemin du fichier

        self.thumb = toga.ImageView(style=toga.style.Pack(width=120, height=68, margin=(5, 5, 5, 5)))
        self.thumb.image = self._default_image
        self.title_label = toga.Label(title, style=toga.style.Pack(font_size=12, font_weight="bold"))
        self.size_label = toga.Label(size_text, style=toga.style.Pack(margin_top=4))

        right = toga.Box(style=toga.style.Pack(direction="column", margin=(5, 5, 5, 5)))
        right.add(self.title_label)
        right.add(self.size_label)
        
        file_button = toga.Button("Fichier", on_press=self._show_file)
        r_right = toga.Box(style=toga.style.Pack(direction="column", margin=(5, 5, 5, 5)))
        r_right.add(file_button)
        
        main_container = toga.Box(
            children=[self.thumb, right, r_right],
            style=toga.style.Pack(
                direction="row", 
                margin=1.5, 
                background_color="#f0f0f0", #couleur de fond
                flex=1
            )
        )

        self.add(main_container)
        self.app = None  # Sera défini par l'application

    def set_app_reference(self, app) -> None:
        """Définit la référence à l'application principale"""
        self.app = app

    def _show_file(self, widget: toga.Button) -> None:
        """Ouvre le dossier de destination dans l'explorateur système"""
        if self.file_path and self.file_path.exists():
            try:
                import os
                import subprocess
                import platform
                
                system = platform.system()
                
                if system == "Windows":
                    # Windows : ouvre l'explorateur sur le dossier
                    os.startfile(str(self.file_path))
                elif system == "Darwin":  # macOS
                    # macOS : ouvre Finder sur le dossier
                    subprocess.run(["open", str(self.file_path)], check=True)
                elif system == "Linux":
                    # Linux : essaie différentes méthodes avec meilleure gestion d'erreur
                    success = False
                    
                    # Liste des gestionnaires de fichiers à essayer
                    file_managers = [
                        ("nautilus", "GNOME"),
                        ("dolphin", "KDE"), 
                        ("thunar", "XFCE"),
                        ("pcmanfm", "LXDE"),
                        ("caja", "MATE"),
                        ("nemo", "Cinnamon")
                    ]
                    
                    for fm, desktop in file_managers:
                        try:
                            subprocess.run([fm, str(self.file_path)], check=True, timeout=5)
                            success = True
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                            continue
                    
                    # Si aucun gestionnaire de fichiers n'a fonctionné, essayer xdg-open
                    if not success:
                        try:
                            subprocess.run(["xdg-open", str(self.file_path)], check=True, timeout=5)
                            success = True
                        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                            pass
                    
                    # Si tout a échoué, essayer d'ouvrir avec le navigateur de fichiers par défaut
                    if not success:
                        try:
                            # Utiliser python-magic pour détecter le type ou fallback simple
                            import webbrowser
                            webbrowser.open(f"file://{self.file_path}")
                            success = True
                        except Exception:
                            pass
                else:
                    # Système non supporté : fallback vers xdg-open
                    subprocess.run(["xdg-open", str(self.file_path)], check=True)
                    
            except Exception as e:
                # En cas d'erreur, affiche un message d'erreur informatif
                import toga
                system = platform.system()
                
                if system == "Linux":
                    error_msg = f"Impossible d'ouvrir le dossier:\n\n{str(e)}\n\nDossier: {self.file_path}\n\n" \
                             "Solutions possibles:\n" \
                             "1. Installer xdg-utils: sudo apt install xdg-utils (Ubuntu/Debian)\n" \
                             "2. Installer votre gestionnaire de fichiers: sudo apt install nautilus (GNOME)\n" \
                             "3. Ou naviguez manuellement vers: {self.file_path}"
                else:
                    error_msg = f"Impossible d'ouvrir le dossier:\n\n{str(e)}\n\nDossier: {self.file_path}"
                
                dialog = toga.InfoDialog(
                    title="Erreur",
                    message=error_msg
                )
                # Créer une tâche async pour le dialogue
                import asyncio
                if hasattr(self, 'app') and hasattr(self.app, 'main_window'):
                    asyncio.create_task(self.app.main_window.dialog(dialog))
        else:
            # Dossier introuvable
            import toga
            dialog = toga.InfoDialog(
                title="Dossier introuvable",
                message=f"Le dossier n'existe plus:\n\n{self.file_path}"
            )
            # Créer une tâche async pour le dialogue
            import asyncio
            if hasattr(self, 'app') and hasattr(self.app, 'main_window'):
                asyncio.create_task(self.app.main_window.dialog(dialog))