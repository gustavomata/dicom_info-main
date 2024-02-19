import os
from numpy import roots
import pydicom as dicom
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
from threading import Thread
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
from dicom_utils import plot_slices
from gui_utils import open_viewer_window, update_table, on_double_click_column_resize, filter_by_name, on_startup
from gui_utils import format_date, extract_clean_name, get_sex
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Table, TableStyle, SimpleDocTemplate
from reportlab.lib import colors, pagesizes  # Adiciona a importação da biblioteca pagesizes
from reportlab.platypus import PageBreak, Table, TableStyle, SimpleDocTemplate, Image as RLImage
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import partial


def calculate_slice_thickness(ds):
    try:
        return "{:.2f} mm".format(float(getattr(ds, 'SliceThickness', "N/A")))
    except ValueError:
        return "N/A"
    
def calculate_age(birth_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y%m%d")
        current_date = datetime.now()
        age = current_date.year - birth_date.year -- ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
        return age
    except ValueError:
        return "N/D"

# Modifique a lista de cabeçalhos para incluir apenas as colunas desejadas
headers = ["Paciente", "Nasicmento" , "Sexo", "Idade", "Exame", "Descrição do Estudo", "Quantidade de Slices", "Espessura do Slice"]

def get_table_data(tree):
    # Obtém os cabeçalhos da tabela
    headers = tree["columns"]
    # Obtém os dados das linhas da tabela
    data = []
    for item in tree.get_children():
        row_values = tree.item(item, "values")
        data.append([tree.item(item, "text")] + [row_values[headers.index(column)] for column in headers])
    # Retorna os cabeçalhos e os dados da tabela
    return [headers] + data

def show_context_menu(event, tree, column):
    print(f"Column: {column}, Event: {event}")
    if column == "#0":
        # Se a coluna for a primeira coluna, crie um menu suspenso personalizado
        item = tree.identify_row(event.y)
        selected_item = tree.selection()[0]
        patient_name = tree.item(selected_item, "text")
        context_menu = tk.Menu(root, tearoff=0)  # Correção aqui, substitua 'roots' por 'root'
        context_menu.add_command(label=f"Editar Dados de {patient_name}", command=lambda: edit_patient_name(selected_item))
        context_menu.post(event.x_root, event.y_root)  # Correção aqui, substitua 'x_roots' por 'x_root' e 'y_roots' por 'y_root'
    else:
        # Se a coluna não for a primeira, use o menu padrão
        item = tree.identify_row(event.y)
        context_menu = tk.Menu(root, tearoff=0)  # Correção aqui, substitua 'roots' por 'root'
        context_menu.add_command(label="Editar Dados", command=lambda: edit_patient_name(item))
        context_menu.post(event.x_root, event.y_root)  # Correção aqui, substitua 'x_roots' por 'x_root' e 'y_roots' por 'y_root'

def edit_patient_name(event):
    # Obtenha a linha selecionada
    selected_item = tree.selection()[0]
    patient_name = tree.item(selected_item, "text")
    # Crie uma janela de diálogo para editar o nome do paciente
    new_name = simpledialog.askstring("Editar Nome do Paciente", f"Novo Nome para {patient_name}:")

    if new_name:
        # Atualize o nome na árvore
        tree.item(selected_item, text=new_name)
        # Exiba uma mensagem de confirmação
        result = tkinter.messagebox.askyesno("Salvar Alterações", "Deseja salvar as alterações?")
        if result:
            # Salvar as alterações
            messagebox.showinfo("Edição Confirmada", "Você editou os dados com sucesso!")
        else:
            # Reverter para o nome anterior
            tree.item(selected_item, text=patient_name)
            messagebox.showinfo("Edição Cancelada", "As alterações foram canceladas.")


def generate_pdf_report_and_open(tree):
    
    # Mapeamento dos índices das colunas para os nomes dos cabeçalhos
    header_mapping = {
        0: "Nome do paciente",
        1: "Data de nascimento",
        3: "Idade",
        2: "Sexo",
        4: "Data do exame",
        6: "Fabricante",
        7: "Equipamento",
        9: "Quantidade de Slices",
        10: "Espessura do Slice"
    }
    
    # Obtém os dados da tabela
    table_data = get_table_data(tree)
    
    # Seleciona apenas as colunas desejadas (colunas 1, 2, 4, 5, 7, 8, 10 e 11)
    selected_columns_indices = [0, 1, 3, 2, 4, 6, 7, 9]
    table_data_selected = [[row[i] for i in selected_columns_indices] for row in table_data]
    
    # Renomeia os cabeçalhos das colunas
    headers = [header_mapping.get(i, "") for i in selected_columns_indices]
    table_data_selected.insert(1, headers)
    
    # Define o nome do arquivo PDF
    filename = "dicom_report.pdf"
    
    # Cria um documento PDF em modo paisagem
    pdf = SimpleDocTemplate(filename, pagesize=landscape(letter))
    
    # Adiciona os dados da tabela ao PDF, excluindo a primeira linha (cabeçalhos)
    table = Table(table_data_selected[1:], repeatRows=1)

    # Define o estilo da tabela
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 8)  # Reduz o tamanho da fonte da tabela
    ]))
    
    # Define o estilo do cabeçalho da tabela
    header_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9)  # Reduz o tamanho da fonte do cabeçalho
    ])
    
    # Aplica o estilo do cabeçalho à primeira linha da tabela
    for i, header in enumerate(headers):
        header_style.add('BACKGROUND', (i, 0), (i, 0), colors.grey)
        header_style.add('TEXTCOLOR', (i, 0), (i, 0), colors.whitesmoke)
    
    # Adiciona a tabela ao documento PDF
    table.setStyle(header_style)
     # Adiciona o logo ao início do documento PDF
    logo_path = ".\img\logo.png"  # Substitua pelo caminho real do seu arquivo de logo
    original_logo = RLImage(logo_path)  # Adiciona um salto de página após o logo
    scaled_logo = RLImage(logo_path, width=320, height=100)
    pdf.build([scaled_logo, table])
    
    # Abre o relatório PDF no visualizador padrão do sistema
    subprocess.Popen([filename], shell=True)

