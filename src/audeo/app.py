# -*- encoding:utf-8 -*-

"""
App download video
"""
import toga
import os
import platform
import json
import sys
import threading
import asyncio
from threading import Thread

from pathlib import Path
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from ytdlp import downloader
from ytdlp import tools

if getattr(sys, 'frozen', False):
    # Si le programme est exécuté en tant qu'exécutable
    base_path = sys._MEIPASS  # Répertoire temporaire créé par PyInstaller
else:
    # Si le programme est exécuté en tant que script Python normal
    base_path = os.path.dirname(__file__)

image_audeo_path = os.path.join(base_path, 'resources', 'audeo.png')
image_default_path = os.path.join(base_path, 'resources', 'default.png')
image_stop_path = os.path.join(base_path, 'resources', 'stop.png')
image_close_path = os.path.join(base_path, 'resources', 'close.png')

class ProgressWidgets():
    """Classe pour les widgets de progression"""
    
    def __init__(self, id):
        self.dow_pic = toga.ImageView(image=image_default_path, style=Pack(height=90, width=90, padding=(0, 5)))
        self.progress_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1))
        self.progress = toga.ProgressBar(max=100, style=Pack(flex=1), value=0)
        self.progress_label = toga.Label('0%', style=Pack(padding_left=5))
        self.file_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))
        self.widget_progress = toga.Box(style=Pack(direction=ROW, alignment=CENTER, padding_top=3, padding_bottom=3, padding_left=3, padding_right=3))
        self.file_name = toga.Label('File Name', style=Pack(font_weight='bold', font_size=12, padding_left=5))
        self.file_size = toga.Label('File Size', style=Pack(padding_left=5))
        self.file_index = toga.Label('File Index', style=Pack(padding_left=5))
        self.control_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding_top=5))
        # Boutons de controle
        self.stop_button = toga.Button(
            id=id,
            icon=toga.Icon(image_stop_path),
            on_press=Audeo.instance.download_stopped,
            style=Pack(width=30, height=30)
        )
        self.remove_button = toga.Button(
            icon=toga.Icon(image_close_path),
            on_press=Audeo.instance.remove_widget,
            style=Pack(width=30, height=30)
        )
        
        # Configuration initiale
        self.control_box.add(self.remove_button)
        self.control_box.add(self.stop_button)
        
        self.file_box.add(self.file_name, self.file_size, self.file_index)
        self.progress_box.add(self.file_box, self.progress_label, self.progress)
        self.widget_progress.add(self.dow_pic, self.progress_box, self.control_box)
        Audeo.instance.dow_box.add(self.widget_progress)

