from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import toga
from toga.style import Pack
import yt_dlp

from ..settings import AppSettings
from ..i18n import _


class VideoInfoView:
    def __init__(self, app: toga.App) -> None:
        self.app = app
        self.current_info = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Créer l'interface
        self._build_ui()
        
    def _build_ui(self) -> None:
        """Construit l'interface utilisateur"""
        # Conteneur principal
        main_box = toga.Box(style=Pack(direction="column", flex=1, padding=5))
        
        # Section URL avec boutons
        url_section = toga.Box(style=Pack(direction="row", margin_bottom=15))
        self.url_input = toga.TextInput(
            placeholder=_("Enter video URL..."),
            style=Pack(flex=1, margin_right=10)
        )
        self.analyze_btn = toga.Button(
            _("Analyze"),
            on_press=self._on_analyze,
            style=Pack(width=100, margin_right=5)
        )
        self.download_btn = toga.Button(
            _("Download"),
            on_press=self._on_download,
            style=Pack(width=120),
            enabled=False
        )
        url_section.add(self.url_input)
        url_section.add(self.analyze_btn)
        url_section.add(self.download_btn)
        
        # Section informations vidéo
        info_section = toga.Box(style=Pack(direction="column", margin_bottom=15))
        info_title = toga.Label(
            _("Video Info"),
            style=Pack(font_size=14, font_weight="bold", margin_bottom=5)
        )
        
        # Conteneur pour les informations
        self.info_container = toga.Box(style=Pack(direction="column", margin_left=20))
        self._create_info_labels()
        
        info_section.add(info_title)
        info_section.add(self.info_container)
        
        # Section formats disponibles
        formats_section = toga.Box(style=Pack(direction="column", flex=1))
        formats_title = toga.Label(
            _("Available formats"),
            style=Pack(font_size=14, font_weight="bold", margin_bottom=5)
        )
        
        # Tableau des formats
        self.formats_table = toga.Table(
            headings=[_("Format"), _("Resolution"), _("Extension"), _("Codec"), _("Size"), _("FPS")],
            style=Pack(flex=1)
        )
        
        formats_section.add(formats_title)
        formats_section.add(self.formats_table)
        
        # Assembler l'interface
        main_box.add(url_section)
        main_box.add(info_section)
        main_box.add(formats_section)
        
        self.widget = main_box
        
    def _create_info_labels(self) -> None:
        """Crée les labels pour afficher les informations"""
        self.info_labels = {
            'title': toga.Label(f"{_("Title")}: -", style=Pack(font_weight="bold", font_size=12, margin_bottom=2)),
            'duration': toga.Label(f"{_("Duration")}: -", style=Pack(margin_bottom=2)),
            'uploader': toga.Label(f"{_("Uploader")}: -", style=Pack(margin_bottom=2)),
            'view_count': toga.Label(f"{_("Views")}: -", style=Pack(margin_bottom=2)),
            'upload_date': toga.Label(f"{_("Upload date")}: -", style=Pack(margin_bottom=2)),
            'description': toga.Label(f"{_("Description")}: -", style=Pack(margin_bottom=2)),
        }
        
        for label in self.info_labels.values():
            self.info_container.add(label)
            
    def _on_analyze(self, widget: toga.Button) -> None:
        """Gère le clic sur le bouton analyser"""
        url = self.url_input.value.strip()
        if not url:
            self._show_error("Veuillez entrer une URL valide")
            return
            
        if not self._is_valid_url(url):
            self._show_error("URL invalide. Utilisez une URL http(s) valide.")
            return
            
        # Désactiver le bouton pendant l'analyse
        self.analyze_btn.enabled = False
        self.analyze_btn.text = "Analyse..."
        
        # Lancer l'analyse en arrière-plan
        self.executor.submit(self._analyze_video, url)
        
    def _is_valid_url(self, url: str) -> bool:
        """Valide l'URL"""
        try:
            from urllib.parse import urlparse
            parts = urlparse(url)
            return parts.scheme in {"http", "https"} and bool(parts.netloc)
        except Exception:
            return False
            
    def _analyze_video(self, url: str) -> None:
        """Analyse la vidéo et extrait les métadonnées"""
        try:
            # Configuration yt-dlp pour l'extraction sans téléchargement
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            # Ajouter le proxy s'il est configuré
            settings = self.app.settings
            if settings.general.proxy_url:
                from urllib.parse import urlparse
                parsed = urlparse(settings.general.proxy_url)
                if settings.general.proxy_id and settings.general.proxy_pw:
                    # URL avec identifiants: http://user:pass@host:port
                    proxy_url = f"{parsed.scheme}://{settings.general.proxy_id}:{settings.general.proxy_pw}@{parsed.hostname}:{parsed.port}"
                else:
                    # URL sans identifiants: http://host:port
                    proxy_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                ydl_opts['proxy'] = proxy_url
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            # Mettre à jour l'interface depuis le thread principal
            self.app.loop.call_soon_threadsafe(self._update_ui, info)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            self.app.loop.call_soon_threadsafe(self._show_error, error_msg)
        finally:
            # Réactiver le bouton
            self.app.loop.call_soon_threadsafe(self._reset_analyze_button)
            
    def _update_ui(self, info: dict) -> None:
        """Met à jour l'interface avec les informations extraites"""
        self.current_info = info
        
        # Activer le bouton de téléchargement
        self.download_btn.enabled = True
        
        # Mettre à jour les informations de base
        self.info_labels['title'].text = f"{_("Title")}: {info.get('title', 'N/A')}"
        
        # Formater la durée
        duration = info.get('duration')
        if duration:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            else:
                duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = "N/A"
        self.info_labels['duration'].text = f"{_("Duration")}: {duration_str}"
        
        self.info_labels['uploader'].text = f"{_("Uploader")}: {info.get('uploader', 'N/A')}"
        
        # Formater le nombre de vues
        view_count = info.get('view_count')
        if view_count:
            if view_count >= 1000000:
                views_str = f"{view_count/1000000:.1f}M"
            elif view_count >= 1000:
                views_str = f"{view_count/1000:.1f}K"
            else:
                views_str = str(view_count)
        else:
            views_str = "N/A"
        self.info_labels['view_count'].text = f"{_("Views")}: {views_str}"
        
        # Formater la date
        upload_date = info.get('upload_date')
        if upload_date and len(upload_date) >= 8:
            date_str = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
        else:
            date_str = "N/A"
        self.info_labels['upload_date'].text = f"{_("Upload date")}: {date_str}"
        
        # Description (tronquée)
        description = info.get('description', '')
        if description:
            description = description[:100] + "..." if len(description) > 100 else description
        self.info_labels['description'].text = f"Description: {description or 'N/A'}"
        
        # Mettre à jour le tableau des formats
        self._update_formats_table(info.get('formats', []))
        
    def _update_formats_table(self, formats: list) -> None:
        """Met à jour le tableau des formats disponibles"""
        # Vider le tableau actuel
        self.formats_table.data.clear()
        
        # Trier les formats par qualité (résolution)
        sorted_formats = sorted(formats, key=self._format_sort_key, reverse=True)
        
        for fmt in sorted_formats:
            # Ignorer les formats sans informations utiles
            if not fmt.get('format_id'):
                continue
                
            # Extraire les informations
            format_id = fmt.get('format_id', 'N/A')
            
            # Résolution
            width = fmt.get('width')
            height = fmt.get('height')
            if width and height:
                resolution = f"{width}x{height}"
            else:
                resolution = "Audio" if fmt.get('acodec') != 'none' else "N/A"
            
            # Extension
            ext = fmt.get('ext', 'N/A')
            
            # Codec
            vcodec = fmt.get('vcodec', 'N/A')
            acodec = fmt.get('acodec', 'N/A')
            if vcodec != 'none' and vcodec != 'N/A':
                codec = vcodec.split('.')[0] if '.' in vcodec else vcodec
            elif acodec != 'none' and acodec != 'N/A':
                codec = acodec.split('.')[0] if '.' in acodec else acodec
            else:
                codec = 'N/A'
            
            # Taille
            filesize = fmt.get('filesize')
            if filesize:
                size_str = self._format_bytes(filesize)
            else:
                size_str = "N/A"
            
            # FPS
            fps = fmt.get('fps', 'N/A')
            if isinstance(fps, float):
                fps_str = f"{fps:.1f}"
            else:
                fps_str = str(fps) if fps else "N/A"
            
            # Ajouter au tableau
            self.formats_table.data.append([
                format_id,
                resolution,
                ext,
                codec,
                size_str,
                fps_str
            ])
            
    def _format_sort_key(self, fmt: dict) -> tuple:
        """Clé de tri pour les formats (priorité: vidéo > audio, puis résolution)"""
        # Priorité aux formats vidéo
        is_video = fmt.get('vcodec', 'none') != 'none'
        priority = 1 if is_video else 0
        
        # Résolution pour le tri
        width = fmt.get('width', 0) or 0
        height = fmt.get('height', 0) or 0
        resolution = width * height
        
        return (priority, resolution)
        
    def _format_bytes(self, n: int) -> str:
        """Formate les octets en unités lisibles"""
        if n <= 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        v = float(n)
        while v >= 1024.0 and i < len(units) - 1:
            v /= 1024.0
            i += 1
        return f"{v:.1f} {units[i]}"
        
    def _show_error(self, message: str) -> None:
        """Affiche un message d'erreur"""
        # Utiliser un dialogue d'erreur
        dialog = toga.ErrorDialog(_("Error"), message)
        # Créer une tâche async pour le dialogue
        import asyncio
        asyncio.create_task(self.app.main_window.dialog(dialog))
        
    def _reset_analyze_button(self) -> None:
        """Réinitialise le bouton d'analyse"""
        self.analyze_btn.enabled = True
        self.analyze_btn.text = _("Analyze")
        
    def _on_download(self, widget: toga.Button) -> None:
        """Gère le clic sur le bouton télécharger"""
        if not self.current_info:
            self._show_error(_("Please analyze a video first"))
            return
            
        url = self.url_input.value.strip()
        if not url:
            self._show_error(_("URL not available"))
            return
            
        # Basculer vers l'onglet de téléchargement et lancer le téléchargement
        self.app._show_view("Téléchargements")
        
        # Remplir l'URL dans la vue de téléchargement et lancer
        self.app.downloads_view.url_input.value = url
        
        # Simuler un clic sur le bouton d'ajout
        self.app._on_add(None)
