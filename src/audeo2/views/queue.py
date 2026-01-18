from __future__ import annotations

import toga
from toga.style import Pack


class QueueView:
    def __init__(self, app: toga.App) -> None:
        self.app = app

        label = toga.Label("File d'attente (MVP)", style=Pack(margin_top=20, margin_left=20, margin_bottom=20, font_size=16))
        self.widget = toga.Box(style=Pack(direction="column", flex=1, margin_left=15, margin_right=15))
        self.widget.add(label)
