from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path

import customtkinter as ctk
from PIL import Image as PILImage

from ..i18n import _, i18n
from ..widgets import load_themed_icon


class SettingsView:
    def __init__(self, app) -> None:
        self.app = app

        self._metadata_example_rules = (
            """# Parsing des métadonnées

album_artist:(?s)(?P<album_artist>.+)
Audeo, v 1.0:(?s)(?P<meta_comment>.+)
%(playlist_index)s /%(playlist_count)s:(?s)(?P<track_number>.+)
description:(Composer: (?P<composer>[^\\n]+))
description:(Vol\\.\\s+(?P<volume>[^\\n]+))
"""
        )

        # Charger l'icône en premier (avant _build_general)
        
        icon_path = Path(__file__).resolve().parent.parent / "ressources" / "pictures"
        
        def load_icon(name, size=(24, 24)):
            try:
                img_path = icon_path / "settings" / name
                if img_path.exists():
                    return load_themed_icon(img_path, size=size)
            except Exception:
                pass
            return None
        
        self._folder_dest_icon = load_icon("folder-2-32.png")
        self._file_name_icon = load_icon("write-3-32.png")
        self._file_rewrite_icon = load_icon("file-32.png")
        self._file_format_icon = load_icon("write-2-32.png")
        self._ignore_errors_icon = load_icon("ignore-error-32.png")
        self._speed_icon = load_icon("speed-32.png")
        self._fragments_icon = load_icon("fragements-48.png")
        self._thumbnail_icon = load_icon("thumbnail-32.png")
        self._playlist_icon = load_icon("playlist-32.png")
        self._folder_playlist_icon = load_icon("folder-32.png")
        self._proxy_icon = load_icon("proxy-48.png")
        
        self._metadata_icon = load_icon("metadata-32.png")
        self._metadata_search_icon = load_icon("script-32.png")
        
        self._codec_audio_icon = load_icon("codec-audio-32.png")
        self._ext_audio_icon = load_icon("container-audio-32.png")
        self._square_audio_icon = load_icon("square-48.png")
        self._codec_video_icon = load_icon("codec-video-32.png")
        self._ext_video_icon = load_icon("container-video-32.png")
        self._subs_icon = load_icon("subtitles-32.png")
        self._chapters_icon = load_icon("chapters-32.png")

        # Create main widget
        self.widget = ctk.CTkFrame(app.content)
        
        # Language selection
        _lang_pairs = [
            ("French", "fr"),
            ("English", "en"),
            ("Italian", "it"),
            ("German", "de"),
            ("Spanish", "es"),
            ("Portuguese", "pt"),
            ("Russian", "ru"),
            ("Polish", "pl"),
        ]
        lang_display_to_code = {_(label): code for label, code in _lang_pairs}

        current_lang_code = self.app.settings.general.lang_code
        current_lang_label = next((_(label) for label, code in _lang_pairs if code == current_lang_code), _("French"))

        self._lang_display_to_code = lang_display_to_code
        
        # Top bar with language and buttons
        top_bar = ctk.CTkFrame(self.widget)
        top_bar.pack(fill="x", padx=10, pady=10)
        
        lang_select = ctk.CTkOptionMenu(
            top_bar,
            values=list(lang_display_to_code.keys()),
            command=self._lang_change,
            width=150,
            height=30,
        )
        lang_select.set(current_lang_label)
        lang_select.pack(side="left", padx=5)
        
        apply_all_btn = ctk.CTkButton(top_bar, text=_("Apply all"), command=self._apply_all, width=100, height=30)
        apply_all_btn.pack(side="right", padx=5)
        
        import_btn = ctk.CTkButton(top_bar, text=_("Import"), command=self._import, width=100, height=30)
        import_btn.pack(side="right", padx=5)
        
        export_btn = ctk.CTkButton(top_bar, text=_("Export"), command=self._export, width=100, height=30)
        export_btn.pack(side="right", padx=5)
        
        # Tabview for settings
        self.tabview = ctk.CTkTabview(self.widget)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add(_("General"))
        self.tabview.add(_("Metadata"))
        self.tabview.add(_("Audio"))
        self.tabview.add(_("Video"))
        
        # Build each tab content
        general_tab = self.tabview.tab(_("General"))
        general = self._build_general(general_tab)
        general.pack(fill="both", expand=True, padx=5, pady=5)
        
        metadata_tab = self.tabview.tab(_("Metadata"))
        metadata = self._build_metadata(metadata_tab)
        metadata.pack(fill="both", expand=True, padx=5, pady=5)
        
        audio_tab = self.tabview.tab(_("Audio"))
        audio = self._build_audio(audio_tab)
        audio.pack(fill="both", expand=True, padx=5, pady=5)
        
        video_tab = self.tabview.tab(_("Video"))
        video = self._build_video(video_tab)
        video.pack(fill="both", expand=True, padx=5, pady=5)


    def _lang_change(self, choice):
        """Gère le changement de langue"""
        lang_name = str(choice or "")
        lang_code = getattr(self, "_lang_display_to_code", {}).get(lang_name)
        if not lang_code:
            return

        # Sauvegarder la langue dans les paramètres
        self.app.settings.general.lang_code = lang_code
        self.app.save_settings()
        
        # Changer la langue
        i18n.set_language(lang_code)
        
        # Notifier toutes les vues du changement de langue
        self.app.notify_language_change()
        
        # Message de confirmation
        self.app._show_info_dialog(
            _("Language changed"),
            _("Language changed to {} ({})").format(lang_name, lang_code)
        )
    
    def on_language_changed(self) -> None:
        """Méthode appelée quand la langue change"""
        self._update_ui_language()

    @staticmethod
    def _add_icon(parent, icon) -> None:
        if icon is not None:
            ctk.CTkLabel(parent, image=icon, text="").pack(side="left", padx=(5, 2))

    def _row(self, parent, label: str, create_widget, icon=None):
        # create_widget(parent) doit retourner le widget à placer à droite de la ligne
        row = ctk.CTkFrame(parent, height=40)
        row.pack(fill="x", pady=5)

        left = ctk.CTkFrame(row)
        left.pack(side="left", padx=5)

        if icon:
            icon_label = ctk.CTkLabel(left, image=icon, text="")
            icon_label.pack(side="left", padx=5)

        label_widget = ctk.CTkLabel(left, text=_(label), font=("CTkFont", 12))
        label_widget.pack(side="left", padx=5)

        widget = create_widget(row)
        widget.pack(side="right", padx=5)

        return row

    def _column(self, parent, label: str, create_widget):
        # create_widget(parent) doit retourner le widget à placer sous le label
        column = ctk.CTkFrame(parent)
        column.pack(fill="both", pady=5)

        label_widget = ctk.CTkLabel(column, text=_(label), font=("CTkFont", 12))
        label_widget.pack(pady=5)

        widget = create_widget(column)
        widget.pack(fill="both", expand=True, pady=5)

        return column

    @staticmethod
    def _init_switch(parent, value: bool) -> ctk.CTkSwitch:
        switch = ctk.CTkSwitch(parent, text="", onvalue=True, offvalue=False)
        if value:
            switch.select()
        return switch

    @staticmethod
    def _set_switch(switch, value: bool) -> None:
        if value:
            switch.select()
        else:
            switch.deselect()

    def _build_general(self, parent):
        g = self.app.settings.general

        container = ctk.CTkScrollableFrame(parent)
        
        # Destination folder
        dest_frame = ctk.CTkFrame(container, height=40)
        dest_frame.pack(fill="x", pady=5)
        
        self._add_icon(dest_frame, self._folder_dest_icon)
        self.dest_label = ctk.CTkLabel(dest_frame, text=str(self.app.download_dir), font=("CTkFont", 12))
        self.dest_label.pack(side="left", padx=5)
        
        choose_dest_btn = ctk.CTkButton(dest_frame, text=_("Choose…"), command=self._choose_destination, width=100, height=30)
        choose_dest_btn.pack(side="right", padx=5)

        # Output template
        template_frame = ctk.CTkFrame(container, height=40)
        template_frame.pack(fill="x", pady=5)
        self._add_icon(template_frame, self._file_name_icon)
        ctk.CTkLabel(template_frame, text=_("Output template"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.output_template_input = ctk.CTkEntry(template_frame, placeholder_text=_("%(title)s.%(ext)s"), width=300, height=30, font=("CTkFont", 12))
        self.output_template_input.insert(0, g.output_template)
        self.output_template_input.pack(side="right", padx=5)

        # Output format
        format_frame = ctk.CTkFrame(container, height=40)
        format_frame.pack(fill="x", pady=5)
        self._add_icon(format_frame, self._file_format_icon)
        ctk.CTkLabel(format_frame, text=_("Output format"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.output_format_input = ctk.CTkEntry(format_frame, width=300, height=30, font=("CTkFont", 12))
        self.output_format_input.insert(0, g.output_format)
        self.output_format_input.pack(side="right", padx=5)
        
        # Overwrite switch
        overwrite_frame = ctk.CTkFrame(container, height=40)
        overwrite_frame.pack(fill="x", pady=5)
        self._add_icon(overwrite_frame, self._file_rewrite_icon)
        ctk.CTkLabel(overwrite_frame, text=_("Overwrite existing files"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.overwrite_switch = self._init_switch(overwrite_frame, g.overwrite)
        self.overwrite_switch.pack(side="right", padx=5)
        
        # Ignore errors switch
        ignore_frame = ctk.CTkFrame(container, height=40)
        ignore_frame.pack(fill="x", pady=5)
        self._add_icon(ignore_frame, self._ignore_errors_icon)
        ctk.CTkLabel(ignore_frame, text=_("Ignore errors"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.ignore_errors_switch = self._init_switch(ignore_frame, g.ignore_errors)
        self.ignore_errors_switch.pack(side="right", padx=5)

        # Limit rate
        rate_frame = ctk.CTkFrame(container, height=40)
        rate_frame.pack(fill="x", pady=5)
        self._add_icon(rate_frame, self._speed_icon)
        ctk.CTkLabel(rate_frame, text=_("Limit download rate (KiB/s)"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.limit_rate_switch = self._init_switch(rate_frame, g.limit_rate_enabled)
        self.limit_rate_switch.pack(side="right", padx=5)
        self.limit_rate_input = ctk.CTkEntry(rate_frame, width=150, height=30, font=("CTkFont", 12))
        self.limit_rate_input.insert(0, str(max(0, g.limit_rate_kib_s)))
        self.limit_rate_input.pack(side="right", padx=5)

        # Concurrent fragments
        fragments_frame = ctk.CTkFrame(container, height=40)
        fragments_frame.pack(fill="x", pady=5)
        self._add_icon(fragments_frame, self._fragments_icon)
        ctk.CTkLabel(fragments_frame, text=_("Concurrent fragments"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.fragments_input = ctk.CTkEntry(fragments_frame, width=150, height=30, font=("CTkFont", 12))
        self.fragments_input.insert(0, str(max(1, g.concurrent_fragments)))
        self.fragments_input.pack(side="right", padx=5)
        
        # Add thumbnail switch
        thumbnail_frame = ctk.CTkFrame(container, height=40)
        thumbnail_frame.pack(fill="x", pady=5)
        self._add_icon(thumbnail_frame, self._thumbnail_icon)
        ctk.CTkLabel(thumbnail_frame, text=_("Add thumbnail"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.add_thumbnail_switch = self._init_switch(thumbnail_frame, g.add_thumbnail)
        self.add_thumbnail_switch.pack(side="right", padx=5)
        
        # Download playlist switch
        playlist_frame = ctk.CTkFrame(container, height=40)
        playlist_frame.pack(fill="x", pady=5)
        self._add_icon(playlist_frame, self._playlist_icon)
        ctk.CTkLabel(playlist_frame, text=_("Download playlist"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.download_playlist_switch = self._init_switch(playlist_frame, g.download_playlist)
        self.download_playlist_switch.pack(side="right", padx=5)
        
        # Playlist folder
        playlist_folder_frame = ctk.CTkFrame(container, height=40)
        playlist_folder_frame.pack(fill="x", pady=5)
        self._add_icon(playlist_folder_frame, self._folder_playlist_icon)
        ctk.CTkLabel(playlist_folder_frame, text=_("Playlist folder name"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.playlist_folder_input = ctk.CTkEntry(playlist_folder_frame, placeholder_text=_("%(album,playlist_title)s/"), width=300, height=30, font=("CTkFont", 12))
        self.playlist_folder_input.insert(0, g.playlist_folder_name)
        self.playlist_folder_input.pack(side="right", padx=5)
        
        # Proxy URL
        proxy_frame = ctk.CTkFrame(container, height=40)
        proxy_frame.pack(fill="x", pady=5)
        self._add_icon(proxy_frame, self._proxy_icon)
        ctk.CTkLabel(proxy_frame, text=_("Proxy URL"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.proxy_url_input = ctk.CTkEntry(proxy_frame, placeholder_text=_("http://proxy.example.com:8080"), width=300, height=30, font=("CTkFont", 12))
        self.proxy_url_input.insert(0, g.proxy_url)
        self.proxy_url_input.pack(side="right", padx=5)
        
        # Proxy ID
        proxy_id_frame = ctk.CTkFrame(container, height=40)
        proxy_id_frame.pack(fill="x", pady=5)
        self._add_icon(proxy_id_frame, self._proxy_icon)
        ctk.CTkLabel(proxy_id_frame, text=_("Proxy username"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.proxy_id_input = ctk.CTkEntry(proxy_id_frame, placeholder_text=_("username"), width=300, height=30, font=("CTkFont", 12))
        self.proxy_id_input.insert(0, g.proxy_id)
        self.proxy_id_input.pack(side="right", padx=5)
        
        # Proxy password
        proxy_pw_frame = ctk.CTkFrame(container, height=40)
        proxy_pw_frame.pack(fill="x", pady=5)
        self._add_icon(proxy_pw_frame, self._proxy_icon)
        ctk.CTkLabel(proxy_pw_frame, text=_("Proxy password"), font=("CTkFont", 12)).pack(side="left", padx=5)
        self.proxy_pw_input = ctk.CTkEntry(proxy_pw_frame, placeholder_text=_("password"), show="*", width=300, height=30, font=("CTkFont", 12))
        self.proxy_pw_input.insert(0, g.proxy_pw)
        self.proxy_pw_input.pack(side="right", padx=5)

        return container

    def _choose_destination(self):
        try:
            from tkinter import filedialog
            folder = filedialog.askdirectory(title=_("Choose destination folder"))
        except Exception:
            folder = None
        if folder:
            self.app.download_dir = Path(str(folder))
            self.dest_label.configure(text=str(self.app.download_dir))
            self.app.settings.general.download_dir = str(self.app.download_dir)
            self.app.save_settings()

    def _apply_general(self):
        g = self.app.settings.general

        g.output_template = (self.output_template_input.get() or "").strip() or g.output_template
        g.output_format = (self.output_format_input.get() or "").strip()
        g.overwrite = bool(self.overwrite_switch.get())
        g.ignore_errors = bool(self.ignore_errors_switch.get())

        g.limit_rate_enabled = bool(self.limit_rate_switch.get())
        try:
            g.limit_rate_kib_s = int(self.limit_rate_input.get() or 0)
        except (TypeError, ValueError):
            g.limit_rate_kib_s = 0
        if g.limit_rate_kib_s < 0:
            g.limit_rate_kib_s = 0

        try:
            g.concurrent_fragments = int(self.fragments_input.get() or 1)
        except (TypeError, ValueError):
            g.concurrent_fragments = 1
        if g.concurrent_fragments < 1:
            g.concurrent_fragments = 1
        if g.concurrent_fragments > 16:
            g.concurrent_fragments = 16
        self.fragments_input.delete(0, 'end')
        self.fragments_input.insert(0, str(g.concurrent_fragments))

        g.add_thumbnail = bool(self.add_thumbnail_switch.get())
        g.download_playlist = bool(self.download_playlist_switch.get())
        g.playlist_folder_name = (self.playlist_folder_input.get() or "").strip()
        
        # Validate proxy URL
        proxy_url = (self.proxy_url_input.get() or "").strip()
        if proxy_url and not self._is_valid_proxy_url(proxy_url):
            # Invalid proxy URL - reset to empty but don't block other settings
            proxy_url = ""
            self.proxy_url_input.delete(0, 'end')
        g.proxy_url = proxy_url
        
        g.proxy_id = (self.proxy_id_input.get() or "").strip()
        g.proxy_pw = (self.proxy_pw_input.get() or "").strip()
        self.app.save_settings()

    def _is_valid_proxy_url(self, url: str) -> bool:
        """Validate proxy URL format (http://host:port or https://host:port)"""
        if not url:
            return True  # Empty is valid (no proxy)
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            # Must have scheme http or https
            if parsed.scheme not in ("http", "https"):
                return False
            # Must have a hostname
            if not parsed.hostname:
                return False
            # Port should be valid if specified
            if parsed.port is not None and (parsed.port < 1 or parsed.port > 65535):
                return False
            return True
        except Exception:
            return False

    def _build_metadata(self, parent) -> ctk.CTkScrollableFrame:
        g = self.app.settings.general

        container = ctk.CTkScrollableFrame(parent)

        def make_metadata_switch(p):
            self.add_metadata_switch = self._init_switch(p, getattr(g, "add_metadata", True))
            return self.add_metadata_switch

        def make_metadata_box(p):
            self.custom_metadata_input = ctk.CTkTextbox(p, height=140, font=("CTkFont", 11))
            self.custom_metadata_input.configure(fg_color=p.cget("fg_color"))
            self.custom_metadata_input.insert("1.0", getattr(g, "custom_metadata", ""))
            return self.custom_metadata_input

        def make_parse_switch(p):
            self.parse_metadata_switch = self._init_switch(p, getattr(g, "parse_metadata_enabled", False))
            return self.parse_metadata_switch

        def make_rules_box(p):
            self.parse_metadata_rules_input = ctk.CTkTextbox(p, height=180, font=("CTkFont", 11))
            self.parse_metadata_rules_input.configure(fg_color=p.cget("fg_color"))
            self.parse_metadata_rules_input.insert(
                "1.0",
                getattr(g, "parse_metadata_rules", "") or self._metadata_example_rules,
            )
            return self.parse_metadata_rules_input

        open_cfg_btn = ctk.CTkButton(
            container,
            text=_("Open settings folder"),
            command=self._open_config_dir,
            height=30,
        )

        self._row(container, _("Add metadata"), make_metadata_switch, icon=self._metadata_icon)
        self._column(container, _("Custom metadata (key=value)"), make_metadata_box)
        self._row(container, _("Detect metadata (parse-metadata)"), make_parse_switch, icon=self._metadata_search_icon)
        self._column(container, _("Parse-metadata rules (1 per line)"), make_rules_box)
        open_cfg_btn.pack(fill="x", pady=10)
        return container

    def _open_config_dir(self) -> None:
        try:
            cfg_dir_raw = getattr(self.app, "config_dir", None)
            if cfg_dir_raw:
                cfg_dir = Path(str(cfg_dir_raw))
            else:
                cfg_dir = Path.home() / ".config" / "Audeo-2"
        except Exception as e:
            self.app._show_info_dialog("Paramètres", f"Chemin de config invalide: {e}")
            return

        try:
            cfg_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.app._show_info_dialog(
                "Paramètres",
                f"Impossible de créer le dossier de config :\n{cfg_dir}\n\n{e}",
            )
            return

        try:
            cfg_dir = cfg_dir.resolve()
        except Exception:
            cfg_dir = Path(str(cfg_dir))

        if not cfg_dir.exists() or not cfg_dir.is_dir():
            self.app._show_info_dialog(
                "Paramètres",
                f"Le dossier de config n'existe pas (ou n'est pas un dossier) :\n{cfg_dir}",
            )
            return

        try:
            os.startfile(str(cfg_dir))
            return
        except Exception:
            pass

        try:
            subprocess.Popen(["explorer", str(cfg_dir)])
            return
        except Exception as e:
            self.app._show_info_dialog(
                "Paramètres",
                f"Impossible d'ouvrir le dossier :\n{cfg_dir}\n\n{e}",
            )
            return

    def _apply_metadata(self) -> None:
        g = self.app.settings.general

        g.add_metadata = bool(self.add_metadata_switch.get())
        g.custom_metadata = str(self.custom_metadata_input.get("1.0", "end") or "").strip()

        g.parse_metadata_enabled = bool(self.parse_metadata_switch.get())
        g.parse_metadata_rules = str(self.parse_metadata_rules_input.get("1.0", "end") or "").strip()

        self.app.save_settings()

    def _build_audio(self, parent) -> ctk.CTkScrollableFrame:
        a = self.app.settings.audio

        container = ctk.CTkScrollableFrame(parent)

        def make_codec(p):
            self.audio_codec_select = ctk.CTkOptionMenu(
                p,
                values=["auto", "mp3", "aac", "opus", "vorbis", "flac", "alac"],
                width=250, height=30, font=("CTkFont", 12),
            )
            self.audio_codec_select.set(a.preferred_codec)
            return self.audio_codec_select

        def make_ext(p):
            self.audio_ext_select = ctk.CTkOptionMenu(
                p,
                values=["mp3", "aac", "opus", "m4a", "wav", "flac", "alac"],
                width=250, height=30, font=("CTkFont", 12),
            )
            self.audio_ext_select.set(a.ext)
            return self.audio_ext_select

        def make_square_thumb(p):
            self.audio_square_thumb_switch = self._init_switch(p, a.square_thumbnail)
            return self.audio_square_thumb_switch

        self._row(container, "Preferred codec", make_codec, icon=self._codec_audio_icon)
        self._row(container, "Extension / container", make_ext, icon=self._ext_audio_icon)
        self._row(container, "Square thumbnail", make_square_thumb, icon=self._square_audio_icon)
        return container

    def _apply_audio(self) -> None:
        a = self.app.settings.audio
        a.preferred_codec = str(self.audio_codec_select.get() or "auto")
        a.ext = str(self.audio_ext_select.get() or "mp3")
        a.square_thumbnail = bool(self.audio_square_thumb_switch.get())
        self.app.save_settings()

    def _build_video(self, parent) -> ctk.CTkScrollableFrame:
        v = self.app.settings.video

        container = ctk.CTkScrollableFrame(parent)

        def make_codec(p):
            self.video_codec_select = ctk.CTkOptionMenu(
                p,
                values=["auto", "h264", "vp9", "av1"],
                width=250, height=30, font=("CTkFont", 12),
            )
            self.video_codec_select.set(v.preferred_codec)
            return self.video_codec_select

        def make_ext(p):
            self.video_ext_select = ctk.CTkOptionMenu(
                p,
                values=["auto", "mp4", "mkv", "webm"],
                width=250, height=30, font=("CTkFont", 12),
            )
            self.video_ext_select.set(v.ext)
            return self.video_ext_select

        def make_subs(p):
            self.video_subs_switch = self._init_switch(p, v.subtitles)
            return self.video_subs_switch

        def make_chapters(p):
            self.video_chapters_switch = self._init_switch(p, v.chapters)
            return self.video_chapters_switch

        self._row(container, "Preferred codec", make_codec, icon=self._codec_video_icon)
        self._row(container, "Extension / container", make_ext, icon=self._ext_video_icon)
        self._row(container, "Subtitles", make_subs, icon=self._subs_icon)
        self._row(container, "Chapters", make_chapters, icon=self._chapters_icon)
        return container

    def _apply_video(self) -> None:
        v = self.app.settings.video
        v.preferred_codec = str(self.video_codec_select.get() or "auto")
        v.ext = str(self.video_ext_select.get() or "auto")
        v.subtitles = bool(self.video_subs_switch.get())
        v.chapters = bool(self.video_chapters_switch.get())
        self.app.save_settings()

    def _apply_all(self) -> None:
        """Applique tous les paramètres de tous les onglets"""
        self._apply_general()
        self._apply_metadata()
        self._apply_audio()
        self._apply_video()
        
    def _import(self) -> None:
        """Importe les paramètres depuis un fichier JSON"""
        try:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title=_("Import settings"),
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if not file_path:
                return  # L'utilisateur a annulé

            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

            if "general" in settings_data:
                general = settings_data["general"]
                for key, value in general.items():
                    if hasattr(self.app.settings.general, key):
                        setattr(self.app.settings.general, key, value)

            if "video" in settings_data:
                video = settings_data["video"]
                for key, value in video.items():
                    if hasattr(self.app.settings.video, key):
                        setattr(self.app.settings.video, key, value)

            if "audio" in settings_data:
                audio = settings_data["audio"]
                for key, value in audio.items():
                    if hasattr(self.app.settings.audio, key):
                        setattr(self.app.settings.audio, key, value)

            self.app.save_settings()
            self._refresh_ui_from_settings()

            self.app._show_info_dialog(
                _("Import settings"),
                _("Settings imported successfully\n\nAll settings have been applied."),
            )

        except json.JSONDecodeError:
            self.app._show_info_dialog(
                _("Format error"),
                _("The selected file is not a valid JSON file."),
            )
        except Exception as e:
            self.app._show_info_dialog(
                _("Unable to import settings"),
                _("Unable to import settings:\n{}").format(str(e)),
            )

    @staticmethod
    def _set_entry(entry, value) -> None:
        try:
            entry.delete(0, "end")
            entry.insert(0, str(value))
        except Exception:
            pass

    @staticmethod
    def _set_textbox(box, value) -> None:
        try:
            box.delete("1.0", "end")
            box.insert("1.0", str(value or ""))
        except Exception:
            pass

    def _refresh_ui_from_settings(self) -> None:
        """Rafraîchit l'interface avec les paramètres actuels"""
        try:
            g = self.app.settings.general

            if hasattr(self, 'dest_label'):
                self.dest_label.configure(text=str(getattr(self.app, "download_dir", "") or ""))
            if hasattr(self, 'output_template_input'):
                self._set_entry(self.output_template_input, g.output_template)
            if hasattr(self, 'output_format_input'):
                self._set_entry(self.output_format_input, g.output_format)

            for name, value in (
                ("overwrite_switch", g.overwrite),
                ("ignore_errors_switch", g.ignore_errors),
                ("limit_rate_switch", g.limit_rate_enabled),
                ("add_thumbnail_switch", g.add_thumbnail),
                ("download_playlist_switch", g.download_playlist),
                ("add_metadata_switch", g.add_metadata),
                ("parse_metadata_switch", g.parse_metadata_enabled),
            ):
                switch = getattr(self, name, None)
                if switch is not None:
                    self._set_switch(switch, bool(value))

            if hasattr(self, 'limit_rate_input'):
                self._set_entry(self.limit_rate_input, g.limit_rate_kib_s)
            if hasattr(self, 'fragments_input'):
                self._set_entry(self.fragments_input, g.concurrent_fragments)
            if hasattr(self, 'playlist_folder_input'):
                self._set_entry(self.playlist_folder_input, g.playlist_folder_name)
            if hasattr(self, 'proxy_url_input'):
                self._set_entry(self.proxy_url_input, g.proxy_url)
            if hasattr(self, 'proxy_id_input'):
                self._set_entry(self.proxy_id_input, g.proxy_id)
            if hasattr(self, 'proxy_pw_input'):
                self._set_entry(self.proxy_pw_input, g.proxy_pw)

            if hasattr(self, 'custom_metadata_input'):
                self._set_textbox(self.custom_metadata_input, g.custom_metadata)
            if hasattr(self, 'parse_metadata_rules_input'):
                self._set_textbox(self.parse_metadata_rules_input, g.parse_metadata_rules)

            if hasattr(self, 'video_codec_select'):
                self.video_codec_select.set(self.app.settings.video.preferred_codec)
            if hasattr(self, 'video_ext_select'):
                self.video_ext_select.set(self.app.settings.video.ext)
            for name, value in (
                ("video_subs_switch", self.app.settings.video.subtitles),
                ("video_chapters_switch", self.app.settings.video.chapters),
            ):
                switch = getattr(self, name, None)
                if switch is not None:
                    self._set_switch(switch, bool(value))

            if hasattr(self, 'audio_codec_select'):
                self.audio_codec_select.set(self.app.settings.audio.preferred_codec)
            if hasattr(self, 'audio_ext_select'):
                self.audio_ext_select.set(self.app.settings.audio.ext)
            if hasattr(self, 'audio_square_thumb_switch'):
                self._set_switch(self.audio_square_thumb_switch, bool(self.app.settings.audio.square_thumbnail))

        except Exception:
            pass

    def _export(self) -> None:
        """Exporte les paramètres actuels dans un fichier JSON"""
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title=_("Export settings"),
                defaultextension=".json",
                initialfile="audeo_settings.json",
                filetypes=[("JSON files", "*.json")],
            )

            if not file_path:
                return  # L'utilisateur a annulé

            settings_data = {
                "general": {
                    "lang_code": self.app.settings.general.lang_code,
                    "download_dir": self.app.settings.general.download_dir,
                    "output_format": self.app.settings.general.output_format,
                    "output_template": self.app.settings.general.output_template,
                    "overwrite": self.app.settings.general.overwrite,
                    "limit_rate_enabled": self.app.settings.general.limit_rate_enabled,
                    "limit_rate_kib_s": self.app.settings.general.limit_rate_kib_s,
                    "concurrent_fragments": self.app.settings.general.concurrent_fragments,
                    "add_thumbnail": self.app.settings.general.add_thumbnail,
                    "add_metadata": self.app.settings.general.add_metadata,
                    "custom_metadata": self.app.settings.general.custom_metadata,
                    "parse_metadata_enabled": self.app.settings.general.parse_metadata_enabled,
                    "parse_metadata_rules": self.app.settings.general.parse_metadata_rules,
                    "download_playlist": self.app.settings.general.download_playlist,
                    "playlist_folder_name": self.app.settings.general.playlist_folder_name,
                    "proxy_url": self.app.settings.general.proxy_url,
                    "proxy_id": self.app.settings.general.proxy_id,
                    "proxy_pw": self.app.settings.general.proxy_pw
                },
                "video": {
                    "preferred_codec": self.app.settings.video.preferred_codec,
                    "ext": self.app.settings.video.ext,
                    "subtitles": self.app.settings.video.subtitles,
                    "chapters": self.app.settings.video.chapters
                },
                "audio": {
                    "preferred_codec": self.app.settings.audio.preferred_codec,
                    "ext": self.app.settings.audio.ext,
                    "square_thumbnail": self.app.settings.audio.square_thumbnail
                }
            }
            
            # Écrire le fichier JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)

            self.app._show_info_dialog(
                _("Export settings"),
                _("Settings exported successfully\n\nFile saved to: {}").format(file_path),
            )

        except Exception as e:
            self.app._show_info_dialog(
                _("Unable to export settings"),
                _("Unable to export settings:\n{}").format(str(e)),
            )

