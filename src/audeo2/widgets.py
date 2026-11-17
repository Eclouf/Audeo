from __future__ import annotations

import math
from os import path
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import customtkinter as ctk
from PIL import Image as PILImage

from .i18n import _


def load_themed_icon(path, size=(24, 24)) -> Optional[ctk.CTkImage]:
    """Charge un PNG et remplace les pixels sombres par une teinte claire (thème sombre)."""
    try:
        img = PILImage.open(path).convert("RGBA")
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                if a > 40 and r < 100 and g < 100 and b < 100:
                    px[x, y] = (230, 230, 230, a)
        return ctk.CTkImage(img, size=size)
    except Exception:
        return None


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


class CardsBox(ctk.CTkFrame):
    """Conteneur de cartes avec une API .add() compatible avec l'ancien code Toga."""

    def add(self, widget) -> None:
        widget.pack(fill="x", padx=5, pady=8)


@dataclass
class DownloadCardModel:
    task_id: str
    title: str
    url: str
    kind: str


class DownloadCard(ctk.CTkFrame):
    def __init__(self, model: DownloadCardModel, parent=None) -> None:
        super().__init__(parent, corner_radius=10, border_width=1)
        self.model = model

        default_path = Path(__file__).resolve().parent / "ressources"
        
        # Load icons
        self._default_image = None
        try:
            if (default_path / "default-200.png").exists():
                img = PILImage.open(default_path / "default-200.png")
                self._default_image = ctk.CTkImage(img, size=(200, 120))
        except Exception:
            pass
        
        icons_dir = default_path / "pictures"
        self._play = load_themed_icon(icons_dir / "play-24.png")
        self._pause = load_themed_icon(icons_dir / "pause-24.png")
        self._stop = load_themed_icon(icons_dir / "stop-24.png")

        # Thumbnail
        self.thumb = ctk.CTkLabel(self, image=self._default_image, text="", width=200, height=120)
        self.thumb.grid(row=0, column=0, padx=8, pady=8)

        # Right side with info
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.grid_columnconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(right, text=model.title, font=("CTkFont", 13, "bold"), anchor="w")
        self.title_label.pack(anchor="w", fill="x", pady=(0, 2))
        
        self.meta_label = ctk.CTkLabel(right, text="-", anchor="w")
        self.meta_label.pack(anchor="w", fill="x", pady=1)
        
        self.status_label = ctk.CTkLabel(right, text=_("Preparing"), anchor="w")
        self.status_label.pack(anchor="w", fill="x", pady=1)
        
        self.percent_label = ctk.CTkLabel(right, text="0%", anchor="w")
        self.percent_label.pack(anchor="w", fill="x", pady=1)

        self.progress = ctk.CTkProgressBar(right, height=10)
        self.progress.pack(fill="x", pady=(4, 0))
        self.progress.set(0)
        
        # Variables pour l'animation du post-traitement
        self._post_processing_animation = None
        self._is_post_processing = False
        
        # Conteneur pour les boutons de contrôle
        controls_box = ctk.CTkFrame(self, fg_color="transparent")
        controls_box.grid(row=0, column=2, padx=8, pady=8)
        controls_box.grid_propagate(False)
        controls_box.configure(width=44)
        
        self.pause_btn = ctk.CTkButton(controls_box, text="", image=self._pause, width=36, height=36, command=self.on_pause)
        self.pause_btn.pack(pady=4)
        
        self.stop = ctk.CTkButton(controls_box, text="", image=self._stop, width=36, height=36, command=self.on_stop)
        self.stop.pack(pady=4)
        
        self.post_processing_anim = ctk.CTkLabel(controls_box, text="⏳", font=("CTkFont", 16))
        self.post_processing_anim.pack(pady=4)
        self.post_processing_anim.pack_forget()  # Hide initially
        
        self.task_id = model.task_id
        self.app = None  # Sera défini par l'application
        self.is_paused = False

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
        self.progress.set(max(0.0, min(1.0, percent)))
        self.percent_label.configure(text=f"{int(self.progress.get() * 100)}%")
        
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
            
            self.meta_label.configure(text=" | ".join(meta_parts))
        else:
            # Format standard pour les vidéos simples
            self.meta_label.configure(text=(
                f"{_fmt_bytes(downloaded_bytes)} / {_fmt_bytes(total_bytes)} | "
                f"{_fmt_speed(speed_bytes_s)} | ETA: {_fmt_eta(eta_seconds)}"
            ))
        
        if status == "finished":
            self.status_label.configure(text=_("Finished"))
        elif status == "downloading":
            self.status_label.configure(text=f"{_('Downloading')}: {int(self.progress.get() * 100)}%")
        elif status == "paused":
            self.status_label.configure(text=_("Paused"))
        elif status == "preparing":
            self.status_label.configure(text=_("Preparing"))
        elif status == "post_processing":
            self.status_label.configure(text=_("Post-processing..."))
            # Démarrer l'animation de la barre de progression
            if not self._is_post_processing:
                self._is_post_processing = True
                self._start_post_processing_animation()
        else:
            # Arrêter l'animation si on n'est plus en post-traitement
            if self._is_post_processing:
                self._is_post_processing = False
                self._stop_post_processing_animation()
            self.status_label.configure(text=status)

    def mark_error(self, message: str) -> None:
        self.status_label.configure(text=f"{_('Error')}: {message}")
        
    def on_pause(self) -> None:
        """Gère le clic sur le bouton pause"""
        if self.app and hasattr(self.app, 'manager'):
            try:
                if self.is_paused:
                    # Reprendre le téléchargement
                    self.app.manager.resume_download(self.task_id)
                    self.pause_btn.configure(image=self._pause)
                    self.status_label.configure(text=f"{_('Downloading')}...")
                    self.is_paused = False
                else:
                    # Mettre en pause le téléchargement
                    self.app.manager.pause_download(self.task_id)
                    self.pause_btn.configure(image=self._play)
                    self.status_label.configure(text=_("Paused"))
                    self.is_paused = True
            except Exception as e:
                self.status_label.configure(text=f"{_('Error')}: {str(e)}")
                
    def on_stop(self) -> None:
        """Gère le clic sur le bouton d'arrêt"""
        if self.app and hasattr(self.app, 'manager'):
            try:
                # Désactiver tous les contrôles
                self.pause_btn.configure(state="disabled")
                self.stop.configure(state="disabled")
                self.status_label.configure(text=_("Stop downloading"))
                
                # Arrêter le téléchargement via le manager
                self.app.manager.cancel_download(self.task_id)
                
                # Supprimer la carte après un court délai
                import threading
                import time
                
                def remove_card():
                    # Attendre un peu pour que l'annulation prenne effet
                    time.sleep(0.5)

                    if not self.app:
                        return

                    def _remove_card_ui() -> None:
                        if self.app and hasattr(self.app, '_cards') and hasattr(self.app, 'cards_box'):
                            try:
                                self.app._cards.pop(self.task_id, None)
                                self.destroy()
                                if hasattr(self.app, 'downloads_view') and self.app.downloads_view:
                                    self.app.downloads_view.log_info(f"{_('Cart')} {self.task_id} {_('removed')}")
                            except Exception as e:
                                if hasattr(self.app, 'downloads_view') and self.app.downloads_view:
                                    self.app.downloads_view.log_error(f"{_('Error')} {_('removing card')}: {e}")

                    try:
                        self.app.after(0, _remove_card_ui)
                    except Exception as e:
                        # Log the error but don't break the card removal process
                        if hasattr(self.app, 'downloads_view') and self.app.downloads_view:
                            self.app.downloads_view.log_debug(f"Error scheduling UI update: {e}")
                        # Continue with background removal anyway
                
                # Lancer la suppression en arrière-plan
                threading.Thread(target=remove_card, daemon=True).start()
                
            except Exception as e:
                self.status_label.configure(text=f"{_('Error')}: {str(e)}")
                self.pause_btn.configure(state="normal")
                self.stop.configure(state="normal")
                
    def set_app_reference(self, app) -> None:
        """Définit la référence à l'application principale"""
        self.app = app

    def _start_post_processing_animation(self) -> None:
        """Démarre l'animation de la barre de progression pour le post-traitement"""
        if self._is_post_processing:
            return
        
        self._is_post_processing = True
        self._post_processing_animation = True
        self.post_processing_anim.pack()  # Show the animation label
    
    def _stop_post_processing_animation(self) -> None:
        """Arrête l'animation de post-traitement"""
        self._is_post_processing = False
        self._post_processing_animation = None
        # Remettre la barre à 100% quand le post-traitement est terminé
        self.post_processing_anim.pack_forget()  # Hide the animation label


