"""
Constants for Audeo2 application
"""
from __future__ import annotations

from enum import Enum, auto


class ViewName(Enum):
    """View identifiers - language independent constants for navigation"""
    DOWNLOADS = "downloads"
    INFO = "info"
    FINISHED = "finished"
    SETTINGS = "settings"


# Mapping from ViewName to display names (for internal use if needed)
VIEW_DISPLAY_NAMES = {
    ViewName.DOWNLOADS: "Téléchargements",
    ViewName.INFO: "Informations",
    ViewName.FINISHED: "Terminés",
    ViewName.SETTINGS: "Paramètres",
}