class Audeo(toga.App):
    instance = None  # Attribut de classe pour stocker l'instance de l'application 
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Audeo.instance = self  # Initialiser l'attribut instance dans le constructeur
        from ytdlp.downloader import Downloader
        from ytdlp.tools import Tools
        self.downloader = Downloader()
        self.tools = Tools()
        self.nub_parser = True
        self.thread_nb = -1

    def load_saved_options(self):
        """Charge les options sauvegardées depuis le fichier de configuration"""
        config_path = os.path.join(os.path.dirname(__file__), 'settings', 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    saved_options = json.load(f)
                    self.options.update(saved_options)
        except Exception as e:
            print(f"Erreur lors du chargement des options : {e}")
    
    def startup(self):
        
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        self.folder_path = Path.home() / 'Downloads'
        self.ffmpeg = self.setup_ffmpeg()
        self.options = {
            'paths':                    {'home': self.folder_path},            # Dictionary of output paths.
            'outtmpl':                  {'default': '%(title)s.%(ext)s'},                   # Template for output names.
            'ffmpeg_location': self.ffmpeg,                                                # Location of the ffmpeg binary.
        }
        
        # Charger les options sauvegardées
        self.load_saved_options()

        self.main_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
        r_box = toga.Box(style=Pack(width=5, flex=1))
        l_box = toga.Box(style=Pack(width=5, flex=1))
        
        c_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER,flex=1))
        c_b_box = toga.Box(style=Pack(height=5, flex=1 ))
        c_c_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER,flex=1))
        c_t_box = toga.Box(style=Pack(height=5, flex=1))
        
        ico_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding_left=5))
        ico_1_box = toga.Box()
        ico_2_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1))
        
        title = toga.Label("Audeo",style=Pack(alignment=CENTER,font_variant='small-caps', font_size=15, flex=1))
        ico = toga.ImageView(image=image_audeo_path, style=Pack(height=80, width=80, padding=(0, 5)))
        self.url_input = toga.TextInput(style=Pack(flex=1), placeholder='Entrez une URL', on_change=self.on_url_input_change)
        
        self.select_box = toga.Box(style=Pack(flex=1, padding_left=5))
        self.settings = toga.Button('Paramètres', on_press=self.open_settings, style=Pack(padding_top=5, padding_bottom=5, padding_left=5, padding_right=5))
        self.folder = toga.Button('Dossier', on_press=self.select_folder, style=Pack(padding_top=5, padding_bottom=5, padding_left=5, padding_right=5))
        self.format_table = toga.Button('Format',enabled=False, on_press=self.open_format, style=Pack(padding_top=5, padding_bottom=5, padding_left=5, padding_right=5))
        self.launch_command = toga.Command(self.launch_operation, 'Lancer', shortcut='l')
        self.launch_button = toga.Button('Lancer', on_press=self.launch_command.action, enabled=False, style=Pack(padding_top=5, padding_bottom=5, padding_left=5, padding_right=5))
        
        self.select_box.add(self.settings, self.folder, self.format_table, self.launch_button)
        
        ico_1_box.add(ico)
        ico_2_box.add(title, self.url_input, self.select_box)
        self.dow_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, background_color='#D3D3D3', padding_left=5, flex=1))
        self.dow_scrol = toga.ScrollContainer(style=Pack(direction=COLUMN, alignment=CENTER, flex=1 ), content=self.dow_box)  # Initialiser dow_box
        
        ico_box.add(ico_1_box, ico_2_box)
        c_c_box.add(ico_box, self.dow_scrol)
        c_box.add(c_b_box, c_c_box, c_t_box)
        self.main_box.add(l_box, c_box, r_box)
        
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()
        print("Audeo instance initialized in startup:", Audeo.instance)
    
    def open_settings(self, widget):
        from settings.gui_settings import SettingsWindow
        settings_window = SettingsWindow(self)
    
    def open_format(self, widget):
        from settings.gui_format import FormatWindow
        format_window = FormatWindow(self)
        
    def setup_ffmpeg(self):
        """Configure ffmpeg according to the platform"""
    
        # Detect the architecture
        machine = platform.machine().lower()
        is_arm = 'arm' in machine or 'aarch64' in machine
    
        # Detect the operating system
        if sys.platform.startswith('win'):
            platform_name = 'windows'
            ffmpeg_name = 'ffmpeg.exe'
        elif sys.platform.startswith('darwin'):
            platform_name = 'macos'
            ffmpeg_name = 'ffmpeg'
        else:
            platform_name = 'linux'
            ffmpeg_name = 'ffmpeg'
        
        # Construct the path to the binary
        arch_suffix = '-arm64' if is_arm else '-x64'
        binary_dir = Path(__file__).parent / 'resources' / 'ffmpeg' / f'{platform_name}{arch_suffix}'
        ffmpeg_path = binary_dir / ffmpeg_name
        
        # Store the path for future use
        self.ffmpeg_path = str(ffmpeg_path)
        
        # Check if the binary exists
        if not ffmpeg_path.exists():
            raise RuntimeError(f"FFmpeg binary not found for your platform ({platform_name}{arch_suffix})")
        
        # Make the binary executable on Unix
        if platform_name in ('linux', 'macos'):
            try:
                os.chmod(ffmpeg_path, 0o755)
            except Exception as e:
                print(f"Warning: Could not set executable permissions on ffmpeg: {e}")
                
        return self.ffmpeg_path
        
    def create_progress_widgets(self, id):
        """Créer un widget de progression
        
        :param id: ID unique pour le widget de progression correspondant au thread de téléchargement
        """
        return ProgressWidgets(id)
    
    def on_url_input_change(self, widget):
        # Activer ou désactiver le bouton de lancement en fonction de la validité de l'URL
        self.launch_button.enabled = self.is_valid_url(self.url_input.value)
        self.format_table.enabled = self.is_valid_url(self.url_input.value)
    
    async def launch_operation(self, widget, event):
        """Lance l'opération de téléchargement"""
        from yt_dlp.postprocessor import MetadataParserPP
        
        url = self.url_input.value
        if not url:
            self.main_window.info_dialog(
                'Erreur',
                'Veuillez entrer une URL valide'
            )
            return
        
        # Vérifier si le dossier de destination existe
        if not os.path.exists(self.options['paths']['home']):
            dialog = toga.QuestionDialog(
                'Dossier de destination non trouvé',
                f'Le dossier de destination "{self.options["paths"]["home"]}" n\'existe pas. Voulez-vous le créer ?'
            )

            result = await toga.Window.dialog(self.main_window, dialog)
            if not result:
                return
            
        # Mise en forme de options
        for x in range(len(self.options['postprocessors'])):
            if self.options['postprocessors'][x]['key'] == 'MetadataParser' and self.nub_parser == True:
                self.nub_parser = False
                
                actions_ytdlp = str(self.options['postprocessors'][x]['actions'][0])
                actions_ytdlp = actions_ytdlp.split(';')
                actions_meta = str(self.options['postprocessors'][x]['actions'][1])
                actions_meta = actions_meta.split(';')
                action_interpret = MetadataParserPP.Actions.INTERPRET
                self.options['postprocessors'][x]['actions'] = []
                
                for i in range(len(actions_ytdlp)):
                    self.options['postprocessors'][x]['actions'].append((action_interpret, actions_ytdlp[i], actions_meta[i]))
                
            else:
                self.nub_parser = True
        
        # Lancer le téléchargement
        download_thread = threading.Thread(target=self.start_download, args=(url,))
        download_thread.start()
        
        self.thread_nb += 1
        print(f"Lancement de l'opération pour l'URL: {url}")
    
    def start_download(self, url):
        """Lance l'opération de téléchargement
        
        :param url: URL de la vidéo
        """
        down = downloader.Downloader()
        down.download(url, self.options, Audeo.instance)
    
    async def select_folder(self, widget):
        """Select the folder where the video will be downloaded"""
        # Determine the initial directory based on the platform
        if sys.platform.startswith('win'):
            # On Windows, use Downloads folder
            initial_dir = os.path.expanduser('~\\Downloads')
        elif sys.platform.startswith('darwin'):
            # On macOS, use Downloads folder
            initial_dir = os.path.expanduser('~/Downloads')
        else:
            # On Linux, use Téléchargements or Downloads folder
            downloads_fr = os.path.expanduser('~/Téléchargements')
            downloads_en = os.path.expanduser('~/Downloads')
            initial_dir = downloads_fr if os.path.exists(downloads_fr) else downloads_en

        dialog = toga.SelectFolderDialog('Select a folder', initial_directory=initial_dir)
        self.folder_path = await toga.Window.dialog(self.main_window, dialog)
        
        if self.folder_path:
            self.options['paths']['home'] = str(self.folder_path)
            print(f"Selected folder: {self.folder_path} ")
            
            # Sauvegarder les options dans un fichier de configuration
            config_path = Path(__file__).parent / 'settings' / 'config.json'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Écrire les nouvelles options
                config_path.write_text(json.dumps(self.options, indent=4), encoding='utf-8')
            except Exception as e:
                print(f"Erreur lors de la sauvegarde des options : {e}")
        else:
            print("No folder selected")
    
    def update_options(self, new_options):
        """Met à jour les options de l'application avec les nouvelles options
        
        :param new_options: Dictionnaire contenant les nouvelles options
        """
        # Fusionner les nouvelles options avec les options existantes
        self.options = dict()
        self.options.update({'paths': {'home': str(self.folder_path)},
                             'ffmpeg_location': self.ffmpeg_path})
        self.options.update(new_options)
        
        # Sauvegarder les options dans un fichier de configuration
        config_path = Path(__file__).parent / 'settings' / 'config.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Écrire les nouvelles options
            config_path.write_text(json.dumps(self.options, indent=4), encoding='utf-8')
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des options : {e}")
                
    def update_progress(self, d, progress_widgets):
        """Mettre à jour l'interface utilisateur avec les informations de progression
        
        :param d: Dictionnaire contenant les informations du fichier
        :param progress_widgets: Widget de progression
        """
        if d['status'] == 'downloading':
            percent_str = d['_percent_str'].strip('%')  # Extraire la valeur numérique
            progress_widgets.progress.value = float(percent_str)
            progress_widgets.progress_label.text = f"{d['_percent_str']} at {d['_speed_str']} ETA {d['_eta_str']}"
        elif d['status'] == 'finished':
            progress_widgets.progress.value = 100
            progress_widgets.progress_label.text = "Download complete"
        
    def update_file_info(self, file_info, progress_widgets):
        """Mettre à jour l'interface utilisateur avec les informations du fichier
        
        :param file_info: Dictionnaire contenant les informations du fichier
        :param progress_widgets: Widget de progression
        """
        progress_widgets.file_name.text = file_info['filename'][0:50] + ('...' if len(file_info['filename']) > 30 else '')
        progress_widgets.file_size.text = file_info['filesize']
        progress_widgets.file_index.text = str(file_info['index']) + '/' + str(file_info['total_entries'])
        if 'thumbnail_path' in file_info:
            print(file_info['thumbnail_path'])
            progress_widgets.dow_pic.image = str(file_info['thumbnail_path']).replace('\\', '/')

    def download_stopped(self, widget=None):
        """
        Arrête le téléchargement en cours et nettoie l'interface
        """
        thread_id = widget.id
        
        try:
            # Arrêter le téléchargement via l'instance du downloader
            if hasattr(self, 'downloader') and self.downloader:
                self.downloader.stop_download(thread_id)
            
            # Supprimer le widget de progression
            self.remove_widget(widget)
            
            # Réinitialiser le widget de progression
            self.current_progress_widgets = None
            
            # Réinitialiser l'état du téléchargement
            if hasattr(self, 'downloader'):
                self.downloader.clean_up()
            
            message = "Téléchargement arrêté par l'utilisateur"
        except Exception as e:
            print(f"Erreur lors de l'arrêt du téléchargement : {e}")
            message = f"Une erreur est survenue lors du téléchargement : \n{e}"
        
        dialog = toga.InfoDialog(
            title="Information",
            message=message
        )
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.dialog_closed)
        
        # Nettoyer les widgets
        if hasattr(self, 'current_progress_widgets'):
            self.dow_box.remove(self.current_progress_widgets.widget_progress)
            self.current_progress_widgets = None
    
    def remove_widget(self, widget=None):
        """
        Supprime le widget de téléchargement associé au bouton 
        """
        try:
            # Trouver le widget parent à supprimer
            widget_to_remove = widget.parent.parent
            
            # Supprimer le widget de la boîte de téléchargement
            if widget_to_remove in self.dow_box.children:
                self.dow_box.remove(widget_to_remove)
            
            # Optionnellement, arrêter le téléchargement associé
            # Vous pouvez ajouter une logique pour identifier et arrêter le téléchargement spécifique
        except Exception as e:
            print(f"Erreur lors de la suppression du widget : {e}")
    
    def download_complete(self, error, items):
        """Appelé lorsque le téléchargement est terminé
        
        :param error: Message d'erreur si le téléchargement a échoué
        :param items: Nombre total d'erreurs
        """
        if error == 'Le fichier a déjà été téléchargé':
            title = "Information"
            msg = "Le fichier a déjà été téléchargé"
        elif error:
            title = "Erreur"
            msg = f"{error}\\{items} files failed to download\n{items-error} files downloaded successfully"
        else:
            title = "Succès"
            msg = "Téléchargement terminé avec succès !"
        dialog = toga.InfoDialog(
            title=title,
            message=msg
        )
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.dialog_closed) 
    
    def download_error(self, message):
        """Appelé lorsque le téléchargement rencontre une erreur
        
        :param message: Message d'erreur
        """
        dialog = toga.ErrorDialog(
            title="Erreur",
            message=message
        )
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.dialog_closed)
    
    def dialog_closed(self, task):
        # Nettoyer les widgets de progression
        if hasattr(self, 'current_progress_widgets'):
            self.dow_box.remove(self.current_progress_widgets.widget_progress)
            self.current_progress_widgets = None          
    
    @staticmethod
    def is_valid_url(url):
        # Vérifier si l'URL est valide
        return url.startswith('http://') or url.startswith('https://')

def main():
    return Audeo()

if __name__ == "__main__":
    main()
