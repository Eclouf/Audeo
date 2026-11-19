from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from urllib.parse import urlparse

import customtkinter as ctk
import yt_dlp

from ..i18n import _
from ..formatting import fmt_bytes
from ..constants import ViewName


class VideoInfoView:
    def __init__(self, app) -> None:
        self.app = app
        self.current_info = None
        self.executor = ThreadPoolExecutor(max_workers=1)

        self._build_ui()

    def _build_ui(self) -> None:
        """Construit l'interface utilisateur"""
        self.widget = ctk.CTkFrame(self.app.content)

        # Section URL avec boutons
        top_frame = ctk.CTkFrame(self.widget)
        top_frame.pack(fill="x", padx=5, pady=5)

        self.url_input = ctk.CTkEntry(top_frame, placeholder_text=_("Enter video URL..."))
        self.url_input.bind("<Return>", lambda e: self._on_analyze())
        self.url_input.pack(side="left", fill="x", expand=True, padx=5)

        self.analyze_btn = ctk.CTkButton(
            top_frame,
            text=_("Analyze"),
            command=self._on_analyze,
            width=100,
        )
        self.analyze_btn.pack(side="left", padx=5)

        # Sélecteur vidéo/audio pour le téléchargement
        self._kind_display_to_code = {_("video"): "video", _("audio"): "audio"}
        self.kind_select = ctk.CTkOptionMenu(
            top_frame,
            values=list(self._kind_display_to_code.keys()),
            width=130,
        )
        self.kind_select.set(_("video"))
        self.kind_select.pack(side="left", padx=5)

        self.download_btn = ctk.CTkButton(
            top_frame,
            text=_("Download"),
            command=self._on_download,
            width=120,
            state="disabled",
        )
        self.download_btn.pack(side="left", padx=5)

        # Zone scrollable pour les informations et les formats
        scroller = ctk.CTkScrollableFrame(self.widget)
        scroller.pack(fill="both", expand=True, padx=5, pady=5)

        info_title = ctk.CTkLabel(
            scroller,
            text=_("Video Info"),
            font=("CTkFont", 14, "bold"),
        )
        info_title.pack(anchor="w", pady=(10, 5))

        self.info_container = ctk.CTkFrame(scroller)
        self.info_container.pack(fill="x")
        self._create_info_labels()

        formats_title = ctk.CTkLabel(
            scroller,
            text=_("Available formats"),
            font=("CTkFont", 14, "bold"),
        )
        formats_title.pack(anchor="w", pady=(15, 5))

        self.formats_box = ctk.CTkScrollableFrame(scroller, height=260)
        self.formats_box.pack(fill="both", expand=True, pady=(0, 10))

        self._formats_inner = ctk.CTkFrame(self.formats_box)
        self._formats_inner.pack(fill="x")
        for col in range(6):
            self._formats_inner.grid_columnconfigure(col, weight=1)
        self._render_formats_header()

    def _render_formats_header(self) -> None:
        headers = [_("Format"), _("Resolution"), _("Extension"), _("Codec"), _("Size"), _("FPS")]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                self._formats_inner,
                text=text,
                font=("CTkFont", 11, "bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=5, pady=3)

    def _create_info_labels(self) -> None:
        """Crée les labels pour afficher les informations"""
        self.info_labels = {
            'title': ctk.CTkLabel(self.info_container, text=f"{_('Title')}: -", font=("CTkFont", 12, "bold"), anchor="w"),
            'duration': ctk.CTkLabel(self.info_container, text=f"{_('Duration')}: -", anchor="w"),
            'uploader': ctk.CTkLabel(self.info_container, text=f"{_('Uploader')}: -", anchor="w"),
            'view_count': ctk.CTkLabel(self.info_container, text=f"{_('Views')}: -", anchor="w"),
            'upload_date': ctk.CTkLabel(self.info_container, text=f"{_('Upload date')}: -", anchor="w"),
            'description': ctk.CTkLabel(self.info_container, text=f"{_('Description')}: -", anchor="w"),
        }

        for label in self.info_labels.values():
            label.pack(fill="x", pady=2)

    def _on_analyze(self) -> None:
        """Gère le clic sur le bouton analyser"""
        url = self.url_input.get().strip()
        if not url:
            self._show_error(_("Please enter a valid URL"))
            return

        if not self._is_valid_url(url):
            self._show_error(_("Invalid URL. Please use a valid http(s) URL."))
            return

        self.analyze_btn.configure(state="disabled", text=_("Analyzing..."))
        self.executor.submit(self._analyze_video, url)

    def _is_valid_url(self, url: str) -> bool:
        """Valide l'URL"""
        try:
            parts = urlparse(url)
            return parts.scheme in {"http", "https"} and bool(parts.netloc)
        except Exception:
            return False

    def _analyze_video(self, url: str) -> None:
        """Analyse la vidéo et extrait les métadonnées"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            settings = self.app.settings
            if settings.general.proxy_url:
                parsed = urlparse(settings.general.proxy_url)
                if settings.general.proxy_id and settings.general.proxy_pw:
                    proxy_url = f"{parsed.scheme}://{settings.general.proxy_id}:{settings.general.proxy_pw}@{parsed.hostname}:{parsed.port}"
                else:
                    proxy_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                ydl_opts['proxy'] = proxy_url

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if hasattr(self.app, 'dispatch_ui'):
                self.app.dispatch_ui(lambda: self._update_ui(info))
            else:
                self.app.after(0, self._update_ui, info)

        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            if hasattr(self.app, 'dispatch_ui'):
                self.app.dispatch_ui(lambda: self._show_error(error_msg))
            else:
                self.app.after(0, self._show_error, error_msg)
        finally:
            if hasattr(self.app, 'dispatch_ui'):
                self.app.dispatch_ui(self._reset_analyze_button)
            else:
                self.app.after(0, self._reset_analyze_button)

    def _update_ui(self, info: dict) -> None:
        """Met à jour l'interface avec les informations extraites"""
        self.current_info = info

        self.download_btn.configure(state="normal")

        self.info_labels['title'].configure(text=f"{_('Title')}: {info.get('title', 'N/A')}")

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
        self.info_labels['duration'].configure(text=f"{_('Duration')}: {duration_str}")

        self.info_labels['uploader'].configure(text=f"{_('Uploader')}: {info.get('uploader', 'N/A')}")

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
        self.info_labels['view_count'].configure(text=f"{_('Views')}: {views_str}")

        upload_date = info.get('upload_date')
        if upload_date and len(upload_date) >= 8:
            date_str = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
        else:
            date_str = "N/A"
        self.info_labels['upload_date'].configure(text=f"{_('Upload date')}: {date_str}")

        description = info.get('description', '')
        if description:
            description = description[:100] + "..." if len(description) > 100 else description
        self.info_labels['description'].configure(text=f"{_('Description')}: {description or 'N/A'}")

        self._update_formats_table(info.get('formats', []))

    def _update_formats_table(self, formats: list) -> None:
        """Met à jour le tableau des formats disponibles"""
        for widget in self._formats_inner.winfo_children():
            widget.destroy()
        self._render_formats_header()

        sorted_formats = sorted(formats, key=self._format_sort_key, reverse=True)

        row = 1
        for fmt in sorted_formats:
            if not fmt.get('format_id'):
                continue

            format_id = fmt.get('format_id', 'N/A')

            width = fmt.get('width')
            height = fmt.get('height')
            if width and height:
                resolution = f"{width}x{height}"
            else:
                resolution = "Audio" if fmt.get('acodec') != 'none' else "N/A"

            ext = fmt.get('ext', 'N/A')

            vcodec = fmt.get('vcodec', 'N/A')
            acodec = fmt.get('acodec', 'N/A')
            if vcodec != 'none' and vcodec != 'N/A':
                codec = vcodec.split('.')[0] if '.' in vcodec else vcodec
            elif acodec != 'none' and acodec != 'N/A':
                codec = acodec.split('.')[0] if '.' in acodec else acodec
            else:
                codec = 'N/A'

            filesize = fmt.get('filesize')
            size_str = fmt_bytes(filesize) if filesize else "N/A"

            fps = fmt.get('fps')
            if isinstance(fps, float):
                fps_str = f"{fps:.1f}"
            else:
                fps_str = str(fps) if fps else "N/A"

            values = [format_id, resolution, ext, codec, size_str, fps_str]
            for col, value in enumerate(values):
                ctk.CTkLabel(
                    self._formats_inner,
                    text=str(value),
                    anchor="w",
                ).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            row += 1

    def _format_sort_key(self, fmt: dict) -> tuple:
        """Clé de tri pour les formats (priorité: vidéo > audio, puis résolution)"""
        is_video = fmt.get('vcodec', 'none') != 'none'
        priority = 1 if is_video else 0
        width = fmt.get('width', 0) or 0
        height = fmt.get('height', 0) or 0
        resolution = width * height
        return (priority, resolution)

    def _show_error(self, message: str) -> None:
        """Affiche un message d'erreur"""
        self.app._show_info_dialog(_("Error"), message)

    def _reset_analyze_button(self) -> None:
        """Réinitialise le bouton d'analyse"""
        self.analyze_btn.configure(state="normal", text=_("Analyze"))

    def _on_download(self) -> None:
        """Gère le clic sur le bouton télécharger"""
        if not self.current_info:
            self._show_error(_("Please analyze a video first"))
            return

        url = self.url_input.get().strip()
        if not url:
            self._show_error(_("URL not available"))
            return

        self.app._show_view(ViewName.DOWNLOADS)

        target = self.app.downloads_view.url_input
        target.delete(0, "end")
        target.insert(0, url)

        kind_display = str(self.kind_select.get() or "")
        kind = self._kind_display_to_code.get(kind_display, "video")
        self.app._on_add(kind=kind)
