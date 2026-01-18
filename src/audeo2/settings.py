from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(slots=True)
class GeneralSettings:
    download_dir: Optional[str] = None
    output_format: str = ""  # texte libre (interprété comme format yt-dlp si non vide)
    output_template: str = "%(title)s [%(id)s].%(ext)s"
    overwrite: bool = False
    limit_rate_enabled: bool = False
    limit_rate_kib_s: int = 0
    concurrent_fragments: int = 1
    add_thumbnail: bool = True
    add_metadata: bool = True
    custom_metadata: str = ""
    parse_metadata_enabled: bool = False
    parse_metadata_rules: str = ""
    download_playlist: bool = False
    playlist_folder_name: str = ""  # Nom du dossier pour les playlists


@dataclass(slots=True)
class VideoSettings:
    preferred_codec: str = "auto"  # e.g. auto, h264, vp9, av1
    ext: str = "auto"  # e.g. auto, mp4, webm, mkv
    subtitles: bool = False
    chapters: bool = False


@dataclass(slots=True)
class AudioSettings:
    preferred_codec: str = "auto"  # e.g. auto, mp3, aac, opus
    ext: str = "mp3"  # extracted audio file extension/codec
    square_thumbnail: bool = False


@dataclass(slots=True)
class AppSettings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    video: VideoSettings = field(default_factory=VideoSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    ffmpeg_path: Optional[str] = None


def load_settings(config_dir: Path) -> AppSettings:
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "settings.json"
    if not path.exists():
        return AppSettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AppSettings()

    def _get(d: dict, key: str, default: Any) -> Any:
        v = d.get(key)
        return default if v is None else v

    g = data.get("general", {}) if isinstance(data.get("general"), dict) else {}
    v = data.get("video", {}) if isinstance(data.get("video"), dict) else {}
    a = data.get("audio", {}) if isinstance(data.get("audio"), dict) else {}

    settings = AppSettings(
        general=GeneralSettings(
            download_dir=_get(g, "download_dir", None),
            output_format=str(_get(g, "output_format", "") or ""),
            output_template=str(_get(g, "output_template", "%(title)s [%(id)s].%(ext)s")),
            overwrite=bool(_get(g, "overwrite", False)),
            limit_rate_enabled=bool(_get(g, "limit_rate_enabled", False)),
            limit_rate_kib_s=int(_get(g, "limit_rate_kib_s", 0) or 0),
            concurrent_fragments=int(_get(g, "concurrent_fragments", 1) or 1),
            add_thumbnail=bool(_get(g, "add_thumbnail", True)),
            add_metadata=bool(_get(g, "add_metadata", True)),
            custom_metadata=str(_get(g, "custom_metadata", "") or ""),
            parse_metadata_enabled=bool(_get(g, "parse_metadata_enabled", False)),
            parse_metadata_rules=str(_get(g, "parse_metadata_rules", "") or ""),
            download_playlist=bool(_get(g, "download_playlist", False)),
            playlist_folder_name=str(_get(g, "playlist_folder_name", "") or ""),
        ),
        video=VideoSettings(
            preferred_codec=str(_get(v, "preferred_codec", "auto")),
            ext=str(_get(v, "ext", "auto")),
            subtitles=bool(_get(v, "subtitles", False)),
            chapters=bool(_get(v, "chapters", False)),
        ),
        audio=AudioSettings(
            preferred_codec=str(_get(a, "preferred_codec", "auto")),
            ext=str(_get(a, "ext", "mp3")),
            square_thumbnail=bool(_get(a, "square_thumbnail", False)),
        ),
        ffmpeg_path=data.get("ffmpeg_path"),
    )

    if settings.general.custom_metadata.strip().startswith("<member '"):
        settings.general.custom_metadata = ""
    if settings.general.parse_metadata_rules.strip().startswith("<member '"):
        settings.general.parse_metadata_rules = ""

    if settings.general.concurrent_fragments < 1:
        settings.general.concurrent_fragments = 1
    if settings.general.concurrent_fragments > 16:
        settings.general.concurrent_fragments = 16
    if settings.general.limit_rate_kib_s < 0:
        settings.general.limit_rate_kib_s = 0

    return settings


def save_settings(config_dir: Path, settings: AppSettings) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "settings.json"
    payload = asdict(settings)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
