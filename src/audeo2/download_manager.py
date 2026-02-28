"""
files for downloading videos and playlists
"""

from __future__ import annotations

import logging
import re
import threading
import time
import urllib.parse
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse, urlunparse

import yt_dlp
import toga

from .settings import AppSettings
from .views import DownloadsView
from .download_models import DownloadProgress, DownloadTask
from .i18n import _

class YdlLogHandler(logging.Handler):
    """Handler presonal for yt-dlp"""
    
    def __init__(self, downloads_view):
        super().__init__()
        self.downloads_view = downloads_view
        self.setLevel(logging.DEBUG)
    
    def emit(self, record):
        """Handle the logging"""
        try:
            message = self.format(record)
            if self.downloads_view:
                # Filtrer les messages trop verbeux mais garder plus d'informations utiles
                message_lower = message.lower()
                skip_patterns = ['[debug] frame=', '[debug] request', '[debug] downloaded ', '[debug] writing ']
                
                # Garder les messages importants de yt-dlp
                if not any(skip in message_lower for skip in skip_patterns):
                    # Ajouter un préfixe pour identifier les messages yt-dlp
                    if '[info]' in message_lower:
                        self.downloads_view.log_info(_("yt-dlp: {}").format(message.strip()))
                    elif '[warning]' in message_lower:
                        self.downloads_view.log_warning(_("yt-dlp: {}").format(message.strip()))
                    elif '[error]' in message_lower:
                        self.downloads_view.log_error(_("yt-dlp: {}").format(message.strip()))
                    elif 'download' in message_lower and '%' in message_lower:
                        # Messages de progression de téléchargement
                        self.downloads_view.log_info(_("yt-dlp: {}").format(message.strip()))
                    elif any(keyword in message_lower for keyword in ['extracting', 'downloading', 'finished', 'playlist']):
                        # Messages importants sur le déroulement
                        self.downloads_view.log_info(_("yt-dlp: {}").format(message.strip()))
                    else:
                        # Autres messages debug moins importants
                        self.downloads_view.log_debug(_("yt-dlp: {}").format(message.strip()))
        except Exception as e:
            # Afficher l'erreur pour le debugging
            print(_("Error in YdlLogHandler.emit: {}").format(e))
            # Ignorer les erreurs de logging pour ne pas bloquer yt-dlp
            pass


