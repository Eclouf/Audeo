import yt_dlp
import os
import queue
import ctypes
from contextlib import contextmanager
from yt_dlp import YoutubeDL

class Tools:
    def __init__(self):
        self. options = {
                'playlist_items': '1',
                'listformats': True,
                'get_format': True
            }
        
    def check_existing_file(self, url, result_queue=queue.Queue()):
        """Vérifie si la vidéo existe déjà dans le dossier de destination"""
        try:
            with yt_dlp.YoutubeDL(self.options) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        result_queue.put((True, filename)) 
        except Exception as e:
            print(f"Erreur lors de la vérification du fichier: {e}")
            result_queue.put((False, None))
        
        return result_queue
    
    
    @contextmanager
    def get_yt_dlp_format(self, url):
        """Récupère les formats disponibles pour une URL donnée.
        
        Args:
            url (str): L'URL de la vidéo
            
        Yields:
            list: Liste des formats disponibles
        """
        try:
           
            with YoutubeDL(self.options) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                # Préparer les données pour la table
                table_data = []
                for f in formats:
                        # Format ID
                        format_id = f.get('format_id', 'N/A')
                        
                        # Extension
                        extension = f.get('ext', 'N/A')
                        
                        # Gestion de la résolution
                        width = f.get('width', 'N/A')
                        height = f.get('height', 'N/A')
                        resolution = f'{width}x{height}' if width != 'N/A' and height != 'N/A' else 'audio only'
                        
                        # Gestion de la taille du fichier
                        filesize = f.get('filesize')
                        filesize_approx = f.get('filesize_approx')
                        if filesize:
                            filesize_mb = filesize / 1024 / 1024
                            filesize_str = f'{filesize_mb:.1f} MB'
                        elif filesize_approx:
                            filesize_approx_mb = filesize_approx / 1024 / 1024
                            filesize_str = f'{filesize_approx_mb:.1f} MB'
                        else:
                            filesize_str = 'N/A'
                        
                        # Gestion des codecs
                        vcodec = f.get('vcodec', 'none')
                        acodec = f.get('acodec', 'none')
                        vcodec_str = 'none' if vcodec == 'none' else vcodec
                        acodec_str = 'none' if acodec == 'none' else acodec
                        
                        # Gestion du FPS et bitrate
                        fps = f.get('fps', 'N/A')
                        tbr = f.get('tbr', 0)
                        bitrate = f'{tbr:0.0f}k' if tbr else 'N/A'
                        
                        row = [
                            format_id,
                            extension,
                            resolution,
                            filesize_str,
                            vcodec_str,
                            acodec_str,
                            fps,
                            bitrate,
                            f.get('protocol', 'N/A')
                        ]
                        table_data.append(row)
                
                yield table_data
                
        except Exception as e:
            print(f"Erreur lors de la récupération des formats : {str(e)}")
            yield []