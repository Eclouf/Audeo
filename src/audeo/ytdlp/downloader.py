import yt_dlp
import os
import time
import threading
import requests
import tempfile

from ytdlp.dict_options_formateur import Formateur
from app import Audeo, ProgressWidgets
from PIL import Image


class Downloader:
    
    def __init__(self):
        self.thumbnail = True
        self.lock = threading.Lock()
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.pause_event.set()
    
    def download(self, url, options, instance):
        options_formateur = Formateur()
        options = options_formateur.formater(options)
        
        Audeo.instance = instance
        if Audeo.instance is None:
            raise RuntimeError("Audeo.instance is not initialized")
        
        # Utiliser toga.App pour exécuter sur le thread principal
        Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(lambda: self.create_progress_widgets_and_start_download(url, options))
    
    def create_progress_widgets_and_start_download(self, url, options):
        from app import Audeo  # Importation locale pour éviter les importations circulaires
        progress_widgets = Audeo.instance.create_progress_widgets()
        
        # Ajouter un hook de progression pour obtenir les informations de téléchargement
        def progress_hook(d):
            Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(lambda: Audeo.instance.update_progress(d, progress_widgets))
            
            if d['status'] == 'downloading':
                file_info = {
                    'filename': d.get('info_dict').get('title'),
                    'index': d.get('info_dict').get('playlist_index'),
                    'total_entries': d.get('info_dict').get('__last_playlist_index')
                }
                if '_percent_str' in d:
                    if 'total_bytes' in d:
                        t = d['total_bytes']
                        if t < 1000000:
                            totales_bt = int(float(t))
                            file_info['filesize'] = str(totales_bt) + " B"
                        elif t > 1000000 and t < 1000000000:
                            totales_mb = int(float(t / 1000000))
                            file_info['filesize'] = str(totales_mb) + " MB"
                        elif t > 1000000000:
                            totales_gbites = int(float(t / 1000000000))
                            file_info['filesize'] = str(totales_gbites) + " GB"
                    else:
                        file_info['filesize'] = 'Unknown'
                else:
                    file_info['filesize'] = 'Unknown'
                
                thumbnail_url = d.get('info_dict').get('thumbnail')
                if thumbnail_url and self.thumbnail:
                    print("Thumbnail URL:", thumbnail_url)
                    thumbnail_path = self.download_thumbnail(thumbnail_url)
                    file_info['thumbnail_path'] = thumbnail_path
                print(self.thumbnail)
                with self.lock:
                    Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(lambda: Audeo.instance.update_file_info(file_info, progress_widgets))

        options['progress_hooks'] = [progress_hook]
        options['writethumbnail'] = True
        
        # Lancer le téléchargement dans un thread séparé
        download_thread = threading.Thread(target=self.start_download, args=(url, options))
        download_thread.start()
    
    def download_thumbnail(self, thumbnail_url):
        self.thumbnail = False
        response = requests.get(thumbnail_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
            
        # Convertir l'image en JPG ou PNG et la recadrer en carré
        with Image.open(tmp_file_path) as img:
            # Convertir en PNG (ou JPG si vous préférez)
            converted_path = tmp_file_path.replace('.jpg', '.png')  # Changez en '.jpg' si vous voulez JPG
            img = img.convert("RGB")
            
            # Recadrer l'image en carré
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) / 2
            top = (height - min_dim) / 2
            right = (width + min_dim) / 2
            bottom = (height + min_dim) / 2
            img = img.crop((left, top, right, bottom))
            
            img.save(converted_path, 'PNG')  # Changez en 'JPEG' si vous voulez JPG
        
        os.remove(tmp_file_path)  # Supprimer le fichier temporaire original
        return converted_path
    
    def start_download(self, url, options):
        try:
            ydl = yt_dlp.YoutubeDL(options)
            ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            print(f"DownloadError: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
    def pause_download(self, widget):
        self.pause_event.clear()  # Mettre en pause le téléchargement
    
    def resume_download(self, widget):
        self.pause_event.set()  # Reprendre le téléchargement
    
    def stop_download(self, widget):
        self.stop_event.set()  # Arrêter le téléchargement

    def download_with_pause_resume(self, url, options):
        ydl = yt_dlp.YoutubeDL(options)
        for chunk in ydl.download([url]):
            if self.stop_event.is_set():
                break  # Arrêter le téléchargement
            self.pause_event.wait()  # Attendre si le téléchargement est en pause
            # Traiter le chunk de téléchargement ici
            time.sleep(0.1)  # Simuler le traitement du chunk