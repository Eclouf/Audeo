# -*- encoding:utf-8 -*-

import toga

from pathlib import Path
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from yt_dlp.postprocessor import MetadataParserPP

from .get_settings import GetSettings

class SettingsWindow:
    instance = None
    
    def __init__(self, parent_app):
        
        SettingsWindow.instance = self
        self.get_settings = GetSettings(self)
        self.app = parent_app
        self.create_window()

    def create_window(self):
    
        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Section choix audio/vidéo
        mode_box = toga.Box(style=Pack(direction=ROW, padding=5))
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
        
        # Créer les contenus des onglets
        general_box = self._create_general_tab()
        audio_box = self._create_audio_tab()
        video_box = self._create_video_tab()
        reseau_box = self._create_reseau_tab()
        advanced_box = self._create_advanced_tab()
        
        # Créer l'OptionContainer et ajouter les onglets
        self.option_container = toga.OptionContainer(style=Pack(flex=1))
        self.option_container.content.append('Général', general_box)
        self.option_container.content.append('Audio', audio_box)
        self.option_container.content.append('Vidéo', video_box)
        self.option_container.content.append('Réseau', reseau_box)
        self.option_container.content.append('Avancé', advanced_box)
        
        # Boutons
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        save_button = toga.Button(
            'Sauvegarder',
            on_press=self.save_config,
            style=Pack(padding=5)
        )
        
        close_button = toga.Button(
            'Fermer',
            on_press=self.close_window,
            style=Pack(padding=5)
        )
        
        buttons_box.add(save_button)
        buttons_box.add(close_button)
        
        main_box.add(self.option_container)
        main_box.add(buttons_box)
        
        self.settings()
        
        self.window = toga.Window(title="Paramètres")
        self.window.content = main_box
        self.app.windows.add(self.window)
        self.window.show()

    def settings(self):
        self.get_settings.settings()
        
    def save_settings(self):
        self.get_settings.save_settings()
    
    def get_config(self):
        yt_dlp_dic = self.get_settings.get_config()
        return yt_dlp_dic

    async def save_config(self, widget):
        """Sauvegarde la configuration et met à jour l'application principale"""
        
        config = self.get_config()
        # Mettre à jour les options de l'application principale
        self.app.update_options(config)
        # Afficher un message de confirmation
        dialog = toga.InfoDialog(
            'Succès',
            'Les paramètres ont bien été sauvegardés'
        )
        await toga.Window.dialog(self.app.main_window, dialog)

    def close_window(self, widget):
        """Ferme la fenêtre des paramètres"""
        
        self.save_settings()
        self.window.close()

    def _create_general_tab(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # Conteneur principal
        #main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))

        # Créer un OptionContainer pour les sous-onglets
        sub_tabs = toga.OptionContainer(style=Pack(flex=1))
        
        # 1. Sous-onglet Format
        format_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        format_box.add(toga.Label('Format de nom de fichier', style=Pack(font_weight='bold')))
        
        # Extension préférée
        ext_label = toga.Label('Extension préférée:')
        self.preferred_ext_input = toga.Selection(
            items=['mp4', 'mkv', 'webm', 'avi'], #bestaudio[ext=alac]/bestaudio[ext=flac]/bestaudio[ext=wav]/bestaudio[ext=aiff]/bestaudio[ext=mqa]/bestaudio[ext=aac]/bestaudio[ext=m4a]/bestaudio[ext=opus]/bestaudio/best
            style=Pack(padding=(0, 5), padding_top=5, padding_bottom=5)
        )
        ext_final_label = toga.Label('Extension finale:')
        self.final_ext_input = toga.TextInput(
            placeholder='Extension finale',
            value='mp4',
            style=Pack(padding=(0, 5), padding_top=5, padding_bottom=5)
        )
        format_box.add(ext_label)
        format_box.add(self.preferred_ext_input)
        format_box.add(ext_final_label)
        format_box.add(self.final_ext_input)
        
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
        format_help = toga.MultilineTextInput(readonly=True, value="""\
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
        """.strip(),
        style=Pack(flex=1))
        
        format_box.add(self.template_select)
        format_box.add(format_help)
        
        # 2. Sous-onglet Métadonnées
        metadata_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        metadata_box.add(toga.Label('Options des métadonnées', style=Pack(font_weight='bold')))

        self.write_metadata = toga.Switch('Inclure les métadonnées')
        self.write_description = toga.Switch('Sauvegarder la description')
        self.write_info_json = toga.Switch('Sauvegarder le fichier info.json')
        self.thumb_switch_1 = toga.Switch('Sauvegarder les miniatures')
        self.square = toga.Switch('Miniatures carrées', style=Pack(padding=(0, 5)))
        
        # Metadata Parser
        metadata_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        metadata_box.add(toga.Label('Analyse des métadonnées', style=Pack(font_weight='bold')))
        self.metadata_parser_switch = toga.Switch('Activer l\'analyse des métadonnées', on_change=self.metadata_parser_change)
        self.metadata_field = toga.TextInput(placeholder='Champ (ex: playlist_index)', value='playlist_index; __last_playlist_index', style=Pack(padding=(0, 5)))
        self.metadata_pattern = toga.TextInput(placeholder='Pattern regex (ex: (?P<track_number>.+))', value='(?P<track_number>.+); (?P<total_tracks>.+)', style=Pack(padding=(0, 5)))

        self.metadata_field.enabled = False
        self.metadata_pattern.enabled = False
        
        metadata_box.add(self.write_metadata)
        metadata_box.add(self.write_description)
        metadata_box.add(self.write_info_json)
        metadata_box.add(self.thumb_switch_1)
        metadata_box.add(self.square)
        
        metadata_box.add(self.metadata_parser_switch)
        metadata_box.add(toga.Label('Champ à analyser'))
        metadata_box.add(self.metadata_field)
        metadata_box.add(toga.Label('Pattern regex'))
        metadata_box.add(self.metadata_pattern)
        
        # 3. Sous-onglet Playlists
        playlist_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        self.noplaylist_switch = toga.Switch('Ignorer les playlists')
        self.playlist_items = toga.TextInput(placeholder='1-5,10', style=Pack(padding=(0, 5)))
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
        scroll_box = toga.ScrollContainer(style=Pack(direction=COLUMN, padding=5))
        box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        scroll_box.content = box
        
        # Options vidéo
        box.add(toga.Label('Format Vidéo'))
        self.video_format_switch = toga.Switch('Choisir un format:',on_change=self.video_format_change, style=Pack(padding=(0, 5)))
        self.video_format_select = toga.Selection(items=['mp4', 'webm', 'mkv', 'avi', 'mov', 'wmv'])
        self.video_format_select.enabled = False
        box.add(self.video_format_switch,self.video_format_select)
        
        # Miniatures
        thumbnails_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        thumbnails_box.add(toga.Label('Options des miniatures', style=Pack(font_weight='bold')))
        self.thumb_switch = toga.Switch('Télécharger miniature', style=Pack(padding=(0, 5)))
        self.thumb_format = toga.Selection(
            items=['jpg', 'png', 'webp'],
            style=Pack(padding=(0, 5))
        )
        thumbnails_box.add(self.thumb_switch)
        thumbnails_box.add(self.thumb_format)
        
        # Sous-titres
        subtitles_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        subtitles_box.add(toga.Label('Options des sous-titres', style=Pack(font_weight='bold')))
        self.embed_subs_switch = toga.Switch('Intégrer les sous-titres', style=Pack(padding=(0, 5)))
        self.subs_format = toga.Selection(
            items=['srt', 'vtt', 'ass'],
            style=Pack(padding=(0, 5))
        )
        subtitles_box.add(self.embed_subs_switch)
        subtitles_box.add(self.subs_format)
        
        # Chapitres
        chapters_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        chapters_box.add(toga.Label('Options des chapitres', style=Pack(font_weight='bold')))
        self.split_chapters = toga.Switch('Séparer par chapitres', style=Pack(padding=(0, 5)))
        self.add_sponsorblock = toga.Switch('Ajouter infojson', style=Pack(padding=(0, 5)))
        chapters_box.add(self.split_chapters)
        chapters_box.add(self.add_sponsorblock)
        
        # Filigrane et texte
        overlay_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        overlay_box.add(toga.Label('Filigrane et texte', style=Pack(font_weight='bold')))
        self.watermark_file = toga.TextInput(placeholder='Chemin du filigrane', style=Pack(padding=(0, 5)))
        self.watermark_position = toga.Selection(
            items=['top-right', 'top-left', 'bottom-right', 'bottom-left', 'center'],
            style=Pack(padding=(0, 5))
        )
        self.overlay_text = toga.TextInput(placeholder='Texte à superposer', style=Pack(padding=(0, 5)))
        self.overlay_position = toga.Selection(
            items=['top-right', 'top-left', 'bottom-right', 'bottom-left', 'center'],
            style=Pack(padding=(0, 5))
        )
        overlay_box.add(self.watermark_file)
        overlay_box.add(self.watermark_position)
        overlay_box.add(self.overlay_text)
        overlay_box.add(self.overlay_position)
        
        # Extraction d'images
        frames_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        frames_box.add(toga.Label('Extraction d\'images', style=Pack(font_weight='bold')))
        self.extract_frames = toga.Switch('Extraire des images', style=Pack(padding=(0, 5)))
        self.frames_timestamps = toga.TextInput(placeholder='Timestamps (ex: 10,20,30)', style=Pack(padding=(0, 5)))
        self.frames_output = toga.TextInput(placeholder='Dossier de sortie', style=Pack(padding=(0, 5)))
        frames_box.add(self.extract_frames)
        frames_box.add(self.frames_timestamps)
        frames_box.add(self.frames_output)
        
        # Post-processeurs vidéo
        self.merge_files_switch = toga.Switch('Fusionner les fichiers', style=Pack(padding=(0, 5)))
        self.fixup_m3u8_switch = toga.Switch('Corriger M3U8', on_change=self.on_fixup_m3u8_switch, style=Pack(padding=(0, 5)))
        self.fixup_m3u8 = toga.Selection(
            items=['never', 'warn', 'detect_or_warn'],
            style=Pack(padding=(5)),
            enabled=False
        )
        
        # Ajouter tous les widgets
        box.add(thumbnails_box)
        box.add(subtitles_box)
        box.add(chapters_box)
        box.add(overlay_box)
        box.add(frames_box)
        box.add(self.merge_files_switch)
        box.add(toga.Label('Correction M3U8', style=Pack(font_weight='bold')))
        box.add(self.fixup_m3u8_switch)
        box.add(self.fixup_m3u8)
        
        return scroll_box
    
    def _create_reseau_tab(self):
        box_scroll = toga.ScrollContainer(style=Pack(direction=COLUMN, padding=5))
        box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        box_scroll.content = box
        
        # Section General
        general_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        general_box.add(toga.Label('General', style=Pack(font_weight='bold')))
        self.legacyserverconnect = toga.Switch('Autoriser la connexion HTTPS aux serveurs sans renégociation sécurisée.', style=Pack(padding=(0, 5)))
        self.prefer_insecure = toga.Switch('Utiliser HTTP au lieu de HTTPS.', style=Pack(padding=(0, 5)))
        self.enable_file_urls = toga.Switch('Activer les URLs file://.', style=Pack(padding=(0, 5)))
        general_box.add(self.prefer_insecure)
        general_box.add(self.enable_file_urls)
        general_box.add(self.legacyserverconnect)
        box.add(general_box)
        
        # Connection proxy
        proxy_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        proxy_box.add(toga.Label('Connection proxy', style=Pack(font_weight='bold')))
        self.proxy_switch = toga.Switch('Connection proxy', on_change=self.on_proxy_switch)
        self.proxy = toga.TextInput(placeholder='URL du proxy ex: http://proxy.example.com:8080', style=Pack(padding=(0, 5)))
        self.geo_verification_proxy = toga.TextInput(placeholder='geo verification proxy ex: http://geo-proxy.example.com:8080', style=Pack(padding=(0, 5)))
        self.proxy.enabled = False
        self.geo_verification_proxy.enabled = False
        
        proxy_box.add(self.proxy_switch)
        proxy_box.add(self.proxy)
        proxy_box.add(self.geo_verification_proxy)
        
        box.add(proxy_box)
        
        # Contourner les restrictions géographiques.
        geo_bypass_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        geo_bypass_box.add(toga.Label('Restrictions géographiques', style=Pack(font_weight='bold')))
        self.geo_bypass_switch = toga.Switch('Contourner les restrictions géographiques', on_change=self.on_geo_bypass_switch)
        self.geo_bypass_country = toga.Selection(items=['FR', 'US', 'CA'], style=Pack(padding=(5)))
        self.geo_bypass_ip_block = toga.TextInput(placeholder='IP block', style=Pack(padding=(0, 5)))
        self.geo_bypass_country.enabled = False
        self.geo_bypass_ip_block.enabled = False
        
        geo_bypass_box.add(self.geo_bypass_switch)
        geo_bypass_box.add(self.geo_bypass_country)
        geo_bypass_box.add(self.geo_bypass_ip_block)
        
        box.add(geo_bypass_box)
        
        # SSL
        ssl_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        ssl_box.add(toga.Label('SSL', style=Pack(font_weight='bold')))
        self.ssl_switch = toga.Switch('SSL', on_change=self.on_ssl_switch)
        self.nocheckcertificate = toga.Switch('Ignorer les certificats SSL.', style=Pack(padding=(0, 5)))
        self.client_certificate = toga.TextInput(placeholder='client.pem', style=Pack(padding=(0, 5)))
        self.client_certificate_key = toga.TextInput(placeholder='client-key.pem', style=Pack(padding=(0, 5)))
        self.client_certificate_password = toga.TextInput(placeholder='password', style=Pack(padding=(0, 5)))
        
        self.nocheckcertificate.enabled = False
        self.client_certificate.enabled = False
        self.client_certificate_key.enabled = False
        self.client_certificate_password.enabled = False
        
        ssl_box.add(self.ssl_switch)
        ssl_box.add(self.nocheckcertificate)
        ssl_box.add(self.client_certificate)
        ssl_box.add(self.client_certificate_key)
        ssl_box.add(self.client_certificate_password)
        
        box.add(ssl_box)
        
        return box_scroll

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
        
        # Section Authentification par cookie
        cookie_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        cookie_box.add(toga.Label('Cookie', style=Pack(font_weight='bold')))
        self.cookie_switch = toga.Switch('Utiliser Cookie', on_change=self.on_cookie_switch)
        self.cookie_input = toga.Selection(
            items=['chrome', 'firefox', 'edge', 'opera', 'safari', 'brave'],
            style=Pack(padding=(0, 5))
        )
        self.cookie_input.enabled = False
        cookie_box.add(self.cookie_switch)
        cookie_box.add(self.cookie_input)
        box.add(cookie_box)
        
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
    
    def video_format_change(self, widget):
        if widget.value:
            self.video_format_select.enabled = True
        else:
            self.video_format_select.enabled = False
            self.video_format_select.value = None
    
    def on_fixup_m3u8_switch(self, widget):
        if widget.value:
            self.fixup_m3u8.enabled = True
        else:
            self.fixup_m3u8.enabled = False
            
    def metadata_parser_change(self, widget):
        if widget.value:
            self.metadata_field.enabled = True
            self.metadata_field.read_only = False
            self.metadata_pattern.enabled = True
            self.metadata_pattern.read_only = False
        else:
            self.metadata_field.enabled = False
            self.metadata_field.read_only = True
            self.metadata_field.value = None
            self.metadata_pattern.enabled = False
            self.metadata_pattern.read_only = True
            self.metadata_pattern.value = None
            
    def on_proxy_switch(self, widget):
        if widget.value:
            self.proxy.enabled = True
            self.geo_verification_proxy.enabled = True
            self.geo_verification_proxy.read_only = False
        else:
            self.proxy.enabled = False
            self.proxy.value = None
            self.geo_verification_proxy.enabled = False
            self.geo_verification_proxy.read_only = True
            self.geo_verification_proxy.value = None
            
    def on_geo_bypass_switch(self, widget):
        if widget.value:
            self.geo_bypass_country.enabled = True
            self.geo_bypass_country.read_only = False
            
            self.geo_bypass_ip_block.enabled = True
            self.geo_bypass_ip_block.read_only = False
        else:
            self.geo_bypass_country.enabled = False
            self.geo_bypass_country.read_only = True
            self.geo_bypass_country.value = None
            
            self.geo_bypass_ip_block.enabled = False
            
    def on_ssl_switch(self, widget):
        if widget.value:
            self.nocheckcertificate.enabled = True
            self.client_certificate.enabled = True
            self.client_certificate_key.enabled = True
            self.client_certificate_password.enabled = True
            
        else:
            self.nocheckcertificate.enabled = False
            self.nocheckcertificate.value = False
            
            self.client_certificate.enabled = False
            self.client_certificate.value = None
            
            self.client_certificate_key.enabled = False
            self.client_certificate_key.value = None
            
            self.client_certificate_password.enabled = False
            self.client_certificate_password.value = None
        
    def on_cookie_switch(self, widget):
        if widget.value:
            self.cookie_input.enabled = True
        else:
            self.cookie_input.enabled = False
            
            