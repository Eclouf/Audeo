# -*- encoding:utf-8 -*-
import subprocess

class SpotDL():
    
    def __init__(self, url):
        self.url = url
    
    def download(self, options):
        output_format = options["format"]
        command = ["spotdl", self.url, "--output", f"{output_format}"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            if "Downloading" in line:
                print(line.strip())
            elif "100%" in line:
                print("Téléchargement terminé.")

option =[{'format':'m4a'}]    
test = SpotDL.download("C:\Users\msergent\Downloads\spotdl-4.2.6-win32.exe", option)
test()