# -*- encoding:utf-8 -*-
"""
Audeo is a GUI for downloading video and music from the Internet. It uses yt-dlp, ffmpeg, spotDL...
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import os 
from toga import ImageView
from toga.style.pack import CENTER
import threading
from threading import Thread
from queue import Queue
import time



class Audeo(toga.App):
    def startup(self):
        # Création du layout principal avec alignement horizontal centré
        main_box = toga.Box()
        self.left = toga.Box(style=Pack(width=10))
        self.center = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1))
        self.right = toga.Box(style=Pack(width=10))
        main_box.add(self.left, self.center, self.right)
        # Création de l'image
        title_image = toga.ImageView(image='./resources/audeo.png', style=Pack(padding=(0, 5)))

        # Ajout de l'image au layout principal
        self.center.add(title_image)

        # Création des widgets
        
        self.url_input = toga.TextInput(style=Pack(flex=1), placeholder='Entrez une URL', on_change=self.on_url_input_change)
        self.folder_button = toga.Button('Choisissez un dossier', on_press=self.select_folder)
        # Créer une commande pour lancer l'opération
        self.launch_command = toga.Command(self.launch_operation, 'Lancer', shortcut='l')

        # Ajouter la commande au bouton
        self.launch_button = toga.Button('Lancer', on_press=self.launch_command.action, enabled=False)

        self.pytube = toga.Box(style=Pack(flex=1))
        self.spotDL = toga.Box(style=Pack(flex=1))
        self.univer = toga.Box(style=Pack(flex=1))
        
        self.source = toga.OptionContainer(
            content=[
                toga.OptionItem("Youtube", self.pytube),
                toga.OptionItem("Spotify", self.spotDL),
                toga.OptionItem("All", self.univer)
            ],
            style=Pack(flex=1,direction=COLUMN, alignment=CENTER),
            
        )
        
        self.center.add(self.source)
        ### self.pytube ################################################################################
        self.pytube_rigth = toga.Box(style=Pack(alignment=CENTER, flex=1))
        self.pytube_left = toga.Box(style=Pack(alignment=CENTER, background_color = '#E3E3E3'))
        self.pytube_pict = toga.ImageView(image='./resources/pytube90.png', style=Pack(background_color = '#E3E3E3',padding=(0, 5)))
        
        self.pytube_audio = toga.Switch('Audio', value=False)
        self.pytube_video = toga.Switch('Video', value=False)
        self.pytube_play_list = toga.Switch('Liste de lecture', value=False)
        self.pytube_thumbnail = toga.Switch('Miniature', value=False)
        self.pytube_best_ext = toga.Switch('Meilleure extention', value=False)
        self.pytube_meta = toga.Switch('Ajouter les métadonnées', value=False)
        self.pytube_sub_title = toga.Switch('Sous-titre', value=False)
        self.pytube_chapter = toga.Switch('Chapitre', value=False)
        pytube_column1 = toga.Box(style=Pack(direction=COLUMN))
        pytube_column2 = toga.Box(style=Pack(direction=COLUMN))
        pytube_column1.add(self.pytube_audio, self.pytube_thumbnail, self.pytube_play_list, self.pytube_best_ext)
        pytube_column2.add(self.pytube_video,self.pytube_meta, self.pytube_sub_title, self.pytube_chapter)
        pytube_columns_row = toga.Box(style=Pack(direction=ROW))
        pytube_columns_row.add(pytube_column1)
        pytube_columns_row.add(pytube_column2)
        self.pytube_rigth.add(pytube_columns_row)
        self.pytube_left.add(self.pytube_pict)
        self.pytube.add(self.pytube_left, self.pytube_rigth)
        
        ### self.spotDL ################################################################################
        self.spotDL_rigth = toga.Box()
        self.spotDL_left = toga.Box(style=Pack(alignment=CENTER, background_color = '#2AC341'))
        self.spotDL_pict = toga.ImageView(image='./resources/spotdl90.png', style=Pack(background_color = '#2AC341',padding=(0, 5)))
        
        self.spotDL_left.add(self.spotDL_pict)
        self.spotDL.add(self.spotDL_left)
        
        ### Self.univer ################################################################################
        # Création des options avec un switch pour chaque option
        self.play_list = toga.Switch('Liste de lecture', value=False)
        self.thumbnail = toga.Switch('Miniature', value=False)
        self.best_ext = toga.Switch('Meilleure extention', value=False)
        self.meta = toga.Switch('Ajouter les métadonnées', value=False)
        self.sub_title = toga.Switch('Sous-titre', value=False)
        self.chapter = toga.Switch('Chapitre', value=False)
        column1 = toga.Box(style=Pack(direction=COLUMN))
        column2 = toga.Box(style=Pack(direction=COLUMN))
        column1.add(self.thumbnail, self.play_list, self.best_ext)
        column2.add(self.meta, self.sub_title, self.chapter)
        columns_row = toga.Box(style=Pack(direction=ROW))
        columns_row.add(column1)
        columns_row.add(column2)
        self.univer.add(columns_row)
        
        # Définir le dossier de téléchargements par défaut
        self.folder = os.path.expanduser('~/Downloads')
        self.ffmpeg = os.path.join('./ressources/ffmpeg.exe')
        
        
        # Création d'une ligne pour les widgets
        row = toga.Box(style=Pack(direction=ROW))
        row.add(self.url_input)
        row.add(self.folder_button)
        row.add(self.launch_button)

        # Ajout du titre et de la ligne au layout principal
        self.center.add(row)

        #contenaire pour les téléchargement:
        self.box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))  
        self.scroll = toga.ScrollContainer(content=self.box, style=Pack(direction=COLUMN, alignment=CENTER, flex=1))  # Ajoutez la boîte à ScrollContainer
        self.center.add(self.scroll)
        
        # Création de la fenêtre principale
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


        
        
    def select_folder(self, widget):
        # Ouvrir le sélecteur de fichiers pour choisir un dossier
        self.folder = self.main_window.select_folder_dialog(title="Choisissez un dossier")

    def launch_operation(self, widget, event):
        url = self.url_input.value
        

        
        # Vérification de l'URL
        if self.is_valid_url(url):
            Opt_dlp = {}
            print(f"L'URL {url} est valide.")
            if self.play_list.value == False:
                play_liste = True
            else:
                play_liste = False
            thunm=self.thumbnail.value
            best_ext=self.best_ext.value
            meta=self.meta.value
            sub_title=self.sub_title.value
            chapter=self.chapter.value
            print(play_liste,thunm,best_ext,meta,sub_title,chapter)

            self.titre = toga.Label('Extraction des informations')
            self.prcen = toga.Label('0.0 %')
            #self.idplaylist = toga.Label('Liste de lecture : non')
            self.idplay = toga.Label('0/0')
            self.x = 0
            

            # Créez une boîte avec une direction ROW pour les labels
            label_box = toga.Box(style=Pack(direction=COLUMN))
            label_box.add(self.titre, self.idplay, self.prcen)#self.idplaylist,

            self.progressbar = toga.ProgressBar(max=100)
            self.progressbar.value=0

            # Créez une boîte avec une direction COLUMN pour chaque ensemble de texte et de barre de progression
            operation_box = toga.Box(style=Pack(direction=COLUMN))
            operation_box.add(label_box)
            operation_box.add(self.progressbar)

            # Ajoutez operation_box à self.box
            self.box.add(operation_box)
            
            queu = Queue()
            queu_info = Queue()
            ui_queue = Queue()
           
            
            def run():
                
                
                pass
            
            def info():
                title, id, = queu_info.get()
                self.titre.text = title
                #self.idplaylist.text = liste
                self.idplay.text = id
                self.x=1
                
            
            def update():
                prct = queu.get()
                print('prct = ',prct)
                if prct != 100:
                    self.progressbar.value = prct
                    self.prcen.text = f'{self.progressbar.value}%'
                else:
                    self.progressbar.value = 100  # force la barre de progression à se remplir complètement
                    self.prcen.text = '100%'
                    self.x=0
        
            def message_def():
                while not ui_queue.empty():
                    message_type, message = ui_queue.get()
                    print(message)
                    if message_type == 'info':
                        self.main_window.info_dialog('info', message)
                    elif message_type == 'error':
                        self.main_window.error_dialog('Erreur', message)
                
            # Ici, vous pouvez ajouter le code pour télécharger l'URL vers le dossier spécifié
        else:
            self.main_window.info_dialog('Erreur', 'L\'URL entrée n\'est pas valide.')

    def on_url_input_change(self, widget):
        # Activer ou désactiver le bouton de lancement en fonction de la validité de l'URL
        self.launch_button.enabled = self.is_valid_url(self.url_input.value)

    @staticmethod
    def is_valid_url(url):
        # Vérifier si l'URL est valide
        return url.startswith('http://') or url.startswith('https://')


def main():
    return Audeo()


if __name__ == '__main__':
    main().main_loop()