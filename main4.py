import os
import pydicom as dicom
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from threading import Thread
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
from fpdf import FPDF

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
            items = tree.get_children()
            items.sort(key=lambda item: tree.item(item, 'text').lower())
            for item in items:
                tree.move(item, "", "end")

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
                                    "Pasta": patient_folder
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
                            info["Pasta"]
                        ))

                    for col in tree["columns"]:
                        tree.column(col, anchor=tk.CENTER)

                    analyzed_directories.add(current_directory)
                    total_rows_label.config(text=f"Total de Tomografias Analisadas: {len(tree.get_children())}")

            finally:
                progress_bar.stop()
                progress_window.destroy()

        analysis_thread = Thread(target=analyze_directory_async)
        analysis_thread.start()

    def generate_pdf_report():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Relatório de Tomografias", ln=True, align='C')

        for item in tree.get_children():
            values = tree.item(item, 'values')
            pdf.ln(10)
            pdf.cell(0, 10, txt=f"Paciente: {tree.item(item, 'text')}", ln=True)
            pdf.cell(0, 10, txt=f"Nascimento: {values[0]}", ln=True)
            pdf.cell(0, 10, txt=f"Sexo: {values[1]}", ln=True)
            pdf.cell(0, 10, txt=f"Idade: {values[2]}", ln=True)
            pdf.cell(0, 10, txt=f"Exame: {values[3]}", ln=True)
            pdf.cell(0, 10, txt=f"Descrição do Estudo: {values[4]}", ln=True)
            pdf.cell(0, 10, txt=f"Fabricante do Equipamento: {values[5]}", ln=True)
            pdf.cell(0, 10, txt=f"Equipamento: {values[6]}", ln=True)
            pdf.cell(0, 10, txt=f"Tipo de Exame: {values[7]}", ln=True)
            pdf.cell(0, 10, txt=f"Quantidade de Slices: {values[8]}", ln=True)
            pdf.cell(0, 10, txt=f"Espessura do Slice: {values[9]}", ln=True)
            pdf.cell(0, 10, txt=f"Tamanho da Pasta: {values[10]}", ln=True)
            pdf.cell(0, 10, txt="", ln=True)

        pdf_output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])

        if pdf_output_path:
            pdf.output(pdf_output_path)

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

    def on_double_click(event):
        selected_item = tree.selection()[0]
        values = tree.item(selected_item, 'values')
        patient_key = selected_item.split(" - ")[1]
        dicom_files = values[-1]  # Assuming values[-1] contains the list of DICOM files
        open_viewer_window(patient_key, dicom_files)

    def open_folder(event):
        item = tree.selection()[0]
        folder_path = tree.item(item, 'values')[-1]
        os.startfile(folder_path)

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
        for col in tree["columns"]:
            tree.column(col, anchor=tk.CENTER)
        on_double_click_column_resize(tree)

    script_dir = os.path.dirname(os.path.realpath(__file__))

    root = ThemedTk(theme="clam")
    root.title("Cad4Share - Dicom Info")

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
    tree.heading("Pasta", text="Pasta", anchor=tk.CENTER)

    for col in tree["columns"]:
        tree.column(col, anchor=tk.CENTER)

    style = ttk.Style()
    style.configure("TButton", padding=5, relief="flat", foreground="black", background="#e4e4e4")

    frame_buttons.pack(side=tk.BOTTOM, fill=tk.X)

    btn_choose_directory = ttk.Button(frame_buttons, text="Escolher Diretório", command=choose_directory)
    btn_choose_directory.grid(row=0, column=0, padx=10, pady=10)

    btn_analyze_directory = ttk.Button(frame_buttons, text="Analisar Diretório", command=analyze_directory)
    btn_analyze_directory.grid(row=0, column=1, padx=10, pady=10)

    btn_generate_pdf = ttk.Button(frame_buttons, text="Gerar Relatório PDF", command=generate_pdf_report)
    btn_generate_pdf.grid(row=0, column=2, padx=10, pady=10)

    btn_clear_table = ttk.Button(frame_buttons, text="Limpar Tabela", command=clear_table_and_cache)
    btn_clear_table.grid(row=0, column=3, padx=10, pady=10)

    btn_dark_mode = ttk.Button(frame_buttons, text="Dark Mode", command=toggle_dark_mode)
    btn_dark_mode.grid(row=0, column=4, padx=10, pady=10)

    btn_light_mode = ttk.Button(frame_buttons, text="Light Mode", command=toggle_light_mode)
    btn_light_mode.grid(row=0, column=5, padx=10, pady=10)

    total_rows_label = ttk.Label(frame_buttons, text="Total de Tomografias Analisadas: 0")
    total_rows_label.grid(row=0, column=6, padx=10, pady=10)

    entry_search = ttk.Entry(frame_buttons, font=('Arial', 12))
    entry_search.grid(row=0, column=7, padx=10, pady=10)
    entry_search.bind('<KeyRelease>', lambda event: filter_by_name())

    tree.bind("<Double-1>", on_double_click)
    tree.bind("<Return>", open_folder)
    tree.bind("<ButtonRelease-1>", lambda event: on_double_click_column_resize(tree))
    tree.bind("<Configure>", lambda event: on_double_click_column_resize(tree))

    tree.pack(expand=True, fill=tk.BOTH)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.bind("<Configure>", on_double_click_column_resize)
    root.bind("<Configure>", on_startup)

    root.mainloop()


if __name__ == "__main__":
    show_dicom_info(tk.StringVar())
