from __future__ import annotations

import toga
from toga.style import Pack

from ..i18n import _


class FinishedDownloadsView:
    def __init__(self, app: toga.App) -> None:
        self.app = app

        clear_btn = toga.Button(_("Clear history"), on_press=self.app._on_clear_finished, style=Pack(width=150, margin=10))

        bottom_box = toga.Box(style=Pack(direction="row", margin=10))
        bottom_box.add(toga.Box(style=Pack(flex=1)))
        bottom_box.add(clear_btn)
        self.cards_box = toga.Box(style=Pack(direction="column"))
        scroller = toga.ScrollContainer(content=self.cards_box, style=Pack(flex=1, margin_top=10))

        self.widget = toga.Box(style=Pack(direction="column", flex=1))
        self.widget.add(toga.Label(_("Finished downloads"), style=Pack(font_weight="bold", align_items="center", font_size=12,margin=5)))
        self.widget.add(scroller)
        self.widget.add(bottom_box)
