from __future__ import annotations

import threading
import time
from io import StringIO
from typing import Optional

import toga
from toga.style import Pack
from pathlib import Path

from ..i18n import _

class TerminalWindow(toga.Window):
    """Fenêtre de terminal personnalisée avec gestion du focus"""
    
    def _on_gain_focus(self):
        """Gestion du focus pour éviter les erreurs"""
        pass


class DownloadsView:
    def __init__(self, app: toga.App) -> None:
        self.app = app
        self._log_buffer = StringIO()
        self._log_lock = threading.Lock()
        self._terminal_window: Optional[TerminalWindow] = None
        self._terminal_text: Optional[toga.MultilineTextInput] = None

        self.url_input = toga.TextInput(placeholder=_("URL ..."), style=Pack(flex=1, margin=5))
        self.kind_select = toga.Selection(
            items=[
                {"name": _("video"), "value": "video"}, 
                {"name": _("audio"), "value": "audio"}
            ], 
            accessor="name", 
            style=Pack(width=130, margin=5))
        self.kind_select.value.value = "video"
        add_btn = toga.Button(_("Add"), on_press=self.app._on_add, style=Pack(width=70, margin=5))
        self.process_anim = toga.ActivityIndicator(running=False, style=Pack(margin=5))
        icons_dir = Path(__file__).resolve().parent.parent / "ressources" / "pictures"
        terminal_icon = toga.Icon(str(icons_dir / "terminal-24.png"))
        terminal_btn = toga.Button(icon=terminal_icon, on_press=self._show_terminal, style=Pack(margin=5))

        top = toga.Box(style=Pack(direction="row"))
        top.add(self.url_input)
        top.add(self.kind_select)
        top.add(add_btn)
        top.add(self.process_anim)
        top.add(terminal_btn)

        self.cards_box = toga.Box(style=Pack(direction="column"))
        
        # Image par défaut quand aucune carte n'est affichée
        icons_dir = Path(__file__).resolve().parent.parent / "ressources"
        self.default_image = toga.Image(str(icons_dir / "default.png"))
        self.default_image_view = toga.ImageView(
            self.default_image, 
            style=Pack(width=80, height=80, margin_top=50)
        )
        
        # Conteneur pour centrer l'image
        self.center_box = toga.Box(style=Pack(direction="column", align_items="center", justify_content="center", flex=1))
        self.center_box.add(self.default_image_view)
        
        # Conteneur principal qui peut contenir soit les cartes, soit l'image par défaut
        self.main_content_box = toga.Box(style=Pack(direction="column", flex=1))
        self.main_content_box.add(self.center_box)
        
        scroller = toga.ScrollContainer(content=self.main_content_box, style=Pack(flex=1))

        self.widget = toga.Box(style=Pack(direction="column", flex=1))
        self.widget.add(top)
        self.widget.add(scroller)

    def _show_terminal(self, widget: toga.Button) -> None:
        """Affiche la fenêtre de terminal avec la sortie en temps réel"""
        if self._terminal_window is None or not self._terminal_window.visible:
            self._terminal_text = toga.MultilineTextInput(
                readonly=True,
                style=Pack(flex=1, font_family="monospace")
            )
            
            # Afficher le contenu actuel du buffer
            with self._log_lock:
                current_content = self._log_buffer.getvalue()
                if current_content:
                    self._terminal_text.value = current_content
            
            # Boutons de contrôle
            clear_btn = toga.Button(_("Clear"), on_press=self._clear_terminal, style=Pack(margin=6))
            refresh_btn = toga.Button(_("Refresh"), on_press=self._refresh_terminal, style=Pack(margin=6))
            close_btn = toga.Button(_("Close"), on_press=self._close_terminal, style=Pack(margin=6))
            
            button_box = toga.Box(style=Pack(direction="row"))
            button_box.add(clear_btn)
            button_box.add(refresh_btn)
            button_box.add(toga.Box(style=Pack(flex=1)))  # Espaceur
            button_box.add(close_btn)
            
            # Conteneur principal
            main_box = toga.Box(style=Pack(direction="column", margin=15))
            main_box.add(self._terminal_text)
            main_box.add(button_box)
            
            # Créer la fenêtre
            self._terminal_window = TerminalWindow(
                title=_("Terminal - Real-time output"),
                content=main_box,
                size=(850, 650)
            )
            
            # Centrer et afficher
            self._terminal_window.show()
            
            # NE PAS démarrer la mise à jour automatique pour éviter le blocage
            # L'utilisateur peut cliquer sur "Rafraîchir" pour voir les nouveaux logs
    
    def _refresh_terminal(self, widget: toga.Button) -> None:
        """Rafraîchit manuellement le contenu du terminal"""
        if self._terminal_text:
            with self._log_lock:
                current_content = self._log_buffer.getvalue()
                self._terminal_text.value = current_content
    
    def _clear_terminal(self, widget: toga.Button) -> None:
        """Efface le contenu du terminal"""
        with self._log_lock:
            self._log_buffer.seek(0)
            self._log_buffer.truncate(0)
        
        if self._terminal_text:
            self._terminal_text.value = ""
    
    def _close_terminal(self, widget: toga.Button) -> None:
        """Ferme la fenêtre de terminal"""
        if self._terminal_window:
            self._terminal_window.close()
            self._terminal_window = None
            self._terminal_text = None
    
    def _start_terminal_update(self) -> None:
        """Démarre la mise à jour automatique du terminal (non-bloquante)"""
        def update_loop():
            while self._terminal_window and self._terminal_window.visible:
                try:
                    if self._terminal_text:
                        with self._log_lock:
                            current_content = self._log_buffer.getvalue()
                            if current_content != self._terminal_text.value:
                                # Mettre à jour le texte de manière thread-safe
                                try:
                                    self._terminal_text.value = current_content
                                except Exception:
                                    # Si la fenêtre est fermée pendant la mise à jour
                                    break
                except Exception:
                    # Si une erreur occurs, arrêter la boucle
                    break
                
                # Utiliser un temps plus court pour être plus réactif mais moins bloquant
                time.sleep(0.2)
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    def _update_content_display(self) -> None:
        """Met à jour l'affichage en fonction du nombre de cartes"""
        # Vérifier si des cartes sont présentes
        has_cards = hasattr(self.cards_box, 'children') and len(self.cards_box.children) > 0
        
        # Vider le conteneur principal
        self.main_content_box.clear()
        
        if has_cards:
            # Afficher les cartes
            self.main_content_box.add(self.cards_box)
        else:
            # Afficher l'image par défaut centrée
            self.main_content_box.add(self.center_box)
    
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
    
    def log_error(self, message: str) -> None:
        """Ajoute un message d'erreur au buffer de log"""
        self.log_message(f"ERROR: {message}")
    
    def log_info(self, message: str) -> None:
        """Ajoute un message d'info au buffer de log"""
        self.log_message(f"INFO: {message}")
