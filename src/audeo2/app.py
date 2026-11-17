from __future__ import annotations

from io import BytesIO
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
import webbrowser
import threading
import customtkinter as ctk
from PIL import Image as PILImage, ImageTk
import imageio_ffmpeg

from .download_manager import DownloadManager, DownloadProgress
from .widgets import DownloadCard, DownloadCardModel, FinishedDownloadCard
from .views import DownloadsView, FinishedDownloadsView, VideoInfoView, SettingsView
from .settings import AppSettings, load_settings, save_settings
from .ffmpeg import FFmpegManager
from .i18n import i18n, _
from .constants import ViewName
from . import update as updater

FRAME_COLOR = "#d3d3d3"
FRAME_THICKNESS = 1.5

class Audeo2App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize CustomTkinter settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.title("Audeo-2")
        self.geometry("1100x600")
        
        # Initialize paths and settings
        self.download_dir = Path.home() / "Downloads" / "Audeo-2"
        self.max_workers = 3

        cfg_dir = Path.home() / ".config" / "Audeo-2"
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

        # Restaurer le dossier de destination sauvegardé s'il existe
        if self.settings.general.download_dir:
            try:
                candidate = Path(self.settings.general.download_dir)
                candidate.mkdir(parents=True, exist_ok=True)
                self.download_dir = candidate
            except Exception:
                pass

        # Appliquer la langue sauvegardée
        i18n.set_language(self.settings.general.lang_code)
        
        # Vérifier si le chemin ffmpeg sauvegardé existe
        if self.settings.ffmpeg_path and not Path(self.settings.ffmpeg_path).exists():
            print(f"[Startup] Saved ffmpeg path does not exist: {self.settings.ffmpeg_path}")
            print("[Startup] Resetting ffmpeg path")
            self.settings.ffmpeg_path = None
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
        
        # Build UI
        self._build_ui()
        
        # Create views
        self.downloads_view = DownloadsView(self)
        self.finished_downloads_view = FinishedDownloadsView(self)
        self.video_info_view = VideoInfoView(self)
        self.settings_view = SettingsView(self)
        
        # Create manager after views
        self.manager = self._build_manager()
        
        # Set references
        self.url_input = self.downloads_view.url_input
        self.kind_select = self.downloads_view.kind_select
        self.cards_box = self.downloads_view.cards_box
        self.finished_cards_box = self.finished_downloads_view.cards_box
        
        # Show downloads view by default
        self._show_view(ViewName.DOWNLOADS)
        
        # Bootstrap ffmpeg
        self._bootstrap_ffmpeg()
    
    def _build_ui(self) -> None:
        # Set app icon
        app_icon_path = Path(__file__).resolve().parent / "ressources" / "audeo.png"
        if app_icon_path.exists():
            try:
                icon = PILImage.open(app_icon_path)
                self.iconbitmap(app_icon_path)
            except Exception:
                pass

        # Create main layout
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Navigation sidebar
        self.nav_box = ctk.CTkFrame(self.main_container, width=60)
        self.nav_box.pack(side="left", fill="y", padx=5, pady=5)
        
        # Create navigation buttons
        icons_dir = Path(__file__).resolve().parent / "ressources" / "pictures"
        
        def load_icon(icon_name):
            icon_path = icons_dir / f"{icon_name}-24.png"
            try:
                if icon_path.exists():
                    from .widgets import load_themed_icon
                    return load_themed_icon(icon_path, size=(24, 24))
            except Exception:
                pass
            return None

        download_icon = load_icon("download")
        info_icon = load_icon("info")
        finished_icon = load_icon("list_end")
        settings_icon = load_icon("settings")
        update_icon = load_icon("update")

        self.nav_btn_downloads = ctk.CTkButton(
            self.nav_box, 
            text="", 
            image=download_icon,
            width=50, 
            height=50,
            command=self._go_downloads
        )
        self.nav_btn_downloads.pack(pady=5)
        
        self.nav_btn_info = ctk.CTkButton(
            self.nav_box, 
            text="", 
            image=info_icon,
            width=50, 
            height=50,
            command=self._go_info
        )
        self.nav_btn_info.pack(pady=5)
        
        self.nav_btn_finished = ctk.CTkButton(
            self.nav_box, 
            text="", 
            image=finished_icon,
            width=50, 
            height=50,
            command=self._go_finished
        )
        self.nav_btn_finished.pack(pady=5)
        
        self.nav_btn_settings = ctk.CTkButton(
            self.nav_box, 
            text="", 
            image=settings_icon,
            width=50, 
            height=50,
            command=self._go_settings
        )
        self.nav_btn_settings.pack(pady=5)
        
        # Spacer
        ctk.CTkLabel(self.nav_box, text="").pack(expand=True)
        
        self.nav_btn_update = ctk.CTkButton(
            self.nav_box, 
            text="", 
            image=update_icon,
            width=50, 
            height=50,
            command=self._go_update
        )
        self.nav_btn_update.pack(pady=5)

        # Content area
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.content = ctk.CTkFrame(self.content_frame)
        self.content.pack(fill="both", expand=True)


    def notify_language_change(self) -> None:
        """Reconstruit toutes les vues quand la langue change"""
        try:
            # Détruire les anciennes vues (les widgets tk ne peuvent pas être reparentés)
            for old_view in (
                getattr(self, "downloads_view", None),
                getattr(self, "finished_downloads_view", None),
                getattr(self, "video_info_view", None),
                getattr(self, "settings_view", None),
            ):
                try:
                    if old_view is not None:
                        # Fermer la fenêtre terminal si elle existe (CTkToplevel orpheline)
                        if hasattr(old_view, "_close_terminal"):
                            old_view._close_terminal()
                        if old_view.widget.winfo_exists():
                            old_view.widget.destroy()
                except Exception:
                    pass
            self._cards.clear()

            # Recréer proprement les vues
            self.downloads_view = DownloadsView(self)
            self.finished_downloads_view = FinishedDownloadsView(self)
            self.video_info_view = VideoInfoView(self)
            self.settings_view = SettingsView(self)

            # Mettre à jour les références utilisées par l'app
            self.url_input = self.downloads_view.url_input
            self.kind_select = self.downloads_view.kind_select
            self.cards_box = self.downloads_view.cards_box
            self.finished_cards_box = self.finished_downloads_view.cards_box

            # Mettre à jour les références internes du manager (logs, etc.)
            try:
                if hasattr(self, "manager") and self.manager is not None:
                    if hasattr(self.manager, "_downloads_view"):
                        self.manager._downloads_view = self.downloads_view
                    if hasattr(self.manager, "_ydl_handler") and self.manager._ydl_handler is not None:
                        if hasattr(self.manager._ydl_handler, "downloads_view"):
                            self.manager._ydl_handler.downloads_view = self.downloads_view
            except Exception:
                pass

            # Rester sur l'onglet courant (downloads par défaut)
            self._show_view(ViewName.DOWNLOADS)
            
        except Exception as e:
            print(f"Erreur lors de la reconstruction des vues: {e}")
    
    def save_settings(self) -> None:
        save_settings(self.config_dir, self.settings)

    def _update_progress_ui(self, progress_bar, details_label, percent, message):
        """Met à jour la GUI de progression (appelée depuis le thread principal)"""
        try:
            progress_bar.set(percent)
            details_label.configure(text=message)
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
        def _prompt_and_install() -> None:
            try:
                # Create custom dialog
                dialog = ctk.CTkToplevel(self)
                dialog.title("Télécharger ffmpeg complet ?")
                dialog.geometry("500x200")
                
                message_label = ctk.CTkLabel(
                    dialog,
                    text="ffmpeg et ffprobe sont nécessaires pour l'extraction audio,\nl'intégration de vignettes et certaines options.\n\nSouhaitez-vous les télécharger automatiquement ?",
                    wraplength=450
                )
                message_label.pack(pady=20, padx=20)
                
                button_frame = ctk.CTkFrame(dialog)
                button_frame.pack(pady=10)
                
                result = {"ok": False}
                
                def on_ok():
                    result["ok"] = True
                    dialog.destroy()
                
                def on_cancel():
                    result["ok"] = False
                    dialog.destroy()
                
                ok_btn = ctk.CTkButton(button_frame, text="Oui", command=on_ok, width=100)
                ok_btn.pack(side="left", padx=10)
                
                cancel_btn = ctk.CTkButton(button_frame, text="Non", command=on_cancel, width=100)
                cancel_btn.pack(side="left", padx=10)
                
                dialog.wait_window()
                
                if not result["ok"]:
                    print("[Bootstrap] FFmpeg download declined by user")
                    return

                print("[Bootstrap] Starting FFmpeg download...")
                
                # Créer une fenêtre de progression
                progress_window = ctk.CTkToplevel(self)
                progress_window.title("Téléchargement ffmpeg")
                progress_window.geometry("400x150")
                
                progress_frame = ctk.CTkFrame(progress_window)
                progress_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                status_label = ctk.CTkLabel(progress_frame, text="Téléchargement de ffmpeg...")
                status_label.pack(pady=5)
                
                progress_bar = ctk.CTkProgressBar(progress_frame, width=350)
                progress_bar.pack(pady=10)
                progress_bar.set(0)
                
                details_label = ctk.CTkLabel(progress_frame, text="Initialisation...")
                details_label.pack(pady=5)
                
                # Créer le callback de progression thread-safe
                def on_progress(percent, message):
                    """Callback appelé par le téléchargeur (depuis un thread)"""
                    # Mettre à jour la GUI de façon thread-safe
                    self.after(0, self._update_progress_ui, progress_bar, details_label, percent, message)
                
                def download_in_thread():
                    try:
                        exe = ffmpeg_mgr.download_and_install(progress_callback=on_progress)
                        if exe:
                            self.settings.ffmpeg_path = str(exe)
                            self.save_settings()
                            print(f"[Bootstrap] FFmpeg saved: {exe}")
                            self.after(0, lambda: status_label.configure(text="ffmpeg installé avec succès!"))
                            self.after(0, lambda: progress_bar.set(100))
                            self.after(0, lambda: details_label.configure(text=str(exe)))
                            # Fermer la fenêtre après 2 secondes
                            self.after(2000, progress_window.destroy)
                        else:
                            print("[Bootstrap] FFmpeg download failed (returned None)")
                            self.after(0, lambda: status_label.configure(text="Erreur lors du téléchargement"))
                            self.after(0, lambda: details_label.configure(text="Veuillez réessayer plus tard"))
                    except Exception as e:
                        print(f"[Bootstrap] FFmpeg download error: {e}")
                        import traceback
                        traceback.print_exc()
                        self.after(0, lambda: status_label.configure(text="Erreur lors du téléchargement"))
                        self.after(0, lambda: details_label.configure(text=str(e)))
                
                # Lancer le téléchargement dans un thread séparé
                thread = threading.Thread(target=download_in_thread, daemon=True)
                thread.start()
                
            except Exception as e:
                print(f"[Bootstrap] Error: {e}")

        # Utiliser after pour planifier après le démarrage complet
        self.after(100, _prompt_and_install)

    def _go_downloads(self) -> None:
        self._show_view(ViewName.DOWNLOADS)

    def _go_info(self) -> None:
        self._show_view(ViewName.INFO)

    def _go_finished(self) -> None:
        self._show_view(ViewName.FINISHED)

    def _go_settings(self) -> None:
        self._show_view(ViewName.SETTINGS)
        
    def _go_update(self) -> None:
        self._cmd_check_updates()

    def _cmd_check_updates(self) -> None:
        try:
            threading.Thread(target=self._check_for_updates, daemon=True).start()
        except Exception:
            pass

    def _check_for_updates(self) -> None:
        repo = "Eclouf/Audeo"
        releases_page_url = f"https://github.com/{repo}/releases"

        def _do_check() -> updater.UpdateCheckResult:
            return updater.check_for_updates(repo=repo, current_version="0.6.0")

        try:
            result = _do_check()
        except Exception as e:
            msg = (
                f"{_('Unable to check updates')}: {e}\n\n"
                f"{_('Open the releases page instead?')}\n{releases_page_url}"
            )
            self._show_question_dialog(_("Updates"), msg, lambda: webbrowser.open(releases_page_url))
            return

        current_display = updater.normalize_version_str(result.current_version) or str(result.current_version)
        latest_display = updater.normalize_version_str(result.latest_tag) or str(result.latest_tag)

        if result.is_update_available:
            if result.asset_url:
                msg = (
                    f"{_('A new version is available')}: {latest_display}\n"
                    f"{_('Current version')}: {current_display}\n\n"
                    f"{_('Download and open the installer?')}"
                )
                self._show_question_dialog(_("Updates"), msg, lambda: self._download_update_asset(result.asset_url))
            else:
                msg = (
                    f"{_('A new version is available')}: {latest_display}\n"
                    f"{_('Current version')}: {current_display}\n\n"
                    f"{_('Open download page?')}"
                )
                self._show_question_dialog(_("Updates"), msg, lambda: updater.open_updates_page(result.open_url))
        else:
            msg = (
                f"{_('You are up to date')}\n"
                f"{_('Current version')}: {current_display}\n"
                f"{_('Latest version')}: {latest_display or '-'}"
            )
            self._show_info_dialog(_("Updates"), msg)

    def _show_info_dialog(self, title: str, message: str) -> None:
        """Show an info dialog using CustomTkinter"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("500x200")
        
        message_label = ctk.CTkLabel(dialog, text=message, wraplength=450)
        message_label.pack(pady=20, padx=20)
        
        ok_btn = ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=100)
        ok_btn.pack(pady=10)
    
    def _show_question_dialog(self, title: str, message: str, on_yes_callback) -> None:
        """Show a question dialog using CustomTkinter"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("500x200")
        
        message_label = ctk.CTkLabel(dialog, text=message, wraplength=450)
        message_label.pack(pady=20, padx=20)
        
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=10)
        
        def on_yes():
            dialog.destroy()
            if on_yes_callback:
                on_yes_callback()
        
        def on_no():
            dialog.destroy()
        
        yes_btn = ctk.CTkButton(button_frame, text=_("Yes"), command=on_yes, width=100)
        yes_btn.pack(side="left", padx=10)
        
        no_btn = ctk.CTkButton(button_frame, text=_("No"), command=on_no, width=100)
        no_btn.pack(side="left", padx=10)

    def _download_update_asset(self, asset_url: str) -> None:
        filename = updater.asset_filename_from_url(asset_url)
        cache_dir = Path.home() / ".cache" / "audeo-2"
        cache_dir.mkdir(parents=True, exist_ok=True)

        progress_window = ctk.CTkToplevel(self)
        progress_window.title(_("Downloading update"))
        progress_window.geometry("520x160")
        
        progress_frame = ctk.CTkFrame(progress_window)
        progress_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        status_label = ctk.CTkLabel(progress_frame, text=_("Downloading..."))
        status_label.pack(pady=5)
        
        details_label = ctk.CTkLabel(progress_frame, text=filename)
        details_label.pack(pady=5)
        
        progress_bar = ctk.CTkProgressBar(progress_frame, width=450)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        def on_progress(downloaded: int, total: int | None) -> None:
            try:
                if total and total > 0:
                    pct = int((downloaded / total) * 100)
                    pct = max(0, min(100, pct))
                    self.after(0, lambda: progress_bar.set(pct / 100))
                    self.after(0, lambda: details_label.configure(text=f"{filename} ({pct}%)"))
                else:
                    # Unknown size: show an indeterminate-ish progress by clamping.
                    current_val = progress_bar.get()
                    new_val = min(0.99, current_val + 0.01)
                    self.after(0, lambda: progress_bar.set(new_val))
                    self.after(0, lambda: details_label.configure(text=filename))
            except Exception:
                pass

        def download_in_thread():
            try:
                downloaded_path = updater.download_and_open_update_asset(
                    asset_url=asset_url,
                    cache_dir=cache_dir,
                    on_progress=on_progress,
                )
                
                self.after(0, lambda: progress_bar.set(1.0))
                self.after(0, lambda: status_label.configure(text=_("Download complete")))
                self.after(0, lambda: details_label.configure(text=str(downloaded_path)))
                
                # Give UI a moment to refresh
                self.after(300, progress_window.destroy)
                
            except Exception as e:
                try:
                    progress_window.destroy()
                except Exception:
                    pass
                try:
                    self.after(0, lambda: self._show_info_dialog(_("Error"), f"{_('Unable to download update')}: {e}"))
                except Exception:
                    pass

        # Start download in background thread
        thread = threading.Thread(target=download_in_thread, daemon=True)
        thread.start()

    def _show_view(self, name: ViewName) -> None:
        # Masquer toutes les vues sans les détruire (pack_forget)
        for widget in self.content.winfo_children():
            try:
                widget.pack_forget()
            except Exception:
                pass

        # Add new view
        if name == ViewName.DOWNLOADS:
            self.downloads_view.widget.pack(fill="both", expand=True)
        elif name == ViewName.INFO:
            self.video_info_view.widget.pack(fill="both", expand=True)
        elif name == ViewName.FINISHED:
            self.finished_downloads_view.widget.pack(fill="both", expand=True)
        else:
            self.settings_view.widget.pack(fill="both", expand=True)

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
            main_window=self,
            on_tasks_ready=self._on_tasks_ready,
        )
        return self.manager

    def _on_add(self) -> None:
        url = (self.downloads_view.url_input.get() or "").strip()
        if not url:
            return

        if not self._is_valid_url(url):
            self._show_info_dialog(_("Invalid URL"), _("Please enter a valid URL http(s)"))
            return

        # L'OptionMenu affiche des libellés localisés : convertir vers le code stable
        kind_display = str(self.downloads_view.kind_select.get() or "")
        kind = getattr(self.downloads_view, "_kind_display_to_code", {}).get(kind_display, "video")

        # Lancer le téléchargement (retourne immédiatement, les tâches seront créées de manière asynchrone)
        self.manager.submit(url=url, output_dir=self.download_dir, kind=kind, settings=self.settings)
        
        # L'interface reste responsive, les cartes seront créées via le callback _on_tasks_ready
        self.downloads_view.url_input.delete(0, 'end')

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
            card = DownloadCard(DownloadCardModel(task_id=task.task_id, title=task.url, url=task.url, kind=task.kind), parent=self.cards_box)
            card.set_app_reference(self)  # Définir la référence à l'application
            self._cards[task.task_id] = card
            self.downloads_view.cards_box.add(card)
            
        # Mettre à jour l'affichage
        self.downloads_view._update_content_display()

    def _threadsafe_progress(self, progress: DownloadProgress) -> None:
        self.after(0, self._apply_progress, progress)

    def _threadsafe_finished(self, task_id: str) -> None:
        self.after(0, self._apply_finished, task_id)

    def _threadsafe_error(self, task_id: str, e: Exception) -> None:
        self.after(0, self._apply_error, task_id, e)

    def _apply_progress(self, progress: DownloadProgress) -> None:
        card = self._cards.get(progress.task_id)
        if not card:
            return
                
        if progress.title:
            card.title_label.configure(text=progress.title)
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
            current = getattr(card.thumb, 'image', None)
            default_img = getattr(card, "_default_image", None)
            if current is None or (default_img is not None and current is default_img):
                try:
                    img = PILImage.open(cached)
                    ctk_image = ctk.CTkImage(img, size=(200, 120))
                    card.thumb.configure(image=ctk_image)
                except Exception:
                    return
            return

        if url in self._thumb_inflight:
            return
        self._thumb_inflight.add(url)

        def _bg() -> None:
            try:
                target_dir = Path.home() / ".cache" / "audeo-2" / "thumbs"
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / f"{abs(hash(url))}.png"
                if not target.exists():
                    with urlopen(url, timeout=15) as resp:
                        data = resp.read()
                    img = PILImage.open(BytesIO(data))
                    img = img.convert("RGB")
                    img.thumbnail((480, 270))
                    img.save(target, format="PNG", optimize=True)
                self.after(0, _apply, target)
            except Exception:
                self.after(0, _clear_inflight)
                return

        def _apply(path: Path) -> None:
            self._thumb_cache[url] = path
            _clear_inflight(url)
            current = getattr(card.thumb, 'image', None)
            default_img = getattr(card, "_default_image", None)
            if current is None or (default_img is not None and current is default_img):
                try:
                    img = PILImage.open(path)
                    ctk_image = ctk.CTkImage(img, size=(200, 120))
                    card.thumb.configure(image=ctk_image)
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
        
        self.downloads_view.log_info(f"{_("Download finished")}: {card.title_label.cget('text')}")

        finished_card = FinishedDownloadCard(title=card.title_label.cget('text'), size_text=size_text, file_path=download_dir, parent=self.finished_downloads_view.cards_box)
        finished_card.set_app_reference(self)  # Définir la référence à l'application
        if hasattr(card.thumb, 'image') and card.thumb.image is not None:
            finished_card.thumb.configure(image=card.thumb.image)

        try:
            card.destroy()
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
            # Afficher une fenêtre de dialogue d'erreur
            self._show_info_dialog(_("Download error"), f"{str(e)}")

    def _on_clear_finished(self) -> None:
        try:
            for widget in self.finished_downloads_view.cards_box.winfo_children():
                widget.destroy()
        except Exception:
            pass

DESCRIPTION = """
Audeo is a user-friendly application built with Python and CustomTkinter that enables users to download audio and video content from various online sources.
The application provides a queue-based management system, download tracking, and a clean graphical interface for managing your media library.
    
    - Developed with Python and CustomTkinter
    - Uses api yt-dlp
    - Uses ffmpeg, ffprobe
"""

def main() -> None:
    app = Audeo2App()
    app.mainloop()


if __name__ == "__main__":
    main()
