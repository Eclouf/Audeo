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
    def __init__(self, *, title: str, size_text: str) -> None:
        super().__init__(style=toga.style.Pack(direction="row", margin=10))

        default_path = Path(__file__).resolve().parent / "ressources" / "default-200.png"
        self._default_image = toga.Image(str(default_path))

        self.thumb = toga.ImageView(style=toga.style.Pack(width=120, height=68, margin_right=10))
        self.thumb.image = self._default_image
        self.title_label = toga.Label(title, style=toga.style.Pack(font_size=12, font_weight="bold"))
        self.size_label = toga.Label(size_text, style=toga.style.Pack(margin_top=4))

        right = toga.Box(style=toga.style.Pack(direction="column", flex=1))
        right.add(self.title_label)
        right.add(self.size_label)

        self.add(self.thumb)
        self.add(right)
