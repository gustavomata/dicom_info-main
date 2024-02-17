    current_theme = root.tk.call("ttk::style", "theme", "use")
        
        # Definindo as características do tema escuro
        dark_theme = {
            "treeview_background": "#2e2e2e",
            "treeview_fieldbackground": "#2e2e2e",
            "treeview_foreground": "#ffffff",
            "treeview_selected_background": "#555555",
            "window_background": "#2e2e2e",
            "label_background": "#2e2e2e",
            "label_foreground": "#ffffff",
            "button_text": "Modo Claro"
        }
        
        if current_theme == "clam":
            # Altera o plano de fundo da tabela para o modo escuro
            tree_style.configure("Treeview", background=dark_theme["treeview_background"],
                                fieldbackground=dark_theme["treeview_fieldbackground"],
                                foreground=dark_theme["treeview_foreground"])
            tree_style.map("Treeview", background=[("selected", dark_theme["treeview_selected_background"])])
            btn_dark_mode.config(text=dark_theme["button_text"])

            # Altera o plano de fundo e o texto da janela principal para o modo escuro
            root.configure(background=dark_theme["window_background"])
            total_rows_label.configure(background=dark_theme["label_background"], foreground=dark_theme["label_foreground"])
            reserved_rights_label.configure(background=dark_theme["label_background"], foreground=dark_theme["label_foreground"])

            # Altera o comando do botão para a função toggle_dark_mode
            btn_dark_mode.config(command=toggle_dark_mode)

        else:
            # Restaura o plano de fundo da tabela para o modo claro
            tree_style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
            tree_style.map("Treeview", background=[("selected", "#a6a6a6")])
            btn_dark_mode.config(text="Modo Escuro")  # Altera o texto do botão para indicar o modo escuro

            # Restaura o plano de fundo e o texto da janela principal para o modo claro
            root.configure(background="white")
            total_rows_label.configure(background="white", foreground="black")
            reserved_rights_label.configure(background="white", foreground="black")

            # Altera o comando do botão para a função toggle_dark_mode
            btn_dark_mode.config(command=toggle_dark_mode)
