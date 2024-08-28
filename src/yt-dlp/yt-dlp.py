# -*- encoding:utf-8 -*-
import yt_dlp
from yt_dlp.postprocessor import MetadataParserPP

class MyLogger:
    def debug(self, msg):
        print(msg)
    def warning(self, msg):
        print(msg)
    def error(self, msg):
        print(msg)

class YtDlpDownloader():
    
    def __init__(self, url):
        self.url = url
        
    def on_progress(self, d):
        print("progress")
        if d['status'] == 'downloading':
            print(f"Téléchargement en cours : {d['_percent_str']}")

        
    def download(self, options:dict, path:str, path_ffmpeg):
        ydl_opts = {
            'format': options.get('format', 'bestvideo+bestaudio/best'),
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'writethumbnail': options['add_thumbnails'],
            'progress_hooks': [self.on_progress],
            'ffmpeg_location':path_ffmpeg,
            'postprocessors':[
                {'key': 'MetadataParser',
                'when': 'pre_process',
                'actions': [(MetadataParserPP.Actions.INTERPRET, 'playlist_index', r'(?s)(?P<track_number>.+)')]},
                
                {'key': 'FFmpegMetadata',
                'add_chapters': options['add_chapters'],
                'add_metadata': options['add_metadata']},

                {'key': 'FFmpegEmbedSubtitle',
                'already_have_subtitle': options['add_subtitles']},

                {'key': 'EmbedThumbnail',
                'already_have_thumbnail': False}]
        }
        
        # Ajouter les options spécifiques basées sur le dictionnaire options
        if options['type'] == 'audio':
            print(1)
            
            ydl_opts.update({
                'format':'bestaudio[ext=alac]/bestaudio[ext=flac]/bestaudio[ext=wav]/bestaudio[ext=aiff]/bestaudio[ext=mqa]/bestaudio[ext=aac]/bestaudio[ext=opus]/bestaudio/best'
            })

        print(ydl_opts)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
    
    def get_metadata(self):
        ydl_opts = {'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.url, download=False)
            metadata = {
                'title': info_dict.get('title', ''),
                'author': info_dict.get('uploader', ''),
                'publish_date': info_dict.get('upload_date', ''),
                'views': info_dict.get('view_count', ''),
                'description': info_dict.get('description', ''),
                'thumbnail_url': info_dict.get('thumbnail', ''),
            }
            
            # Ajouter les métadonnées supplémentaires si demandé
            if self.options.get('extract_metadata', False):
                metadata.update({
                    'duration': info_dict.get('duration'),
                    'length_seconds': info_dict.get('duration_seconds'),
                    'rating': info_dict.get('average_rating'),
                    'comment_count': info_dict.get('comment_count'),
                    'favorite_count': info_dict.get('favorite_count'),
                    'dislike_count': info_dict.get('dislike_count'),
                    'like_count': info_dict.get('like_count'),
                    'tags': info_dict.get('tags'),
                    'license': info_dict.get('license'),
                    'channel_url': info_dict.get('channel_url'),
                    'channel_name': info_dict.get('channel_name'),
                    'channel_description': info_dict.get('channel_description'),
                    'channel_thumbnail': info_dict.get('channel_thumbnail'),
                    'channel_country': info_dict.get('channel_country'),
                    'channel_region': info_dict.get('channel_region'),
                    'channel_language': info_dict.get('channel_language'),
                    'channel_age_restricted': info_dict.get('channel_age_restricted'),
                    'channel_verified': info_dict.get('channel_verified'),
                    'channel_subscriber_count': info_dict.get('channel_subscriber_count'),
                    'channel_view_count': info_dict.get('channel_view_count'),
                    'channel_video_count': info_dict.get('channel_video_count'),
                    'channel_upload_date': info_dict.get('channel_upload_date'),
                })
            
            return metadata
        
option = {
    "type":"",
    "format": "mp4",
    "outtmpl": "%(title)s.%(ext)s",
    "progress_hooks": [lambda x: None],
    "add_thumbnails": True,
    "add_metadata": True,
    "add_subtitles": True,
    "add_chapters": True,
    "extract_metadata": False
}        
test = YtDlpDownloader("https://youtu.be/RKvd4tMkFHc")
meta = test.get_metadata()
print(meta)
test.download(option, r"C:\Users\msergent\Downloads", r"\Users\msergent\Downloads\yt-dlp\ffmpeg.exe")
