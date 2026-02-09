from __future__ import annotations

import os
import json
import subprocess
import asyncio
from pathlib import Path

import toga
from toga import style
from toga.style import Pack

from ..i18n import _, i18n


class SettingsView:
    def __init__(self, app: toga.App) -> None:
        self.app = app

        self._metadata_example_rules = (
            "# Parsing des métadonnées\n"
            "artist:(.+)\n"
            '"description:(Composer: ([^\\n]+))"\n\n'
            "album_artist:(?s)(.+)\n"
            "'Audeo, v 1.0':(?s)(.+)\n\n"
            '"%(playlist_index)s /%(playlist_count)s":(?s)(.+)\n'
            '"description:(Vol\\. ([^\\n]+))"\n'
        )

        # Charger l'icône en premier (avant _build_general)
        
        icon_path = Path(__file__).resolve().parent.parent / "ressources" / "pictures"
        self._folder_dest_icon = toga.Image(str(icon_path / "settings" / "folder-2-32.png"))
        self._file_name_icon = toga.Image(str(icon_path / "settings" / "write-3-32.png"))
        self._file_rewrite_icon = toga.Image(str(icon_path / "settings" / "file-32.png"))
        self._speed_icon = toga.Image(str(icon_path / "settings" / "speed-32.png"))
        self._fragments_icon = toga.Image(str(icon_path / "settings" / "fragements-48.png"))
        self._thumbnail_icon = toga.Image(str(icon_path / "settings" / "thumbnail-32.png"))
        self._playlist_icon = toga.Image(str(icon_path / "settings" / "playlist-32.png"))
        self._folder_playlist_icon = toga.Image(str(icon_path / "settings" / "folder-32.png"))
        self._proxy_icon = toga.Image(str(icon_path / "settings" / "proxy-48.png"))
        
        self._metadata_icon = toga.Image(str(icon_path / "settings" / "metadata-32.png"))
        self._metadata_search_icon = toga.Image(str(icon_path / "settings" / "script-32.png"))
        
        self._codec_audio_icon = toga.Image(str(icon_path / "settings" / "codec-audio-32.png"))
        self._ext_audio_icon = toga.Image(str(icon_path / "settings" / "container-audio-32.png"))
        self._square_audio_icon = toga.Image(str(icon_path / "settings" / "square-48.png"))
        self._codec_video_icon = toga.Image(str(icon_path / "settings" / "codec-video-32.png"))
        self._ext_video_icon = toga.Image(str(icon_path / "settings" / "container-video-32.png"))
        self._subs_icon = toga.Image(str(icon_path / "settings" / "subtitles-32.png"))
        self._chapters_icon = toga.Image(str(icon_path / "settings" / "chapters-32.png"))
        


        general = self._wrap_scroll(self._build_general())
        metadata = self._wrap_scroll(self._build_metadata())
        audio = self._wrap_scroll(self._build_audio())
        video = self._wrap_scroll(self._build_video())

        # Bouton d'application global
        lang_select = toga.Selection(
            items=[
                {"name": _("French"), "value": "fr"}, 
                {"name": _("English"), "value": "en"},
                {"name": _("Italian"), "value": "it"},
                {"name": _("German"), "value": "de"},
                {"name": _("Spanish"), "value": "es"},
                
                {"name": _("Portuguese"), "value": "pt"},
                {"name": _("Russian"), "value": "ru"},
                {"name": _("Polish"), "value": "pl"},
            ],
            accessor="name", 
            on_change=self._lang_change, 
            style=Pack(width=150, margin=10)
        )
        apply_all_btn = toga.Button(_("Apply all"), on_press=self._apply_all, style=Pack(width=100, margin=10))
        import_btn = toga.Button(_("Import"), on_press=self._import, style=Pack(width=100, margin=10))
        export_btn = toga.Button(_("Export"), on_press=self._export, style=Pack(width=100, margin=10))
        
        # Conteneur principal avec onglets et bouton
        main_box = toga.Box(style=Pack(direction="column", flex=1, margin_bottom=15))
        main_box.add(lang_select)
        main_box.add(toga.OptionContainer(
            style=Pack(flex=1),
            content=[
                toga.OptionItem(_("General"), general),
                toga.OptionItem(_("Metadata"), metadata),
                toga.OptionItem(_("Audio"), audio),
                toga.OptionItem(_("Video"), video),
            ],
        ))
        main_box.add(
            toga.Box(
                children=[
                    import_btn,
                    export_btn,
                    toga.Box(children=[], style=Pack(flex=1)),
                    apply_all_btn,
                ], 
                style=Pack(direction="row")
            )
        )

        self.widget = main_box


    async def _lang_change(self, widget, **kwargs):
        """Gère le changement de langue"""
        lang_code = widget.value.value
        lang_name = widget.value.name
        
        # Sauvegarder la langue dans les paramètres
        self.app.settings.general.lang_code = lang_code
        self.app.save_settings()
        
        # Changer la langue
        i18n.set_language(lang_code)
        
        # Notifier toutes les vues du changement de langue
        self.app.notify_language_change()
        
        # Message de confirmation
        success_dialog = toga.InfoDialog(
            title=_("Language changed"),
            message=_("Language changed to {} ({})").format(lang_name, lang_code)
        )
        
        await self.app.main_window.dialog(success_dialog)
    
    def on_language_changed(self) -> None:
        """Méthode appelée quand la langue change"""
        self._update_ui_language()
    
    

    def _wrap_scroll(self, content: toga.Widget) -> toga.ScrollContainer:
        return toga.ScrollContainer(content=content, style=Pack(flex=1))

    def _row(self, label: str, widget: toga.Widget, icon=None) -> toga.Box:
        # Traduire le label dynamiquement
        translated_label = _(label)
        
        if icon:
            left = toga.Box(
                children=[
                    toga.ImageView(icon, style=Pack(width=24, height=24, margin=(5, 5, 5, 5))),
                    toga.Label(translated_label, style=Pack(margin=(5, 5, 5, 5))),
                ],
                style=Pack(direction="row", align_items="center", width=100)
            )
        else:
            left = toga.Label(translated_label, style=Pack(width=100, margin=(5, 5, 5, 5)))

        widget.style=Pack(direction="row", margin=(5, 5, 5, 5), flex=1)
        frame = toga.Box(
            children=[
                toga.Box(  # Row interne pour label+widget
                    children=[left, toga.Box(style=Pack(flex=1)), widget],
                    style=Pack(direction="row", margin=1.5, background_color="#f0f0f0", flex=1)
                )
            ],
            style=Pack(
                margin=2,         # Espace interne
                background_color="#d3d3d3",  # Fond cadre
                # border_radius=6        # Si supporté
                #flex=1
            )
        )
        return frame
    
    def _column(self, label: str, widget: toga.Widget) -> toga.Box:
        # Traduire le label dynamiquement
        translated_label = _(label)
        
        left = toga.Label(translated_label, style=Pack(flex=1, margin=(5, 5, 5, 5)))
        widget.style=Pack(margin=(5, 5, 5, 5), flex=1)
        frame = toga.Box(
            children=[
                toga.Box(  # Row interne pour label+widget
                    children=[left, widget],
                    style=Pack(direction="column", margin=1.5, background_color="#f0f0f0", flex=1)
                )
            ],
            style=Pack(
                margin=1.5,         # Espace interne
                background_color="#d3d3d3",  # Fond cadre
                # border_radius=6        # Si supporté
                #flex=1
            )
        )
        return frame

    def _build_general(self) -> toga.Widget:
        g = self.app.settings.general

        self.dest_label = toga.Label(str(self.app.download_dir), style=Pack(flex=1, margin_top=3))
        choose_dest_btn = toga.Button(_("Choose…"), on_press=self._choose_destination, style=Pack(margin_left=15, margin_top=5, margin_bottom=5, margin_right=10))
        dest_row = toga.Box(style=Pack(direction="row", flex=1))
        dest_row.add(self.dest_label)
        dest_row.add(choose_dest_btn)

        self.output_template_input = toga.TextInput(value=g.output_template, placeholder=_("%(title)s.%(ext)s"), style=Pack(flex=1, margin_top=5, margin_bottom=5))
        self.output_format_input = toga.TextInput(value=g.output_format, style=Pack(flex=1, margin_top=5, margin_bottom=5))
        
        self.overwrite_switch = toga.Switch("", value=g.overwrite)

        self.limit_rate_switch = toga.Switch("", value=g.limit_rate_enabled, style=Pack(margin_right=5))
        self.limit_rate_input = toga.NumberInput(value=max(0, g.limit_rate_kib_s), style=Pack(flex=1))
        limit_rate_row = toga.Box(style=Pack(direction="row", margin_top=5))
        limit_rate_row.add(self.limit_rate_switch)
        limit_rate_row.add(self.limit_rate_input)

        self.fragments_input = toga.NumberInput(value=max(1, g.concurrent_fragments), style=Pack(width=150, margin=5))
        self.add_thumbnail_switch = toga.Switch("", value=g.add_thumbnail)
        self.download_playlist_switch = toga.Switch("", value=g.download_playlist)
        self.playlist_folder_input = toga.TextInput(value=g.playlist_folder_name, placeholder=_("%(album,playlist_title)s/"), style=Pack(flex=1, margin_top=5, margin_bottom=5))
        
        box_proxy = toga.Box(style=Pack(direction="column", flex=1))
        self.proxy_url_input = toga.TextInput(value=g.proxy_url, placeholder=_("http://proxy.example.com:8080"), style=Pack(margin_top=5, margin_bottom=5))
        self.proxy_id_input = toga.TextInput(value=g.proxy_id, placeholder=_("username"), style=Pack(margin_top=5, margin_bottom=5))
        self.proxy_pw_input = toga.PasswordInput(value=g.proxy_pw, placeholder=_("password"), style=Pack(margin_top=5, margin_bottom=5))
        box_proxy.add(self.proxy_url_input)
        box_proxy.add(self.proxy_id_input)
        box_proxy.add(self.proxy_pw_input)

        box = toga.Box(style=Pack(direction="column", flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Destination folder", dest_row, icon=self._folder_dest_icon))
        box.add(self._row("Output template", self.output_format_input))
        box.add(self._row("Output format", self.output_template_input, icon=self._file_name_icon))
        box.add(self._row("Overwrite existing files", self.overwrite_switch, icon=self._file_rewrite_icon))
        box.add(self._row("Limit download rate", limit_rate_row, icon=self._speed_icon))
        box.add(self._row("Simultaneous download fragments", self.fragments_input, icon=self._fragments_icon))
        box.add(self._row("Add thumbnail", self.add_thumbnail_switch, icon=self._thumbnail_icon))
        box.add(self._row("Download playlists", self.download_playlist_switch, icon=self._playlist_icon))
        box.add(self._row("Playlist folder name", self.playlist_folder_input, icon=self._folder_playlist_icon))
        box.add(self._row("Proxy URL", toga.Box(children=[box_proxy]), icon=self._proxy_icon))
        return box

    async def _choose_destination(self, widget: toga.Button) -> None:
        try:
            folder = await self.app.main_window.dialog(toga.SelectFolderDialog(_("Choose destination folder")))
        except Exception:
            folder = None
        if folder:
            self.app.download_dir = Path(str(folder))
            self.dest_label.text = str(self.app.download_dir)
            self.app.settings.general.download_dir = str(self.app.download_dir)
            self.app.save_settings()

    def _apply_general(self, widget: toga.Button) -> None:
        g = self.app.settings.general

        g.output_template = (self.output_template_input.value or "").strip() or g.output_template
        g.output_format = (self.output_format_input.value or "").strip()
        g.overwrite = bool(self.overwrite_switch.value)

        g.limit_rate_enabled = bool(self.limit_rate_switch.value)
        try:
            g.limit_rate_kib_s = int(self.limit_rate_input.value or 0)
        except (TypeError, ValueError):
            g.limit_rate_kib_s = 0
        if g.limit_rate_kib_s < 0:
            g.limit_rate_kib_s = 0

        try:
            g.concurrent_fragments = int(self.fragments_input.value or 1)
        except (TypeError, ValueError):
            g.concurrent_fragments = 1
        if g.concurrent_fragments < 1:
            g.concurrent_fragments = 1
        if g.concurrent_fragments > 16:
            g.concurrent_fragments = 16
        self.fragments_input.value = g.concurrent_fragments

        g.add_thumbnail = bool(self.add_thumbnail_switch.value)
        g.download_playlist = bool(self.download_playlist_switch.value)
        g.playlist_folder_name = (self.playlist_folder_input.value or "").strip()
        g.proxy_url = (self.proxy_url_input.value or "").strip()
        g.proxy_id = (self.proxy_id_input.value or "").strip()
        g.proxy_pw = (self.proxy_pw_input.value or "").strip()
        self.app.save_settings()

    def _build_metadata(self) -> toga.Widget:
        g = self.app.settings.general

        self.add_metadata_switch = toga.Switch("", value=getattr(g, "add_metadata", True))
        self.custom_metadata_input = toga.MultilineTextInput(
            value=getattr(g, "custom_metadata", ""),
            style=Pack(flex=1, height=140),
        )

        self.parse_metadata_switch = toga.Switch("", value=getattr(g, "parse_metadata_enabled", False))
        self.parse_metadata_rules_input = toga.MultilineTextInput(
            value=getattr(g, "parse_metadata_rules", "") or self._metadata_example_rules,
            style=Pack(flex=1, height=180),
        )

        open_cfg_btn = toga.Button(
            _("Open settings folder"),
            on_press=self._open_config_dir,
            style=Pack(margin_top=10),
        )

        box = toga.Box(style=Pack(direction="column", flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row(_("Add metadata"), self.add_metadata_switch, icon=self._metadata_icon))
        box.add(self._column(_("Custom metadata (key=value)"), self.custom_metadata_input))
        box.add(self._row(_("Detect metadata (parse-metadata)"), self.parse_metadata_switch, icon=self._metadata_search_icon))
        box.add(self._column(_("Parse-metadata rules (1 per line)"), self.parse_metadata_rules_input))
        box.add(open_cfg_btn)
        return box

    def _open_config_dir(self, widget: toga.Button) -> None:
        try:
            cfg_dir_raw = getattr(self.app, "config_dir", None)
            if cfg_dir_raw:
                cfg_dir = Path(str(cfg_dir_raw))
            else:
                cfg_dir = Path(str(self.app.paths.config))
        except Exception as e:
            try:
                self.app.main_window.dialog(toga.ErrorDialog("Paramètres", f"Chemin de config invalide: {e}"))
            except Exception:
                pass
            return

        try:
            cfg_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            try:
                self.app.main_window.dialog(toga.ErrorDialog(
                    "Paramètres",
                    f"Impossible de créer le dossier de config :\n{cfg_dir}\n\n{e}",
                ))
            except Exception:
                pass
            return

        try:
            cfg_dir = cfg_dir.resolve()
        except Exception:
            cfg_dir = Path(str(cfg_dir))

        if not cfg_dir.exists() or not cfg_dir.is_dir():
            try:
                self.app.main_window.dialog(toga.ErrorDialog(
                    "Paramètres",
                    f"Le dossier de config n'existe pas (ou n'est pas un dossier) :\n{cfg_dir}",
                ))
            except Exception:
                pass
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
            try:
                self.app.main_window.dialog(toga.ErrorDialog(
                    "Paramètres",
                    f"Impossible d'ouvrir le dossier :\n{cfg_dir}\n\n{e}",
                ))
            except Exception:
                pass
            return

    def _apply_metadata(self, widget: toga.Button) -> None:
        g = self.app.settings.general

        g.add_metadata = bool(self.add_metadata_switch.value)
        g.custom_metadata = str(self.custom_metadata_input.value or "").strip()

        g.parse_metadata_enabled = bool(self.parse_metadata_switch.value)
        g.parse_metadata_rules = str(self.parse_metadata_rules_input.value or "").strip()

        self.app.save_settings()

    def _build_audio(self) -> toga.Widget:
        a = self.app.settings.audio

        self.audio_codec_select = toga.Selection(items=["auto", "mp3", "aac", "opus", "vorbis", "flac", "alac"], style=Pack(width=250))
        self.audio_codec_select.value = a.preferred_codec

        self.audio_ext_select = toga.Selection(items=["mp3", "aac", "opus", "m4a", "wav", "flac", "alac"], style=Pack(width=250))
        self.audio_ext_select.value = a.ext

        self.audio_square_thumb_switch = toga.Switch("", value=a.square_thumbnail)

        box = toga.Box(style=Pack(direction="column", flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Preferred codec", self.audio_codec_select, icon=self._codec_audio_icon))
        box.add(self._row("Extension / container", self.audio_ext_select, icon=self._ext_audio_icon))
        box.add(self._row("Square thumbnail", self.audio_square_thumb_switch, icon=self._square_audio_icon))
        return box

    def _apply_audio(self, widget: toga.Button) -> None:
        a = self.app.settings.audio
        a.preferred_codec = str(self.audio_codec_select.value or "auto")
        a.ext = str(self.audio_ext_select.value or "mp3")
        a.square_thumbnail = bool(self.audio_square_thumb_switch.value)
        self.app.save_settings()

    def _build_video(self) -> toga.Widget:
        v = self.app.settings.video

        self.video_codec_select = toga.Selection(items=["auto", "h264", "vp9", "av1"], style=Pack(width=250))
        self.video_codec_select.value = v.preferred_codec

        self.video_ext_select = toga.Selection(items=["auto", "mp4", "mkv", "webm"], style=Pack(width=250))
        self.video_ext_select.value = v.ext

        self.video_subs_switch = toga.Switch("", value=v.subtitles)
        self.video_chapters_switch = toga.Switch("", value=v.chapters)

        box = toga.Box(style=Pack(direction="column", flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Preferred codec", self.video_codec_select, icon=self._codec_video_icon))
        box.add(self._row("Extension / container", self.video_ext_select, icon=self._ext_video_icon))
        box.add(self._row("Subtitles", self.video_subs_switch, icon=self._subs_icon))
        box.add(self._row("Chapters", self.video_chapters_switch, icon=self._chapters_icon))
        return box

    def _apply_video(self, widget: toga.Button) -> None:
        v = self.app.settings.video
        v.preferred_codec = str(self.video_codec_select.value or "auto")
        v.ext = str(self.video_ext_select.value or "auto")
        v.subtitles = bool(self.video_subs_switch.value)
        v.chapters = bool(self.video_chapters_switch.value)
        self.app.save_settings()

    def _apply_all(self, widget: toga.Button) -> None:
        """Applique tous les paramètres de tous les onglets"""
        self._apply_general(None)
        self._apply_metadata(None)
        self._apply_audio(None)
        self._apply_video(None)
        
    async def _import(self, widget: toga.Button) -> None:
        """Importe les paramètres depuis un fichier JSON"""
        try:
            # Créer le dialogue d'ouverture de fichier
            open_dialog = toga.OpenFileDialog(
                title="Importer les paramètres",
                file_types=["json"]
            )
            
            # Afficher le dialogue et obtenir le chemin
            file_path = await self.app.main_window.dialog(open_dialog)
            
            if not file_path:
                return  # L'utilisateur a annulé
            
            # Lire et parser le fichier JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            # Importer les paramètres généraux
            if "general" in settings_data:
                general = settings_data["general"]
                for key, value in general.items():
                    if hasattr(self.app.settings.general, key):
                        setattr(self.app.settings.general, key, value)
            
            # Importer les paramètres vidéo
            if "video" in settings_data:
                video = settings_data["video"]
                for key, value in video.items():
                    if hasattr(self.app.settings.video, key):
                        setattr(self.app.settings.video, key, value)
            
            # Importer les paramètres audio
            if "audio" in settings_data:
                audio = settings_data["audio"]
                for key, value in audio.items():
                    if hasattr(self.app.settings.audio, key):
                        setattr(self.app.settings.audio, key, value)
            
            # Sauvegarder les nouveaux paramètres
            self.app.save_settings()
            
            # Mettre à jour l'interface avec les nouveaux paramètres
            self._refresh_ui_from_settings()
            
            # Message de succès avec la nouvelle syntaxe
            success_dialog = toga.InfoDialog(
                title=_("Import settings"),
                message=_("Settings imported successfully\n\nAll settings have been applied.")
            )
            await self.app.main_window.dialog(success_dialog)
            
        except json.JSONDecodeError:
            error_dialog = toga.ErrorDialog(
                title=_("Format error"),
                message=_("The selected file is not a valid JSON file.")
            )
            await self.app.main_window.dialog(error_dialog)
        except Exception as e:
            error_dialog = toga.ErrorDialog(
                title=_("Unable to import settings"),
                message=_("Unable to import settings:\n{}").format(str(e))
            )
            await self.app.main_window.dialog(error_dialog)
    
    def _refresh_ui_from_settings(self) -> None:
        """Rafraîchit l'interface avec les paramètres actuels"""
        try:
            # Mettre à jour les champs généraux
            if hasattr(self, 'dest_label'):
                self.dest_label.text = self.app.settings.general.download_dir or ""
            if hasattr(self, 'output_template_input'):
                self.output_template_input.value = self.app.settings.general.output_template
            if hasattr(self, 'output_format_input'):
                self.output_format_input.value = self.app.settings.general.output_format
            if hasattr(self, 'overwrite_switch'):
                self.overwrite_switch.value = self.app.settings.general.overwrite
            if hasattr(self, 'limit_rate_switch'):
                self.limit_rate_switch.value = self.app.settings.general.limit_rate_enabled
            if hasattr(self, 'limit_rate_input'):
                self.limit_rate_input.value = self.app.settings.general.limit_rate_kib_s
            if hasattr(self, 'fragments_input'):
                self.fragments_input.value = self.app.settings.general.concurrent_fragments
            if hasattr(self, 'add_thumbnail_switch'):
                self.add_thumbnail_switch.value = self.app.settings.general.add_thumbnail
            if hasattr(self, 'download_playlist_switch'):
                self.download_playlist_switch.value = self.app.settings.general.download_playlist
            if hasattr(self, 'playlist_folder_input'):
                self.playlist_folder_input.value = self.app.settings.general.playlist_folder_name
            
            # Mettre à jour les champs vidéo
            if hasattr(self, 'video_codec_select'):
                self.video_codec_select.value = self.app.settings.video.preferred_codec
            if hasattr(self, 'video_ext_select'):
                self.video_ext_select.value = self.app.settings.video.ext
            if hasattr(self, 'video_subs_switch'):
                self.video_subs_switch.value = self.app.settings.video.subtitles
            if hasattr(self, 'video_chapters_switch'):
                self.video_chapters_switch.value = self.app.settings.video.chapters
            
            # Mettre à jour les champs métadonnées
            if hasattr(self, 'add_metadata_switch'):
                self.add_metadata_switch.value = self.app.settings.general.add_metadata
            if hasattr(self, 'custom_metadata_input'):
                self.custom_metadata_input.value = self.app.settings.general.custom_metadata
            if hasattr(self, 'parse_metadata_switch'):
                self.parse_metadata_switch.value = self.app.settings.general.parse_metadata_enabled
            if hasattr(self, 'parse_metadata_rules_input'):
                self.parse_metadata_rules_input.value = self.app.settings.general.parse_metadata_rules
            
            # Mettre à jour les champs audio
            if hasattr(self, 'audio_codec_select'):
                self.audio_codec_select.value = self.app.settings.audio.preferred_codec
            if hasattr(self, 'audio_ext_select'):
                self.audio_ext_select.value = self.app.settings.audio.ext
            if hasattr(self, 'audio_square_thumb_switch'):
                self.audio_square_thumb_switch.value = self.app.settings.audio.square_thumbnail
                
        except Exception as e:
            # En cas d'erreur, ne pas bloquer l'import
            pass
    
    async def _export(self, widget: toga.Button) -> None:
        """Exporte les paramètres actuels dans un fichier JSON"""
        try:
            # Créer le dialogue de sauvegarde
            save_dialog = toga.SaveFileDialog(
                title="Exporter les paramètres",
                suggested_filename="audeo_settings.json",
                file_types=["json"]
            )
            
            # Afficher le dialogue et obtenir le chemin
            file_path = await self.app.main_window.dialog(save_dialog)
            
            if not file_path:
                return  # L'utilisateur a annulé
            
            # Utiliser la structure JSON des settings existants
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
            
            # Message de succès avec la nouvelle syntaxe
            success_dialog = toga.InfoDialog(
                title=_("Export settings"),
                message=_("Settings exported successfully\n\nFile saved to: {}").format(file_path)
            )
            await self.app.main_window.dialog(success_dialog)
            
        except Exception as e:
            # Message d'erreur avec la nouvelle syntaxe
            error_dialog = toga.ErrorDialog(
                title=_("Unable to export settings"),
                message=_("Unable to export settings:\n{}").format(str(e))
            )
            await self.app.main_window.dialog(error_dialog)

