import yt_dlp
from ytdlp.dict_options_formateur import Formateur
from app import Audeo
import threading

class Downloader:
    
    def download(self, url, options, instance):
        options_formateur = Formateur()
        options = options_formateur.formater(options)
        
        Audeo.instance = instance
        if Audeo.instance is None:
            raise RuntimeError("Audeo.instance is not initialized")
        
        # Créer les widgets de progression pour ce téléchargement
        print("Audeo instance in download:", Audeo.instance)
        
        # Utiliser toga.App pour exécuter sur le thread principal
        Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(lambda: self.create_progress_widgets_and_start_download(url, options))
    
    def create_progress_widgets_and_start_download(self, url, options):
        progress_box, progress, progress_label = Audeo.instance.create_progress_widgets()
        
        # Ajouter un hook de progression pour obtenir les informations de téléchargement
        def progress_hook(d):
            Audeo.instance.main_window.app._impl.loop.call_soon_threadsafe(lambda: Audeo.instance.update_progress(d, progress_box, progress, progress_label))

        options['progress_hooks'] = [progress_hook]
        
        # Lancer le téléchargement dans un thread séparé
        download_thread = threading.Thread(target=self.start_download, args=(url, options))
        download_thread.start()
    
    def start_download(self, url, options):
        ydl = yt_dlp.YoutubeDL(options)
        ydl.download([url])