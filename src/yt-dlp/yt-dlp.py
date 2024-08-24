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

class Audio():
    def audio(option : dict, url):
        option.update({'format': 'bestaudio[ext=alac]/bestaudio[ext=flac]/bestaudio[ext=wav]/bestaudio[ext=aiff]/bestaudio[ext=mqa]/bestaudio[ext=aac]/bestaudio[ext=m4a]/bestaudio[ext=opus]/bestaudio/best',
                                    
                                    'postprocessors':
                                    [{'key': 'MetadataParser',
                                    'when': 'pre_process',
                                    'actions': [(MetadataParserPP.Actions.INTERPRET, 'playlist_index', r'(?s)(?P<track_number>.+)')]},

                                    {'key': 'EmbedThumbnail',
                                    'already_have_thumbnail': False}]}) 
        with yt_dlp.YoutubeDL(option) as ydl:
            ydl.download([url])
        pass
    pass

class Video():
    def video(option : dict, url):
        with yt_dlp.YoutubeDL(option) as ydl:
            ydl.download([url])
        pass
    pass