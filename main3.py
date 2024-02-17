import os
import pydicom as dicom
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from threading import Thread
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
from fpdf import FPDF
from dicom_utils import view_dicom_series, on_table_click
from gui_utils import create_gui, open_viewer_window, update_table, on_double_click_column_resize, filter_by_name


def format_date(date_str):
    return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"


def calculate_age(birth_date_str, exam_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y%m%d")
        exam_date = datetime.strptime(exam_date_str, "%Y%m%d")
        age = (exam_date - birth_date).days // 365
        return age
    except ValueError:
        return "N/A"


def extract_clean_name(given_name, family_name):
    given_name = ''.join(char for char in given_name if char.isalpha() or char.isspace())
    family_name = ''.join(char for char in family_name if char.isalpha() or char.isspace())
    return f"{given_name.strip()} {family_name.strip()}"


def calculate_slice_thickness(ds):
    return "{:.2f}".format(float(getattr(ds, 'SliceThickness', "N/A")))


def get_sex(ds):
    return getattr(ds, 'PatientSex', "N/A")


def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if filename.lower().endswith('.dcm'):
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
    total_size_mb = total_size / (1024 * 1024)
    return "{:.2f} MB".format(total_size_mb)


def show_dicom_info(main_directory):
    analyzed_directories = set()


def update_table(new_directory, sort_by_name=False, analyze_folders=False):
    tree.delete(*tree.get_children())
    main_directory.set(new_directory)
    analyzed_directories.clear()

    if new_directory and analyze_folders:
        analyze_directory()

    if sort_by_name:
        items = list(tree.get_children())
        items.sort(key=lambda item: tree.item(item, 'text').lower())
        for item in items:
            tree.move(item, "", "end")
    on_double_click_column_resize(tree)


def choose_directory():
    new_directory = filedialog.askdirectory(title="Escolha o diretório para análise")
    if new_directory:
        analyze_folders = analyze_on_button_click.get()
        update_table(new_directory, sort_by_name=True, analyze_folders=analyze_folders)


def analyze_directory():
    current_directory = main_directory.get()
    if current_directory in analyzed_directories:
        tk.messagebox.showinfo("Diretório Já Analisado", "Este diretório já foi analisado e está na tabela.")
        return

    progress_window = tk.Toplevel(root)
    progress_window.title("Analisando Diretório")

    progress_window.update_idletasks()
    screen_width = progress_window.winfo_screenwidth()
    screen_height = progress_window.winfo_screenheight()
    window_width = 300
    window_height = 100
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    progress_label = tk.Label(progress_window, text="Analisando... Aguarde.")
    progress_label.pack(pady=10)

    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
    progress_bar.pack(pady=10)
    progress_bar.start()

    def analyze_directory_async():
        nonlocal progress_bar, progress_label
        try:
            for root_folder, _, _ in os.walk(current_directory):
                dicom_files = [f for f in os.listdir(root_folder) if f.lower().endswith('.dcm')]

                patient_info = {}

                for dicom_file in dicom_files:
                    dicom_path = os.path.join(root_folder, dicom_file)
                    try:
                        ds = dicom.dcmread(dicom_path, force=True)

                        patient_key = f"{extract_clean_name(ds.PatientName.given_name, ds.PatientName.family_name)}_{ds.PatientID}"

                        if patient_key not in patient_info:
                            patient_folder = os.path.join(current_directory, root_folder)
                            patient_info[patient_key] = {
                                "Nascimento": format_date(ds.PatientBirthDate),
                                "Sexo": get_sex(ds),
                                "Idade": calculate_age(ds.PatientBirthDate, ds.StudyDate),
                                "Exame": format_date(ds.StudyDate),
                                "Descrição do Estudo": getattr(ds, 'StudyDescription', "N/A"),
                                "Fabricante do Equipamento": getattr(ds, 'Manufacturer', "N/A"),
                                "Equipamento": getattr(ds, 'ManufacturerModelName', "N/A"),
                                "Tipo de Exame": getattr(ds, 'Modality', "N/A"),
                                "Quantidade de Slices": 0,
                                "Espessura do Slice": "N/A",
                                "Tamanho da Pasta": get_folder_size(patient_folder),
                                "Visualizar": "👁️",
                                "Pasta": patient_folder  # Adiciona a coluna para abrir a pasta
                            }

                        patient_info[patient_key]["Quantidade de Slices"] += 1
                        patient_info[patient_key]["Espessura do Slice"] = calculate_slice_thickness(ds)

                    except dicom.errors.InvalidDicomError:
                        print(f"Aviso: Ignorando arquivo DICOM inválido: {dicom_path}")

                for patient_key, info in patient_info.items():
                    tree.insert("", "end", text=f"{os.path.basename(root_folder)} - {patient_key}", values=(
                        info["Nascimento"],
                        info["Sexo"],
                        info["Idade"],
                        info["Exame"],
                        info["Descrição do Estudo"],
                        info["Fabricante do Equipamento"],
                        info["Equipamento"],
                        info["Tipo de Exame"],
                        info["Quantidade de Slices"],
                        info["Espessura do Slice"],
                        info["Tamanho da Pasta"],
                        info["Visualizar"],
                        info["Pasta"]  # Adiciona o valor da nova coluna "Abrir Pasta"
                    ))

                for col in tree["columns"]:
                    tree.column(col, anchor=tk.CENTER)

                analyzed_directories.add(current_directory)
                total_rows_label.config(text=f"Total de Tomografias Analisadas: {len(tree.get_children())}")
                on_double_click_column_resize(tree)

        finally:
            progress_bar.stop()
            progress_window.destroy()

    analysis_thread = Thread(target=analyze_directory_async)
    analysis_thread.start()


def generate_pdf_report():
    # Função para gerar o relatório PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Adiciona cabeçalhos
    headers = ["Paciente", "Nascimento", "Sexo", "Idade", "Exame", "Descrição do Estudo",
               "Fabricante do Equipamento", "Equipamento", "Tipo de Exame",
               "Quantidade de Slices", "Espessura do Slice", "Tamanho da Pasta"]
    for header in headers:
        pdf.cell(40, 10, header, 1)
    pdf.ln()

    # Adiciona dados da tabela ao PDF
    for item in tree.get_children():
        values = tree.item(item, 'values')
        pdf.cell(40, 10, tree.item(item, "text"), 1)
        for value in values:
            pdf.cell(40, 10, value, 1)
        pdf.ln()

    # Salva o PDF
    pdf.output("dicom_report.pdf")


def clear_table_and_cache():
    tree.delete(*tree.get_children())
    main_directory.set("")
    analyzed_directories.clear()
    total_rows_label.config(text="Total de Tomografias Analisadas: 0")


def toggle_dark_mode():
    current_theme = root.option_get('theme', 'theme')
    if current_theme == "":
        root.tk_setPalette(background='#2e2e2e', foreground='#ffffff', activeBackground='#4c4c4c', activeForeground='#ffffff')
        tree_style.configure("Treeview", background="#2e2e2e", fieldbackground="#2e2e2e", foreground="#ffffff")
        tree_style.map("Treeview", background=[("selected", "#555555")])
        btn_dark_mode.config(text="Light Mode")
        style_entry = ttk.Style()
        style_entry.configure("LightMode.TEntry", foreground="black")
        entry_search = ttk.Entry(frame_buttons, style="LightMode.TEntry")
    else:
        root.tk_setPalette(background='', foreground='', activeBackground='', activeForeground='')
        tree_style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        tree_style.map("Treeview", background=[("selected", "#a6a6a6")])
        btn_dark_mode.config(text="Dark Mode")
        style_entry.configure("DarkMode.TEntry", foreground="black")


def toggle_light_mode():
    current_theme = root.option_get('theme', 'theme')
    if current_theme == "":
        root.tk_setPalette(background='white', foreground='black', activeBackground='#e4e4e4', activeForeground='black')
        tree_style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        tree_style.map("Treeview", background=[("selected", "#a6a6a6")])
        btn_light_mode.config(text="Dark Mode")
    else:
        root.tk_setPalette(background='', foreground='', activeBackground='', activeForeground='')
        tree_style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        tree_style.map("Treeview", background=[("selected", "#a6a6a6")])
        btn_light_mode.config(text="Light Mode")
        entry_style = "DarkMode.TEntry" if current_theme != "" else "LightMode.TEntry"
        entry_search = ttk.Entry(frame_buttons, style=entry_style)


def on_double_click(event, tree):
    selected_item = tree.selection()[0]
    values = tree.item(selected_item, 'values')
    patient_key = selected_item.split(" - ")[1]
    dicom_files = values[-1]["Dicom Files"]  # Recupere a lista de arquivos DICOM
    open_viewer_window(patient_key, dicom_files)


def open_folder(event):
    item = tree.selection()[0]
    folder_path = tree.item(item, 'values')[-1]  # Pega o valor da coluna "Abrir Pasta"
    os.startfile(folder_path)  # Abre a pasta no Windows Explorer


def filter_by_name():
    query = entry_search.get().lower()
    for item in tree.get_children():
        if query in tree.item(item, "text").lower():
            tree.item(item, open=True)
            tree.selection_add(item)
        else:
            tree.item(item, open=False)
            tree.selection_remove(item)


def on_startup(event):
    on_double_click_column_resize(tree)


def generate_pdf_report():
    # Função para gerar o relatório PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Adiciona cabeçalhos
    headers = ["Paciente", "Nascimento", "Sexo", "Idade", "Exame", "Descrição do Estudo",
               "Fabricante do Equipamento", "Equipamento", "Tipo de Exame",
               "Quantidade de Slices", "Espessura do Slice", "Tamanho da Pasta"]
    for header in headers:
        pdf.cell(40, 10, header, 1)
    pdf.ln()

    # Adiciona dados da tabela ao PDF
    for item in tree.get_children():
        values = tree.item(item, 'values')
        pdf.cell(40, 10, tree.item(item, "text"), 1)
        for value in values:
            pdf.cell(40, 10, value, 1)
        pdf.ln()

    # Salva o PDF
    pdf.output("dicom_report.pdf")


# Obtém o diretório do script
script_dir = os.path.dirname(os.path.realpath(__file__))

root = ThemedTk(theme="clam")
root.title("Cad4Share - Dicom Info")

# Adiciona a linha abaixo para maximizar a janela ao iniciar
root.wm_state('zoomed')

main_directory = tk.StringVar(value="./data2")
analyze_on_button_click = tk.BooleanVar(value=False)

tree_style = ttk.Style()
tree_style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
tree_style.map("Treeview", background=[("selected", "#a6a6a6")])

frame_buttons = ttk.Frame(root)

tree = ttk.Treeview(root, columns=("Nascimento", "Sexo", "Idade", "Exame", "Descrição do Estudo",
                                   "Fabricante do Equipamento", "Equipamento", "Tipo de Exame",
                                   "Quantidade de Slices", "Espessura do Slice", "Tamanho da Pasta", "Visualizar", "Pasta"))
tree.heading("#0", text="Paciente")
tree.heading("Nascimento", text="Data de Nascimento", anchor=tk.CENTER)
tree.heading("Sexo", text="Sexo", anchor=tk.CENTER)
tree.heading("Idade", text="Idade", anchor=tk.CENTER)
tree.heading("Exame", text="Data do Exame", anchor=tk.CENTER)
tree.heading("Descrição do Estudo", text="Descrição do Estudo", anchor=tk.CENTER)
tree.heading("Fabricante do Equipamento", text="Fabricante do Equipamento", anchor=tk.CENTER)
tree.heading("Equipamento", text="Equipamento", anchor=tk.CENTER)
tree.heading("Tipo de Exame", text="Tipo de Exame", anchor=tk.CENTER)
tree.heading("Quantidade de Slices", text="Quantidade de Slices", anchor=tk.CENTER)
tree.heading("Espessura do Slice", text="Espessura do Slice (mm)", anchor=tk.CENTER)
tree.heading("Tamanho da Pasta", text="Tamanho da Pasta", anchor=tk.CENTER)
tree.heading("Visualizar", text="Visualizar", anchor=tk.CENTER)
tree.heading("Pasta", text="Abrir Pasta", anchor=tk.CENTER)

tree.column("#0", anchor=tk.CENTER, width=200)
tree.column("Nascimento", anchor=tk.CENTER, width=100)
tree.column("Sexo", anchor=tk.CENTER, width=50)
tree.column("Idade", anchor=tk.CENTER, width=50)
tree.column("Exame", anchor=tk.CENTER, width=100)
tree.column("Descrição do Estudo", anchor=tk.CENTER, width=150)
tree.column("Fabricante do Equipamento", anchor=tk.CENTER, width=150)
tree.column("Equipamento", anchor=tk.CENTER, width=150)
tree.column("Tipo de Exame", anchor=tk.CENTER, width=100)
tree.column("Quantidade de Slices", anchor=tk.CENTER, width=100)
tree.column("Espessura do Slice", anchor=tk.CENTER, width=100)
tree.column("Tamanho da Pasta", anchor=tk.CENTER, width=100)
tree.column("Visualizar", anchor=tk.CENTER, width=80)
tree.column("Pasta", anchor=tk.CENTER, width=80)

tree.bind("<Double-1>", lambda event: on_double_click(event, tree))

# Adiciona um ícone para a coluna de visualização
eye_icon_path = os.path.join(script_dir, "eye_icon.png")
eye_icon = Image.open(eye_icon_path)
eye_icon = eye_icon.resize((20, 20), Image.ANTIALIAS)
eye_icon = ImageTk.PhotoImage(eye_icon)
tree.image_create("Visualizar", image=eye_icon)

# Adiciona um ícone para a coluna de abrir pasta
folder_icon_path = os.path.join(script_dir, "folder_icon.png")
folder_icon = Image.open(folder_icon_path)
folder_icon = folder_icon.resize((20, 20), Image.ANTIALIAS)
folder_icon = ImageTk.PhotoImage(folder_icon)
tree.image_create("Pasta", image=folder_icon)

total_rows_label = ttk.Label(frame_buttons, text="Total de Tomografias Analisadas: 0")
total_rows_label.grid(row=0, column=0, padx=10)

btn_open = ttk.Button(frame_buttons, text="Escolher Diretório", command=choose_directory)
btn_open.grid(row=0, column=1, padx=10)

btn_analyze = ttk.Checkbutton(frame_buttons, text="Analisar ao clicar", variable=analyze_on_button_click)
btn_analyze.grid(row=0, column=2, padx=10)

btn_clear = ttk.Button(frame_buttons, text="Limpar Tabela", command=clear_table_and_cache)
btn_clear.grid(row=0, column=3, padx=10)

btn_pdf_report = ttk.Button(frame_buttons, text="Gerar Relatório PDF", command=generate_pdf_report)
btn_pdf_report.grid(row=0, column=4, padx=10)

entry_search = ttk.Entry(frame_buttons)
entry_search.grid(row=0, column=5, padx=10)

btn_search = ttk.Button(frame_buttons, text="Buscar", command=filter_by_name)
btn_search.grid(row=0, column=6, padx=10)

btn_dark_mode = ttk.Button(frame_buttons, text="Dark Mode", command=toggle_dark_mode)
btn_dark_mode.grid(row=0, column=7, padx=10)

btn_light_mode = ttk.Button(frame_buttons, text="Light Mode", command=toggle_light_mode)
btn_light_mode.grid(row=0, column=8, padx=10)

frame_buttons.pack(pady=10)
tree.pack(expand=True, fill="both")

# Adiciona menu de contexto para abrir a pasta no Explorer
tree_context_menu = tk.Menu(root, tearoff=0)
tree_context_menu.add_command(label="Abrir Pasta", command=lambda: open_folder(None))
tree.bind("<Button-3>", lambda event: tree_context_menu.post(event.x_root, event.y_root))

root.bind("<Return>", on_startup)

# Inicia o loop principal
root.mainloop()
