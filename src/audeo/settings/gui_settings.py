import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import json
import os
import pathlib

class SettingsApp(toga.App):
    def __init__(self, name, app_id):
        super().__init__(name, app_id, icon='/resources/audeo.png')

    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Créer les contenus des onglets
        general_box = self._create_general_tab()
        audio_box = self._create_audio_tab()
        video_box = self._create_video_tab()
        advanced_box = self._create_advanced_tab()
        
        # Créer l'OptionContainer et ajouter les onglets
        self.option_container = toga.OptionContainer(style=Pack(flex=1))
        self.option_container.content.append('Général', general_box)
        self.option_container.content.append('Audio', audio_box)
        self.option_container.content.append('Vidéo', video_box)
        self.option_container.content.append('Avancé', advanced_box)
        
        # Bouton de sauvegarde
        save_button = toga.Button(
            'Sauvegarder',
            on_press=self.save_config,
            style=Pack(padding=5)
        )
        
        main_box.add(self.option_container)
        main_box.add(save_button)
        
        self.main_window = toga.MainWindow(title="Paramètres")
        self.main_window.content = main_box
        self.main_window.show()

    def get_config(self):
        """Récupère la configuration avec les post-processeurs"""
        config = {
            # Format de sortie
            'outtmpl': {'default': self.template_select.value},
            
            # Options de base yt-dlp
            'format': 'bestaudio' if self.audio_mode.value else 'bestvideo+bestaudio',  # Format par défaut
            'writethumbnail': self.thumb_switch.value,
            'writeinfojson': self.write_info_json.value,
            'writedescription': self.write_description.value,
        
            # Post-processeurs
            'postprocessors': {
                # Audio
                'FFmpegExtractAudio': [
                    self.audio_format_select.value,  # codec
                    self.audio_quality_select.value, # qualité
                    False  # nopostoverwrites
                ],
                
                # Métadonnées
                'FFmpegMetadata': [
                    self.write_info_json.value,    # metadata
                    self.split_chapters.value,     # chapters
                    False                          # sponsorblock
                ],
                
                # Sous-titres
                'FFmpegEmbedSubtitle': self.embed_subs_switch.value,
                
                # Miniatures
                'FFmpegEmbedThumbnail': self.thumb_switch.value,
                
                # Fusion
                'FFmpegMerger': self.merge_files_switch.value,
                
                # Format vidéo
                'FFmpegVideoConvertor': self.preferred_ext_input.value
            },
            
            # Options générales
            'verbose': self.verbose_switch.value,
            'quiet': self.quiet_switch.value,
            #'no_warnings': self.no_warnings.value,
            'ignoreerrors': 'only_download',
            
            # Options de playlist
            'noplaylist': self.noplaylist_switch.value,
            'playlist_items': self.playlist_items.value,
            #'playlistrandom': self.random_playlist.value,
        }
        
        return {k: v for k, v in config.items() if v is not None}

    async def save_config(self, widget):
        """Sauvegarde la configuration dans config.json"""
        config = self.get_config()
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            dialog = toga.InfoDialog(
                title='Succès',
                message='Configuration sauvegardée'
            )
            await self.main_window.dialog(dialog)
            
        except Exception as e:
            error_dialog = toga.InfoDialog(
                title='Erreur',
                message=f'Erreur lors de la sauvegarde: {str(e)}'
            )
            await self.main_window.dialog(error_dialog)

    def _create_general_tab(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # Section choix audio/vidéo
        mode_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        mode_box.add(toga.Label('Mode de téléchargement', style=Pack(font_weight='bold')))
        
        # Création des switches
        self.audio_mode = toga.Switch(
            'Mode Audio', 
            value=True,
            on_change=self.on_audio_switch
        )
        self.video_mode = toga.Switch(
            'Mode Vidéo',
            value=False,
            on_change=self.on_video_switch
        )
        
        mode_box.add(self.audio_mode)
        mode_box.add(self.video_mode)
        main_box.add(mode_box)

        # Conteneur principal
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))

        # Créer un OptionContainer pour les sous-onglets
        sub_tabs = toga.OptionContainer(style=Pack(flex=1))
        
        # 1. Sous-onglet Format
        format_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        format_box.add(toga.Label('Format de nom de fichier', style=Pack(font_weight='bold')))
        
        # Extension préférée
        ext_label = toga.Label('Extension préférée:')
        self.preferred_ext_input = toga.Selection(
            items=['mp4', 'mkv', 'webm', 'avi'],
            style=Pack(padding=(0, 5), padding_top=5, padding_bottom=5)
        )
        format_box.add(ext_label)
        format_box.add(self.preferred_ext_input)
        
        # Formats disponibles
        self.template_select = toga.Selection(items=[
            # Formats basiques
            '%(title)s.%(ext)s',
            '%(id)s - %(title)s.%(ext)s',
            
            # Formats avec créateur
            '%(uploader)s - %(title)s.%(ext)s',
            '%(channel)s/%(title)s.%(ext)s',
            '%(uploader)s/%(upload_date)s - %(title)s.%(ext)s',
            
            # Formats avec date
            '%(upload_date)s - %(title)s.%(ext)s',
            '%(year)s/%(title)s.%(ext)s',
            '%(year)s/%(month)s/%(title)s.%(ext)s',
            
            # Formats playlist
            '%(playlist_title)s/%(title)s.%(ext)s',
            '%(playlist_index)s - %(title)s.%(ext)s',
            '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s',
            
            # Formats détaillés
            '%(playlist_index)s-%(id)s-%(title)s.%(ext)s',
            '%(uploader)s/%(playlist_title)s/%(title)s.%(ext)s',
            '%(channel)s/%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'
        ])
        
        # Information sur les variables
        format_help = toga.MultilineTextInput(readonly=True, value="""
Variables disponibles:
- title: Titre de la vidéo
- ext: Extension du fichier
- id: Identifiant de la vidéo
- uploader: Nom du créateur
- channel: Nom de la chaîne
- upload_date: Date de mise en ligne
- year/month: Année/Mois
- playlist_title: Titre de la playlist
- playlist_index: Position dans la playlist
        """.strip())
        
        format_box.add(self.template_select)
        format_box.add(format_help)
        
        # 2. Sous-onglet Métadonnées
        metadata_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        metadata_box.add(toga.Label('Options des métadonnées', style=Pack(font_weight='bold')))

        self.write_metadata = toga.Switch('Inclure les métadonnées')
        self.write_description = toga.Switch('Sauvegarder la description')
        self.write_info_json = toga.Switch('Sauvegarder le fichier info.json')
        self.thumb_switch = toga.Switch('Sauvegarder les miniatures')

        metadata_box.add(self.write_metadata)
        metadata_box.add(self.write_description)
        metadata_box.add(self.write_info_json)
        metadata_box.add(self.thumb_switch)
        
        # 3. Sous-onglet Playlists
        playlist_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        self.noplaylist_switch = toga.Switch('Ignorer les playlists')
        self.playlist_items = toga.TextInput(placeholder='1-5,10')
        playlist_box.add(self.noplaylist_switch)
        playlist_box.add(self.playlist_items)
        
        # 4. Sous-onglet Options
        options_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        self.verbose_switch = toga.Switch('Mode verbeux')
        self.quiet_switch = toga.Switch('Mode silencieux')
        options_box.add(self.verbose_switch)
        options_box.add(self.quiet_switch)
        
        # Ajouter les sous-onglets
        sub_tabs.content.append('Format', format_box)
        sub_tabs.content.append('Métadonnées', metadata_box)
        sub_tabs.content.append('Playlists', playlist_box)
        sub_tabs.content.append('Options', options_box)
        
        main_box.add(sub_tabs)
        
        return main_box

    def on_audio_switch(self, widget):
        """Gestion du switch audio"""
        if widget.value:
            self.video_mode.value = False

    def on_video_switch(self, widget):
        """Gestion du switch vidéo"""
        if widget.value:
            self.audio_mode.value = False

    def _create_audio_tab(self):
        box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # FFmpegExtractAudio options
        box.add(toga.Label('Format Audio'))
        self.audio_format_select = toga.Selection(items=['mp3', 'wav', 'aac'])
        box.add(self.audio_format_select)
        
        box.add(toga.Label('Qualité Audio'))
        self.audio_quality_select = toga.Selection(items=['192', '256', '320'])
        box.add(self.audio_quality_select)
        
        box.add(toga.Switch('Garder la vidéo', style=Pack(padding=5)))
        
        return box

    def _create_video_tab(self):
        box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # Options vidéo
        box.add(toga.Label('Format Vidéo'))
        box.add(toga.Selection(items=['mp4', 'webm', 'mkv']))
        
        box.add(toga.Switch('Télécharger miniature', style=Pack(padding=5)))
        box.add(toga.Switch('Télécharger sous-titres', style=Pack(padding=5)))
        
        box.add(toga.Label('Langues sous-titres'))
        box.add(toga.Selection(items=['fr', 'en', 'es']))

        # Section Chapitres
        chapters_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        chapters_box.add(toga.Label('Options des chapitres', style=Pack(font_weight='bold')))
        
        self.split_chapters = toga.Switch('Séparer par chapitres', value=False)
        self.remove_chapters = toga.Switch('Supprimer les chapitres', value=False)
        
        chapters_box.add(self.split_chapters)
        chapters_box.add(self.remove_chapters)
        
        box.add(chapters_box)
        
        # Post-processeurs vidéo
        self.embed_subs_switch = toga.Switch('Intégrer les sous-titres')
        self.embed_thumb_switch = toga.Switch('Intégrer la miniature')
        self.merge_files_switch = toga.Switch('Fusionner les fichiers')
        
        box.add(self.embed_subs_switch)
        box.add(self.embed_thumb_switch)
        box.add(self.merge_files_switch)
        
        return box

    def _create_advanced_tab(self):
        box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # Section Authentification basique
        auth_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        auth_box.add(toga.Label('Authentification', style=Pack(font_weight='bold')))
        self.username_input = toga.TextInput(placeholder='Nom d\'utilisateur')
        self.password_input = toga.PasswordInput(placeholder='Mot de passe')#, password=True)
        self.video_password_input = toga.PasswordInput(placeholder='Mot de passe vidéo')
        auth_box.add(self.username_input)
        auth_box.add(self.password_input)
        auth_box.add(self.video_password_input)
        
        # Section Netrc
        netrc_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        netrc_box.add(toga.Label('Configuration Netrc', style=Pack(font_weight='bold')))
        self.use_netrc_switch = toga.Switch('Utiliser Netrc')
        self.netrc_location_input = toga.TextInput(placeholder='Chemin fichier Netrc')
        netrc_box.add(self.use_netrc_switch)
        netrc_box.add(self.netrc_location_input)

        box.add(auth_box)
        box.add(netrc_box)

        
        # Adobe Pass section
        adobe_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        adobe_box.add(toga.Label('Adobe Pass', style=Pack(font_weight='bold')))
        self.ap_mso_input = toga.TextInput(placeholder='Adobe Pass MSO')
        self.ap_username_input = toga.TextInput(placeholder='Adobe Pass Username')
        self.ap_password_input = toga.PasswordInput(placeholder='Adobe Pass Password')
        adobe_box.add(self.ap_mso_input)
        adobe_box.add(self.ap_username_input)
        adobe_box.add(self.ap_password_input)
        
        # Commande Netrc
        netrc_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.netrc_cmd_input = toga.TextInput(placeholder='Commande credentials')
        netrc_box.add(self.netrc_cmd_input)
        
        box.add(adobe_box)
        box.add(netrc_box)
        return box

def main():
    return SettingsApp('Settings', 'org.beeware.settingsapp')

if __name__ == '__main__':
    main().main_loop()