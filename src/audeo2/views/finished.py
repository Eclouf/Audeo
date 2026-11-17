from __future__ import annotations

import customtkinter as ctk

from ..i18n import _
from ..widgets import CardsBox


class FinishedDownloadsView:
    def __init__(self, app) -> None:
        self.app = app

        # Create main widget
        self.widget = ctk.CTkFrame(app.content)
        
        # Title
        title_label = ctk.CTkLabel(
            self.widget,
            text=_("Finished downloads"),
            font=("CTkFont", 12, "bold")
        )
        title_label.pack(pady=5)
        
        # Scrollable area for cards
        scroller = ctk.CTkScrollableFrame(self.widget)
        scroller.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.cards_box = CardsBox(scroller)
        self.cards_box.pack(fill="both", expand=True)
        
        # Bottom box with clear button
        bottom_box = ctk.CTkFrame(self.widget)
        bottom_box.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(bottom_box, text="").pack(side="left", expand=True)  # Spacer
        
        clear_btn = ctk.CTkButton(
            bottom_box,
            text=_("Clear history"),
            command=self.app._on_clear_finished,
            width=150
        )
        clear_btn.pack(side="right")
