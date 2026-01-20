__all__ = ["DownloadsView", "VideoInfoView", "SettingsView", "FinishedDownloadsView"]

from .downloads import DownloadsView
from .finished import FinishedDownloadsView
from .queue import VideoInfoView
from .settings import SettingsView
