__all__ = ["DownloadsView", "QueueView", "SettingsView", "FinishedDownloadsView"]

from .downloads import DownloadsView
from .finished import FinishedDownloadsView
from .queue import QueueView
from .settings import SettingsView
