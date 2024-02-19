""# gui_utils.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dicom_utils import view_dicom_series, calculate_slice_thickness

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

def on_startup(event=None):
    # Distribui uniformemente as colunas ao iniciar o programa
    total_width = tree.winfo_width()
    num_columns = len(tree["columns"])
    column_width = total_width / num_columns
    for col in tree["columns"]:
        tree.column(col, width=int(column_width))
    tree.column("#0", width=400)
    
    for col in tree["columns"]:
        tree.tag_bind(col, "<Button-3>", lambda event, col=col: show_context_menu(event, tree, col))
    tree.tag_bind("#0", "<Button-3>", lambda event: show_context_menu(event, tree, "#0"))


def format_date(date_str):
    return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"


def extract_clean_name(given_name, family_name):
    given_name = ''.join(char for char in given_name if char.isalpha() or char.isspace())
    family_name = ''.join(char for char in family_name if char.isalpha() or char.isspace())
    return f"{given_name.strip()} {family_name.strip()}"
    
def get_sex(ds):
    return getattr(ds, 'PatientSex', "N/A")