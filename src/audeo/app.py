"""
App download video
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER


class Audeo(toga.App):
    
    async def select_folder(self, widget):
        """Select the folder where the video will be downloaded"""
        dialog = toga.SelectFolderDialog('Select a folder', initial_directory='~/Downloads')
        folder = await toga.Window.dialog(self, dialog)
        
        if folder:
            print(f"Selected folder: {folder} ")
        else:
            print("No folder selected")
    async def update_progress(self, d):
        print(f"Downloading: {d['_percent_str']} at {d['_speed_str']} ETA {d['_eta_str']}")
        
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
        r_box = toga.Box(style=Pack(width=5, background_color="red", flex=1))
        l_box = toga.Box(style=Pack(width=5, background_color="green", flex=1))
        
        c_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER,flex=1))
        c_b_box = toga.Box(style=Pack(height=5,background_color="green", flex=1 ))
        c_c_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER,flex=1))
        c_t_box = toga.Box(style=Pack(height=5,background_color="green", flex=1))
        
        ico_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
        ico_1_box = toga.Box()
        ico_2_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1))
        title = toga.Label("Audeo",style=Pack(alignment=CENTER, flex=1))
        ico = toga.ImageView(image='./resources/audeo.png', style=Pack(padding=(0, 5)))
        url_input = toga.TextInput(style=Pack(flex=1), placeholder='Entrez une URL')
        folder = toga.Button('Dossier', on_press=self.select_folder)
        ico_1_box.add(ico)
        ico_2_box.add(title, url_input, folder)
        dow_box = toga.Box(style=Pack(flex=1))
        
        
        ico_box.add(ico_1_box, ico_2_box)
        c_c_box.add(ico_box, dow_box)
        c_box.add(c_b_box, c_c_box, c_t_box)
        main_box.add(l_box, c_box, r_box)
        

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return Audeo()
