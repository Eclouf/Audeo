import yt_dlp
from dict_options_formateur import Formateur
from app import update_progress

class Downloader:
    def download(self, url, options):
        options = Formateur()
        options.formater(options)
        # Add a progress hook to get download information
        def progress_hook(d):
            if d['status'] == 'finished':
                print('Done downloading, now converting ...')
            if d['status'] == 'downloading':
                print(f"Downloading: {d['_percent_str']} at {d['_speed_str']} ETA {d['_eta_str']}")
            # Here you can add code to transmit the information to app.py
            # Assuming you have a method in app.py to handle the progress update
            update_progress(d)

        options['progress_hooks'] = [progress_hook]
        """Download the video"""
        ydl = yt_dlp.YoutubeDL(options)
        ydl.download([url])
    