# -*- encoding:utf-8 -*-

import re
import json

from pathlib import Path

EXT_TO_OUT_FORMATS = {
    'aac': 'adts',
    'flac': 'flac',
    'm4a': 'ipod',
    'mka': 'matroska',
    'mkv': 'matroska',
    'mpg': 'mpeg',
    'ogv': 'ogg',
    'ts': 'mpegts',
    'wma': 'asf',
    'wmv': 'asf',
    'weba': 'webm',
    'vtt': 'webvtt',
}

ACODECS = {
    # name: (ext, encoder, opts)
    'mp3': ('mp3', 'libmp3lame', ()),
    'aac': ('m4a', 'aac', ('-f', 'adts')),
    'm4a': ('m4a', 'aac', ('-bsf:a', 'aac_adtstoasc')),
    'opus': ('opus', 'libopus', ()),
    'vorbis': ('ogg', 'libvorbis', ()),
    'flac': ('flac', 'flac', ()),
    'alac': ('m4a', None, ('-acodec', 'alac')),
    'wav': ('wav', None, ('-f', 'wav')),
}

def create_mapping_re(supported):
    return re.compile(r'{0}(?:/{0})*$'.format(r'(?:\s*\w+\s*>)?\s*(?:{})\s*'.format('|'.join(supported))))

def resolve_mapping(source, mapping):
    """
    Get corresponding item from a mapping string like 'A>B/C>D/E'
    @returns    (target, error_message)
    """
    for pair in mapping.lower().split('/'):
        kv = pair.split('>', 1)
        if len(kv) == 1 or kv[0].strip() == source:
            target = kv[-1].strip()
            if target == source:
                return target, f'already is in target format {source}'
            return target, None
    return None, f'could not find a mapping for {source}'


