import tkinter as tk
from tkinter import ttk  # Importa ttk para estilos adicionais
from app.utils import ScreenNavigationManager as snm, DatabaseConnectionManager as dcm
from app.core import Comparer

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

        self._frame_top()

        self._frame_treeview()

        self._frame_object_body()


        self.treeview.bind("<Button-1>", self._on_treeview_click)

    def _frame_top(self):
        # Topo (substitua o frame_top atual por este)
        frame_top = tk.Frame(self.root, bg="#FFFFFF", height=60)  # Altura fixa para duas linhas
        frame_top.pack(fill="x", side="top")

        # Botão Compare (pequeno, canto superior esquerdo)
        btn_start_compare = tk.Button(frame_top,
                                      text="Compare",
                                      bg="#F0F0F0",
                                      font=("Inter", 10),
                                      fg="#000000",
                                      command=self._on_compare_click
                                      )
        btn_start_compare.place(relx=0.01, rely=0.1, relwidth=0.08, height=25)

        # Botão Filter (pequeno, ao lado do Compare)
        self.btn_filter = tk.Button(frame_top,
                                    text="Filter",
                                    bg="#F0F0F0",
                                    font=("Inter", 10),
                                    fg="#000000",
                                    command=lambda: snm(self.root).navigate_to_filter_screen(
                                        {'x': self.btn_filter.winfo_rootx(),
                                        'y': self.btn_filter.winfo_rooty()}
                                        )
                                    )
        self.btn_filter.place(relx=0.095, rely=0.1, relwidth=0.05, height=25)

        # Botão Select Source (grande, linha inferior)
        self.btn_select_source = tk.Button(frame_top,
                                           text="Select source",
                                           bg="#F0F0F0",
                                           font=("Inter", 10),
                                           fg="#000000",
                                           command=lambda: snm(self.root).navigate_to_connect_screen(
                                               {'x': self.btn_select_source.winfo_rootx(),
                                                'y': self.btn_select_source.winfo_rooty()},
                                                self._handle_source_connection
                                                )
                                            )
        self.btn_select_source.place(relx=0.01, rely=0.6, relwidth=0.489, height=25)

        # Botão Select Target (grande, linha inferior)
        self.btn_select_target = tk.Button(frame_top,
                                           text="Select target",
                                           bg="#F0F0F0",
                                           font=("Inter", 10),
                                           fg="#000000",
                                           command=lambda: snm(self.root).navigate_to_connect_screen(
                                               {'x': self.btn_select_target.winfo_rootx(),
                                                'y': self.btn_select_target.winfo_rooty()},
                                                self._handle_target_connection
                                                )
                                            )
        self.btn_select_target.place(relx=0.5, rely=0.6, relwidth=0.49, height=25)

    def _frame_treeview(self):
        # Treeview para objetos diferentes
        frame_treeview = tk.Frame(self.root, bg="#FFFFFF")
        frame_treeview.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("Object Name", "Object Type", "Action")
        self.treeview = ttk.Treeview(frame_treeview, columns=columns, show="headings", selectmode="browse")

        # Configuração das colunas
        self.treeview.heading("Object Name", text="Object Name")
        self.treeview.heading("Object Type", text="Object Type")
        self.treeview.heading("Action", text="Action")

        self.treeview.column("Object Name", anchor="center")
        self.treeview.column("Object Type", anchor="center")
        self.treeview.column("Action", anchor="center")

        self.treeview.pack(fill="both", expand=True)

    def _frame_object_body(self):
        ## Corpo dos objetos
        frame_object_body = tk.Frame(self.root)
        frame_object_body.pack(fill="both", expand=True, padx=5, pady=5)

        # Configuração do grid
        frame_object_body.grid_columnconfigure(0, weight=1)  # Texto fonte
        frame_object_body.grid_columnconfigure(1, weight=0)  # Contador (largura fixa)
        frame_object_body.grid_columnconfigure(2, weight=1)  # Texto alvo

        # Frame para o texto fonte (esquerda)
        frame_source_scroll = tk.Frame(frame_object_body)
        frame_source_scroll.grid(row=0, column=0, sticky="nsew", padx=(0,5))

        scrollbar_source_y = tk.Scrollbar(frame_source_scroll, orient="vertical")
        scrollbar_source_y.pack(side="right", fill="y")
        scrollbar_source_x = tk.Scrollbar(frame_source_scroll, orient="horizontal")
        scrollbar_source_x.pack(side="bottom", fill="x")

        self.text_source_body = tk.Text(frame_source_scroll, bg="#FFFFFF", wrap="none", 
                                 yscrollcommand=scrollbar_source_y.set, 
                                 xscrollcommand=scrollbar_source_x.set)
        self.text_source_body.pack(side="left", fill="both", expand=True)

        scrollbar_source_y.config(command=self.text_source_body.yview)
        scrollbar_source_x.config(command=self.text_source_body.xview)

        # Frame para o contador de linhas (centro)
        frame_line_numbers = tk.Frame(frame_object_body, width=30)
        frame_line_numbers.grid(row=0, column=1, sticky="ns")

        # Contador de linhas
        line_numbers = tk.Text(frame_line_numbers, width=4, bg="#F0F0F0", state="disabled", wrap="none")
        line_numbers.pack(side="left", fill="y")

        # Frame para o texto alvo (direita)
        frame_target_scroll = tk.Frame(frame_object_body)
        frame_target_scroll.grid(row=0, column=2, sticky="nsew", padx=(5,0))

        scrollbar_target_y = tk.Scrollbar(frame_target_scroll, orient="vertical")
        scrollbar_target_y.pack(side="right", fill="y")
        scrollbar_target_x = tk.Scrollbar(frame_target_scroll, orient="horizontal")
        scrollbar_target_x.pack(side="bottom", fill="x")

        self.text_target_body = tk.Text(frame_target_scroll, bg="#FFFFFF", wrap="none", 
                                 yscrollcommand=scrollbar_target_y.set, 
                                 xscrollcommand=scrollbar_target_x.set)
        self.text_target_body.pack(side="left", fill="both", expand=True)

        # Frame para as informações de data (fixo na parte inferior)
        frame_bottom_info = tk.Frame(self.root, height=20, bg="#F0F0F0", bd=1, relief="sunken")
        frame_bottom_info.place(relx=0, rely=1, relwidth=1, anchor="sw", y=-5)  # 5px da borda inferior
        
        # Label para data do source (esquerda)
        self.lbl_source_date = tk.Label(
            frame_bottom_info, 
            text="Última modificação: -", 
            bg="#F0F0F0", 
            anchor="w", 
            padx=10
        )
        self.lbl_source_date.pack(side="left", fill="x", expand=True)
        
        # Label para data do target (direita)
        self.lbl_target_date = tk.Label(
            frame_bottom_info, 
            text="Última modificação: -", 
            bg="#F0F0F0", 
            anchor="e", 
            padx=10
        )
        self.lbl_target_date.pack(side="right", fill="x", expand=True)

        # Ajuste no frame_object_body para deixar espaço para as informações
        frame_object_body.pack_configure(pady=(5,25))  # Remove padding inferior pois o frame_bottom_info já tem

        scrollbar_target_y.config(command=self.text_target_body.yview)
        scrollbar_target_x.config(command=self.text_target_body.xview)

        # Sincroniza as barras de rolagem
        self.text_source_body['yscrollcommand'] = lambda *args: [scrollbar_source_y.set(*args), scrollbar_target_y.set(*args)]
        self.text_target_body['yscrollcommand'] = lambda *args: [scrollbar_target_y.set(*args), scrollbar_source_y.set(*args)]

        scrollbar_source_y.config(command=lambda *args: [self.text_source_body.yview(*args), self.text_target_body.yview(*args)])
        scrollbar_target_y.config(command=lambda *args: [self.text_source_body.yview(*args), self.text_target_body.yview(*args)])

        # Ajusta a função de rolagem do mouse para Windows
        def _on_mousewheel(event):
            delta = -1 if event.delta > 0 else 1  # Define o delta com base na direção da rolagem

            self.text_source_body.yview_scroll(delta, "units")
            self.text_target_body.yview_scroll(delta, "units")
            line_numbers.yview_scroll(delta, "units")

        # Vincula o evento de rolagem do mouse para Windows
        self.text_source_body.bind_all("<MouseWheel>", _on_mousewheel)
        self.text_target_body.bind_all("<MouseWheel>", _on_mousewheel)

        def _update_line_numbers():
            line_numbers.config(state="normal")
            line_numbers.delete("1.0", "end")
            max_lines = max(
                int(self.text_source_body.index("end-1c").split(".")[0]),
                int(self.text_target_body.index("end-1c").split(".")[0])
            )
            for i in range(1, max_lines + 1):
                line_numbers.insert("end", f"{i}\n")
            line_numbers.config(state="disabled")

        def _sync_scroll(*args):
            scrollbar_source_y.set(*args)
            scrollbar_target_y.set(*args)
            line_numbers.yview_moveto(args[0])

        def _on_scroll(*args):
            self.text_source_body.yview(*args)
            self.text_target_body.yview(*args)
            line_numbers.yview(*args)

        # Atualiza o comando de rolagem para sincronizar com o contador central
        self.text_source_body['yscrollcommand'] = _sync_scroll
        self.text_target_body['yscrollcommand'] = _sync_scroll
        scrollbar_source_y.config(command=_on_scroll)
        scrollbar_target_y.config(command=_on_scroll)

        # Atualiza o contador de linhas ao modificar o conteúdo
        self.text_source_body.bind("<KeyRelease>", lambda event: _update_line_numbers())
        self.text_target_body.bind("<KeyRelease>", lambda event: _update_line_numbers())
        self.text_source_body.bind("<MouseWheel>", lambda event: _update_line_numbers())
        self.text_target_body.bind("<MouseWheel>", lambda event: _update_line_numbers())

        # Bloqueia os widgets text_source_body e text_target_body para edição
        self.text_source_body.config(state="disabled")
        self.text_target_body.config(state="disabled")

        # Inicializa o contador de linhas
        _update_line_numbers()
        # self._set_source_modification_date("2023-11-15 14:30")
        # self._set_target_modification_date("2023-11-14 09:45")
        self.text_source_body.tag_config("++", background="pale green")
        self.text_source_body.tag_config("--", background="misty rose")
        self.text_source_body.tag_config("~~", background="light goldenrod")

        self.text_target_body.tag_config("++", background="pale green")
        self.text_target_body.tag_config("--", background="misty rose")
        self.text_target_body.tag_config("~~", background="light goldenrod")

    def _handle_source_connection(self, connection_data):
        # Aqui você pode armazenar os dados para uso posterior
        try:
            self.source_connection = dcm(server=connection_data['server_name'],
                                        username=connection_data['user_name'],
                                        password=connection_data['password'],
                                        authentication=connection_data['authentication'],
                                        database=connection_data['database_name'])

            self.btn_select_source.config(
                text=f"{connection_data['server_name']}/{connection_data['database_name']}"
            )
        except:
            self.btn_select_source.config(
                text="Select source",
                state="normal"
            )
            return
        
    def _handle_target_connection(self, connection_data):
        # Aqui você pode armazenar os dados para uso posterior
        try:
            self.target_connection = dcm(server=connection_data['server_name'],
                                        username=connection_data['user_name'],
                                        password=connection_data['password'],
                                        authentication=connection_data['authentication'],
                                        database=connection_data['database_name'])

            self.btn_select_target.config(
                text=f"{connection_data['server_name']}/{connection_data['database_name']}"
            )
        except:
            self.btn_select_target.config(
                text="Select target",
                state="normal"
            )
            return

    def _on_compare_click(self):
        """inicia a comparação entre source e target"""
        if not hasattr(self, 'source_connection') or not hasattr(self, 'target_connection'):
            return
        
        self.source_connection.connect()
        self.target_connection.connect()

        self.source_procedure_schema = self.source_connection.get_procedures_schema()
        self.target_procedure_schema = self.target_connection.get_procedures_schema()

        self.diff_procedures = []
        self.to_create_procedures = []

        target_procs_map = {p['procedure_name']: p for p in self.target_procedure_schema}
        
        comparer = Comparer()
        for source_proc in self.source_procedure_schema:
            target_proc = target_procs_map.get(source_proc['procedure_name'])

            if target_proc:
                # Compara apenas se as datas de modificação forem diferentes
                if source_proc['last_modified_date'] != target_proc['last_modified_date']:
                    source_diff, target_diff = comparer.compare_procedure(
                    source_proc['procedure_body'],
                    target_proc['procedure_body']
                    )

                    # Só adiciona se houver diferenças reais
                    if source_diff is not None and target_diff is not None:
                        self.diff_procedures.append({
                        'id': source_proc['id'],
                        'procedure_name': source_proc['procedure_name'],
                        'source_body': (source_diff),
                        'target_body': (target_diff),
                        'source_modified': source_proc['last_modified_date'],
                        'target_modified': target_proc['last_modified_date']
                        })
                    else:
                        # Procedure não existe no target
                        self.to_create_procedures.append(source_proc)
            self._populate_treeview_with_differences()

    def _populate_treeview_with_differences(self):
        """Popula a treeview com as diferenças encontradas entre source e target"""
        # Limpa a treeview antes de adicionar novos dados
        self.treeview.delete(*self.treeview.get_children())

        for diff in self.diff_procedures:
            action = "Alter"
            
            self.treeview.insert("", "end", iid=diff['id'], values=(
                diff['procedure_name'],
                "Procedure",
                action
            ))

        for proc in self.to_create_procedures:
            action = "Create"
            self.treeview.insert("", "end", iid=proc['id'], values=(
                proc['procedure_name'],
                "Procedure",
                action
            ))

    def _insert_line(self, txt, line, tag=None):
        print(f"Inserindo linha: {line} com tag: {tag}")
        txt.insert(tk.END, line + '\n', tag)

    def _on_treeview_click(self, event):
        """Exibe o conteúdo do objeto selecionado na treeview nos campos de texto"""
        selected_item = self.treeview.selection()
        if not selected_item:
            return
        
        iid = selected_item[0]
        item_values = self.treeview.item(selected_item, "values")
        action = item_values[2]

        # Limpa os campos de texto
        self.text_source_body.config(state="normal")
        self.text_target_body.config(state="normal")
        self.text_source_body.delete("1.0", "end")
        self.text_target_body.delete("1.0", "end")

        # Verifica se é uma diferença ou criação
        if action == "Alter":
            # Busca o objeto na lista de diferenças
            for diff in self.diff_procedures:
                if diff['id'] == int(iid):
                    for l1, l2 in zip(diff['source_body'], diff['target_body']):
                        if len(l1) >= 3:
                            self._insert_line(txt=self.text_source_body, line=l1[2:], tag=l1[:2])
                        else:
                            self._insert_line(txt=self.text_source_body, line=l1, tag=None)

                        if len(l2) >= 3:
                            self._insert_line(txt=self.text_target_body, line=l2[2:], tag=l2[:2])
                        else:
                            self._insert_line(txt=self.text_target_body, line=l2, tag=None)

                    self.text_source_body.config(state=tk.NORMAL)
                    self.text_target_body.config(state=tk.NORMAL)

                    self._set_source_modification_date(diff['source_modified'])
                    self._set_target_modification_date(diff['target_modified'])
                    break

    def _set_source_modification_date(self, date_str):
        """Atualiza a data de modificação do source"""
        self.lbl_source_date.config(text=f"Última modificação: {date_str}")

    def _set_target_modification_date(self, date_str):
        """Atualiza a data de modificação do target"""
        self.lbl_target_date.config(text=f"Última modificação: {date_str}")
        
# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = MainScreen(root)
    root.mainloop()