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


class Audeo(toga.App):
    instance = None  # Attribut de classe pour stocker l'instance de l'application 
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Audeo.instance = self  # Initialiser l'attribut instance dans le constructeur

    
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
        
        ico_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
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
        self.dow_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))  # Initialiser dow_box
        
        ico_box.add(ico_1_box, ico_2_box)
        c_c_box.add(ico_box, self.dow_box)
        c_box.add(c_b_box, c_c_box, c_t_box)
        self.main_box.add(l_box, c_box, r_box)
        
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()
        print("Audeo instance initialized in startup:", Audeo.instance)
        
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
            print(f"Selected folder: {folder} ")
        else:
            print("No folder selected")
            
    def update_progress(self, d, progress_box, progress, progress_label):
        if d['status'] == 'downloading':
            progress_value = float(d['_percent_str'].replace('%', ''))
            progress.value = progress_value
            progress_label.text = f"{d['_percent_str']} at {d['_speed_str']} ETA {d['_eta_str']}"
        elif d['status'] == 'finished':
            progress.value = 100
            progress_label.text = "Download complete"
        
        
    def create_progress_widgets(self):
        progress_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
        progress = toga.ProgressBar(max=100,style=Pack(flex=1), value=0)
        progress_label = toga.Label('0%', style=Pack(padding_left=5))
        progress_box.add(progress, progress_label)
        self.dow_box.add(progress_box)
        return progress_box, progress, progress_label
    
    @staticmethod
    def is_valid_url(url):
        # Vérifier si l'URL est valide
        return url.startswith('http://') or url.startswith('https://')

def main():
    return Audeo()