class GetSettings():
    def __init__(self, instance):
        self.gui = instance
        
    def get_config(self):
        """Retourne la configuration formatée directement pour yt-dlp"""
        
        # Initialiser la liste des post-processeurs
        postprocessors = []
        
        if self.gui.video_format_select.value:
            format_video = self.gui.video_format_select.value
        else:
            format_video = 'bestvideo[ext=mkv]/bestvideo[ext=mp4]/bestvideo[ext=webm]/bestvideo[ext=flv]/bestvideo[ext=mov]/bestvideo[ext=avi]/bestvideo[ext=mpg]/bestvideo[ext=3gp]/bestvideo[ext=rm]/bestvideo[ext=rmvb]/bestvideo[ext=mpeg]/bestvideo[ext=m2ts]/bestvideo/best'
        
        # Configuration principale
        config = {
            # Format de sortie
            'outtmpl': self.gui.template_select.value,
            
            # Options de base yt-dlp
            'format': 'bestaudio[ext=alac]/bestaudio[ext=flac]/bestaudio[ext=wav]/bestaudio[ext=aiff]/bestaudio[ext=mqa]/bestaudio[ext=aac]/bestaudio[ext=m4a]/bestaudio[ext=opus]/bestaudio/best' if self.gui.audio_mode.value else format_video,
            'writethumbnail': self.gui.thumb_switch.value,
            'writeinfojson': self.gui.write_info_json.value,
            'writedescription': self.gui.write_description.value,
            
            # Options générales
            'verbose': self.gui.verbose_switch.value,
            'quiet': self.gui.quiet_switch.value,
            'ignoreerrors': 'only_download',
            
            # Options de playlist
            'noplaylist': self.gui.noplaylist_switch.value,
            'playlist_items': self.gui.playlist_items.value if self.gui.playlist_items.value else None,

            # Authentification
            'username': self.gui.username_input.value if self.gui.username_input.value else None,
            'password': self.gui.password_input.value if self.gui.password_input.value else None,
            'videopassword': self.gui.video_password_input.value if self.gui.video_password_input.value else None,
            
            # Options Netrc
            'usenetrc': self.gui.use_netrc_switch.value,
            'netrc_location': self.gui.netrc_location_input.value if self.gui.netrc_location_input.value else None,
            
            # Adobe Pass
            'ap_mso': self.gui.ap_mso_input.value if self.gui.ap_mso_input.value else None,
            'ap_username': self.gui.ap_username_input.value if self.gui.ap_username_input.value else None,
            'ap_password': self.gui.ap_password_input.value if self.gui.ap_password_input.value else None,
            
            # Reseau:
            'legacyserverconnect': self.gui.legacyserverconnect.value if self.gui.legacyserverconnect.value else None,
            'nocheckcertificate': self.gui.nocheckcertificate.value if self.gui.nocheckcertificate.value else None,
            'client_certificate': self.gui.client_certificate.value if self.gui.client_certificate.value else None,
            'client_certificate_key': self.gui.client_certificate_key.value if self.gui.client_certificate_key.value else None,
            'client_certificate_password': self.gui.client_certificate_password.value if self.gui.client_certificate_password.value else None,
            'enable_file_urls': self.gui.enable_file_urls.value if self.gui.enable_file_urls.value else None,
            'prefer_insecure': self.gui.prefer_insecure.value if self.gui.prefer_insecure.value else None,
            
            # Connection proxy
            'proxy': self.gui.proxy.value if self.gui.proxy.value else None,
            'geo_verification_proxy': self.gui.geo_verification_proxy.value if self.gui.geo_verification_proxy.value else None,
            
        }
        # Audio post-processor
        if self.gui.audio_mode.value:
            audio_opts = {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.gui.audio_format_select.value,
                'preferredquality': self.gui.audio_quality_select.value,
                'nopostoverwrites': False
            }
            # Ne pas inclure les options supplémentaires car elles ne sont pas supportées par FFmpegExtractAudioPP
            postprocessors.append(audio_opts)

        # Metadata post-processor
        if self.gui.write_metadata.value:
            postprocessors.append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
                'add_chapters': self.gui.split_chapters.value,
                'add_infojson': 'if_exists'
            })

        # Subtitle post-processor
        if self.gui.embed_subs_switch.value:
            if hasattr(self.gui, 'subs_format') and self.gui.subs_format.value:
                postprocessors.append({
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': self.gui.subs_format.value
                })
            postprocessors.append({
                'key': 'FFmpegEmbedSubtitle',
                'already_have_subtitle': False
            })

        # Thumbnail post-processor
        if self.gui.thumb_switch.value:
            if hasattr(self.gui, 'thumb_format') and self.gui.thumb_format.value:
                postprocessors.append({
                    'key': 'FFmpegThumbnailsConvertor',
                    'format': self.gui.thumb_format.value
                })
        if self.gui.thumb_switch_1.value:
            postprocessors.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
                'square': self.gui.square.value
            })

        # Merger post-processor
        if self.gui.merge_files_switch.value:
            postprocessors.append({
                'key': 'FFmpegMerger',
                'only_merge': True
            })

        # M3U8 Fixup post-processor
        if self.gui.fixup_m3u8_switch.value:
            if hasattr(self.gui, 'fixup_m3u8') and self.gui.fixup_m3u8.value:
                postprocessors.append({
                    'key': 'FFmpegFixupM3u8',
                    'fixup': self.gui.fixup_m3u8.value
                })

        # Timestamp Fixup post-processor
        if hasattr(self.gui, 'fixup_timestamp') and self.gui.fixup_timestamp.value:
            postprocessors.append({
                'key': 'FFmpegFixupTimestamp',
                'trim': float(self.gui.fixup_timestamp_trim.value or 0.001)
            })

        # Video format post-processor
        if not self.gui.audio_mode.value and self.gui.preferred_ext_input.value:
            target_format, error = resolve_mapping(
                self.gui.preferred_ext_input.value.lower(),
                EXT_TO_OUT_FORMATS.get(self.gui.preferred_ext_input.value.lower(), self.gui.preferred_ext_input.value)
            )
            if not error:
                postprocessors.append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': target_format
                })
        
        # Metadata parser
        if self.gui.metadata_parser_switch.value:
            postprocessors.append({
                'key': 'MetadataParser',
                'when': 'pre_process',
                'actions': [f'{self.gui.metadata_field.value}', f'{self.gui.metadata_pattern.value}']
            })
            
        # Contourner les restrictions géographiques.
        if self.gui.geo_bypass_switch.value:
            config.update({
                'geo_bypass': True,
                'geo_bypass_country': self.gui.geo_bypass_country.value if self.gui.geo_bypass_country.value else None,
                'geo_bypass_ip_block': self.gui.geo_bypass_ip_block.value if self.gui.geo_bypass_ip_block.value else None,})
            
        if self.gui.cookie_switch.value:
            config.update({
                'cookiesfrombrowser': (self.gui.cookie_input.value, 'default')
            })

        config.update({
            # Post-processeurs
            'postprocessors': postprocessors,
        })
        
        # Nettoyer les options None
        return {k: v for k, v in config.items() if v is not None}
    
    def settings(self):
        """Charge les paramètres depuis le fichier settings.json"""
        
        try:
            settings_path = Path(__file__).parent / 'settings.json'
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    
                # Configuration générale
                self.gui.audio_mode.value = settings.get('audio_mode', True)
                self.gui.video_mode.value = settings.get('video_mode', False)
                self.gui.template_select.value = settings.get('template', '%(title)s.%(ext)s')
                
                # Format audio/vidéo
                if hasattr(self.gui, 'preferred_ext_input'):
                    self.gui.preferred_ext_input.value = settings.get('preferred_ext', '')
                if hasattr(self.gui, 'audio_format_select'):    
                    self.gui.audio_format_select.value = settings.get('audio_format', 'mp3')
                if hasattr(self.gui, 'audio_quality_select'):
                    self.gui.audio_quality_select.value = settings.get('audio_quality', '192')
                if hasattr(self.gui, 'video_format_select'):
                    self.gui.video_format_select.value = settings.get('video_format', '')
                
                # Métadonnées
                self.gui.write_metadata.value = settings.get('write_metadata', False)
                self.gui.write_description.value = settings.get('write_description', False)
                self.gui.write_info_json.value = settings.get('write_info_json', False)
                self.gui.thumb_switch.value = settings.get('thumb_switch', False)
                self.gui.thumb_switch_1.value = settings.get('thumb_switch_1', False)
                self.gui.square.value = settings.get('square', False)
                
                # Metadata Parser
                self.gui.metadata_parser_switch.value = settings.get('metadata_parser_switch', False)
                self.gui.metadata_field.value = settings.get('metadata_field', '')
                self.gui.metadata_pattern.value = settings.get('metadata_pattern', '')
                
                # Playlists
                self.gui.noplaylist_switch.value = settings.get('noplaylist_switch', False)
                self.gui.playlist_items.value = settings.get('playlist_items', '')
                
                # Verbosité
                self.gui.verbose_switch.value = settings.get('verbose_switch', False)
                self.gui.quiet_switch.value = settings.get('quiet_switch', False)
                
                # Réseau
                self.gui.proxy_switch.value = settings.get('proxy_switch', False)
                self.gui.proxy.value = settings.get('proxy', '')
                self.gui.geo_verification_proxy.value = settings.get('geo_verification_proxy', '')
                
                # Geo bypass
                self.gui.geo_bypass_switch.value = settings.get('geo_bypass_switch', False)
                self.gui.geo_bypass_country.value = settings.get('geo_bypass_country', '')
                self.gui.geo_bypass_ip_block.value = settings.get('geo_bypass_ip_block', '')
                
                # SSL
                self.gui.ssl_switch.value = settings.get('ssl_switch', False)
                self.gui.nocheckcertificate.value = settings.get('nocheckcertificate', False)
                self.gui.client_certificate.value = settings.get('client_certificate', '')
                self.gui.client_certificate_key.value = settings.get('client_certificate_key', '')
                self.gui.client_certificate_password.value = settings.get('client_certificate_password', '')
                
                # Auth
                self.gui.username_input.value = settings.get('username', '')
                self.gui.password_input.value = settings.get('password', '') 
                self.gui.video_password_input.value = settings.get('videopassword', '')
                
                # Cookies
                self.gui.cookie_switch.value = settings.get('cookie_switch', False)
                self.gui.cookie_input.value = settings.get('cookie_input', '')
                
                # Netrc
                self.gui.use_netrc_switch.value = settings.get('use_netrc_switch', False)
                self.gui.netrc_location_input.value = settings.get('netrc_location', '')
                
                # Adobe Pass
                self.gui.ap_mso_input.value = settings.get('ap_mso', '')
                self.gui.ap_username_input.value = settings.get('ap_username', '')
                self.gui.ap_password_input.value = settings.get('ap_password', '')
                
        except Exception as e:
            print(f"Erreur lors du chargement des paramètres: {e}")
            
    def save_settings(self):
        """Sauvegarde tous les paramètres dans le fichier settings.json"""
        
        settings = {
            # Configuration générale
            'audio_mode': self.gui.audio_mode.value,
            'video_mode': self.gui.video_mode.value,
            'template': self.gui.template_select.value,
            
            # Format audio/vidéo 
            'preferred_ext': self.gui.preferred_ext_input.value if hasattr(self.gui, 'preferred_ext_input') else None,
            'audio_format': self.gui.audio_format_select.value if hasattr(self.gui, 'audio_format_select') else None,
            'audio_quality': self.gui.audio_quality_select.value if hasattr(self.gui, 'audio_quality_select') else None,
            'video_format': self.gui.video_format_select.value if hasattr(self.gui, 'video_format_select') else None,
            
            # Métadonnées
            'write_metadata': self.gui.write_metadata.value,
            'write_description': self.gui.write_description.value,
            'write_info_json': self.gui.write_info_json.value,
            'thumb_switch': self.gui.thumb_switch.value, 
            'thumb_switch_1': self.gui.thumb_switch_1.value,
            'square': self.gui.square.value,
            'thumb_format': self.gui.thumb_format.value if hasattr(self.gui, 'thumb_format') else None,
            
            # Metadata Parser
            'metadata_parser_switch': self.gui.metadata_parser_switch.value,
            'metadata_field': self.gui.metadata_field.value,
            'metadata_pattern': self.gui.metadata_pattern.value,
            
            # Sous-titres
            'embed_subs_switch': self.gui.embed_subs_switch.value if hasattr(self.gui, 'embed_subs_switch') else None,
            'subs_format': self.gui.subs_format.value if hasattr(self.gui, 'subs_format') else None,
            
            # Chapitres
            'split_chapters': self.gui.split_chapters.value if hasattr(self.gui, 'split_chapters') else None,
            'add_sponsorblock': self.gui.add_sponsorblock.value if hasattr(self.gui, 'add_sponsorblock') else None,
            
            # Filigrane et texte
            'watermark_file': self.gui.watermark_file.value if hasattr(self.gui, 'watermark_file') else None,
            'watermark_position': self.gui.watermark_position.value if hasattr(self.gui, 'watermark_position') else None,
            'overlay_text': self.gui.overlay_text.value if hasattr(self.gui, 'overlay_text') else None,
            'overlay_position': self.gui.overlay_position.value if hasattr(self.gui, 'overlay_position') else None,
            
            # Extraction d'images
            'extract_frames': self.gui.extract_frames.value if hasattr(self.gui, 'extract_frames') else None,
            'frames_timestamps': self.gui.frames_timestamps.value if hasattr(self.gui, 'frames_timestamps') else None,
            'frames_output': self.gui.frames_output.value if hasattr(self.gui, 'frames_output') else None,
            
            # Playlists
            'noplaylist_switch': self.gui.noplaylist_switch.value,
            'playlist_items': self.gui.playlist_items.value,
            
            # Options de verbosité
            'verbose_switch': self.gui.verbose_switch.value,
            'quiet_switch': self.gui.quiet_switch.value,
            
            # Options réseau
            'legacyserverconnect': self.gui.legacyserverconnect.value if hasattr(self.gui, 'legacyserverconnect') else None,
            'prefer_insecure': self.gui.prefer_insecure.value if hasattr(self.gui, 'prefer_insecure') else None,
            'enable_file_urls': self.gui.enable_file_urls.value if hasattr(self.gui, 'enable_file_urls') else None,
            
            # Proxy
            'proxy_switch': self.gui.proxy_switch.value,
            'proxy': self.gui.proxy.value,
            'geo_verification_proxy': self.gui.geo_verification_proxy.value,
            
            # Geo bypass
            'geo_bypass_switch': self.gui.geo_bypass_switch.value,
            'geo_bypass_country': self.gui.geo_bypass_country.value,
            'geo_bypass_ip_block': self.gui.geo_bypass_ip_block.value,
            
            # SSL
            'ssl_switch': self.gui.ssl_switch.value,
            'nocheckcertificate': self.gui.nocheckcertificate.value,
            'client_certificate': self.gui.client_certificate.value,
            'client_certificate_key': self.gui.client_certificate_key.value,
            'client_certificate_password': self.gui.client_certificate_password.value,
            
            # Authentification
            'username': self.gui.username_input.value,
            'password': self.gui.password_input.value,
            'videopassword': self.gui.video_password_input.value,
            
            # Cookies
            'cookie_switch': self.gui.cookie_switch.value,
            'cookie_input': self.gui.cookie_input.value,
            
            # Netrc
            'use_netrc_switch': self.gui.use_netrc_switch.value,
            'netrc_location': self.gui.netrc_location_input.value,
            'netrc_cmd': self.gui.netrc_cmd_input.value if hasattr(self.gui, 'netrc_cmd_input') else None,
            
            # Adobe Pass
            'ap_mso': self.gui.ap_mso_input.value,
            'ap_username': self.gui.ap_username_input.value,
            'ap_password': self.gui.ap_password_input.value,
            
            # Post-processeurs
            'merge_files_switch': self.gui.merge_files_switch.value if hasattr(self.gui, 'merge_files_switch') else None,
            'fixup_m3u8_switch': self.gui.fixup_m3u8_switch.value if hasattr(self.gui, 'fixup_m3u8_switch') else None,
            'fixup_m3u8': self.gui.fixup_m3u8.value if hasattr(self.gui, 'fixup_m3u8') else None,
        }

        # Nettoyer les valeurs None
        settings = {k: v for k, v in settings.items() if v is not None}

        try:
            settings_path = Path(__file__).parent / 'settings.json'
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres: {e}")