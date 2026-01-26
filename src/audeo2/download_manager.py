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

from .settings import AppSettings


class YdlLogHandler(logging.Handler):
    """Handler personnalisé pour rediriger les logs yt-dlp vers le terminal"""
    
    def __init__(self, downloads_view):
        super().__init__()
        self.downloads_view = downloads_view
        self.setLevel(logging.DEBUG)
    
    def emit(self, record):
        """Émet un message de log vers le terminal"""
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
                        self.downloads_view.log_info(f"yt-dlp: {message.strip()}")
                    elif '[warning]' in message_lower:
                        self.downloads_view.log_warning(f"yt-dlp: {message.strip()}")
                    elif '[error]' in message_lower:
                        self.downloads_view.log_error(f"yt-dlp: {message.strip()}")
                    elif 'download' in message_lower and '%' in message_lower:
                        # Messages de progression de téléchargement
                        self.downloads_view.log_info(f"yt-dlp: {message.strip()}")
                    elif any(keyword in message_lower for keyword in ['extracting', 'downloading', 'finished', 'playlist']):
                        # Messages importants sur le déroulement
                        self.downloads_view.log_info(f"yt-dlp: {message.strip()}")
                    else:
                        # Autres messages debug moins importants
                        self.downloads_view.log_debug(f"yt-dlp: {message.strip()}")
        except Exception as e:
            # Afficher l'erreur pour le debugging
            print(f"Erreur dans YdlLogHandler.emit: {e}")
            # Ignorer les erreurs de logging pour ne pas bloquer yt-dlp
            pass


@dataclass(slots=True)
class DownloadProgress:
    task_id: str
    status: str
    percent: float
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    total_bytes: Optional[int] = None
    downloaded_bytes: Optional[int] = None
    eta_seconds: Optional[int] = None
    speed_bytes_s: Optional[float] = None
    filename: Optional[str] = None
    url: Optional[str] = None  # Pour les playlists
    duration: Optional[int] = None  # Durée de la vidéo
    uploader: Optional[str] = None  # Chaîne/uploader
    item_number: Optional[int] = None  # Numéro d'item dans la playlist
    total_items: Optional[int] = None  # Nombre total d'items


@dataclass(slots=True)
class DownloadTask:
    task_id: str
    url: str
    output_dir: Path
    kind: str  # "video" | "audio"
    settings: AppSettings
    created_at: float = field(default_factory=time.time)
    #urls_dict: dict = field(default_factory=dict)  # Pour les playlists
    future: Optional[object] = field(default=None)  # Future du ThreadPoolExecutor
    cancelled: bool = field(default=False)  # État d'annulation
    paused: bool = field(default=False)  # État de pause
    playlist: bool = field(default=False)  # Indique si c'est une tâche de playlist


