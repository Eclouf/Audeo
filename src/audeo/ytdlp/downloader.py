from math import e
import yt_dlp
import os
import re
import threading
import requests
import tempfile
import ctypes

from app import Audeo
from PIL import Image
from yt_dlp.postprocessor import MetadataParserPP

class CancelableYoutubeDL(yt_dlp.YoutubeDL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._download_canceled = False

    def cancel_download(self):
        self._download_canceled = True

    def _download_webpage_handle(self, *args, **kwargs):
        if self._download_canceled:
            raise Exception("Download canceled")
        return super()._download_webpage_handle(*args, **kwargs)

    def _download_webpage(self, *args, **kwargs):
        if self._download_canceled:
            raise Exception("Download canceled")
        return super()._download_webpage(*args, **kwargs)

    def _download_url(self, *args, **kwargs):
        if self._download_canceled:
            raise Exception("Download canceled")
        return super()._download_url(*args, **kwargs)
    
class MyLogger():
    def __init__(self):
        super().__init__()
        self.erreur = 0
    
    def debug(self, msg):
        print(msg)
        
        totale_items = re.findall(r'\[download\] Downloading item (\d+) of (\d+)', msg)
        if totale_items:
            total = int(totale_items[0][1])
            
        if msg.startswith('[download] Finished'):
            Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                        lambda: Audeo.instance.download_complete(self.erreur, total)
                    )

    
    def warning(self, msg):
        print(msg)
    
    def error(self, msg):
        print(msg)
        self.erreur += 1
        
        Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                        lambda: Audeo.instance.download_error(msg)
                    )
    
    def info(self, msg):
        print("Info: " + msg)
        pass

class Downloader:
    def __init__(self):
        self.thumbnail = True
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.current_thread = None
        self.ydl = None
        self._is_downloading = False
        self.number = 0
        self.total_entries = 1

    def download(self, url, options, instance):
        """Lance le téléchargement avec les options spécifiées"""
        Audeo.instance = instance
        if Audeo.instance is None:
            raise RuntimeError("Audeo.instance is not initialized")

        # Réinitialiser les événements
        self.stop_event.clear()

        # Créer les widgets dans le thread principal
        Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
            lambda: self.create_progress_widgets_and_start_download(url, options)
        )

    def create_progress_widgets_and_start_download(self, url, options):
        """Crée les widgets et démarre le téléchargement"""
        progress_widgets = Audeo.instance.create_progress_widgets()

        def progress_hook(d):
            if self.stop_event.is_set():
                raise Exception("Download canceled")
            
            self.total_entries = d.get('info_dict', {}).get('__last_playlist_index')
            if self.total_entries:
                pass
                #print(f"Total entries: {self.total_entries}")
            else:
                self.total_entries = 1

            # Mettre à jour la progression
            if d['status'] == 'downloading':
                self.update_download_progress(d, progress_widgets)
            

        options['progress_hooks'] = [progress_hook]
        options['logger'] = MyLogger()

        # Démarrer le téléchargement dans un thread séparé
        with self.lock:
            self.current_thread = threading.Thread(
                target=self.start_download,
                args=(url, options)
            )
        self.current_thread.start()

    def start_download(self, url, options):
        """Fonction principale de téléchargement"""
        try:
            with self.lock:
                self.ydl = CancelableYoutubeDL(options)
                self._is_downloading = True
            self.ydl.download([url])
        except Exception as e:
            print("Exception", e)
            if str(e) == "Download canceled":
                print("Téléchargement annulé")
                Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                    lambda: Audeo.instance.download_stopped()
                )
            else:
                print(f"Erreur de téléchargement: {e}")
                message = f"Une erreur est survenue lors du téléchargement : {e}"
                Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                    lambda: Audeo.instance.download_error(str(message))
                )
        finally:
            with self.lock:
                self._is_downloading = False

    def stop_download(self, widget=None):
        """Arrête le téléchargement"""
        print("Arrêt du téléchargement...")
        self.stop_event.set()
        
        with self.lock:
            if self.ydl:
                self.ydl.cancel_download()
        
        self.clean_up()

    def clean_up(self):
        """Nettoie les ressources"""
        with self.lock:
            self.ydl = None
            self._is_downloading = False
            self.current_thread = None
            self.stop_event.clear()

    def update_download_progress(self, d, progress_widgets):
        """Met à jour la progression du téléchargement"""
        try:
            # Préparer les informations de fichier
            file_info = {
                'filename': d.get('info_dict', {}).get('title'),
                'index': d.get('info_dict', {}).get('playlist_index'),
                'total_entries': d.get('info_dict', {}).get('__last_playlist_index')
            }

            # Calculer la taille du fichier
            total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            if total_bytes > 0:
                if total_bytes < 1000000:
                    file_info['filesize'] = f"{total_bytes} B"
                elif total_bytes < 1000000000:
                    file_info['filesize'] = f"{total_bytes / 1000000:.1f} MB"
                else:
                    file_info['filesize'] = f"{total_bytes / 1000000000:.1f} GB"
            else:
                file_info['filesize'] = 'Unknown'

            # Gérer la miniature
            if self.thumbnail:
                thumbnail_url = d.get('info_dict', {}).get('thumbnail')
                if thumbnail_url:
                    file_info['thumbnail_path'] = self.download_thumbnail(thumbnail_url)

            # Mettre à jour l'interface
            Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                lambda: Audeo.instance.update_progress(d, progress_widgets)
            )
            with self.lock:
                Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                    lambda: Audeo.instance.update_file_info(file_info, progress_widgets)
                )

        except Exception as e:
            print(f"Erreur dans update_download_progress: {e}")

    def download_thumbnail(self, thumbnail_url):
        """Télécharge et traite la miniature"""
        try:
            self.thumbnail = False
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name

                with Image.open(tmp_file_path) as img:
                    converted_path = tmp_file_path.replace('.jpg', '.png')
                    img = img.convert("RGB")

                    # Recadrer en carré
                    width, height = img.size
                    min_dim = min(width, height)
                    left = (width - min_dim) / 2
                    top = (height - min_dim) / 2
                    right = (width + min_dim) / 2
                    bottom = (height + min_dim) / 2
                    img = img.crop((left, top, right, bottom))

                    img.save(converted_path, 'PNG')

                os.remove(tmp_file_path)
                return converted_path

        except Exception as e:
            print(f"Erreur lors du téléchargement de la miniature : {e}")
            return None
