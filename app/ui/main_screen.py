import tkinter as tk
from tkinter import ttk  # Importa ttk para estilos adicionais
import utils.screen_navigation as sn  # Corrige o import para ser absoluto

class MainScreen:
    def __init__(self, master):
        # Configuração da janela principal
        self.root = master
        self.root.geometry("1040x585")
        self.root.configure(bg="#F0F0F0")
        self.root.title("SQL Server Compare")
        self.root.resizable(True, True)  # Permite redimensionar a janela
        # Configura a janela para abrir em tela cheia
        self.root.state('zoomed')

        # Topo
        frame_top = tk.Frame(self.root, bg="#FFFFFF")
        frame_top.pack(fill="x", side="top")  # Usa layout responsivo para o topo

        # Botão Compare
        btn_start_compare = tk.Button(frame_top, text="Compare", bg="#F0F0F0", font=("Inter", 10), fg="#000000")
        btn_start_compare.pack(side="left", padx=5, pady=5)

        # Botão Filter
        btn_filter = tk.Button(
            frame_top,
            text="Filter",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=lambda: sn.ScreenNavigation(self.root).navigate_to_filter_screen()
        )
        btn_filter.pack(side="left", padx=5, pady=5)

        # Botão Select Source
        btn_select_source = tk.Button(
            frame_top, text="Select source",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=lambda: sn.ScreenNavigation(self.root).navigate_to_connect_screen(0)
        )
        btn_select_source.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Botão Select Target
        btn_select_target = tk.Button(
            frame_top, text="Select target",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=lambda: sn.ScreenNavigation(self.root).navigate_to_connect_screen(1)
        )
        btn_select_target.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Treeview para objetos diferentes
        frame_treeview = tk.Frame(self.root, bg="#FFFFFF")
        frame_treeview.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Object Name", "Object Type", "Action")
        treeview = ttk.Treeview(frame_treeview, columns=columns, show="headings")

        # Configuração das colunas
        treeview.heading("Object Name", text="Object Name")
        treeview.heading("Object Type", text="Object Type")
        treeview.heading("Action", text="Action")

        treeview.column("Object Name", anchor="center")
        treeview.column("Object Type", anchor="center")
        treeview.column("Action", anchor="center")

        treeview.pack(fill="both", expand=True)

        # Corpo dos objetos
        frame_object_body = tk.Frame(self.root)
        frame_object_body.pack(fill="both", expand=True, padx=10, pady=5)

        # Adiciona scrollbars sincronizados para text_source_body e text_target_body
        frame_source_scroll = tk.Frame(frame_object_body)
        frame_source_scroll.pack(side="left", fill="both", expand=True, padx=5)

        scrollbar_source_y = tk.Scrollbar(frame_source_scroll, orient="vertical")
        scrollbar_source_y.pack(side="right", fill="y")
        scrollbar_source_x = tk.Scrollbar(frame_source_scroll, orient="horizontal")
        scrollbar_source_x.pack(side="bottom", fill="x")

        text_source_body = tk.Text(frame_source_scroll, bg="#FFFFFF", wrap="none", 
                                   yscrollcommand=scrollbar_source_y.set, 
                                   xscrollcommand=scrollbar_source_x.set)
        text_source_body.pack(side="left", fill="both", expand=True)

        scrollbar_source_y.config(command=text_source_body.yview)
        scrollbar_source_x.config(command=text_source_body.xview)

        frame_target_scroll = tk.Frame(frame_object_body)
        frame_target_scroll.pack(side="right", fill="both", expand=True, padx=5)

        scrollbar_target_y = tk.Scrollbar(frame_target_scroll, orient="vertical")
        scrollbar_target_y.pack(side="right", fill="y")
        scrollbar_target_x = tk.Scrollbar(frame_target_scroll, orient="horizontal")
        scrollbar_target_x.pack(side="bottom", fill="x")

        text_target_body = tk.Text(frame_target_scroll, bg="#FFFFFF", wrap="none", 
                                   yscrollcommand=scrollbar_target_y.set, 
                                   xscrollcommand=scrollbar_target_x.set)
        text_target_body.pack(side="left", fill="both", expand=True)

        scrollbar_target_y.config(command=text_target_body.yview)
        scrollbar_target_x.config(command=text_target_body.xview)

        # Sincroniza as barras de rolagem
        text_source_body['yscrollcommand'] = lambda *args: [scrollbar_source_y.set(*args), scrollbar_target_y.set(*args)]
        text_target_body['yscrollcommand'] = lambda *args: [scrollbar_target_y.set(*args), scrollbar_source_y.set(*args)]

        scrollbar_source_y.config(command=lambda *args: [text_source_body.yview(*args), text_target_body.yview(*args)])
        scrollbar_target_y.config(command=lambda *args: [text_source_body.yview(*args), text_target_body.yview(*args)])

        # Ajusta a função de rolagem do mouse para Windows
        def _on_mousewheel(event):
            delta = -1 if event.delta > 0 else 1  # Define o delta com base na direção da rolagem

            text_source_body.yview_scroll(delta, "units")
            text_target_body.yview_scroll(delta, "units")
            line_numbers.yview_scroll(delta, "units")

        # Vincula o evento de rolagem do mouse para Windows
        text_source_body.bind_all("<MouseWheel>", _on_mousewheel)
        text_target_body.bind_all("<MouseWheel>", _on_mousewheel)

        # Remove contadores individuais e adicione um contador de linhas centralizado
        line_numbers = tk.Text(frame_object_body, width=4, bg="#F0F0F0", state="disabled", wrap="none")
        line_numbers.pack(side="left", fill="y")

        def update_line_numbers():
            line_numbers.config(state="normal")
            line_numbers.delete("1.0", "end")
            max_lines = max(
                int(text_source_body.index("end-1c").split(".")[0]),
                int(text_target_body.index("end-1c").split(".")[0])
            )
            for i in range(1, max_lines + 1):
                line_numbers.insert("end", f"{i}\n")
            line_numbers.config(state="disabled")

        def sync_scroll(*args):
            scrollbar_source_y.set(*args)
            scrollbar_target_y.set(*args)
            line_numbers.yview_moveto(args[0])

        def on_scroll(*args):
            text_source_body.yview(*args)
            text_target_body.yview(*args)
            line_numbers.yview(*args)

        # Atualiza o comando de rolagem para sincronizar com o contador central
        text_source_body['yscrollcommand'] = sync_scroll
        text_target_body['yscrollcommand'] = sync_scroll
        scrollbar_source_y.config(command=on_scroll)
        scrollbar_target_y.config(command=on_scroll)

        # Atualiza o contador de linhas ao modificar o conteúdo
        text_source_body.bind("<KeyRelease>", lambda event: update_line_numbers())
        text_target_body.bind("<KeyRelease>", lambda event: update_line_numbers())
        text_source_body.bind("<MouseWheel>", lambda event: update_line_numbers())
        text_target_body.bind("<MouseWheel>", lambda event: update_line_numbers())

        # Bloqueia os widgets text_source_body e text_target_body para edição
        text_source_body.config(state="disabled")
        text_target_body.config(state="disabled")

        # Inicializa o contador de linhas
        update_line_numbers()

# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = MainScreen(root)
    root.mainloop()