class DownloadManager:
    def __init__(
        self,
        *,
        max_workers: int,
        on_progress: Callable[[DownloadProgress], None],
        on_finished: Callable[[str], None],
        on_error: Callable[[str, Exception], None],
        downloads_view=None,
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._on_progress = on_progress
        self._on_finished = on_finished
        self._on_error = on_error
        self._downloads_view = downloads_view
        self._lock = threading.Lock()
        self._tasks: dict[str, DownloadTask] = {}
        
        # Configurer le logger yt-dlp une seule fois
        self._logger = logging.getLogger("yt_dlp")
        self._logger.setLevel(logging.DEBUG)
        
        # Créer un handler personnalisé pour rediriger vers le terminal
        self._ydl_handler = None
        if downloads_view:
            self._ydl_handler = YdlLogHandler(downloads_view)
            self._ydl_handler.setLevel(logging.DEBUG)
            self._logger.addHandler(self._ydl_handler)
            # Empêcher la propagation aux handlers parents pour éviter les doublons
            self._logger.propagate = False

    def shutdown(self) -> None:
        # Retirer le handler avant de fermer
        if self._ydl_handler and self._logger:
            self._logger.removeHandler(self._ydl_handler)
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
                    self._downloads_view.log_info(f"Téléchargement {task_id} marqué pour annulation")
                    
    def pause_download(self, task_id: str) -> None:
        """Met en pause un téléchargement spécifique"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.paused = True
                if self._downloads_view:
                    self._downloads_view.log_info(f"Téléchargement {task_id} mis en pause")
                    
    def resume_download(self, task_id: str) -> None:
        """Reprend un téléchargement spécifique"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.paused = False
                if self._downloads_view:
                    self._downloads_view.log_info(f"Téléchargement {task_id} repris")

    def _detect_playlist_by_url(self, url: str) -> bool:
        """
        Détecte si une URL est une playlist en utilisant urllib.parse
        pour une analyse robuste de l'URL et de ses paramètres
        """
        try:
            # Parser l'URL avec urllib
            parsed = urllib.parse.urlparse(url)
            
            # Extraire les paramètres de la query string
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # Vérifier les paramètres typiques de playlist
            playlist_indicators = {
                'list', 'list_id', 'playlist_id', 'pl', 'playlists',
                'index', 'start_radio', 'rd'  # YouTube radio/autoplay
            }
            
            # Vérifier si un paramètre de playlist est présent
            for param in query_params:
                if any(indicator in param.lower() for indicator in playlist_indicators):
                    return True
            
            # Analyser le chemin de l'URL
            path_segments = parsed.path.lower().split('/')
            
            # Patterns de playlist dans le chemin
            playlist_path_patterns = [
                'playlist', 'playlists', 'album', 'albums', 
                'collection', 'mix', 'radio', 'station'
            ]
            
            for segment in path_segments:
                if any(pattern in segment for pattern in playlist_path_patterns):
                    return True
            
            # Patterns spécifiques par domaine
            domain = parsed.netloc.lower()
            
            # YouTube patterns
            if 'youtube.com' in domain or 'youtu.be' in domain:
                # /playlist?list=...
                if 'playlist' in path_segments:
                    return True
                # Paramètres de type playlist
                if any(key in query_params for key in ['list', 'index', 'start_radio']):
                    return True
            
            # Spotify patterns
            elif 'spotify.com' in domain:
                # /playlist/, /album/, /collection/
                if any(p in path_segments for p in ['playlist', 'album', 'collection']):
                    return True
            
            # SoundCloud patterns
            elif 'soundcloud.com' in domain:
                # /sets/ est le pattern pour les playlists sur SoundCloud
                if 'sets' in path_segments:
                    return True
            
            # Bandcamp patterns
            elif 'bandcamp.com' in domain:
                # /album/, /track/ avec paramètres multiples
                if 'album' in path_segments:
                    return True
            
            # Deezer patterns
            elif 'deezer.com' in domain:
                if any(p in path_segments for p in ['playlist', 'album']):
                    return True
            
            # Pattern générique : recherche textuelle dans l'URL complète
            url_lower = url.lower()
            generic_patterns = [
                r'\bplaylist\b', r'\blist\b', r'\bplaylist_id\b',
                r'\balbum\b', r'\bcollection\b', r'\bset\b',
                r'\bmix\b', r'\bradio\b', r'\bstation\b'
            ]
            
            for pattern in generic_patterns:
                if re.search(pattern, url_lower):
                    return True
            
            return False
            
        except Exception as e:
            if self._downloads_view:
                self._downloads_view.log_debug(f"Erreur lors de l'analyse d'URL: {e}")
            return False

    def submit(self, *, url: str, output_dir: Path, kind: str, settings: AppSettings) -> list[DownloadTask]:
        """Télécharge une URL ou une playlist complète"""
        try:
            # Détection robuste de playlist : URL + extraction
            is_playlist = False
            print("\n Testing playlist detection...\n")
            try:
                # 1. Détection par analyse d'URL avec urllib
                is_playlist = self._detect_playlist_by_url(url)
                options = self._prepare_base_options(settings)
                options['quiet'] = True
                options['extract_flat'] = True
                
                # 2. Extraction complète pour confirmation avec yt-dlp
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=False)
                    print("\n INFO LIST\n" + str(info) + "\n")
                    
                    # Confirmer avec les métadonnées yt-dlp
                    ytdl_is_playlist = (
                        info.get("ie_key") == "Playlist" or 
                        info.get('_type') == 'playlist' or 
                        info.get('playlist_count', 0) > 0 or
                        'entries' in info
                    )
                    print("\nfin\n")
                    # Utiliser la détection yt-dlp si elle est positive, sinon garder l'analyse d'URL
                    is_playlist = is_playlist or ytdl_is_playlist
                    
                if is_playlist:
                    detection_method = "yt-dlp" if ytdl_is_playlist else "URL analysis"
                    self._downloads_view.log_info(f"URL détectée comme une playlist ({detection_method}): {url}")
                    print(f"Playlist detected by {detection_method}")
                else:
                    print("not playlist")
                    
            except Exception as e:
                print(f"Detection error: {e}")
                # Fallback basé sur l'URL seule avec urllib
                is_playlist = self._detect_playlist_by_url(url)
                if is_playlist:
                    self._downloads_view.log_info(f"URL détectée comme playlist (URL analysis fallback): {url}")
                    print("Playlist detected (URL fallback)")
                else:
                    print("not playlist")
            
            if is_playlist and settings.general.download_playlist:
                print("\nProcessing playlist\n")
                self._downloads_view.log_info("Processing playlist")
                self._downloads_view.log_info(f"Items number: {info.get('playlist_count', 0)}")
                if settings.general.download_playlist and settings.general.playlist_folder_name.strip():
                    playlist_folder_name = settings.general.playlist_folder_name.strip()
                    final_output_dir = output_dir / playlist_folder_name
                    self._downloads_view.log_info(f"Dossier playlist: {final_output_dir}")
                    
                elif settings.general.download_playlist:
                    final_output_dir = output_dir
                    self._downloads_view.log_info(f"Dossier playlist: {final_output_dir}")
                    
                return [self._task(url, final_output_dir, kind, settings, True)]
            else:
                print("\nProcessing single item\n")
                final_output_dir = output_dir
                return [self._task(url, final_output_dir, kind, settings, False)]
              
        except Exception as e:
            if self._downloads_view:
                self._downloads_view.log_error(f"Erreur: {str(e)}")
            # Fallback: traiter comme une vidéo normale
            return [self._task(url, output_dir, kind, settings)]
        
    def _task(self, original_url: str, output_dir: Path, kind: str, settings: AppSettings, playlist: bool) -> DownloadTask:
        """
        Crée une tâche de téléchargement pour une URL donnée
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

    def _url_proxy_parsing(self, url: str, id: None | str, pw: None | str) -> str:
        """Build proxy url from url, id and pw"""
        parsed = urlparse(url)
        # Construire l'URL complète avec authentification
        if id and pw:
            # URL avec identifiants: http://user:pass@host:port
            proxy_url = f"{parsed.scheme}://{id}:{pw}@{parsed.hostname}:{parsed.port}"
        else:
            # URL sans identifiants: http://host:port
            proxy_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        return proxy_url

    def _prepare_base_options(self, settings: AppSettings) -> dict:
        """Prépare les options de base pour yt-dlp"""
        base_opts = {
            "quiet": False,
            "no_warnings": False,
            #"ignoreerrors": True,  # Ignorer les erreurs non critiques comme les dates
        }
        
        if settings.ffmpeg_path:
            base_opts["ffmpeg_location"] = settings.ffmpeg_path
        
        if settings.general.proxy_url:
            proxy_url = self._url_proxy_parsing(settings.general.proxy_url, settings.general.proxy_id, settings.general.proxy_pw)
            base_opts["proxy"] = proxy_url
            
        return base_opts

    def _ytdl_options(self, task: DownloadTask, info: dict = None) -> dict:
        """Retourne les options pour yt-dlp"""
        g = task.settings.general
        vset = task.settings.video
        aset = task.settings.audio

        # Utiliser les options de base
        ydl_opts = self._prepare_base_options(task.settings)
        
        # Utiliser le champ playlist de la tâche au lieu de redétecter
        is_playlist = task.playlist
        
        if not info:
            print("\ninfo\n")
            # Vérifier si la tâche a été annulée avant l'extraction
            if task.cancelled:
                raise yt_dlp.DownloadError("Téléchargement annulé avant l'extraction des métadonnées")
                
            # Extraction des métadonnées selon le type
            extract_opts = self._prepare_base_options(task.settings)
            if is_playlist:
                print("\nplaylist\n")
                extract_opts['extract_flat'] = True  # Métadonnées complètes pour playlist
                extract_opts['noplaylist'] = False    # Garder la playlist
            else:
                extract_opts['extract_flat'] = False  # Métadonnées complètes pour vidéo seule
                extract_opts['noplaylist'] = True     # Seulement cette vidéo
            
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                info = ydl.extract_info(task.url, download=False)
                
            # Vérifier si la tâche a été annulée pendant l'extraction
            if task.cancelled:
                raise yt_dlp.DownloadError("Téléchargement annulé pendant l'extraction des métadonnées")
        
        if is_playlist and g.download_playlist:
            print("\nProcessing playlist options\n")
            # Cas playlist : utiliser les métadonnées de la playlist
            title = info.get('title', 'Playlist')
            thumbnail_url = None
            total_bytes = None  # Sera calculé en temps réel
            item_opts = self._prepare_base_options(task.settings)
            item_opts['extract_flat'] = False
            item_opts['noplaylist'] = True
            item_opts['skip_download'] = True
            
            # Essayer d'obtenir une miniature depuis le premier item si disponible
            if 'entries' in info and info['entries'] and len(info['entries']) > 0:
                first_entry = info['entries'][0]
                if isinstance(first_entry, dict) and 'thumbnail' in first_entry:
                    thumbnail_url = first_entry['thumbnail']
                elif isinstance(first_entry, str):
                    # Si c'est juste une URL, extraire les métadonnées du premier item
                    try:
                        with yt_dlp.YoutubeDL(item_opts) as ydl:
                            first_item_info = ydl.extract_info(first_entry, download=False)
                            thumbnail_url = first_item_info.get('thumbnail')
                    except Exception:
                        pass  # Ignorer les erreurs de miniature
            else:
                try:
                    with yt_dlp.YoutubeDL(item_opts) as ydl:
                        first_item_info = ydl.extract_info(task.url, download=False)
                        thumbnail_url = first_item_info.get('thumbnail')
                except Exception:
                    pass  # Ignorer les erreurs de miniature
                
            if self._downloads_view:
                self._downloads_view.log_info(f"Playlist détectée: {title}")
                self._downloads_view.log_info(f"Items: {info.get('playlist_count', 0)}")
                if thumbnail_url:
                    self._downloads_view.log_info(f"Miniature disponible")
                else:
                    self._downloads_view.log_info(f"Pas de miniature disponible")
            
            # Configurer pour télécharger toute la playlist
            ydl_opts["noplaylist"] = False
        
        else:
            print("\nProcessing single item option\n")
            # Cas vidéo seule : utiliser les métadonnées directes
            title = info.get("title", "Vidéo")
            thumbnail_url = info.get("thumbnail")
            total_bytes = info.get("filesize") or info.get("filesize_approx")
            
            if self._downloads_view:
                self._downloads_view.log_info(f"Vidéo seule détectée: {title}")
            
            # Configurer pour télécharger seulement cette vidéo
            ydl_opts["noplaylist"] = True
        
        # Limiter le titre à 32 caractères
        if len(title) > 32:
            title = title[:29] + "..."
        
        if self._downloads_view:
            self._downloads_view.log_info(f"Titre: {title}")
            if thumbnail_url:
                self._downloads_view.log_info(f"Vignette: {thumbnail_url}")
            if total_bytes:
                self._downloads_view.log_info(f"Taille estimée: {self._format_bytes(total_bytes)}")
            else:
                self._downloads_view.log_info("Taille: sera calculée en temps réel")
        
        # Compteur d'items pour les playlists
        item_counter = 0
        if is_playlist:
            item_counter = 1  # Commence à 1 pour la première item
        
        # Définir le hook de progression avec accès aux variables
        def hook(d: dict) -> None:
            nonlocal item_counter
            
            # Vérifier si la tâche a été annulée
            if task.cancelled:
                raise yt_dlp.DownloadError("Téléchargement annulé par l'utilisateur")
            
            # Gérer la pause : attendre que la pause soit levée
            while task.paused and not task.cancelled:
                import time
                time.sleep(0.1)  # Attendre 100ms
                
            # Vérifier à nouveau si la tâche a été annulée pendant la pause
            if task.cancelled:
                raise yt_dlp.DownloadError("Téléchargement annulé par l'utilisateur")
                
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes")
                percent = 0.0
                if total and downloaded is not None and total > 0:
                    percent = max(0.0, min(1.0, downloaded / total))

                # Utiliser le compteur manuel pour les playlists
                current_item = item_counter if is_playlist else None
                total_items = info.get('playlist_count') if is_playlist else None

                self._on_progress(
                    DownloadProgress(
                        task_id=task.task_id,
                        status="paused" if task.paused else "downloading",
                        percent=percent,
                        title=title,
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
                # Incrémenter le compteur pour le prochain item
                if is_playlist:
                    item_counter += 1
                
                current_item = item_counter - 1 if is_playlist else None
                total_items = info.get('playlist_count') if is_playlist else None
                
                self._on_progress(
                    DownloadProgress(
                        task_id=task.task_id,
                        status="finished",
                        percent=1.0,
                        title=f"{title} - Terminé",
                        thumbnail_url=thumbnail_url,
                        filename=d.get("filename"),
                        item_number=current_item,
                        total_items=total_items,
                    )
                )
        
        # Envoyer la progression initiale
        self._on_progress(
            DownloadProgress(
                task_id=task.task_id,
                status="preparing",
                percent=0.0,
                title=title,
                thumbnail_url=thumbnail_url,
                total_bytes=total_bytes,
                downloaded_bytes=0,
                item_number=1 if is_playlist else None,
                total_items=info.get('playlist_count') if is_playlist else None,
            )
        )

        # Gérer la syntaxe %(champ1,champ2)s pour les champs multiples
        output_template = g.output_template
        if ", " in output_template:
            # Convertir %(champ1,champ2)s en %(champ1)s - %(champ2)s ou %(champ1)s_%(champ2)s
            import re
            original_template = output_template
            def convert_multiple_fields(match):
                fields = match.group(1).split(", ")
                if len(fields) == 2:
                    return f"%({fields[0]})s - %({fields[1]})s"
                else:
                    # Pour plus de 2 champs, utiliser des tirets
                    return " - ".join([f"%({field})s" for field in fields])
            
            # Remplacer tous les %(champ1,champ2,etc)s
            output_template = re.sub(r'%\(([^)]+)\)s', convert_multiple_fields, output_template)
            
            if self._downloads_view and original_template != output_template:
                self._downloads_view.log_info(f"Modèle de nom converti: {original_template} -> {output_template}")
        
        ydl_opts.update({
            "outtmpl": str(task.output_dir / output_template),
            "progress_hooks": [hook],
        })

        # Ajouter les autres options spécifiques
        if g.overwrite:
            ydl_opts["overwrites"] = True
        else:
            ydl_opts["nooverwrites"] = True

        if g.limit_rate_enabled and g.limit_rate_kib_s > 0:
            ydl_opts["ratelimit"] = int(g.limit_rate_kib_s) * 1024

        if g.concurrent_fragments > 0:
            ydl_opts["concurrent_fragments"] = int(g.concurrent_fragments)
            
        if g.proxy_url:
            proxy_url = self._url_proxy_parsing(g.proxy_url, g.proxy_id, g.proxy_pw)
            ydl_opts["proxy"] = proxy_url
        
        # Format selection
        if g.output_format:
            ydl_opts["format"] = g.output_format
            if self._downloads_view:
                self._downloads_view.log_info(f"Format personnalisé: {g.output_format}")
        elif task.kind == "audio":
            target_ext = None
            if aset.preferred_codec and aset.preferred_codec != "auto":
                target_ext = aset.preferred_codec
            elif aset.ext and aset.ext != "auto":
                target_ext = aset.ext
            else:
                target_ext = "m4a"
            
            # Stratégie : 1. Essayer le format cible direct, 2. Sinon convertir
            if target_ext and target_ext != "auto":
                # D'abord essayer de trouver le format avec l'extension souhaitée
                ydl_opts["format"] = f"bestaudio[ext={target_ext}]/bestaudio"
                if self._downloads_view:
                    self._downloads_view.log_info(f"Audio: Recherche format {target_ext}, conversion si nécessaire")
                
                # Ajouter le postprocessor de conversion seulement si le format direct n'est pas trouvé
                # yt-dlp utilisera le postprocessor seulement si le format cible n'est pas disponible
                codec_map = {
                    "mp3": "mp3",
                    "m4a": "aac", 
                    "aac": "aac",
                    "opus": "opus",
                    "vorbis": "libvorbis",
                    "wav": "pcm_s16le",
                    "flac": "flac",
                    "alac": "alac"
                }
                
                if target_ext in codec_map:
                    ydl_opts.setdefault("postprocessors", []).append({
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": codec_map[target_ext],
                        "preferredquality": "0",  # Meilleure qualité
                    })
                    if self._downloads_view:
                        self._downloads_view.log_info(f"Audio: Conversion vers {target_ext} si format direct non disponible")
            else:
                ydl_opts["format"] = "bestaudio/best"
                if self._downloads_view:
                    self._downloads_view.log_info("Audio: Meilleur qualité automatique")
        else:
            fmt = "bestvideo+bestaudio/best"
            codec_name = "auto"
            if vset.preferred_codec and vset.preferred_codec != "auto":
                if vset.preferred_codec == "h264":
                    fmt = "bestvideo[vcodec^=avc1]+bestaudio/best"
                    codec_name = "H.264"
                elif vset.preferred_codec == "vp9":
                    fmt = "bestvideo[vcodec^=vp9]+bestaudio/best"
                    codec_name = "VP9"
                elif vset.preferred_codec == "av1":
                    fmt = "bestvideo[vcodec^=av01]+bestaudio/best"
                    codec_name = "AV1"
            ydl_opts["format"] = fmt
            if vset.ext and vset.ext != "auto":
                ydl_opts["merge_output_format"] = vset.ext
                if self._downloads_view:
                    self._downloads_view.log_info(f"Vidéo: Codec {codec_name} -> Extension {vset.ext}")
            elif self._downloads_view:
                self._downloads_view.log_info(f"Vidéo: Codec {codec_name}")
        
        # Handle metadata parsing
        if getattr(g, "parse_metadata_enabled", False):
            if self._downloads_view:
                self._downloads_view.log_info("Parsing métadonnées: Activé")
                
            rules_raw = (getattr(g, "parse_metadata_rules", "") or "").strip()
            if rules_raw:
                if self._downloads_view:
                    self._downloads_view.log_debug(f"Règles brutes: {rules_raw}")
                
                actions = []
                for raw in rules_raw.splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            field_name, pattern = parts[0].strip(), parts[1].strip()
                            # Nettoyer le pattern mais garder les groupes nommés
                            import re
                            # Enlever les guillemets extérieurs s'ils sont présents
                            if (pattern.startswith('"') and pattern.endswith('"')) or \
                               (pattern.startswith("'") and pattern.endswith("'")):
                                pattern = pattern[1:-1]
                            # Remove trailing : if present
                            pattern = pattern.rstrip(':')
                            if pattern:
                                actions.append((yt_dlp.postprocessor.metadataparser.MetadataParserPP.interpretter, field_name, pattern))
                
                if actions:
                    ydl_opts.setdefault("postprocessors", []).append({
                        "key": "MetadataParser",
                        "when": "pre_process",
                        "actions": actions,
                    })
                    if self._downloads_view:
                        self._downloads_view.log_info(f"Actions métadonnées: {len(actions)} règles appliquées")

        if getattr(g, "add_metadata", True):
            ydl_opts["addmetadata"] = True
            # Ajouter le postprocessor FFmpegMetadata comme dans la CLI
            ydl_opts.setdefault("postprocessors", []).append({
                "key": "FFmpegMetadata",
                "add_chapters": True,
                "add_infojson": "if_exists",
                "add_metadata": True,
            })
            if self._downloads_view:
                self._downloads_view.log_info("Métadonnées FFmpeg: Activées")
            
            custom = (getattr(g, "custom_metadata", "") or "").strip()
            if custom:
                args = ydl_opts.setdefault("postprocessor_args", {})
                ffmeta = args.setdefault("FFmpegMetadata", [])
                for raw in custom.splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if not key:
                        continue
                    ffmeta.extend(["-metadata", f"{key}={value}"])
                if self._downloads_view:
                    self._downloads_view.log_info(f"Métadonnées personnalisées: {len(ffmeta)//2} champs ajoutés")

        # Handle thumbnail settings
        if g.add_thumbnail or (task.kind == "audio" and aset.square_thumbnail):
            if self._downloads_view:
                self._downloads_view.log_info("Vignette: Activée")
                if task.kind == "audio" and aset.square_thumbnail:
                    self._downloads_view.log_info("Vignette carrée: Activée (audio)")
            ydl_opts["embedthumbnail"] = True
            ydl_opts["writethumbnail"] = True
            
            # Conversion des miniatures en jpg
            ydl_opts.setdefault("postprocessors", []).append({
                "key": "FFmpegThumbnailsConvertor",
                "format": "jpg",
                "when": "before_dl",
            })
            
            # Arguments pour le recadrage de la miniature carrée
            if task.kind == "audio" and aset.square_thumbnail:
                ydl_opts.setdefault("postprocessor_args", {}).setdefault("thumbnailsconvertor+ffmpeg_o", []).extend([
                    "-c:v", "mjpeg",
                    "-vf", "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
                ])
            
            # EmbedThumbnail doit être ajouté à la FIN de tous les autres postprocessors
            ydl_opts.setdefault("postprocessors", []).append({
                "key": "EmbedThumbnail",
                "already_have_thumbnail": False,
            })

        # Subtitles and chapters
        if vset.subtitles:
            ydl_opts["writesubtitles"] = True
            ydl_opts["writeautomaticsub"] = True
            ydl_opts["subtitleslangs"] = ["all"]
            if self._downloads_view:
                self._downloads_view.log_info("Sous-titres: Activés (toutes les langues)")

        if vset.chapters:
            ydl_opts["embedchapters"] = True
            if self._downloads_view:
                self._downloads_view.log_info("Chapitres: Activés")
        
        return ydl_opts
        
    def _run_playlist_download(self, task: DownloadTask) -> None:
        """Télécharge toute la playlist d'un seul coup"""
        try:
            if self._downloads_view:
                self._downloads_view.log_info(f"Début du téléchargement de playlist: {task.url}")
                self._downloads_view.log_info(f"Répertoire: {task.output_dir}")
                self._downloads_view.log_info(f"Type: {task.kind.upper()} | Mode: Playlist")
            
            # Préparer les options yt-dlp pour la playlist complète
            ytdl_opts = self._ytdl_options(task)
            
            # Ajouter un hook personnalisé pour la progression et gestion pause/stop
            def playlist_hook(d: dict) -> None:
                # Vérifier annulation
                if task.cancelled:
                    raise yt_dlp.DownloadError("Téléchargement annulé par l'utilisateur")
                
                # Gérer la pause
                while task.paused and not task.cancelled:
                    import time
                    time.sleep(0.1)
                
                if task.cancelled:
                    raise yt_dlp.DownloadError("Téléchargement annulé pendant la pause")
                
                # Progression détaillée
                status = d.get("status")
                if status == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    downloaded = d.get("downloaded_bytes")
                    
                    if total and downloaded is not None:
                        progress = downloaded / total
                        filename = d.get("filename", "")
                        
                        self._on_progress(
                            DownloadProgress(
                                task_id=task.task_id,
                                status="downloading",
                                percent=progress,
                                title=f"Playlist - {filename.split('/')[-1] if filename else 'Téléchargement'}",
                                downloaded_bytes=downloaded,
                                total_bytes=total,
                                eta_seconds=d.get("eta"),
                                speed_bytes_s=d.get("speed"),
                                filename=filename,
                            )
                        )
                elif status == "finished":
                    filename = d.get("filename", "")
                    self._on_progress(
                        DownloadProgress(
                            task_id=task.task_id,
                            status="finished",
                            percent=1.0,
                            title=f"Terminé: {filename.split('/')[-1] if filename else 'Item'}",
                            filename=filename,
                        )
                    )
            
            # Ajouter notre hook avant les hooks existants
            ytdl_opts.setdefault("progress_hooks", []).insert(0, playlist_hook)
            
            # Forcer le traitement de playlist comme --yes-playlist (pas d'extraction préalable)
            ytdl_opts['noplaylist'] = False
            # Supprimer extract_flat pour avoir le comportement normal de playlist
            if 'extract_flat' in ytdl_opts:
                del ytdl_opts['extract_flat']
            
            if self._downloads_view:
                self._downloads_view.log_info(f"Téléchargement direct de la playlist: {task.url}")
            
            # Télécharger directement la playlist - yt-dlp gère l'extraction en temps réel
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                ydl.download([task.url])
            
            if self._downloads_view:
                self._downloads_view.log_info("Playlist terminée avec succès!")
            self._on_finished(task.task_id)
            
        except Exception as e:
            if self._downloads_view:
                self._downloads_view.log_error(f"Erreur lors du téléchargement de playlist: {str(e)}")
                self._downloads_view.log_error(f"URL originale: {task.url}")
                self._downloads_view.log_error(f"Répertoire: {task.output_dir}")
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
        try:
            # Vérifier si la tâche a été annulée avant de commencer
            if task.cancelled:
                if self._downloads_view:
                    self._downloads_view.log_info(f"Téléchargement {task.task_id} annulé avant le démarrage")
                return
                
            if self._downloads_view:
                self._downloads_view.log_info(f"Début du téléchargement: {task.url}")
                self._downloads_view.log_info(f"Type: {task.kind.upper()} | Répertoire: {task.output_dir}")
                self._downloads_view.log_info(f"Paramètres: overwrite={task.settings.general.overwrite}, rate_limit={task.settings.general.limit_rate_kib_s}KiB/s")
                # Tester le handler yt-dlp
                self._logger.info("Handler yt-dlp initialisé avec succès")
            
            task.output_dir.mkdir(parents=True, exist_ok=True)
            if self._downloads_view:
                self._downloads_view.log_info(f"Répertoire de sortie vérifié: {task.output_dir}")

            # Préparer les options yt-dlp
            ydl_opts = self._ytdl_options(task)
            
            if self._downloads_view:
                self._downloads_view.log_info(f"Options yt-dlp configurées:")
                self._downloads_view.log_info(f"   - Format: {ydl_opts.get('format', 'default')}")
                self._downloads_view.log_info(f"   - Template: {ydl_opts.get('outtmpl', 'default')}")
                self._downloads_view.log_info(f"   - Postprocessors: {len(ydl_opts.get('postprocessors', []))} configurés")
                self._downloads_view.log_debug("ydl_opts: " + str(ydl_opts))
                self._downloads_view.log_debug(str(task))
                self._downloads_view.log_info("Lancement du téléchargement avec yt-dlp...")
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([task.url])

            # Vérifier si la tâche a été annulée pendant le téléchargement
            if task.cancelled:
                if self._downloads_view:
                    self._downloads_view.log_info(f"Téléchargement {task.task_id} annulé")
                return

            if self._downloads_view:
                self._downloads_view.log_info("Téléchargement terminé avec succès!")
            self._on_finished(task.task_id)
        except yt_dlp.DownloadError as e:
            # Vérifier si c'est une annulation utilisateur
            if "annulé" in str(e).lower() and task.cancelled:
                if self._downloads_view:
                    self._downloads_view.log_info(f"Téléchargement {task.task_id} annulé avec succès")
                # Ne pas appeler on_error pour les annulations normales
                return
            else:
                # Autre erreur de téléchargement
                if self._downloads_view:
                    self._downloads_view.log_error(f"Erreur de téléchargement: {str(e)}")
                self._on_error(task.task_id, e)
        except Exception as e:
            if self._downloads_view:
                self._downloads_view.log_error(f"Erreur lors du téléchargement: {str(e)}")
                self._downloads_view.log_error(f"URL: {task.url}")
                self._downloads_view.log_error(f"Répertoire: {task.output_dir}")
            self._on_error(task.task_id, e)
