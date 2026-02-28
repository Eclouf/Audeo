"""
Data classes for download management
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .settings import AppSettings


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
    future: Optional[object] = field(default=None)  # Future du ThreadPoolExecutor
    cancelled: bool = field(default=False)  # État d'annulation
    paused: bool = field(default=False)  # État de pause
    playlist: bool = field(default=False)  # Indique si c'est une tâche de playlist
