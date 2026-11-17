from __future__ import annotations

import threading
import time
from io import StringIO
from typing import Optional
from pathlib import Path

import customtkinter as ctk
from PIL import Image as PILImage

from ..i18n import _
from ..widgets import CardsBox


class _ProcessAnimation(ctk.CTkLabel):
    """Label animé utilisé par DownloadManager via .start()/.stop()."""

    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, text="", **kwargs)
        self._frame_index = 0
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        self._running = False
        self.configure(text="")

    def _tick(self) -> None:
        if not self._running:
            return
        self.configure(text=self._FRAMES[self._frame_index % len(self._FRAMES)])
        self._frame_index += 1
        self.after(80, self._tick)


class DownloadsView:
    def __init__(self, app) -> None:
        self.app = app
        self._log_buffer = StringIO()
        self._log_lock = threading.Lock()
        self._terminal_window: Optional[ctk.CTkToplevel] = None
        self._terminal_text: Optional[ctk.CTkTextbox] = None

        # Create main widget
        self.widget = ctk.CTkFrame(app.content)
        
        # Top bar with URL input and controls
        top_frame = ctk.CTkFrame(self.widget)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        self.url_input = ctk.CTkEntry(top_frame, placeholder_text=_("URL ..."))
        self.url_input.pack(side="left", fill="x", expand=True, padx=5)
        
        # Valeurs d'affichage localisées, mappées sur des codes stables ("video"/"audio")
        self._kind_display_to_code = {_("video"): "video", _("audio"): "audio"}
        self.kind_select = ctk.CTkOptionMenu(
            top_frame,
            values=list(self._kind_display_to_code.keys()),
            width=130
        )
        self.kind_select.set(_("video"))
        self.kind_select.pack(side="left", padx=5)
        
        add_btn = ctk.CTkButton(top_frame, text=_("Add"), command=self.app._on_add, width=70)
        add_btn.pack(side="left", padx=5)
        
        # Process animation
        self.process_anim = _ProcessAnimation(top_frame)
        self.process_anim.pack(side="left", padx=5)
        
        # Terminal button
        icons_dir = Path(__file__).resolve().parent.parent / "ressources" / "pictures"
        terminal_icon_path = icons_dir / "terminal-24.png"
        terminal_icon = None
        try:
            if terminal_icon_path.exists():
                from ..widgets import load_themed_icon
                terminal_icon = load_themed_icon(terminal_icon_path, size=(24, 24))
        except Exception:
            pass
        
        terminal_btn = ctk.CTkButton(
            top_frame, 
            text="", 
            image=terminal_icon,
            width=40,
            command=self._show_terminal
        )
        terminal_btn.pack(side="left", padx=5)

        # Scrollable area containing either the cards or the default image
        scroller = ctk.CTkScrollableFrame(self.widget)
        scroller.pack(fill="both", expand=True, padx=5, pady=5)
        self.scroller = scroller

        # Cards box (scrollable content when downloads exist)
        self.cards_box = CardsBox(scroller)

        # Default image when no cards
        icons_dir = Path(__file__).resolve().parent.parent / "ressources"
        default_image_path = icons_dir / "default.png"
        self.default_image = None
        try:
            if default_image_path.exists():
                img = PILImage.open(default_image_path)
                self.default_image = ctk.CTkImage(img, size=(80, 80))
        except Exception:
            pass

        self.center_box = ctk.CTkFrame(scroller)
        self.default_image_view = ctk.CTkLabel(self.center_box, image=self.default_image, text="")
        self.default_image_view.pack(expand=True)
        self.center_box.pack(fill="both", expand=True)

    def _show_terminal(self) -> None:
        """Affiche la fenêtre de terminal avec la sortie en temps réel"""
        if self._terminal_window is None or not self._terminal_window.winfo_exists():
            self._terminal_window = ctk.CTkToplevel(self.widget)
            self._terminal_window.title(_("Terminal - Real-time output"))
            self._terminal_window.geometry("850x650")
            
            self._terminal_text = ctk.CTkTextbox(self._terminal_window)
            self._terminal_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Afficher le contenu actuel du buffer
            with self._log_lock:
                current_content = self._log_buffer.getvalue()
                if current_content:
                    self._terminal_text.insert("1.0", current_content)
            
            # Boutons de contrôle
            button_frame = ctk.CTkFrame(self._terminal_window)
            button_frame.pack(fill="x", padx=10, pady=10)
            
            clear_btn = ctk.CTkButton(button_frame, text=_("Clear"), command=self._clear_terminal, width=100)
            clear_btn.pack(side="left", padx=5)
            
            refresh_btn = ctk.CTkButton(button_frame, text=_("Refresh"), command=self._refresh_terminal, width=100)
            refresh_btn.pack(side="left", padx=5)
            
            close_btn = ctk.CTkButton(button_frame, text=_("Close"), command=self._close_terminal, width=100)
            close_btn.pack(side="right", padx=5)
    
    def _refresh_terminal(self) -> None:
        """Rafraîchit manuellement le contenu du terminal"""
        if self._terminal_text:
            with self._log_lock:
                current_content = self._log_buffer.getvalue()
                self._terminal_text.delete("1.0", "end")
                self._terminal_text.insert("1.0", current_content)
    
    def _clear_terminal(self) -> None:
        """Efface le contenu du terminal"""
        with self._log_lock:
            self._log_buffer.seek(0)
            self._log_buffer.truncate(0)
        
        if self._terminal_text:
            self._terminal_text.delete("1.0", "end")
    
    def _close_terminal(self) -> None:
        """Ferme la fenêtre de terminal"""
        if self._terminal_window:
            self._terminal_window.destroy()
            self._terminal_window = None
            self._terminal_text = None
    
    def _update_content_display(self) -> None:
        """Met à jour l'affichage en fonction du nombre de cartes"""
        # Vérifier si des cartes sont présentes
        has_cards = len(self.cards_box.winfo_children()) > 0

        self.center_box.pack_forget()
        self.cards_box.pack_forget()

        if has_cards:
            # Afficher les cartes
            self.cards_box.pack(fill="both", expand=True)
        else:
            # Afficher l'image par défaut centrée
            self.center_box.pack(fill="both", expand=True)
    
    def log_message(self, message: str) -> None:
        """Ajoute un message au buffer de log"""
        timestamp = time.strftime("%H:%M:%S")
        with self._log_lock:
            self._log_buffer.write(f"[{timestamp}] {message}\n")
            
            # Limiter la taille du buffer pour éviter les problèmes de performance
            # Garder seulement les 1000 dernières lignes
            content = self._log_buffer.getvalue()
            lines = content.split('\n')
            if len(lines) > 1000:
                # Garder les 500 dernières lignes pour avoir de la marge
                truncated_content = '\n'.join(lines[-500:])
                self._log_buffer.seek(0)
                self._log_buffer.truncate(0)
                self._log_buffer.write(truncated_content)
    
    def log_debug(self, message: str) -> None:
        """Ajoute un message de debug au buffer de log"""
        self.log_message(f"DEBUG: {message}")
    
    def log_warning(self, message: str) -> None:
        """Ajoute un message d'avertissement au buffer de log"""
        self.log_message(f"WARNING: {message}")

    def log_error(self, message: str) -> None:
        """Ajoute un message d'erreur au buffer de log"""
        self.log_message(f"ERROR: {message}")
    
    def log_info(self, message: str) -> None:
        """Ajoute un message d'info au buffer de log"""
        self.log_message(f"INFO: {message}")