class DownloadManager:
    def __init__(
        self,
        *,
        max_workers: int,
        on_progress: Callable[[DownloadProgress], None],
        on_finished: Callable[[str], None],
        on_error: Callable[[str, Exception], None],
        downloads_view=None,
        main_window=None,
        on_tasks_ready: Optional[Callable[[list], None]] = None,
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._on_progress = on_progress
        self._on_finished = on_finished
        self._on_error = on_error
        self._downloads_view = downloads_view
        self._main_window = main_window
        self._on_tasks_ready = on_tasks_ready
        self._lock = threading.Lock()
        self._tasks: dict[str, DownloadTask] = {}
        
        # Configurer le logger yt-dlp une seule fois
        self._logger = logging.getLogger("yt_dlp")
        self._logger.setLevel(logging.DEBUG)
        
        # Utiliser la vue de téléchargement existante
        if downloads_view is None:
            raise ValueError("Downloads view is required for DownloadManager")
        
        # Créer un handler personnalisé pour rediriger vers le terminal
        self._ydl_handler = None
        if downloads_view:
            self._ydl_handler = YdlLogHandler(downloads_view)
            self._ydl_handler.setLevel(logging.DEBUG)
            self._logger.addHandler(self._ydl_handler)
            # Empêcher la propagation aux handlers parents pour éviter les doublons
            self._logger.propagate = False

    def shutdown(self) -> None:
        # Retirer le handler avant de fermer avec gestion d'erreurs
        try:
            if self._ydl_handler and self._logger:
                self._logger.removeHandler(self._ydl_handler)
                # Réinitialiser le niveau de propagation
                self._logger.propagate = True
        except Exception as e:
            # Logger l'erreur mais continuer le shutdown
            if self._downloads_view:
                self._downloads_view.log_debug(_("Logger cleanup error: {}").format(str(e)))
        finally:
            # Forcer le nettoyage du handler
            self._ydl_handler = None
            
        self._executor.shutdown(wait=False, cancel_futures=False)
        
    def cancel_download(self, task_id: str) -> None:
        """Annule un téléchargement spécifique"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                # Marquer la tâche comme annulée
                task.cancelled = True
                
                # Tenter d'annuler le future si possible
                if hasattr(task, 'future') and task.future:
                    try:
                        task.future.cancel()
                    except Exception:
                        pass
                
                # Notifier l'application
                if self._downloads_view:
                    self._downloads_view.log_info(_("Download {} marked for cancellation").format(task_id))
                    
    def pause_download(self, task_id: str) -> None:
        """Pauses a specific download"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.paused = True
                if self._downloads_view:
                    self._downloads_view.log_info(_("Download {} paused").format(task_id))
                    
    def resume_download(self, task_id: str) -> None:
        """Resumes a specific download"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.paused = False
                if self._downloads_view:
                    self._downloads_view.log_info(_("Download {} resumed").format(task_id))

    def submit(self, *, url: str, output_dir: Path, kind: str, settings: AppSettings) -> list[DownloadTask]:
        """Downloads a URL or a complete playlist"""
        # Start the animation immediately in the main thread
        self._downloads_view.process_anim.start()
        self._downloads_view.log_info(_("URL detection in progress..."))
        
        # Launch detection in a separate thread to avoid blocking the interface
        import threading
        
        def _detect_and_submit():
            try:
                is_playlist = False
                info = None
                try:
                    # Simple detection with yt-dlp only
                    options = {
                        'quiet': True,
                        'extract_flat': 'in_playlist',  # Optimized for playlists
                        'noplaylist': False,  # Keep the playlist
                        'simulate': True,
                        'skip_download': True,
                    }
                    
                    with yt_dlp.YoutubeDL(options) as ydl:
                        info = ydl.extract_info(url, download=False)
                        
                        # Detection playlist yt-dlp
                        is_playlist = (
                            info.get("ie_key") == "Playlist" or 
                            info.get('_type') == 'playlist' or 
                            info.get('playlist_count', 0) > 0 or
                            'entries' in info
                        )
                        
                    if is_playlist:
                        self._downloads_view.log_info(_("Playlist detected: {}").format(url))
                        print(_("Playlist detected by yt-dlp"))
                    else:
                        print(_("Single video detected"))
                        
                except Exception as e:
                    # Detection error - simply log and stop
                    self._downloads_view.log_error(_("Detection error: {}").format(str(e)))
                    
                    # Show an error dialog
                    if self._main_window:
                        try:
                            import asyncio
                            dialog = toga.ErrorDialog(
                                title=_("Detection error"),
                                message=_("Error during playlist detection:\n\n{}\n\nProcess stopped.").format(str(e))
                            )
                            # Schedule dialog display on the main thread with error handling
                            if hasattr(self._main_window, 'app') and hasattr(self._main_window.app, 'loop'):
                                def safe_show_dialog():
                                    try:
                                        asyncio.create_task(self._main_window.dialog(dialog))
                                    except Exception as dialog_error:
                                        # Silently log dialog error
                                        if self._downloads_view:
                                            self._downloads_view.log_error(_("Dialog error: {}").format(str(dialog_error)))
                                
                                self._main_window.app.loop.call_soon_threadsafe(safe_show_dialog)
                        except Exception as outer_error:
                            # Log any dialog error, regardless of language
                            if self._downloads_view:
                                self._downloads_view.log_error(_("Dialog setup error: {}").format(str(outer_error)))
                    
                    # Stop the process as soon as an error occurs
                    self._downloads_view.process_anim.stop()
                    return None  # Return None to indicate a fatal error
                
                # Create tasks
                tasks = []
                if is_playlist and settings.general.download_playlist:
                    print(_("Processing playlist"))
                    self._downloads_view.log_info(_("Processing playlist"))
                    self._downloads_view.log_info(_("Items number: {}").format(info.get('playlist_count', 0)))
                    if settings.general.download_playlist and settings.general.playlist_folder_name.strip():
                        playlist_folder_name = settings.general.playlist_folder_name.strip()
                        final_output_dir = output_dir / playlist_folder_name
                        self._downloads_view.log_info(_("Playlist folder: {}").format(final_output_dir))
                        
                    elif settings.general.download_playlist:
                        final_output_dir = output_dir
                        self._downloads_view.log_info(_("Playlist folder: {}").format(final_output_dir))
                        
                    tasks = [self._task(url, final_output_dir, kind, settings, True)]
                else:
                    print(_("Processing single item"))
                    final_output_dir = output_dir
                    tasks = [self._task(url, final_output_dir, kind, settings, False)]
                
                # Stop the detection animation
                self._downloads_view.process_anim.stop()
                
                # Notify the main thread that tasks are ready
                if self._on_tasks_ready:
                    if hasattr(self._main_window, 'app') and hasattr(self._main_window.app, 'loop'):
                        self._main_window.app.loop.call_soon_threadsafe(
                            lambda: self._on_tasks_ready(tasks)
                        )
                    
            except Exception as e:
                self._downloads_view.process_anim.stop()
                if self._downloads_view:
                    self._downloads_view.log_error(_("Error: {}").format(str(e)))
                
                # Show an error dialog
                if self._main_window:
                    try:
                        import asyncio
                        dialog = toga.ErrorDialog(
                            title=_("Submission error"),
                            message=_("Error during download preparation:\n\n{}\n\nProcess stopped.").format(str(e))
                        )
                        # Schedule dialog display on the main thread with error handling
                        if hasattr(self._main_window, 'app') and hasattr(self._main_window.app, 'loop'):
                            def safe_show_dialog():
                                try:
                                    asyncio.create_task(self._main_window.dialog(dialog))
                                except Exception as dialog_error:
                                    # Silently log dialog error
                                    if self._downloads_view:
                                        self._downloads_view.log_error(_("Dialog error: {}").format(str(dialog_error)))
                            
                            self._main_window.app.loop.call_soon_threadsafe(safe_show_dialog)
                    except Exception as outer_error:
                        # Silently log dialog setup error
                        if self._downloads_view:
                            self._downloads_view.log_error(_("Dialog setup error: {}").format(str(outer_error)))
                
                # Stop the process as soon as an error occurs
                if self._on_tasks_ready:
                    if hasattr(self._main_window, 'app') and hasattr(self._main_window.app, 'loop'):
                        self._main_window.app.loop.call_soon_threadsafe(
                            lambda: self._on_tasks_ready(None)
                        )
        
        # Launch detection in a separate thread
        thread = threading.Thread(target=_detect_and_submit, daemon=True)
        thread.start()
        
        # Return an empty list immediately to avoid blocking
        # Real tasks will be created asynchronously
        return []
    
    def _on_tasks_ready(self, tasks):
        """Callback called when tasks are ready"""
            # Cette méthode sera appelée depuis le thread principal
            # On peut déclencher un événement ou notifier l'application
        pass
        
    def _task(self, original_url: str, output_dir: Path, kind: str, settings: AppSettings, playlist: bool) -> DownloadTask:
        """
        Creates a download task for a given URL
        """
        task = DownloadTask(
            task_id=str(uuid.uuid4()), 
            url=original_url, 
            output_dir=output_dir, 
            kind=kind, 
            settings=settings,
            playlist=playlist   
        )
        with self._lock:
            self._tasks[task.task_id] = task
        
        if playlist:
            task.future = self._executor.submit(self._run_playlist_download, task)
        else:
            task.future = self._executor.submit(self._run_download, task)
        return task

        
    def _hook_progress(self, task: DownloadTask, info: dict = None) -> dict:
        """Hook unifié pour les téléchargements simples et playlists
        
        Returns:
            dict: Hook function ready to be used with yt-dlp
        """
        # Initialiser les variables communes
        title = info.get("title", "Vidéo") if info else "Vidéo"
        thumbnail_url = info.get("thumbnail") if info else None
        total_bytes = info.get("filesize") or info.get("filesize_approx") if info else None
        
        # Pour les playlists, initialiser le compteur d'items avec verrouillage
        item_counter = 1  # Commence à 1 pour le premier item
        if task.playlist:
            item_counter = 1
        
        # Verrou pour protéger l'accès au compteur dans les playlists
        import threading
        counter_lock = threading.Lock() if task.playlist else None
        
        def hook(d: dict) -> None:
            nonlocal item_counter
            
            # Verrouiller l'accès au compteur pour les playlists
            if counter_lock:
                if not counter_lock.acquire(timeout=1.0):
                    # Log warning and continue without lock
                    self._downloads_view.log_warning(_("Lock timeout in progress hook"))
                    return
            
            try:
                # Vérifier si la tâche a été annulée
                if task.cancelled:
                    raise yt_dlp.DownloadError(_("Download cancelled by user"))
                
                # Gérer la pause : attendre que la pause soit levée avec vérification d'annulation
                pause_check_interval = 0.1  # 100ms
                while task.paused and not task.cancelled:
                    import time
                    time.sleep(pause_check_interval)
                    # Vérification plus fréquente de l'annulation pendant la pause
                    if task.cancelled:
                        break
                    
                # Vérifier à nouveau si la tâche a été annulée pendant la pause
                if task.cancelled:
                    raise yt_dlp.DownloadError(_("Download cancelled by user"))
                    
                status = d.get("status")
                if status == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    downloaded = d.get("downloaded_bytes")
                    percent = 0.0
                    if total and downloaded is not None and total > 0:
                        percent = max(0.0, min(1.0, downloaded / total))

                    # Adapter le titre selon le type de téléchargement
                    if task.playlist:
                        current_item = item_counter  # Item actuel pendant le téléchargement
                        total_items = info.get('playlist_count') if task.playlist and info else None
                        # Pour les playlists, utiliser le titre de la vidéo en cours depuis yt-dlp
                        progress_title = d.get("title") or title
                    else:
                        current_item = None
                        total_items = None
                        progress_title = title
                    
                    # Limiter le titre à 32 caractères maximum
                    progress_title = progress_title[:32] + "..." if len(progress_title) > 32 else progress_title
                    
                    self._on_progress(
                        DownloadProgress(
                            task_id=task.task_id,
                            status="paused" if task.paused else "downloading",
                            percent=percent,
                            title=progress_title,
                            thumbnail_url=thumbnail_url,
                            total_bytes=total,
                            downloaded_bytes=downloaded,
                            eta_seconds=d.get("eta"),
                            speed_bytes_s=d.get("speed"),
                            filename=d.get("filename"),
                            item_number=current_item,
                            total_items=total_items,
                        )
                    )
                elif status == "finished":
                    # Incrémenter le compteur pour le prochain item (playlists uniquement)
                    if task.playlist:
                        # L'item terminé est l'item actuel
                        finished_item = item_counter
                        # Préparer le compteur pour le prochain item
                        item_counter += 1
                        
                        # Adapter le titre de completion selon le type
                        current_item = finished_item  # Item qui vient de se terminer
                        total_items = info.get('playlist_count') if info else None
                        # Pour les playlists, utiliser le titre de la vidéo depuis yt-dlp
                        finished_title = d.get("title") or title
                    else:
                        current_item = None
                        total_items = None
                        finished_title = title
                    
                    # Limiter le titre à 32 caractères maximum
                    finished_title = finished_title[:32] + "..." if len(finished_title) > 32 else finished_title
                    
                    self._on_progress(
                        DownloadProgress(
                            task_id=task.task_id,
                            status="finished",
                            percent=1.0,
                            title=finished_title,
                            thumbnail_url=thumbnail_url,
                            filename=d.get("filename"),
                            item_number=current_item,
                            total_items=total_items,
                        )
                    )
            finally:
                # Libérer le verrou pour les playlists uniquement si acquis
                if counter_lock and counter_lock.locked():
                    try:
                        counter_lock.release()
                    except RuntimeError:
                        # Le verrou n'était pas acquis par ce thread
                        pass
        
        # Envoyer la progression initiale
        if task.playlist:
            initial_title = _("Playlist detected: {}").format(info.get('title', 'Playlist')) if info else "Playlist"
            initial_item = 1
            initial_total = info.get('playlist_count') if info else None
        else:
            initial_title = title
            initial_item = None
            initial_total = None
            
        self._on_progress(
            DownloadProgress(
                task_id=task.task_id,
                status="preparing",
                percent=0.0,
                title=initial_title,
                thumbnail_url=thumbnail_url,
                total_bytes=total_bytes,
                downloaded_bytes=0,
                item_number=initial_item,
                total_items=initial_total,
            )
        )
        
        return hook

    def _ytdl_options(self, task: DownloadTask, info: dict = None) -> dict:
        """Utilise OptionsFormatter pour générer les options yt-dlp"""
        # Import local pour éviter l'import circulaire
        from .options_formatter import OptionsFormatter
        
        # Créer le formatter
        formatter = OptionsFormatter(self._downloads_view)
        
        # Générer les options de base avec le formatter
        ydl_opts, info = formatter.ytdl_options(task, info)
        
        # Ajouter le hook de progression depuis le DownloadManager
        hook = self._hook_progress(task, info)
        ydl_opts["progress_hooks"] = [hook]
        
        return ydl_opts
        
    def _run_playlist_download(self, task: DownloadTask) -> None:
        """Télécharge toute la playlist d'un seul coup"""
        self._downloads_view.process_anim.start()
        try:
            if self._downloads_view:
                self._downloads_view.log_info(_("Starting download: {}").format(task.url))
                self._downloads_view.log_info(_("Directory: {}").format(task.output_dir))
                self._downloads_view.log_info(_("Type: {} | Mode: {}").format(task.kind.upper(), "Playlist"))
            
            # Préparer les options yt-dlp pour la playlist complète
            ytdl_opts = self._ytdl_options(task)
            
            # Forcer le traitement de playlist comme --yes-playlist (pas d'extraction préalable)
            ytdl_opts['noplaylist'] = False
            # Supprimer extract_flat pour avoir le comportement normal de playlist
            if 'extract_flat' in ytdl_opts:
                del ytdl_opts['extract_flat']
            
            if self._downloads_view:
                self._downloads_view.log_info(_("Starting download: {}").format(task.url))

            # Télécharger directement la playlist - yt-dlp gère l'extraction en temps réel
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                ydl.download([task.url])
            
            if self._downloads_view:
                self._downloads_view.log_info(_("Playlist completed successfully!"))
            self._on_finished(task.task_id)
            
        except Exception as e:
            if self._downloads_view:
                self._downloads_view.log_error(_("Playlist download error: {}").format(str(e)))
                self._downloads_view.log_error(_("Original URL: {}").format(task.url))
                self._downloads_view.log_error(_("Directory: {}").format(task.output_dir))
            self._on_error(task.task_id, e)

    def _format_bytes(self, num_bytes: int) -> str:
        """Formate un nombre d'octets en unités lisibles"""
        if num_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while num_bytes >= 1024 and i < len(units) - 1:
            num_bytes /= 1024.0
            i += 1
        return f"{num_bytes:.1f} {units[i]}"

    def _run_download(self, task: DownloadTask) -> None:
        self._downloads_view.process_anim.stop()
        try:
            # Vérifier si la tâche a été annulée avant de commencer
            if task.cancelled:
                if self._downloads_view:
                    self._downloads_view.log_info(_("Download cancelled: {}").format(task.task_id))
                return
                
            if self._downloads_view:
                self._downloads_view.log_info(_("Starting download: {}").format(task.url))
                self._downloads_view.log_info(_("Type: {} | Directory: {}").format(task.kind.upper(), task.output_dir))
                self._downloads_view.log_info(_("Parameters: overwrite={}, rate_limit={}KiB/s").format(task.settings.general.overwrite, task.settings.general.limit_rate_kib_s))
                # Tester le handler yt-dlp
                self._logger.info("Handler yt-dlp initialisé avec succès")
            
            task.output_dir.mkdir(parents=True, exist_ok=True)
            if self._downloads_view:
                self._downloads_view.log_info(_("Output directory verified: {}").format(task.output_dir))

            # Préparer les options yt-dlp
            ydl_opts = self._ytdl_options(task)
            
            if self._downloads_view:
                self._downloads_view.log_info(_("yt-dlp options configured:"))
                self._downloads_view.log_info(_("   - Format: {}").format(ydl_opts.get('format', 'default')))
                self._downloads_view.log_info(_("   - Template: {}").format(ydl_opts.get('outtmpl', 'default')))
                self._downloads_view.log_info(_("   - Postprocessors: {} configured").format(len(ydl_opts.get('postprocessors', []))))
                self._downloads_view.log_debug("ydl_opts: " + str(ydl_opts))
                self._downloads_view.log_debug(str(task))
                self._downloads_view.log_info(_("Launching download with yt-dlp..."))
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([task.url])

            # Vérifier si la tâche a été annulée pendant le téléchargement
            if task.cancelled:
                if self._downloads_view:
                    self._downloads_view.log_info(_("Download cancelled: {}").format(task.task_id))
                return

            if self._downloads_view:
                self._downloads_view.log_info(_("Download completed successfully!"))
            self._on_finished(task.task_id)
        except yt_dlp.DownloadError as e:
            # Vérifier si c'est une annulation utilisateur
            if "annulé" in str(e).lower() and task.cancelled:
                if self._downloads_view:
                    self._downloads_view.log_info(_("Download {} cancelled successfully").format(task.task_id))
                # Ne pas appeler on_error pour les annulations normales
                return
            else:
                # Autre erreur de téléchargement
                if self._downloads_view:
                    self._downloads_view.log_error(_("Download error: {}").format(str(e)))
                self._on_error(task.task_id, e)
        except Exception as e:
            if self._downloads_view:
                self._downloads_view.log_error(_("Download error: {}").format(str(e)))
                self._downloads_view.log_error(_("URL: {}").format(task.url))
                self._downloads_view.log_error(_("Directory: {}").format(task.output_dir))
            self._on_error(task.task_id, e)
