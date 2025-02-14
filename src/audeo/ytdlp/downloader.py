from math import e
import yt_dlp
import os
import re
import threading
import weakref
import requests
import tempfile
import ctypes
import sys
import os

from PIL import Image
from yt_dlp.postprocessor import MetadataParserPP


# Ajouter le chemin de la racine du projet au sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

#from audeo.app import Audeo  # Importer Audeo depuis app.py # compilation avec pyinstaller
 # pour le developpement

global threads
threads = {}
    
class MyLogger():
    def __init__(self):
        super().__init__()
        self.erreur = 0
    
    def debug(self, msg):
        from audeo.app import Audeo
        print(msg)
        
        totale_items = re.findall(r'\[download\] Downloading item (\d+) of (\d+)', msg)
        if totale_items:
            total = int(totale_items[0][1])
            
        if msg.startswith('[download] Finished'):
            Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                        lambda: Audeo.instance.download_complete(self.erreur, total)
                    )
        if "has already been downloaded" in msg:
            total = 0
            self.erreur = 'Le fichier a déjà été téléchargé'
            Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(
                        lambda: Audeo.instance.download_complete(self.erreur, total)
                    )

    def warning(self, msg):
        print(msg)
    
    def error(self, msg):
        from audeo.app import Audeo
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
        self.download_thread = None
        
        self.ydl = None
        self._is_downloading = False
        self.number = 0
        self.total_entries = 1

    def _stop_thread(self, thread_id):
        """
        Arrêter un thread spécifique de manière sécurisée
        
        :param thread_id: Identifiant du thread à arrêter
        :return: Booléen indiquant si l'arrêt a réussi
        """
        thread_id = int(thread_id)
        
        try:
            # Récupérer le thread et son événement d'arrêt spécifique
            thread, stop_event = threads[thread_id]
            
            # Définir l'événement d'arrêt
            stop_event.set()
            
            # Attendre que le thread se termine
            if thread.is_alive():
                thread.join(timeout=5)
            
            # Vérifier si le thread est arrêté
            if not thread.is_alive():
                del threads[thread_id]
                return True
            
            return False
        except Exception as e:
            print(f"Erreur lors de l'arrêt du thread {thread_id}: {e}")
            return False

    def download(self, url, options, instance):
        """Lance le téléchargement avec les options spécifiées"""
        
        from audeo.app import Audeo
        
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
        global threads
        
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
        options['no_color'] = True

        # Démarrer le téléchargement dans un thread séparé
        self.download_thread = threading.Thread(
            target=self.start_download,
            args=(url, options)
        )
        self.download_thread.daemon = True
        self.download_thread.start()
        
        # Enregistrer le thread avec son propre événement d'arrêt
        thread_id = self.download_thread.ident
        threads[thread_id] = (self.download_thread, self.stop_event)
        print(f"Thread démarré avec l'ID : {thread_id} et dans {threads}")
        from audeo.app import Audeo
            
        progress_widgets = Audeo.instance.create_progress_widgets(thread_id)

    def start_download(self, url, options):
    
        try:
            with self.lock:
                self.ydl = yt_dlp.YoutubeDL(options)
                self._is_downloading = True
                
            # Vérifier avant de télécharger
            if self.stop_event.is_set():
                return
                
            self.ydl.download([url])
            
        except Exception as download_e:
            # Gérer les exceptions
            if str(download_e) == "Download canceled":
                print("Téléchargement annulé")
            else:
                raise
        
                    
    def stop_download(self, thread_id, widget=None):
        """
        Arrêter le téléchargement de manière agressive
        
        :param thread_id: Identifiant du thread à arrêter
        :param widget: Widget optionnel (non utilisé)
        """
        print("Tentative d'arrêt du téléchargement...")
        print("nb du thread:", thread_id)
        
        # Définir l'événement d'arrêt
        self.stop_event.set()
        
        # Arrêter le thread spécifique
        success = self._stop_thread(thread_id)
        print(f"Arrêt du thread {thread_id} : {'Réussi' if success else 'Échoué'}")
        
        # Annuler le téléchargement de manière thread-safe
        with self.lock:
            if self.ydl:
                try:
                    self.ydl.close()
                except Exception as e:
                    print(f"Erreur lors de l'annulation du téléchargement : {e}")
        
        # Nettoyer les ressources
        self.clean_up()
        
    def clean_up(self):
        """Nettoie les ressources de manière sécurisée"""
        with self.lock:
            self.ydl = None
            self._is_downloading = False
            
            # Réinitialiser le thread
            self.download_thread = None
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
                    
            from audeo.app import Audeo

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
