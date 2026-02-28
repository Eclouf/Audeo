"""
files for formatting yt-dlp options
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

import yt_dlp
import toga

from .settings import AppSettings
from .views import DownloadsView
from .i18n import _
from .download_models import DownloadTask

class OptionsFormatter:
    def __init__(self, downloads_view: DownloadsView, main_window: toga.App = None):
        self._downloads_view = downloads_view
        self._main_window = main_window
    
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
        
    def _base_options(self, settings: AppSettings) -> dict:
        """Return the base options for yt-dlp
        
        Returns:
            dict: The base options for yt-dlp
        """
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
    
    def ytdl_options(self, task: DownloadTask, info: dict = None) -> dict:
        """Return the options for yt-dlp
        
        Returns:
            dict: The options for yt-dlp
        """
        g = task.settings.general
        vset = task.settings.video
        aset = task.settings.audio
        
        ydl_opts = self._base_options(task.settings)
        
        is_playlist = task.playlist
        thumbnail_url = None  # Initialiser thumbnail_url
        
        if not info:
            self._downloads_view.log_info(_("Extracting metadata..."))
            # Vérifier si la tâche a été annulée avant l'extraction
            if task.cancelled:
                raise yt_dlp.DownloadError(_("Download cancelled before extraction"))
                
            # Extraction des métadonnées selon le type
            extract_opts = self._base_options(task.settings)
            extract_opts.update({
                'extract_flat': 'in_playlist' if is_playlist else False,
                "noplaylist": False if is_playlist else True,
                'noprogress': True,
                'simulate': True,  # Ne télécharge rien
                'skip_download': True,  # Ne pas télécharger
                'writethumbnail': False,  # Ne pas écrire les miniatures
                'write_all_thumbnails': False,  # Ne pas écrire toutes les miniatures
            })
            
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                info = ydl.extract_info(task.url, download=False)
            
                # Gestion sécurisée des miniatures
                thumbnail_url = info.get('thumbnail') or info.get('playlist_thumbnail')
                
                if not thumbnail_url and is_playlist and 'thumbnails' in info:
                    thumbnails = info.get('thumbnails')
                    # Validation que thumbnails est bien une liste avant l'indexation
                    if isinstance(thumbnails, list) and len(thumbnails) > 0:
                        first_thumbnail = thumbnails[0]
                        if isinstance(first_thumbnail, dict):
                            thumbnail_url = first_thumbnail.get('url')
                        else:
                            thumbnail_url = str(first_thumbnail) if first_thumbnail else None    
            
                info["thumbnail"] = thumbnail_url 
                # Vérifier si la tâche a été annulée pendant l'extraction
            if task.cancelled:
                raise yt_dlp.DownloadError(_("Download cancelled during metadata extraction"))
        
        if is_playlist and g.download_playlist:
            # Cas playlist
            if self._downloads_view:
                self._downloads_view.log_info(_("Playlist detected: {}").format(info.get('title', 'Playlist')))
                self._downloads_view.log_info(_("Items: {}").format(info.get('playlist_count', 0)))
                if thumbnail_url:
                    self._downloads_view.log_info(_("Playlist thumbnail loaded"))
                else:
                    self._downloads_view.log_info(_("Using default playlist icon"))
            
            # Configurer pour télécharger toute la playlist
            ydl_opts["noplaylist"] = False
        
        else:
            # Cas vidéo seule
            if self._downloads_view:
                self._downloads_view.log_info(_("Single video detected: {}").format(info.get("title", "Vidéo")))
                self._downloads_view.log_info(_("File size: {} bytes").format(info.get("filesize") or info.get("filesize_approx")))
            
            # Configurer pour télécharger seulement cette vidéo
            ydl_opts["noplaylist"] = True
        
        # Gérer la syntaxe %(champ1,champ2)s pour les champs multiples
        output_template = self._convert_multiple_fields(g.output_template)
        
        ydl_opts.update({
            "outtmpl": str(task.output_dir / output_template),
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
            
        self._output_format(ydl_opts, g, vset, aset, task)
        self._metadata_parser(ydl_opts, g)
        self._metadata_ffmpeg(ydl_opts, g, task, aset, vset)
        
        return ydl_opts, info
        
    def _convert_multiple_fields(self, output_template: str) -> str:
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
                self._downloads_view.log_info(_("Filename template converted: {} -> {}").format(original_template, output_template))
        
        return output_template
        

    def _output_format(self, ydl_opts: dict, g, vset, aset, task):
        
        # Format selection
        if g.output_format:
            ydl_opts["format"] = g.output_format
            if self._downloads_view:
                self._downloads_view.log_info(_("Custom format: {}").format(g.output_format))
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
                    self._downloads_view.log_info(_("Preferred audio codec: {}").format(target_ext))
                
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
                        self._downloads_view.log_info(_("Audio extension: {}").format(target_ext))
            else:
                ydl_opts["format"] = "bestaudio/best"
                if self._downloads_view:
                    self._downloads_view.log_info(_("Audio: Best automatic quality"))
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
                    self._downloads_view.log_info(_("Preferred video codec: {}").format(codec_name))
            elif self._downloads_view:
                self._downloads_view.log_info(_("Preferred video codec: {}").format(codec_name))
        return ydl_opts
        
    def _metadata_parser(self, ydl_opts: dict, g):
        # Handle metadata parsing
        if getattr(g, "parse_metadata_enabled", False):
            if self._downloads_view:
                self._downloads_view.log_info(_("Parsing metadata: Enabled"))
                
            rules_raw = (getattr(g, "parse_metadata_rules", "") or "").strip()
            if rules_raw:
                if self._downloads_view:
                    self._downloads_view.log_debug(_("Raw rules: {}").format(rules_raw))
                
                actions = [(yt_dlp.postprocessor.metadataparser.MetadataParserPP.interpretter, '%(artist)s ', '(?s)(?P<artist>.+)')]
                for raw in rules_raw.splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            field_name, pattern = parts[0].strip(), parts[1].strip()
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
                        self._downloads_view.log_info(_("Parse metadata enabled"))
                    if self._downloads_view:
                        self._downloads_view.log_info(_("Parse metadata rules: {}").format(len(actions)))
        return ydl_opts
    
    def _metadata_ffmpeg(self, ydl_opts: dict, g, task, aset, vset):
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
                self._downloads_view.log_info(_("Metadata FFmpeg: Enabled"))
            
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
                    self._downloads_view.log_info(_("Custom metadata: {}").format(len(ffmeta)//2))

        # Handle thumbnail settings
        if g.add_thumbnail or (task.kind == "audio" and aset.square_thumbnail):
            if self._downloads_view:
                self._downloads_view.log_info(_("Thumbnail: Enabled"))
                if task.kind == "audio" and aset.square_thumbnail:
                    self._downloads_view.log_info(_("Square thumbnail: Enabled (audio)"))
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
                self._downloads_view.log_info(_("Subtitles: Enabled (all languages)"))

        if vset.chapters:
            ydl_opts["embedchapters"] = True
            if self._downloads_view:
                self._downloads_view.log_info(_("Chapters: Enabled"))
        
        return ydl_opts