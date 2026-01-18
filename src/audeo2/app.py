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
from typing import Optional
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.request import urlretrieve

import toga
from toga.style import Pack

from PIL import Image as PILImage
import imageio_ffmpeg

from .download_manager import DownloadManager, DownloadProgress
from .widgets import DownloadCard, DownloadCardModel, FinishedDownloadCard
from .views import DownloadsView, FinishedDownloadsView, QueueView, SettingsView
from .settings import AppSettings, load_settings, save_settings


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
        try:
            settings_path = self.config_dir / "settings.json"
            if not settings_path.exists():
                save_settings(self.config_dir, self.settings)
        except Exception:
            pass

        self._cards: dict[str, DownloadCard] = {}
        self._final_files: dict[str, Path] = {}
        self._thumb_cache: dict[str, Path] = {}
        self._thumb_inflight: set[str] = set()

        self.main_window = toga.MainWindow(title=self.formal_name)

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
        
        
        self.nav_btn_queue = icon_button("list", self._go_queue)
        
        self.nav_btn_finished = icon_button("list_end", self._go_finished)
        
        self.nav_btn_settings = icon_button("settings", self._go_settings)
    
        self.nav_box.add(self.nav_btn_downloads)
        self.nav_box.add(self.nav_btn_queue)
        self.nav_box.add(self.nav_btn_finished)
        self.nav_box.add(self.nav_btn_settings)

        self.downloads_view = DownloadsView(self)
        self.queue_view = QueueView(self)
        self.finished_view = FinishedDownloadsView(self)
        self.settings_view = SettingsView(self)

        # Créer le manager après avoir créé les vues
        self.manager = self._build_manager()

        self.url_input = self.downloads_view.url_input
        self.kind_select = self.downloads_view.kind_select
        self.cards_box = self.downloads_view.cards_box
        self.finished_cards_box = self.finished_view.cards_box

        self.content = toga.Box(style=Pack(direction="column", flex=1, margin=10))
        self._show_view("Téléchargements")

        root = toga.Box(style=Pack(direction="row", flex=1))
        root.add(self.nav_box)
        root.add(self.content)

        self.main_window.content = root
        self.main_window.show()

        self._bootstrap_ffmpeg()

    def save_settings(self) -> None:
        save_settings(self.config_dir, self.settings)

    def _bootstrap_ffmpeg(self) -> None:
        if self.settings.ffmpeg_path:
            # Vérifier si ffprobe est disponible avec le ffmpeg actuel
            if self._check_ffprobe_available(self.settings.ffmpeg_path):
                return

        async def _prompt_and_install() -> None:
            try:
                dialog = toga.QuestionDialog(
                    "Télécharger ffmpeg complet ?",
                    "ffmpeg et ffprobe sont nécessaires pour l'extraction audio, l'intégration de vignettes et certaines options.\n\nSouhaitez-vous les télécharger automatiquement ?",
                )
                ok = await dialog
            except Exception:
                ok = False

            if not ok:
                return

            try:
                exe = await self.loop.run_in_executor(self.manager._executor, self._download_complete_ffmpeg)
            except Exception:
                return

            if exe:
                self.settings.ffmpeg_path = str(exe)
                self.save_settings()

        try:
            asyncio.ensure_future(_prompt_and_install(), loop=self.loop)
        except Exception:
            return

    def _check_ffprobe_available(self, ffmpeg_path: str) -> bool:
        """Vérifie si ffprobe est disponible avec le ffmpeg donné"""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            ffmpeg_dir = Path(ffmpeg_path).parent
            ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
            ffprobe_path = ffmpeg_dir / ffprobe_name
            
            if ffprobe_path.exists():
                return True
                
            # Vérifier si ffprobe est dans le PATH
            result = subprocess.run([ffprobe_name, "-version"], 
                                capture_output=True, text=True, timeout=5)
            return result.returncode == 0
            
        except Exception:
            return False

    def _download_complete_ffmpeg(self) -> Optional[Path]:
        """Télécharge ffmpeg complet avec ffprobe en fonction du système"""
        import sys
        import subprocess
        import tempfile
        import urllib.request
        import zipfile
        from pathlib import Path
        
        # Créer une barre de progression
        progress_dialog = toga.ProgressDialog(
            "Téléchargement de ffmpeg",
            "Téléchargement de ffmpeg et ffprobe...",
            max=100
        )
        
        try:
            if sys.platform == "win32":
                # Windows: télécharger ffmpeg-static builds
                url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                filename = "ffmpeg-master-latest-win64-gpl.zip"
                exe_name = "ffmpeg.exe"
                ffprobe_name = "ffprobe.exe"
            elif sys.platform == "darwin":
                # macOS: télécharger builds statiques
                url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-osx64-gpl.zip"
                filename = "ffmpeg-master-latest-osx64-gpl.zip"
                exe_name = "ffmpeg"
                ffprobe_name = "ffprobe"
            else:
                # Linux: télécharger builds statiques
                url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
                filename = "ffmpeg-master-latest-linux64-gpl.tar.xz"
                exe_name = "ffmpeg"
                ffprobe_name = "ffprobe"

            # Créer le répertoire d'installation
            install_dir = Path.home() / ".audeo2" / "ffmpeg"
            install_dir.mkdir(parents=True, exist_ok=True)

            # Télécharger l'archive avec progression
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / filename
                
                def progress_hook(block_num, block_size, total_size):
                    if total_size > 0:
                        progress = min(100, int((block_num * block_size * 100) / total_size))
                        progress_dialog.value = progress
                
                if hasattr(self, 'downloads_view'):
                    self.downloads_view.log_info(f"Téléchargement de ffmpeg complet depuis {url}...")
                
                urllib.request.urlretrieve(url, temp_path, progress_hook)
                progress_dialog.value = 50  # Téléchargement terminé, début de l'extraction
                
                # Extraire l'archive
                if filename.endswith('.zip'):
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                else:
                    # .tar.xz pour Linux
                    import tarfile
                    with tarfile.open(temp_path, 'r:xz') as tar_ref:
                        tar_ref.extractall(temp_dir)
                
                progress_dialog.value = 75  # Extraction terminée
                
                # Trouver le répertoire ffmpeg extrait
                extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir() and 'ffmpeg' in d.name.lower()]
                if not extracted_dirs:
                    extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
                
                if not extracted_dirs:
                    raise Exception("Impossible de trouver le répertoire ffmpeg extrait")
                
                ffmpeg_source_dir = extracted_dirs[0]
                
                # Copier les exécutables
                import shutil
                ffmpeg_source = ffmpeg_source_dir / "bin" / exe_name
                ffprobe_source = ffmpeg_source_dir / "bin" / ffprobe_name
                
                if not ffmpeg_source.exists():
                    # Chercher dans le répertoire principal
                    ffmpeg_source = ffmpeg_source_dir / exe_name
                    ffprobe_source = ffmpeg_source_dir / ffprobe_name
                
                if ffmpeg_source.exists():
                    shutil.copy2(ffmpeg_source, install_dir / exe_name)
                if ffprobe_source.exists():
                    shutil.copy2(ffprobe_source, install_dir / ffprobe_name)
                
                # Rendre les exécutables exécutables (Linux/macOS)
                if sys.platform != "win32":
                    (install_dir / exe_name).chmod(0o755)
                    (install_dir / ffprobe_name).chmod(0o755)
            
            progress_dialog.value = 100  # Installation terminée
            
            ffmpeg_path = install_dir / exe_name
            ffprobe_path = install_dir / ffprobe_name
            
            if ffmpeg_path.exists() and ffprobe_path.exists():
                if hasattr(self, 'downloads_view'):
                    self.downloads_view.log_info(f"ffmpeg complet installé dans: {install_dir}")
                return ffmpeg_path
            else:
                raise Exception("ffmpeg ou ffprobe manquant après extraction")
                
        except Exception as e:
            if hasattr(self, 'downloads_view'):
                self.downloads_view.log_error(f"Erreur lors du téléchargement ffmpeg: {str(e)}")
            return None
        finally:
            try:
                progress_dialog.close()
            except Exception:
                pass

    def _build_downloads_view(self) -> toga.Widget:
        raise RuntimeError("This method is no longer used; use audeo2.views.DownloadsView")

    def _build_queue_view(self) -> toga.Widget:
        raise RuntimeError("This method is no longer used; use audeo2.views.QueueView")

    def _build_settings_view(self) -> toga.Widget:
        raise RuntimeError("This method is no longer used; use audeo2.views.SettingsView")

    def _go_downloads(self, widget: toga.Button) -> None:
        self._show_view("Téléchargements")

    def _go_queue(self, widget: toga.Button) -> None:
        self._show_view("En attente")

    def _go_finished(self, widget: toga.Button) -> None:
        self._show_view("Terminés")

    def _go_settings(self, widget: toga.Button) -> None:
        self._show_view("Paramètres")

    def _show_view(self, name: str) -> None:
        self.content.clear()
        if name == "Téléchargements":
            self.content.add(self.downloads_view.widget)
        elif name == "En attente":
            self.content.add(self.queue_view.widget)
        elif name == "Terminés":
            self.content.add(self.finished_view.widget)
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
        return DownloadManager(
            max_workers=self.max_workers,
            on_progress=self._threadsafe_progress,
            on_finished=self._threadsafe_finished,
            on_error=self._threadsafe_error,
            downloads_view=self.downloads_view,
        )

    def _on_add(self, widget: toga.Button) -> None:
        url = (self.url_input.value or "").strip()
        if not url:
            return

        if not self._is_valid_url(url):
            # Utiliser la méthode recommandée pour les dialogues dans les handlers synchrones
            dialog = toga.InfoDialog(
                title="URL invalide",
                message="Merci de saisir une URL http(s) valide."
            )
            # Créer une tâche async pour le dialogue
            import asyncio
            task = asyncio.create_task(self.main_window.dialog(dialog))
            # Pas besoin de callback pour un simple dialogue d'information
            return

        kind = str(self.kind_select.value or "video")

        # Lancer le téléchargement (retourne une liste de tâches)
        tasks = self.manager.submit(url=url, output_dir=self.download_dir, kind=kind, settings=self.settings)
        
        # Créer une carte pour chaque tâche
        for task in tasks:
            card = DownloadCard(DownloadCardModel(task_id=task.task_id, title=task.url, url=task.url, kind=kind))
            card.set_app_reference(self)  # Définir la référence à l'application
            self._cards[task.task_id] = card
            self.cards_box.add(card)
        
        self.url_input.value = ""

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
        if progress.filename and progress.status == "finished":
            self._final_files[progress.task_id] = Path(progress.filename)
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

        final_path = self._final_files.get(task_id)
        size_text = "-"
        if final_path and final_path.exists():
            try:
                size_text = self._fmt_bytes(os.path.getsize(final_path))
            except OSError:
                size_text = "-"

        finished_card = FinishedDownloadCard(title=card.title_label.text, size_text=size_text)
        if card.thumb.image is not None:
            finished_card.thumb.image = card.thumb.image

        try:
            self.cards_box.remove(card)
        except Exception:
            pass
        self.finished_cards_box.add(finished_card)
        self._cards.pop(task_id, None)
        self._final_files.pop(task_id, None)

    def _apply_error(self, task_id: str, e: Exception) -> None:
        card = self._cards.get(task_id)
        if card:
            card.mark_error(str(e))

    def _on_clear_finished(self, widget: toga.Button) -> None:
        try:
            self.finished_cards_box.clear()
        except Exception:
            # Fallback: remove children one by one
            for child in list(getattr(self.finished_cards_box, "children", [])):
                try:
                    self.finished_cards_box.remove(child)
                except Exception:
                    pass


def main() -> Audeo2App:
    return Audeo2App("Audeo-2", "com.audeo.audeo2")


if __name__ == "__main__":
    main().main_loop()
