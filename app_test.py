from tkinter import *
import customtkinter

root = customtkinter.CTk() 

# Tema
customtkinter.set_appearance_mode("system")  # default
customtkinter.set_default_color_theme("blue")


class Application():
    def __init__(self):
        self.root = root
        self.tela()
        root.mainloop()
    def tela(self):
        self.root.title("Dicom Tool")
        self.root.configure(background="black")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        self.root.maxsize(width= 1400, height = 900)
        self.root.minsize(width = 400, height = 300)

     
# Application()

     

