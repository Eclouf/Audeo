from __future__ import annotations

from io import BytesIO
import asyncio
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.request import urlretrieve

import toga
from toga.style import Pack

from PIL import Image as PILImage
import imageio_ffmpeg

from .download_manager import DownloadManager, DownloadProgress
from .widgets import DownloadCard, DownloadCardModel, FinishedDownloadCard
from .views import DownloadsView, FinishedDownloadsView, VideoInfoView, SettingsView
from .settings import AppSettings, load_settings, save_settings
from .ffmpeg import FFmpegManager
from .i18n import i18n

FRAME_COLOR = "#d3d3d3"
FRAME_THICKNESS = 1.5

class Audeo2App(toga.App):
    def startup(self) -> None:
        self.download_dir = Path.home() / "Downloads" / "Audeo-2"
        self.max_workers = 3

        cfg_dir = Path(str(self.paths.config))
        try:
            cfg_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            cfg_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Audeo-2" / "Config"
            cfg_dir.mkdir(parents=True, exist_ok=True)
        if not cfg_dir.exists():
            cfg_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Audeo-2" / "Config"
            cfg_dir.mkdir(parents=True, exist_ok=True)

        self.config_dir = cfg_dir

        self.settings: AppSettings = load_settings(self.config_dir)
        
        # Appliquer la langue sauvegardée
        i18n.set_language(self.settings.general.lang_code)
        
        # Vérifier si le chemin ffmpeg sauvegardé existe
        if self.settings.ffmpeg_path and not Path(self.settings.ffmpeg_path).exists():
            print(f"[Startup] Saved ffmpeg path does not exist: {self.settings.ffmpeg_path}")
            print("[Startup] Resetting ffmpeg path")
            self.settings.ffmpeg_path = None
            # Sauvegarder immédiatement
            try:
                save_settings(self.config_dir, self.settings)
            except Exception:
                pass
        
        try:
            settings_path = self.config_dir / "settings.json"
            if not settings_path.exists():
                save_settings(self.config_dir, self.settings)
        except Exception:
            pass

        self._cards: dict[str, DownloadCard] = {}
        self._thumb_cache: dict[str, Path] = {}
        self._thumb_inflight: set[str] = set()

        self.main_window = toga.MainWindow(title=self.formal_name, size=(1100, 600))

        app_icon_path = Path(__file__).resolve().parent / "ressources" / "audeo.png"
        if app_icon_path.exists():
            try:
                self.icon = toga.Icon(str(app_icon_path))
                self.main_window.icon = self.icon
            except Exception:
                pass

        self.nav_box = toga.Box(style=Pack(direction="column", margin=(5)))
        
        def icon_button(icon_name:str, action:str):
            icons_dir = Path(__file__).resolve().parent / "ressources" / "pictures"
            
            if sys.platform == "win32":
                size = 38
            else:
                size = 49
            
            icon_path = icons_dir / f"{icon_name}-24.png"
            return toga.Button(
                icon=toga.Icon(str(icon_path)),
                on_press=action,
                style=Pack(margin=1, width=size, height=size)
            )

        self.nav_btn_downloads = icon_button("download", self._go_downloads)  
        
        self.nav_btn_info = icon_button("info", self._go_info)
        
        self.nav_btn_finished = icon_button("list_end", self._go_finished)
        
        self.nav_btn_settings = icon_button("settings", self._go_settings)
    
        self.nav_box.add(self.nav_btn_downloads)
        self.nav_box.add(self.nav_btn_info)
        self.nav_box.add(self.nav_btn_finished)
        self.nav_box.add(self.nav_btn_settings)

        # Créer les vues
        self.downloads_view = DownloadsView(self)
        self.finished_downloads_view = FinishedDownloadsView(self)
        self.video_info_view = VideoInfoView(self)
        self.settings_view = SettingsView(self)

        # Créer le manager après avoir créé les vues
        self.manager = self._build_manager()

        self.url_input = self.downloads_view.url_input
        self.kind_select = self.downloads_view.kind_select
        self.cards_box = self.downloads_view.cards_box
        self.finished_cards_box = self.finished_downloads_view.cards_box

        self.content = toga.Box(style=Pack(direction="column", flex=1))
        self._show_view("Téléchargements")
        self.cadre = toga.Box(
            children=[
                toga.Box(style=Pack(background_color=FRAME_COLOR, height=FRAME_THICKNESS)),
                self.content,
                toga.Box(style=Pack(background_color=FRAME_COLOR, height=FRAME_THICKNESS))
            ],
            style=Pack(direction="column", flex=1)
        )

        root = toga.Box(style=Pack(direction="row", flex=1))
        root.add(self.nav_box)
        root.add(toga.Box(children=[
            toga.Box(style=Pack(height=5)),
            toga.Box(children=[
                toga.Box(style=Pack(background_color=FRAME_COLOR, width=FRAME_THICKNESS)),
                self.cadre,
                toga.Box(style=Pack(background_color=FRAME_COLOR, width=FRAME_THICKNESS))
                ], style=Pack(direction="row", flex=1)),
            toga.Box(style=Pack(height=5))
           ], style=Pack(direction="column", flex=1)))
        root.add(toga.Box(style=Pack(width=5)))

        self.main_window.content = root
        self.main_window.show()

        self._bootstrap_ffmpeg()

    

    def notify_language_change(self) -> None:
        """Reconstruit toutes les vues quand la langue change"""
        try:
            # Reconstruire directement chaque vue
            self.downloads_view.__init__(self)
            self.finished_downloads_view.__init__(self)
            self.video_info_view.__init__(self)
            self.settings_view.__init__(self)
            
            # Mettre à jour le contenu de l'OptionContainer
            self.main_window.content.refresh()
            
        except Exception as e:
            print(f"Erreur lors de la reconstruction des vues: {e}")
    
    def save_settings(self) -> None:
        save_settings(self.config_dir, self.settings)

    def _update_progress_ui(self, progress_bar, details_label, percent, message):
        """Met à jour la GUI de progression (appelée depuis le thread principal)"""
        try:
            progress_bar.value = percent
            details_label.text = message
            print(f"[Progress] {percent}% - {message}")
        except Exception as e:
            print(f"[Progress update error] {e}")

    def _bootstrap_ffmpeg(self) -> None:
        """Vérifie et télécharge ffmpeg/ffprobe si nécessaire"""
        # Créer le gestionnaire ffmpeg
        ffmpeg_mgr = FFmpegManager(ffmpeg_path=self.settings.ffmpeg_path)
        
        # Vérifier si ffmpeg est déjà disponible
        if ffmpeg_mgr.is_available():
            print(f"[Bootstrap] ffmpeg already available: {self.settings.ffmpeg_path}")
            return
        
        # Réinitialiser le chemin s'il n'existe plus
        self.settings.ffmpeg_path = None
        self.save_settings()

        # Planifier le dialogue et téléchargement
        async def _prompt_and_install() -> None:
            try:
                dialog = toga.QuestionDialog(
                    "Télécharger ffmpeg complet ?",
                    "ffmpeg et ffprobe sont nécessaires pour l'extraction audio, l'intégration de vignettes et certaines options.\n\nSouhaitez-vous les télécharger automatiquement ?",
                )
                ok = await self.main_window.dialog(dialog)
            except Exception as e:
                print(f"[Bootstrap] Dialog error: {e}")
                ok = False

            if not ok:
                print("[Bootstrap] FFmpeg download declined by user")
                return

            print("[Bootstrap] Starting FFmpeg download...")
            
            # Créer une fenêtre de progression
            progress_box = toga.Box(style=Pack(direction="column", padding=20, flex=1))
            
            status_label = toga.Label(
                "Téléchargement de ffmpeg...",
                style=Pack(padding=10)
            )
            progress_bar = toga.ProgressBar(
                max=100,
                style=Pack(padding=10, flex=1)
            )
            details_label = toga.Label(
                "Initialisation...",
                style=Pack(padding=10)
            )
            
            progress_box.add(status_label)
            progress_box.add(progress_bar)
            progress_box.add(details_label)
            
            progress_window = toga.Window(
                title="Téléchargement ffmpeg",
                content=progress_box,
                size=(400, 80)
            )
            progress_window.show()
            
            # Créer le callback de progression thread-safe
            def on_progress(percent, message):
                """Callback appelé par le téléchargeur (depuis un thread)"""
                # Mettre à jour la GUI de façon thread-safe
                self.loop.call_soon_threadsafe(
                    self._update_progress_ui, 
                    progress_bar, 
                    details_label, 
                    percent, 
                    message
                )
            
            try:
                exe = await self.loop.run_in_executor(
                    None, 
                    lambda: ffmpeg_mgr.download_and_install(progress_callback=on_progress)
                )
                if exe:
                    self.settings.ffmpeg_path = str(exe)
                    self.save_settings()
                    print(f"[Bootstrap] FFmpeg saved: {exe}")
                    status_label.text = "ffmpeg installé avec succès!"
                    progress_bar.value = 100
                    details_label.text = str(exe)
                    # Fermer la fenêtre après 2 secondes
                    await asyncio.sleep(2)
                    progress_window.close()
                else:
                    print("[Bootstrap] FFmpeg download failed (returned None)")
                    status_label.text = "Erreur lors du téléchargement"
                    details_label.text = "Veuillez réessayer plus tard"
            except Exception as e:
                print(f"[Bootstrap] FFmpeg download error: {e}")
                import traceback
                traceback.print_exc()
                status_label.text = "Erreur lors du téléchargement"
                details_label.text = str(e)

        try:
            # Utiliser call_soon pour planifier après le démarrage complet
            self.loop.call_soon(lambda: asyncio.create_task(_prompt_and_install()))
        except Exception as e:
            print(f"[Bootstrap] Error: {e}")

    def _build_downloads_view(self) -> toga.Widget:
        raise RuntimeError("This method is no longer used; use audeo2.views.DownloadsView")

    def _build_info_view(self) -> toga.Widget:
        raise RuntimeError("This method is no longer used; use audeo2.views.infoView")

    def _build_settings_view(self) -> toga.Widget:
        raise RuntimeError("This method is no longer used; use audeo2.views.SettingsView")

    def _go_downloads(self, widget: toga.Button) -> None:
        self._show_view("Téléchargements")

    def _go_info(self, widget: toga.Button) -> None:
        self._show_view("Informations")

    def _go_finished(self, widget: toga.Button) -> None:
        self._show_view("Terminés")

    def _go_settings(self, widget: toga.Button) -> None:
        self._show_view("Paramètres")

    def _show_view(self, name: str) -> None:
        self.content.clear()
        if name == "Téléchargements":
            self.content.add(self.downloads_view.widget)
        elif name == "Informations":
            self.content.add(self.video_info_view.widget)
        elif name == "Terminés":
            self.content.add(self.finished_downloads_view.widget)
        else:
            self.content.add(self.settings_view.widget)

    def _fmt_bytes(self, n: Optional[int]) -> str:
        if n is None:
            return "-"
        if n <= 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        v = float(n)
        while v >= 1024.0 and i < len(units) - 1:
            v /= 1024.0
            i += 1
        return f"{v:.1f} {units[i]}"

    def _build_manager(self) -> DownloadManager:
        self.manager = DownloadManager(
            max_workers=self.max_workers,
            on_progress=self._threadsafe_progress,
            on_finished=self._threadsafe_finished,
            on_error=self._threadsafe_error,
            downloads_view=self.downloads_view,
            main_window=self.main_window,
            on_tasks_ready=self._on_tasks_ready,
        )
        return self.manager

    def _on_add(self, widget: toga.Button) -> None:
        url = (self.downloads_view.url_input.value or "").strip()
        if not url:
            return

        if not self._is_valid_url(url):
            # Utiliser la méthode recommandée pour les dialogues dans les handlers synchrones
            dialog = toga.InfoDialog(
                title=_("Invalid URL"),
                message=_("Please enter a valid URL http(s)")
            )
            # Créer une tâche async pour le dialogue
            import asyncio
            task = asyncio.create_task(self.main_window.dialog(dialog))
            # Pas besoin de callback pour un simple dialogue d'information
            return

        kind = str(self.downloads_view.kind_select.value.value or "video")

        # Lancer le téléchargement (retourne immédiatement, les tâches seront créées de manière asynchrone)
        self.manager.submit(url=url, output_dir=self.download_dir, kind=kind, settings=self.settings)
        
        # L'interface reste responsive, les cartes seront créées via le callback _on_tasks_ready
        self.downloads_view.url_input.value = ""

    def _is_valid_url(self, url: str) -> bool:
        try:
            parts = urlparse(url)
        except Exception:
            return False
        if parts.scheme not in {"http", "https"}:
            return False
        if not parts.netloc:
            return False
        return True

    def _on_tasks_ready(self, tasks):
        """Callback appelé quand les tâches de téléchargement sont prêtes"""
        if tasks is None:
            # Erreur fatale, ne rien faire
            return
        
        # Créer une carte pour chaque tâche
        for task in tasks:
            card = DownloadCard(DownloadCardModel(task_id=task.task_id, title=task.url, url=task.url, kind=task.kind))
            card.set_app_reference(self)  # Définir la référence à l'application
            self._cards[task.task_id] = card
            self.downloads_view.cards_box.add(card)
            
        # Mettre à jour l'affichage
        self.downloads_view._update_content_display()

    def _threadsafe_progress(self, progress: DownloadProgress) -> None:
        self.loop.call_soon_threadsafe(self._apply_progress, progress)

    def _threadsafe_finished(self, task_id: str) -> None:
        self.loop.call_soon_threadsafe(self._apply_finished, task_id)

    def _threadsafe_error(self, task_id: str, e: Exception) -> None:
        self.loop.call_soon_threadsafe(self._apply_error, task_id, e)

    def _apply_progress(self, progress: DownloadProgress) -> None:
        card = self._cards.get(progress.task_id)
        if not card:
            return
                
        if progress.title:
            card.title_label.text = progress.title
        if progress.thumbnail_url:
            self._ensure_thumbnail(progress.thumbnail_url, card)
        card.update_progress(
            percent=progress.percent,
            downloaded_bytes=progress.downloaded_bytes,
            total_bytes=progress.total_bytes,
            eta_seconds=progress.eta_seconds,
            status=progress.status,
            speed_bytes_s=progress.speed_bytes_s,
            item_number=progress.item_number,
            total_items=progress.total_items,
            duration=progress.duration,
            uploader=progress.uploader,
        )

    def _ensure_thumbnail(self, url: str, card: DownloadCard) -> None:
        cached = self._thumb_cache.get(url)
        if cached and cached.exists():
            current = card.thumb.image
            default_img = getattr(card, "_default_image", None)
            if current is None or (default_img is not None and current is default_img):
                try:
                    card.thumb.image = toga.Image(str(cached))
                except Exception:
                    return
            return

        if url in self._thumb_inflight:
            return
        self._thumb_inflight.add(url)

        def _bg() -> None:
            try:
                target_dir = Path(self.paths.cache) / "thumbs"
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / f"{abs(hash(url))}.png"
                if not target.exists():
                    with urlopen(url, timeout=15) as resp:
                        data = resp.read()
                    img = PILImage.open(BytesIO(data))
                    img = img.convert("RGB")
                    img.thumbnail((480, 270))
                    img.save(target, format="PNG", optimize=True)
                self.loop.call_soon_threadsafe(_apply, target)
            except Exception:
                self.loop.call_soon_threadsafe(_clear_inflight)
                return

        def _apply(path: Path) -> None:
            self._thumb_cache[url] = path
            _clear_inflight(url)
            current = card.thumb.image
            default_img = getattr(card, "_default_image", None)
            if current is None or (default_img is not None and current is default_img):
                try:
                    card.thumb.image = toga.Image(str(path))
                except Exception:
                    return

        def _clear_inflight(u: str = url) -> None:
            self._thumb_inflight.discard(u)

        self.manager._executor.submit(_bg)

    def _apply_finished(self, task_id: str) -> None:
        card = self._cards.get(task_id)
        if not card:
            return

        # Utiliser le dossier de destination directement
        download_dir = Path(self.download_dir)
        size_text = "-"
        
        self.downloads_view.log_info(f"Téléchargement terminé pour: {card.title_label.text}")

        finished_card = FinishedDownloadCard(title=card.title_label.text, size_text=size_text, file_path=download_dir)
        finished_card.set_app_reference(self)  # Définir la référence à l'application
        if card.thumb.image is not None:
            finished_card.thumb.image = card.thumb.image

        try:
            self.downloads_view.cards_box.remove(card)
        except Exception:
            pass
        self.finished_downloads_view.cards_box.add(finished_card)
        self._cards.pop(task_id, None)
        
        # Mettre à jour l'affichage
        self.downloads_view._update_content_display()

    def _apply_error(self, task_id: str, e: Exception) -> None:
        card = self._cards.get(task_id)
        if card:
            card.mark_error(str(e))
            # Afficher une fenêtre de dialogue d'erreur avec la nouvelle syntaxe
            dialog = toga.ErrorDialog(
                title="Erreur de téléchargement",
                message=f"Une erreur est survenue lors du téléchargement:\n\n{str(e)}"
            )
            # Créer une tâche async pour le dialogue
            import asyncio
            task = asyncio.create_task(self.main_window.dialog(dialog))

    def _on_clear_finished(self, widget: toga.Button) -> None:
        try:
            self.finished_downloads_view.cards_box.clear()
        except Exception:
            # Fallback: remove children one by one
            for child in list(getattr(self.finished_downloads_view.cards_box, "children", [])):
                try:
                    self.finished_downloads_view.cards_box.remove(child)
                except Exception:
                    pass

DESCRIPTION = """
Audeo is a user-friendly application built with Python and Toga that enables users to download audio and video content from various online sources.
The application provides a queue-based management system, download tracking, and a clean graphical interface for managing your media library.
    
    - Developed with Python and Toga
    - Uses api yt-dlp
    - Uses ffmpeg, ffprobe
"""

def main() -> Audeo2App:
    return Audeo2App(
        formal_name="Audeo-2",
        app_id="com.audeo.audeo2",
        app_name="Audeo-2",
        version="0.2.0",
        author="Eclouf",
        description=DESCRIPTION,
        icon="ressources/audeo.png",
        home_page="https://github.com/Eclouf/Audeo",
        )


if __name__ == "__main__":
    main().main_loop()
