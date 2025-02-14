# -*- encoding:utf-8 -*-

import toga
import asyncio

from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ytdlp.tools import Tools
from threading import Thread

class FormatWindow:
    def __init__(self, parent_app):
        self.app = parent_app
        self.format_one = ''
        self.format_two = ''
        self.selected_row = None
        self.create_window()
        self.tread_load_formats()
    
    def create_window(self):      
        # Créer le contenu principal
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
                
        # Créer la table des formats
        self.formats_table = toga.Table(
                    headings=[
                        'Format ID',
                        'Extension',
                        'Résolution',
                        'Taille fichier',
                        'Codec vidéo',
                        'Codec audio',
                        'FPS',
                        'Bitrate',
                        'Protocol'
                    ],
                    style=Pack(flex=1),
                    on_select=self.on_format_select
                )
                
                # Boutons de sélection
        button_box = toga.Box(style=Pack(direction=ROW, padding=5))
        self.select_button = toga.Button(
                    'Sélectionner',
                    on_press=self.on_select,
                    style=Pack(padding=5)
                )
        self.cancel_button = toga.Button(
                    'Annuler',
                    on_press=self.on_cancel,
                    style=Pack(padding=5)
                )
        self.format_label = toga.Label('', style=Pack(font_weight='bold', padding=5))
        button_box.add(self.select_button, self.cancel_button, self.format_label)
                
                # Ajouter les widgets au contenu principal
        main_box.add(self.formats_table, button_box)
                
                # Définir le contenu de la fenêtre
                # Charger les formats disponibles
        
        self.window = toga.Window(title="Formats disponibles")
        self.window.content = main_box
        self.app.windows.add(self.window)
        self.window.show()
         
    def load_formats(self):
        """Charge les formats disponibles pour l'URL actuelle"""
        if hasattr(self.app, 'url_input') and self.app.url_input.value:
            try:
                # Options génériques minimales
                tools = Tools()
                with tools.get_yt_dlp_format(self.app.url_input.value) as table_data:
                    if not table_data:
                        message = 'Aucun format disponible pour cette URL.'
                        self.error_dialog(message)
                    
                    self.formats_table.data = table_data
                    
            
            except Exception as e:
                message = f"Impossible de charger les formats: {str(e)}"
                self.error_dialog(message)
    
    def tread_load_formats(self):            
        # Charger les formats disponibles
        Thread(target=self.load_formats()).start()
    
    def on_format_select(self, widget, **kwargs):
        """Gère la sélection des formats dans le tableau.
        Permet de sélectionner jusqu'à deux formats (par exemple audio + vidéo)"""
        
        try:
            # Récupérer le format sélectionné
            if widget.selection is not None:
                selected_format = str(widget.selection.format_id)
                print(f"Format sélectionné : {selected_format}\n{widget.selection}")
            # Si aucun format n'est sélectionné
            if self.format_one == '':
                self.format_one = selected_format
                self.format_label.text = f'Format : {self.format_one}'
            
            # Si un format est déjà sélectionné
            elif self.format_two == '' and selected_format != self.format_one:
                self.format_two = selected_format
                self.format_label.text = f'Format : {self.format_one} + {self.format_two}'
            
            # Si on clique sur un format déjà sélectionné, on le désélectionne
            elif selected_format == self.format_one:
                self.format_one = self.format_two
                self.format_two = ''
                self.format_label.text = f'Format : {self.format_one}' if self.format_one else ''
            elif selected_format == self.format_two:
                self.format_two = ''
                self.format_label.text = f'Format : {self.format_one}'
            
            # Si deux formats sont déjà sélectionnés, on remplace le second
            else:
                self.format_two = selected_format
                self.format_label.text = f'Format : {self.format_one} + {self.format_two}'
            
        except Exception as e:
            print(f"Erreur lors de la sélection du format : {str(e)}")
                      
    def error_dialog(self, message):          
                error = toga.ErrorDialog(
                    'Erreur',
                    message
                )
                task = asyncio.create_task(self.window.dialog(error))
                task.add_done_callback(self.dialog_closed)
    
    def dialog_closed(self, task):
        """Appelé lorsque la boîte de dialogue est fermée"""
        pass
            
    def on_select(self, widget):
        """Appelé lorsque l'utilisateur sélectionne un format"""
        if self.format_one:
            format_id = str(self.format_one) + ('+' + str(self.format_two) if self.format_two else '')
            self.app.options['format'] = str(format_id)
            self.app.update_options(dict(self.app.options))
            self.window.close()
        else:
            message = 'Veuillez choisir au moins un format.'
            self.error_dialog(message)
            
    def on_cancel(self, widget):
        """Ferme la fenêtre sans sélectionner de format"""
        self.window.close()