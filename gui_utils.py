""# gui_utils.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dicom_utils import view_dicom_series, calculate_slice_thickness

def create_gui():
    # Sua implementação aqui
    pass

def open_viewer_window(patient_key, dicom_files):
    viewer_window = tk.Toplevel()
    viewer_window.title("Visualizador de DICOM")

    # Adicione a lógica para exibir a série DICOM na nova janela
    view_dicom_series(patient_key, dicom_files, viewer_window)

def update_table(new_directory):
    # Sua implementação aqui
    pass

def on_double_click_column_resize(event):
    # Sua implementação aqui
    pass

def filter_by_name():
    # Sua implementação aqui
    pass
""