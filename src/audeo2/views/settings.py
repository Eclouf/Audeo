from __future__ import annotations

import os
import subprocess
from pathlib import Path

import toga
from toga import style
from toga.style import Pack


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
        #self._fragments_icon = toga.Image(str(icon_path / "settings" / "layers-32.png"))
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
        apply_all_btn = toga.Button("Appliquer tout", on_press=self._apply_all, style=Pack(margin_top=15, margin=20, margin_bottom=8, margin_left=20, margin_right=20))

        # Conteneur principal avec onglets et bouton
        main_box = toga.Box(style=Pack(direction="column", flex=1, margin_bottom=15))
        main_box.add(toga.OptionContainer(
            style=Pack(flex=1),
            content=[
                toga.OptionItem("Général", general),
                toga.OptionItem("Métadonnées", metadata),
                toga.OptionItem("Audio", audio),
                toga.OptionItem("Vidéo", video),
            ],
        ))
        main_box.add(
            toga.Box(
                children=[
                    toga.Box(children=[], style=Pack(flex=1)),
                    apply_all_btn,
                ], 
                style=Pack(direction="row")
            )
        )

        self.widget = main_box

    def _wrap_scroll(self, content: toga.Widget) -> toga.ScrollContainer:
        return toga.ScrollContainer(content=content, style=Pack(flex=1))

    def _row(self, label: str, widget: toga.Widget, icon=None) -> toga.Box:
        if icon:
            left = toga.Box(
                children=[
                    toga.ImageView(icon, style=Pack(width=24, height=24, margin=(5, 5, 5, 5))),
                    toga.Label(label, style=Pack(margin=(5, 5, 5, 5))),
                ],
                style=Pack(direction="row", align_items="center", width=300)
            )
        else:
            left = toga.Label(label, style=Pack(width=300, margin=(5, 5, 5, 5)))

        widget.style=Pack(direction="row", align_items="end", margin=(5, 5, 5, 5))
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
        left = toga.Label(label, style=Pack(width=600, margin=(5, 5, 5, 5)))
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
        choose_dest_btn = toga.Button("Choisir…", on_press=self._choose_destination, style=Pack(margin_left=15, margin_top=5, margin_bottom=5, margin_right=10))
        dest_row = toga.Box(style=Pack(direction="row", flex=1))
        dest_row.add(self.dest_label)
        dest_row.add(choose_dest_btn)

        self.output_template_input = toga.TextInput(value=g.output_template, style=Pack(flex=1, margin_top=5, margin_bottom=5))
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
        self.playlist_folder_input = toga.TextInput(value=g.playlist_folder_name, style=Pack(flex=1, margin_top=5, margin_bottom=5))
        self.proxy_url_input = toga.TextInput(value=g.proxy_url, placeholder="http://proxy.example.com:8080", style=Pack(margin_top=5, margin_bottom=5))

        box = toga.Box(style=Pack(direction="column", flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Dossier de destination", dest_row, icon=self._folder_dest_icon))
        box.add(self._row("Format de sortie (yt-dlp `format`)", self.output_format_input))
        box.add(self._row("Modèle de nom de fichier (outtmpl)", self.output_template_input, icon=self._file_name_icon))
        box.add(self._row("Remplacer les fichiers existants", self.overwrite_switch, icon=self._file_rewrite_icon))
        box.add(self._row("Limiter la vitesse (KiB/s)", limit_rate_row, icon=self._speed_icon))
        box.add(self._row("Fragments téléchargés simultanément", self.fragments_input, icon=self._folder_playlist_icon))
        box.add(self._row("Ajouter la vignette", self.add_thumbnail_switch, icon=self._thumbnail_icon))
        box.add(self._row("Télécharger les playlists", self.download_playlist_switch, icon=self._playlist_icon))
        box.add(self._row("Nom du dossier pour playlists", self.playlist_folder_input, icon=self._folder_playlist_icon))
        box.add(self._row("URL du proxy", self.proxy_url_input, icon=self._proxy_icon))
        return box

    async def _choose_destination(self, widget: toga.Button) -> None:
        try:
            folder = await self.app.main_window.dialog(toga.SelectFolderDialog("Choisir un dossier de destination"))
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
            "Ouvrir le dossier des paramètres",
            on_press=self._open_config_dir,
            style=Pack(margin_top=10),
        )

        box = toga.Box(style=Pack(direction="column",  flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Ajouter les métadonnées", self.add_metadata_switch, icon=self._metadata_icon))
        box.add(self._column("Métadonnées personnalisées (clé=valeur)", self.custom_metadata_input))
        box.add(self._row("Détecter des métadonnées (parse-metadata)", self.parse_metadata_switch, icon=self._metadata_search_icon))
        box.add(self._column("Règles parse-metadata (1 par ligne)", self.parse_metadata_rules_input))
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

        box = toga.Box(style=Pack(direction="column",  flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Codec préféré", self.audio_codec_select, icon=self._codec_audio_icon))
        box.add(self._row("Extension / conteneur", self.audio_ext_select, icon=self._ext_audio_icon))
        box.add(self._row("Vignette carrée", self.audio_square_thumb_switch, icon=self._square_audio_icon))
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

        box = toga.Box(style=Pack(direction="column",  flex=1, margin_top=15, margin_left=10, margin_right=10))
        box.add(self._row("Codec préféré", self.video_codec_select, icon=self._codec_video_icon))
        box.add(self._row("Extension / conteneur", self.video_ext_select, icon=self._ext_video_icon))
        box.add(self._row("Sous-titres", self.video_subs_switch, icon=self._subs_icon))
        box.add(self._row("Chapitres", self.video_chapters_switch, icon=self._chapters_icon))
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