def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if filename.lower().endswith('.dcm'):
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
    total_size_mb = total_size / (1024 * 1024)
    total_size_mb_int = round(total_size_mb)
    return "{} MB".format(int(total_size_mb_int))

def show_dicom_info(main_directory):
    analyzed_directories = set()
    analysis_interrupted = False  # Flag para verificar se a análise foi interrompida

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
    def on_close():
        nonlocal analysis_interrupted
        analysis_interrupted = True  # Set the flag to indicate that the analysis has been interrupted
        progress_window.destroy()

    def abort_analysis():
        result = tk.messagebox.askyesno("Abort Analysis", "Are you sure you want to abort the analysis?")
        if result:
            nonlocal analysis_interrupted
            analysis_interrupted = True  # Set the flag to indicate that the analysis has been interrupted
            progress_window.destroy()


    def choose_directory():
        new_directory = filedialog.askdirectory(title="Choose the directory for analysis")
        if new_directory:
            analyze_folders = analyze_on_button_click.get()
            update_table(new_directory, sort_by_name=True, analyze_folders=analyze_folders)

    def analyze_directory():
        nonlocal analysis_interrupted
        analysis_interrupted = False  # Reinicia a flag ao iniciar a análise
        current_directory = main_directory.get()
        if current_directory in analyzed_directories:
            tk.messagebox.showinfo("Diretório Já Analisado", "Este diretório já foi analisado e está na tabela.")
            return

        progress_window = tk.Toplevel(root)
        progress_window.title("Analyzing CT scans")

        def on_close():
            nonlocal analysis_interrupted
            analysis_interrupted = True  # Define a flag para indicar que a análise foi interrompida
            progress_window.destroy()


        # Progress Bar
                
        progress_window.protocol("WM_DELETE_WINDOW", on_close)  # Configura o evento de fechar a janela

        progress_label = tk.Label(progress_window, text="Analyzing...Please wait.")
        progress_label.pack(pady=10)

        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
        progress_bar.pack(pady=10)
        progress_bar.start()

        abort_button = ttk.Button(progress_window, text="Abort Analysis", command=abort_analysis, style="TButton")
        abort_button.pack(pady=10, padx=20)

        progress_window.update_idletasks()
        screen_width = progress_window.winfo_screenwidth()
        screen_height = progress_window.winfo_screenheight()
        window_width = 300
        window_height = 100
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        progress_label.pack(pady=10)
        progress_window.geometry("400x150")  # Adjust the dimensions as needed

       

        def analyze_directory_async():
            nonlocal progress_bar, progress_label, analysis_interrupted
            try:
                for root_folder, _, _ in os.walk(current_directory):
                    if analysis_interrupted:  # Verifica se a análise foi interrompida
                        break

                    dicom_files = [f for f in os.listdir(root_folder) if f.lower().endswith('.dcm')]

                    patient_info = {}

                    for dicom_file in dicom_files:
                        dicom_path = os.path.join(root_folder, dicom_file)
                        try:
                            ds = dicom.dcmread(dicom_path, force=True)

                            patient_name = extract_clean_name(ds.PatientName.given_name, ds.PatientName.family_name)
                            patient_key = f"{patient_name}_{ds.PatientID}"

                            if patient_key not in patient_info:
                                patient_folder = os.path.join(current_directory, root_folder)
                                patient_info[patient_key] = {
                                    "Nascimento": format_date(ds.PatientBirthDate),
                                    "Sexo": get_sex(ds),
                                    "Idade": calculate_age(ds.PatientBirthDate),
                                    "Exame": format_date(ds.StudyDate),
                                    "Descrição do Estudo": getattr(ds, 'StudyDescription', "N/A"),
                                    "Fabricante": getattr(ds, 'Manufacturer', "N/A"),
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
                        if analysis_interrupted:  # Verifica se a análise foi interrompida
                            break

                        # Inserção na árvore com o caminho do diretório oculto
                        item_id = tree.insert("", "end", text=f"{patient_name}", values=(
                            info["Nascimento"],
                            info["Sexo"],
                            info["Idade"],
                            info["Exame"],
                            info["Descrição do Estudo"],
                            info["Fabricante"],
                            info["Equipamento"],
                            info["Tipo de Exame"],
                            info["Quantidade de Slices"],
                            info["Espessura do Slice"],
                            info["Tamanho da Pasta"],
                            info["Visualizar"],
                            "Clique para abrir pasta",
                        ))
                        # Define o caminho do diretório como valor oculto
                        tree.set(item_id, "#13", info["Pasta"])

                    for col in tree["columns"]:
                        tree.column(col, anchor=tk.CENTER)

                    if not analysis_interrupted:  # Atualiza a tabela apenas se a análise não foi interrompida
                        analyzed_directories.add(current_directory)
                        total_rows_label.config(text=f"Total number of CT scans analyzed: {len(tree.get_children())}")
                        on_double_click_column_resize(tree)

            finally:
                progress_bar.stop()
                progress_window.destroy()

        analysis_thread = Thread(target=analyze_directory_async)
        analysis_thread.start()

    def clear_table_and_cache():
        tree.delete(*tree.get_children())
        main_directory.set("")
        analyzed_directories.clear()
        total_rows_label.config(text="Total de Tomografias Analisadas: 0")
        entry_search.delete(0, tk.END)     # Limpa o campo de busca

    def toggle_dark_mode():
        current_theme = root.tk.call("ttk::style", "theme", "use")
        
        # Defina as características do tema escuro
        dark_theme = {
            "treeview_background": "#2e2e2e",
            "treeview_fieldbackground": "#2e2e2e",
            "treeview_foreground": "#ffffff",
            "treeview_selected_background": "#555555",
            "window_background": "#2e2e2e",
            "label_background": "#2e2e2e",
            "label_foreground": "#ffffff",
            "button_text": "Light Mode"  # Texto para o botão quando estiver no modo escuro
        }
        
        if current_theme == "clam":  # Verifica se o tema atual é claro
            # Altere os estilos dos elementos para o tema escuro
            tree_style.configure("Treeview", background=dark_theme["treeview_background"],
                                fieldbackground=dark_theme["treeview_fieldbackground"],
                                foreground=dark_theme["treeview_foreground"])
            tree_style.map("Treeview", background=[("selected", dark_theme["treeview_selected_background"])])
            btn_dark_mode.config(text=dark_theme["button_text"])

            # Altere o plano de fundo e texto da janela principal para o tema escuro
            root.configure(background=dark_theme["window_background"])
            total_rows_label.configure(background=dark_theme["label_background"], foreground=dark_theme["label_foreground"])
            reserved_rights_label.configure(background=dark_theme["label_background"], foreground=dark_theme["label_foreground"])

            # Atualize o comando do botão para alternar para o modo claro
            btn_dark_mode.config(text="Light Mode", command=toggle_light_mode)

        else:
            # Restaure os estilos e cores para o tema claro
            tree_style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
            tree_style.map("Treeview", background=[("selected", "#a6a6a6")])
            btn_dark_mode.config(text="Dark Mode")  # Altere o texto do botão para indicar o modo escuro

            # Restaure o plano de fundo e texto da janela principal para o tema claro
            root.configure(background="white")
            total_rows_label.configure(background="white", foreground="black")
            reserved_rights_label.configure(background="white", foreground="black")

            # Atualize o comando do botão para alternar para o modo escuro
            btn_dark_mode.config(command=toggle_dark_mode)



    def toggle_light_mode():
        current_theme = root.tk.call("ttk::style", "theme", "use")

        # Defina as características do tema claro
        light_theme = {
            "treeview_background": "white",
            "treeview_fieldbackground": "white",
            "treeview_foreground": "black",
            "treeview_selected_background": "#a6a6a6",
            "window_background": "white",
            "label_background": "white",
            "label_foreground": "black",
            "button_text": "Dark Mode"  # Texto para o botão quando estiver no modo claro
        }

        if current_theme == "clam":  # Verifica se o tema atual é escuro
            # Altere os estilos dos elementos para o tema claro
            tree_style.configure("Treeview", background=light_theme["treeview_background"],
                                fieldbackground=light_theme["treeview_fieldbackground"],
                                foreground=light_theme["treeview_foreground"])
            tree_style.map("Treeview", background=[("selected", light_theme["treeview_selected_background"])])
            btn_dark_mode.config(text=light_theme["button_text"])

            # Altere o plano de fundo e texto da janela principal para o tema claro
            root.configure(background=light_theme["window_background"])
            total_rows_label.configure(background=light_theme["label_background"], foreground=light_theme["label_foreground"])
            reserved_rights_label.configure(background=light_theme["label_background"], foreground=light_theme["label_foreground"])

            # Atualize o comando do botão para alternar para o modo escuro
            btn_dark_mode.config(command=toggle_dark_mode)

        else:
            # Restaure os estilos e cores para o tema escuro
            tree_style.configure("Treeview", background="#2e2e2e", fieldbackground="#2e2e2e", foreground="#ffffff")
            tree_style.map("Treeview", background=[("selected", "#555555")])
            btn_dark_mode.config(text="Dark Mode")  # Altere o texto do botão para indicar o modo escuro

            # Restaure o plano de fundo e texto da janela principal para o tema escuro
            root.configure(background="#2e2e2e")
            total_rows_label.configure(background="#2e2e2e", foreground="#ffffff")
            reserved_rights_label.configure(background="#2e2e2e", foreground="#ffffff")

            # Atualize o comando do botão para alternar para o modo claro
            btn_dark_mode.config(command=toggle_dark_mode)

    def on_table_click(event):
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            item = tree.identify_row(event.y)
            column = tree.identify_column(event.x)
            if column == "#12":  # Verifica se o clique ocorreu na penúltima coluna
                item_text = tree.item(item)["text"]
                if " - " in item_text:
                    _, patient_key = item_text.split(" - ", 1)  # Dividir apenas uma vez
                    dicom_files = tree.item(item)["values"][-1]
                    path = dicom_files  # Use o caminho diretamente
                    print(f"Patient Key: {patient_key}")
                    print(f"Path to DICOMs: {path}")
                    plot_slices(path)
                else:
                    messagebox.showerror("Erro", "Texto do item da tabela não está no formato esperado.")

    def start_viewer_thread(patient_key, path):
        viewer_thread = Thread(target=plot_slices, args=(path,))
        viewer_thread.daemon = True
        viewer_thread.start()

    
    def on_double_click(event, tree):
        selected_item = tree.selection()[0]
        values = tree.item(selected_item, 'values')
        patient_key = selected_item.split(" - ")[1]
        dicom_files = values[-1]["Dicom Files"]  # Recupere a lista de arquivos DICOM
        open_viewer_window(patient_key, dicom_files)

    def open_folder(event):
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            item = tree.identify_row(event.y)
            column = tree.identify_column(event.x)
            if column == "#13":  # Verifica se o clique ocorreu na última coluna
                # Recupera o caminho do diretório da linha clicada na última coluna
                directory = tree.set(item, "#13")
                os.startfile(directory)  # Abre a pasta no Windows Explorer

    def filter_by_name():
        query = entry_search.get().lower()
        for item in tree.get_children():
            # Obtenha o texto do item e converta para minúsculas para comparar com a consulta
            item_text = tree.item(item, "text").lower()
            # Verifique se a consulta está presente no texto do item
            if query in item_text:
                tree.item(item, open=True)
                tree.selection_add(item)
            else:
                tree.item(item, open=False)
                tree.selection_remove(item)

    def on_startup(event=None):
        # Distribui uniformemente as colunas ao iniciar o programa
        total_width = tree.winfo_width()
        num_columns = len(tree["columns"])
        column_width = total_width / num_columns
        for col in tree["columns"]:
            tree.column(col, width=int(column_width), anchor="center")
        
        # Defina a largura da primeira coluna
        tree.column("#0", width=400)
        
        # Configure o alinhamento da primeira coluna para oeste (west)
        tree.tag_configure("center_align", anchor="center")

    
    def on_search_entry_change(event):
        entry_text = entry_search.get()
        entry_search.delete(0, "end")  # Limpa o conteúdo atual do campo de entrada
        entry_search.insert(0, entry_text.upper())  # Insere o texto em maiúsculas no campo de entrada    

    def on_enter_key(event):
        filter_by_name()

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
                                       "Fabricante", "Equipamento", "Tipo de Exame",
                                       "Quantidade de Slices", "Espessura do Slice", "Tamanho da Pasta", "Visualizar", "Pasta"))
    tree.heading("#0", text="Paciente")
    tree.heading("Nascimento", text="Data de Nascimento", anchor=tk.CENTER)
    tree.heading("Sexo", text="Sexo", anchor=tk.CENTER)
    tree.heading("Idade", text="Idade", anchor=tk.CENTER)
    tree.heading("Exame", text="Data do Exame", anchor=tk.CENTER)
    tree.heading("Descrição do Estudo", text="Descrição do Estudo", anchor=tk.CENTER)
    tree.heading("Fabricante", text="Fabricante", anchor=tk.CENTER)
    tree.heading("Equipamento", text="Equipamento", anchor=tk.CENTER)
    tree.heading("Tipo de Exame", text="Tipo de Exame", anchor=tk.CENTER)
    tree.heading("Quantidade de Slices", text="Quantidade de Slices", anchor=tk.CENTER)
    tree.heading("Espessura do Slice", text="Espessura do Slice", anchor=tk.CENTER)
    tree.heading("Tamanho da Pasta", text="Tamanho da Pasta", anchor=tk.CENTER)
    tree.heading("Visualizar", text="Visualizar", anchor=tk.CENTER)
    tree.heading("Pasta", text="Pasta", anchor=tk.CENTER)  # Adiciona o cabeçalho para a nova coluna


    for col in tree["columns"]:
        tree.column(col, anchor=tk.CENTER)
    style = ttk.Style()
    style.configure("TButton", padding=5, relief="flat", foreground="white", background="#483D8B",
                   font=("Helvetica", 12, "bold"))
    style.map("TButton", background=[("pressed", "#4B0082"), ("active", "#4B0082")])

    btn_choose_dir = ttk.Button(frame_buttons, text="Choose Folder", command=choose_directory, style="TButton")
    btn_analyze = ttk.Button(frame_buttons, text="Analyze", command=analyze_directory, style="TButton")
    btn_dark_mode = ttk.Button(frame_buttons, text="Dark Mode", command=toggle_dark_mode, style="TButton")
    btn_clear_table = ttk.Button(frame_buttons, text="Clean Table", command=clear_table_and_cache, style="TButton")
    btn_gerar_relatorio = ttk.Button(frame_buttons, text="Generate PDF Report", command=clear_table_and_cache, style="TButton")


    scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    scrollbar.grid(row=5, column=5, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)
    entry_search = ttk.Entry(frame_buttons, style="TEntry")
    btn_search = ttk.Button(frame_buttons, text="Search by Name", command=filter_by_name, style="TButton")
    total_rows_label = tk.Label(root, text="Total number of CT scans analyzed: 0", font=("Helvetica", 14, "bold"))
    reserved_rights_label = tk.Label(root, text="Cad4Share - Dicom Info - All rights reserved", font=("Helvetica", 14))
    header_image = tk.PhotoImage(file=r"img\logo.png")

    # Crie um rótulo para exibir a imagem
   
    resized_image = header_image.subsample(2, 2)
    header_image_label = tk.Label(root, image=resized_image)
    header_image_label.grid(row=1, column=0, columnspan=5, pady=5, padx=5, sticky="nsew")

    btn_choose_dir.grid(row=0, column=0, pady=5, padx=5, sticky="nsew")
    btn_analyze.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")
    btn_dark_mode.grid(row=0, column=3, pady=5, padx=5, sticky="nsew")
    btn_clear_table.grid(row=0, column=4, pady=5, padx=5, sticky="nsew")

    entry_search.grid(row=1, column=0, columnspan=3, pady=5, padx=5, sticky="nsew")
    btn_search.grid(row=1, column=3, pady=5, padx=5, sticky="nsew")
    btn_gerar_relatorio.grid(row=1, column=4, pady=5, padx=5, sticky="nsew")
    btn_gerar_relatorio.config(command=lambda: generate_pdf_report_and_open(tree))
   
    entry_search.bind("<KeyRelease>", on_search_entry_change)  # Adiciona o evento de liberação de tecla ao campo de entrada
    entry_search.bind("<Return>", on_enter_key)

    frame_buttons.grid(row=2, column=0, columnspan=5, pady=4, padx=5, sticky="nsew")
    frame_buttons.grid_columnconfigure(0, weight=1)  # Adiciona esta linha para centralizar no eixo horizontal

    total_rows_label.grid(row=3, column=0, columnspan=5, pady=5, padx=5, sticky="n")
    reserved_rights_label.grid(row=0, column=0, columnspan=5, pady=5, padx=5, sticky="nsew")

    tree.grid(row=5, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")
    root.grid_rowconfigure(5, weight=1)
    root.grid_columnconfigure(0, weight=1)
    tree.bind("<Double-1>", open_folder) # Muda o evento de duplo clique para abrir a pasta no Windows Explorer
    tree.bind("<ButtonRelease-1>", on_table_click)

    tree.tag_bind(col, "<Button-3>", lambda event, col=col: show_context_menu(event, tree, root))


    root.bind("<Map>", on_startup)
    root.mainloop()


# Substitua o caminho abaixo pelo caminho real para o diretório com suas imagens DICOM
main_directory = "./data2"

show_dicom_info(main_directory)