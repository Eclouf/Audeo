# -*- encoding:utf-8 -*-

"""
App download video
"""
import toga
import os 
import threading
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from ytdlp import downloader

class ProgressWidgets:
    def __init__(self):
        self.dow_pic = toga.ImageView(image='./resources/default.png', style=Pack(height=90, width=90, padding=(0, 5)))
        self.progress_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1))
        self.progress = toga.ProgressBar(max=100, style=Pack(flex=1), value=0)
        self.progress_label = toga.Label('0%', style=Pack(padding_left=5))
        self.file_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))
        self.widget_progress = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        self.file_name = toga.Label('File Name', style=Pack(font_weight='bold', font_size=12, padding_left=5))
        self.file_size = toga.Label('File Size', style=Pack(padding_left=5))
        self.file_index = toga.Label('File Index', style=Pack(padding_left=5))
        self.control_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding_top=5))
        self.pause_button = toga.Button(icon=toga.Icon('./resources/pause.png'), on_press=Audeo.instance.pause_download, style=Pack(width=30, height=30))
        self.resume_button = toga.Button(icon=toga.Icon('./resources/start.png'), on_press=Audeo.instance.resume_download, style=Pack(width=30, height=30))
        self.stop_button = toga.Button(icon=toga.Icon('./resources/stop.png'), on_press=Audeo.instance.stop_download, style=Pack(width=30, height=30))
        self.control_box.add(self.pause_button, self.resume_button, self.stop_button)
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
        self.downloader = Downloader()

    
    def startup(self):
        
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        
        self.ffmpeg = os.path.join(os.path.dirname(__file__), "resources", "ffmpeg.exe")
        self.options = {
            'paths':                    {'home': '/downloads', 'temp': '/temp'},            # Dictionary of output paths.
            'outtmpl':                  {'default': '%(title)s.%(ext)s'},                   # Template for output names.
            'ffmpeg_location': self.ffmpeg,                                                # Location of the ffmpeg binary.
            #'outtmpl_na_placeholder':   'NA',                                               # Placeholder for unavailable meta fields.
            #'restrictfilenames':        True,                                               # Do not allow "&" and spaces in file names.
            #'trim_file_name':           50,                                                 # Limit length of filename (extension excluded).
        }
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
        ico = toga.ImageView(image='./resources/audeo.png', style=Pack(padding=(0, 5)))
        self.url_input = toga.TextInput(style=Pack(flex=1), placeholder='Entrez une URL', on_change=self.on_url_input_change)
        
        self.select_box = toga.Box(style=Pack(flex=1))
        self.folder = toga.Button('Dossier', on_press=self.select_folder)
        self.launch_command = toga.Command(self.launch_operation, 'Lancer', shortcut='l')
        self.launch_button = toga.Button('Lancer', on_press=self.launch_command.action, enabled=False)
        
        self. select_box.add(self.folder, self.launch_button)
        
        ico_1_box.add(ico)
        ico_2_box.add(title, self.url_input, self.select_box)
        self.dow_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER,  background_color='#D3D3D3',padding_left=5, flex=1))
        self.dow_scrol = toga.ScrollContainer(style=Pack(direction=COLUMN, alignment=CENTER, flex=1 ), content=self.dow_box)  # Initialiser dow_box
        
        ico_box.add(ico_1_box, ico_2_box)
        c_c_box.add(ico_box, self.dow_scrol)
        c_box.add(c_b_box, c_c_box, c_t_box)
        self.main_box.add(l_box, c_box, r_box)
        
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()
        print("Audeo instance initialized in startup:", Audeo.instance)
        
    def create_progress_widgets(self):
        return ProgressWidgets()
    
    def on_url_input_change(self, widget):
        # Activer ou désactiver le bouton de lancement en fonction de la validité de l'URL
        self.launch_button.enabled = self.is_valid_url(self.url_input.value)
    
    def launch_operation(self, widget, event):
        print("Audeo instance in launch_operation:", Audeo.instance)
        download_thread = threading.Thread(target=self.start_download, args=(self.url_input.value,))
        download_thread.start()
        print(f"Lancement de l'opération pour l'URL: {self.url_input.value}")
    
    def start_download(self, url):
        print("Audeo instance in start_download:", Audeo.instance)
        down = downloader.Downloader()
        down.download(url, self.options, Audeo.instance)
    
    async def select_folder(self, widget):
        """Select the folder where the video will be downloaded"""
        dialog = toga.SelectFolderDialog('Select a folder', initial_directory='~/Downloads')
        folder = await toga.Window.dialog(self, dialog)
        
        if folder:
            self.options['paths']['home'] = folder
            print(f"Selected folder: {folder} ")
        else:
            print("No folder selected")
            
    def update_progress(self, d, progress_widgets):
        if d['status'] == 'downloading':
            percent_str = d['_percent_str'].strip('%')  # Extraire la valeur numérique
            progress_widgets.progress.value = float(percent_str)
            progress_widgets.progress_label.text = f"{d['_percent_str']} at {d['_speed_str']} ETA {d['_eta_str']}"
        elif d['status'] == 'finished':
            progress_widgets.progress.value = 100
            progress_widgets.progress_label.text = "Download complete"
        
    def update_file_info(self, file_info, progress_widgets):
        # Mettre à jour l'interface utilisateur avec les informations du fichier
        progress_widgets.file_name.text = file_info['filename'][0:30] + ('...' if len(file_info['filename']) > 30 else '')
        progress_widgets.file_size.text = file_info['filesize']
        progress_widgets.file_index.text = str(file_info['index']) + '/' + str(file_info['total_entries'])
        if 'thumbnail_path' in file_info:
            print(file_info['thumbnail_path'])
            progress_widgets.dow_pic.image = str(file_info['thumbnail_path']).replace('\\', '/')
    
    def pause_download(self, widget):
        self.downloader.pause_download(widget)

    def resume_download(self, widget):
        self.downloader.resume_download(widget)

    def stop_download(self, widget):
        self.downloader.stop_download(widget)
        
        
    @staticmethod
    def is_valid_url(url):
        # Vérifier si l'URL est valide
        return url.startswith('http://') or url.startswith('https://')

def main():
    return Audeo()