class FinishedDownloadCard(ctk.CTkFrame):
    def __init__(self, *, title: str, size_text: str, file_path: Optional[Path] = None, parent=None) -> None:
        super().__init__(parent, corner_radius=10, border_width=1)
        
        default_path = Path(__file__).resolve().parent / "ressources"
        folder_path = default_path / "pictures"
        self.file_path = file_path  # Stocker le chemin du fichier

        # Load default image
        self._default_image = None
        try:
            if (default_path / "default-200.png").exists():
                img = PILImage.open(default_path / "default-200.png")
                self._default_image = ctk.CTkImage(img, size=(120, 68))
        except Exception:
            pass

        folder_icon = load_themed_icon(folder_path / "folder-open-24.png")

        self.thumb = ctk.CTkLabel(self, image=self._default_image, text="", width=120, height=68)
        self.thumb.grid(row=0, column=0, padx=8, pady=8)
        
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.grid_columnconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(right, text=title, font=("CTkFont", 12, "bold"), anchor="w")
        self.title_label.pack(anchor="w", fill="x", pady=(0, 2))
        
        self.size_label = ctk.CTkLabel(right, text=size_text, anchor="w")
        self.size_label.pack(anchor="w", fill="x", pady=1)

        r_right = ctk.CTkFrame(self, fg_color="transparent")
        r_right.grid(row=0, column=2, padx=8, pady=8)
        r_right.grid_propagate(False)
        r_right.configure(width=44)

        file_button = ctk.CTkButton(r_right, text="", image=folder_icon, width=36, height=36, command=self._show_file)

        ctk.CTkLabel(r_right, text="").pack(expand=True)  # Spacer
        file_button.pack(pady=4)
        ctk.CTkLabel(r_right, text="").pack(expand=True)  # Spacer
        
        self.app = None  # Sera défini par l'application

    def set_app_reference(self, app) -> None:
        """Définit la référence à l'application principale"""
        self.app = app

    def _show_file(self) -> None:
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
                        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                            # Log the specific error for debugging
                            import logging
                            logging.getLogger(__name__).debug(f"File manager {fm} failed: {e}")
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
                system = platform.system()
                
                if system == "Linux":
                    error_msg = f"{_('Unable to open folder')}:\n\n{str(e)}\n\n{_('Folder')}: {self.file_path}\n\n" \
                             f"{_('Possible solutions')}:\n" \
                             f"1. {_('Install xdg-utils')}: sudo apt install xdg-utils (Ubuntu/Debian)\n" \
                             f"2. {_('Install your file manager')}: sudo apt install nautilus (GNOME)\n" \
                             f"3. {_('Or navigate manually to')}: {self.file_path}"
                else:
                    error_msg = f"{_('Unable to open folder')}:\n\n{str(e)}\n\n{_('Folder')}: {self.file_path}"
                
                if hasattr(self, 'app') and self.app:
                    self.app._show_info_dialog(_("Error"), error_msg)
        else:
            # Dossier introuvable
            if hasattr(self, 'app') and self.app:
                self.app._show_info_dialog(_("Folder not found"), f"{_('The folder no longer exists')}:\n\n{self.file_path}")