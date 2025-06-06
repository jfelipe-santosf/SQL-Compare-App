import tkinter as tk
from tkinter import ttk, messagebox
from app.utils import ScreenNavigationManager as snm, DatabaseConnectionManager as dcm
from app.core import WinMergeLikeComparator as cps

class MainScreen:
    def __init__(self, master):
        # Configuração da janela principal
        self.root = master
        self.root.geometry("1040x585")
        self.root.configure(bg="#F0F0F0")
        self.root.title("SQL Server Compare")
        self.root.resizable(True, True)
        self.root.state('zoomed')

        # Inicialização de variáveis de estado
        self.source_connection = None
        self.target_connection = None
        self.source_procedure_schema = []
        self.target_procedure_schema = []
        self.diff_procedures = []
        self.to_create_procedures = []

        self._setup_ui()
        
    def _setup_ui(self):
        """Configura a interface do usuário"""
        self._create_top_frame()
        self._create_treeview()
        self._create_text_comparison_area()
        self._create_bottom_info_frame()
        
    def _create_top_frame(self):
        """Cria o frame superior com botões de controle"""
        frame_top = tk.Frame(self.root, bg="#FFFFFF", height=60)
        frame_top.pack(fill="x", side="top")
        frame_top.pack_propagate(False)  # Mantém altura fixa

        # Botão Compare
        btn_start_compare = tk.Button(
            frame_top,
            text="Compare",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=self._on_compare_click
        )
        btn_start_compare.place(relx=0.01, rely=0.1, relwidth=0.08, height=25)

        # Botão Filter
        self.btn_filter = tk.Button(
            frame_top,
            text="Filter",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=self._on_filter_click
        )
        self.btn_filter.place(relx=0.095, rely=0.1, relwidth=0.05, height=25)

        # Botão Select Source
        self.btn_select_source = tk.Button(
            frame_top,
            text="Select source",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=self._on_select_source_click
        )
        self.btn_select_source.place(relx=0.01, rely=0.6, relwidth=0.489, height=25)

        # Botão Select Target
        self.btn_select_target = tk.Button(
            frame_top,
            text="Select target",
            bg="#F0F0F0",
            font=("Inter", 10),
            fg="#000000",
            command=self._on_select_target_click
        )
        self.btn_select_target.place(relx=0.5, rely=0.6, relwidth=0.49, height=25)

    def _create_treeview(self):
        """Cria a TreeView para exibir diferenças"""
        frame_treeview = tk.Frame(self.root, bg="#FFFFFF")
        frame_treeview.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("Object Name", "Object Type", "Action")
        self.treeview = ttk.Treeview(
            frame_treeview, 
            columns=columns, 
            show="headings", 
            selectmode="browse"
        )

        # Configuração das colunas
        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, anchor="center")

        # Scrollbar para a TreeView
        tree_scrollbar = ttk.Scrollbar(frame_treeview, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=tree_scrollbar.set)
        
        self.treeview.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Bind do evento de seleção
        self.treeview.bind("<<TreeviewSelect>>", self._on_treeview_select)

    def _create_text_comparison_area(self):
        """Cria a área de comparação de texto"""
        frame_object_body = tk.Frame(self.root)
        frame_object_body.pack(fill="both", expand=True, padx=5, pady=(5, 30))

        # Configuração do grid
        frame_object_body.grid_columnconfigure(0, weight=1)  # Texto fonte
        frame_object_body.grid_columnconfigure(1, weight=0)  # Contador (largura fixa)
        frame_object_body.grid_columnconfigure(2, weight=1)  # Texto alvo
        frame_object_body.grid_rowconfigure(0, weight=1)     # Main content row
        frame_object_body.grid_rowconfigure(1, weight=0)     # Scrollbar row

        # Frame para o texto fonte (esquerda)
        frame_source_scroll = tk.Frame(frame_object_body)
        frame_source_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.text_source_body = tk.Text(
            frame_source_scroll, 
            bg="#FFFFFF", 
            wrap=tk.NONE, 
            undo=True,
            state="disabled"
        )
        self.text_source_body.pack(side="left", fill="both", expand=True)

        # Frame para o contador de linhas (centro)
        frame_line_numbers = tk.Frame(frame_object_body, width=50, bg="#F0F0F0")
        frame_line_numbers.grid(row=0, column=1, sticky="ns")
        frame_line_numbers.grid_propagate(False)

        self.line_numbers = tk.Text(
            frame_line_numbers, 
            width=4, 
            bg="#F0F0F0", 
            state="disabled", 
            wrap="none",
            font=("Courier", 9)
        )
        self.line_numbers.pack(fill="both", expand=True)

        # Frame para o texto alvo (direita)
        frame_target_scroll = tk.Frame(frame_object_body)
        frame_target_scroll.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        self.text_target_body = tk.Text(
            frame_target_scroll, 
            bg="#FFFFFF", 
            wrap=tk.NONE, 
            undo=True,
            state="disabled"
        )
        self.text_target_body.pack(side="left", fill="both", expand=True)

        # Scrollbars
        self._setup_scrollbars(frame_object_body, frame_source_scroll)
        
        # Configuração das tags de colorização
        self._configure_text_tags()

    def _setup_scrollbars(self, frame_object_body, frame_source_scroll):
        """Configura as scrollbars e sincronização"""
        # Scrollbar vertical
        self.v_scroll = tk.Scrollbar(
            frame_source_scroll, 
            orient=tk.VERTICAL, 
            command=self._on_vertical_scroll
        )
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollbar horizontal
        self.h_scroll = tk.Scrollbar(
            frame_object_body, 
            orient=tk.HORIZONTAL, 
            command=self._on_horizontal_scroll
        )
        self.h_scroll.grid(row=1, column=0, columnspan=3, sticky="ew")

        # Configuração dos widgets de texto
        self.text_source_body.config(
            yscrollcommand=self._on_source_y_scroll,
            xscrollcommand=self._on_source_x_scroll
        )
        self.text_target_body.config(
            yscrollcommand=self._on_target_y_scroll,
            xscrollcommand=self._on_target_x_scroll
        )
        self.line_numbers.config(yscrollcommand=lambda *args: None)  # Não atualiza scrollbar

        # Eventos de mouse wheel
        self._bind_mouse_events()

    def _configure_text_tags(self):
        """Configura as tags de colorização para os widgets de texto"""
        # Tags para o texto fonte
        self.text_source_body.tag_config("--", background="#FFE4E1", foreground="#8B0000")  # Removido
        self.text_source_body.tag_config("||", background="#FFF8DC", foreground="#8B4513")  # Modificado
        self.text_source_body.tag_config("  ", background="white", foreground="black")       # Igual

        # Tags para o texto alvo
        self.text_target_body.tag_config("++", background="#F0FFF0", foreground="#006400")   # Adicionado
        self.text_target_body.tag_config("||", background="#FFF8DC", foreground="#8B4513")   # Modificado
        self.text_target_body.tag_config("  ", background="white", foreground="black")        # Igual

    def _bind_mouse_events(self):
        """Configura eventos de mouse wheel para sincronização"""
        def on_mousewheel(event):
            delta = int(-1 * (event.delta / 120)) if event.delta else (-1 if event.num == 4 else 1)
            self._scroll_all_vertical(delta, "units")
            return "break"

        def on_shift_mousewheel(event):
            delta = int(-1 * (event.delta / 120)) if event.delta else (-1 if event.num == 4 else 1)
            self._scroll_all_horizontal(delta, "units")
            return "break"

        # Bind para ambos os widgets de texto
        for widget in [self.text_source_body, self.text_target_body]:
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Shift-MouseWheel>", on_shift_mousewheel)
            widget.bind("<Button-4>", on_mousewheel)  # Linux
            widget.bind("<Button-5>", on_mousewheel)  # Linux

    def _create_bottom_info_frame(self):
        """Cria o frame inferior com informações de data"""
        frame_bottom_info = tk.Frame(self.root, height=25, bg="#F0F0F0", bd=1, relief="sunken")
        frame_bottom_info.pack(side="bottom", fill="x", padx=5, pady=5)
        frame_bottom_info.pack_propagate(False)

        # Label para data do source (esquerda)
        self.lbl_source_date = tk.Label(
            frame_bottom_info,
            text="Source - Última modificação: -",
            bg="#F0F0F0",
            anchor="w",
            padx=10
        )
        self.lbl_source_date.pack(side="left", fill="x", expand=True)

        # Label para data do target (direita)
        self.lbl_target_date = tk.Label(
            frame_bottom_info,
            text="Target - Última modificação: -",
            bg="#F0F0F0",
            anchor="e",
            padx=10
        )
        self.lbl_target_date.pack(side="right", fill="x", expand=True)

    # Métodos de callback para scrollbars
    def _on_vertical_scroll(self, *args):
        """Sincroniza scroll vertical entre todos os widgets"""
        self.text_source_body.yview(*args)
        self.text_target_body.yview(*args)
        self.line_numbers.yview(*args)

    def _on_horizontal_scroll(self, *args):
        """Sincroniza scroll horizontal entre widgets de texto"""
        self.text_source_body.xview(*args)
        self.text_target_body.xview(*args)

    def _on_source_y_scroll(self, *args):
        """Callback para scroll vertical do texto fonte"""
        self.v_scroll.set(*args)
        self.text_target_body.yview_moveto(args[0])
        self.line_numbers.yview_moveto(args[0])

    def _on_target_y_scroll(self, *args):
        """Callback para scroll vertical do texto alvo"""
        self.v_scroll.set(*args)
        self.text_source_body.yview_moveto(args[0])
        self.line_numbers.yview_moveto(args[0])

    def _on_source_x_scroll(self, *args):
        """Callback para scroll horizontal do texto fonte"""
        self.h_scroll.set(*args)
        self.text_target_body.xview_moveto(args[0])

    def _on_target_x_scroll(self, *args):
        """Callback para scroll horizontal do texto alvo"""
        self.h_scroll.set(*args)
        self.text_source_body.xview_moveto(args[0])

    def _scroll_all_vertical(self, delta, what):
        """Rola todos os widgets verticalmente"""
        self.text_source_body.yview_scroll(delta, what)
        self.text_target_body.yview_scroll(delta, what)
        self.line_numbers.yview_scroll(delta, what)

    def _scroll_all_horizontal(self, delta, what):
        """Rola widgets de texto horizontalmente"""
        self.text_source_body.xview_scroll(delta, what)
        self.text_target_body.xview_scroll(delta, what)

    # Métodos de callback para botões
    def _on_filter_click(self):
        """Callback para o botão Filter"""
        try:
            snm(self.root).navigate_to_filter_screen({
                'x': self.btn_filter.winfo_rootx(),
                'y': self.btn_filter.winfo_rooty()
            })
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir filtros: {str(e)}")

    def _on_select_source_click(self):
        """Callback para o botão Select Source"""
        try:
            snm(self.root).navigate_to_connect_screen(
                {
                    'x': self.btn_select_source.winfo_rootx() + 100,
                    'y': self.btn_select_source.winfo_rooty()
                },
                self._handle_source_connection
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir conexão source: {str(e)}")

    def _on_select_target_click(self):
        """Callback para o botão Select Target"""
        try:
            snm(self.root).navigate_to_connect_screen(
                {
                    'x': self.btn_select_target.winfo_rootx(),
                    'y': self.btn_select_target.winfo_rooty()
                },
                self._handle_target_connection
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir conexão target: {str(e)}")

    def _handle_source_connection(self, connection_data):
        """Manipula dados de conexão do source"""
        if not connection_data:
            return

        try:
            self.source_connection = dcm(
                server=connection_data['server_name'],
                username=connection_data['user_name'],
                password=connection_data['password'],
                authentication=connection_data['authentication'],
                database=connection_data['database_name']
            )
            
            # Testa a conexão
            test_conn = self.source_connection.connect()
            if test_conn:
                test_conn.close()
                
            self.btn_select_source.config(
                text=f"{connection_data['server_name']}/{connection_data['database_name']}"
            )
            print("Fonte conectada:", connection_data)
            
        except Exception as e:
            self.source_connection = None
            self.btn_select_source.config(text="Select source")
            messagebox.showerror("Erro de Conexão", f"Erro ao conectar com source: {str(e)}")

    def _handle_target_connection(self, connection_data):
        """Manipula dados de conexão do target"""
        if not connection_data:
            return

        try:
            self.target_connection = dcm(
                server=connection_data['server_name'],
                username=connection_data['user_name'],
                password=connection_data['password'],
                authentication=connection_data['authentication'],
                database=connection_data['database_name']
            )
            
            # Testa a conexão
            test_conn = self.target_connection.connect()
            if test_conn:
                test_conn.close()
                
            self.btn_select_target.config(
                text=f"{connection_data['server_name']}/{connection_data['database_name']}"
            )
            print("Alvo conectado:", connection_data)
            
        except Exception as e:
            self.target_connection = None
            self.btn_select_target.config(text="Select target")
            messagebox.showerror("Erro de Conexão", f"Erro ao conectar com target: {str(e)}")

    def _on_compare_click(self):
        """Inicia a comparação entre source e target"""
        if not self._validate_connections():
            return

        try:
            # Limpa dados anteriores
            self._clear_previous_results()
            
            # Indica que a comparação está em andamento
            self.root.config(cursor="wait")
            self.root.update()

            # Conecta e obtém schemas
            self._get_procedure_schemas()
            
            # Realiza a comparação
            self._perform_comparison()
            
            # Popula a TreeView com os resultados
            self._populate_treeview_with_differences()
            
            messagebox.showinfo("Sucesso", f"Comparação concluída!\n"
                              f"Procedures alteradas: {len(self.diff_procedures)}\n"
                              f"Procedures para criar: {len(self.to_create_procedures)}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante a comparação: {str(e)}")
            print(f"Erro durante a comparação: {str(e)}")
        finally:
            self.root.config(cursor="")

    def _validate_connections(self):
        """Valida se as conexões estão configuradas"""
        if not self.source_connection:
            messagebox.showwarning("Atenção", "Selecione a conexão source primeiro.")
            return False
        
        if not self.target_connection:
            messagebox.showwarning("Atenção", "Selecione a conexão target primeiro.")
            return False
            
        return True

    def _clear_previous_results(self):
        """Limpa resultados de comparações anteriores"""
        self.diff_procedures.clear()
        self.to_create_procedures.clear()
        self.treeview.delete(*self.treeview.get_children())
        self._clear_text_widgets()

    def _get_procedure_schemas(self):
        """Obtém os schemas das procedures de ambas as conexões"""
        # Conecta e obtém procedures do source
        source_conn = self.source_connection.connect()
        try:
            self.source_procedure_schema = self.source_connection.get_procedures_schema()
        finally:
            if source_conn:
                source_conn.close()

        # Conecta e obtém procedures do target
        target_conn = self.target_connection.connect()
        try:
            self.target_procedure_schema = self.target_connection.get_procedures_schema()
        finally:
            if target_conn:
                target_conn.close()

    def _perform_comparison(self):
        """Realiza a comparação entre os schemas"""
        comparer = cps()
        target_procs_map = {p['procedure_name']: p for p in self.target_procedure_schema}

        for source_proc in self.source_procedure_schema:
            target_proc = target_procs_map.get(source_proc['procedure_name'])

            if target_proc:
                # Procedure existe em ambos - verifica se há diferenças
                source_diff, target_diff = comparer.compare(
                    text1=source_proc['procedure_body'],
                    text2=target_proc['procedure_body']
                )

                # Só adiciona se houver diferenças reais
                if comparer.has_differences():
                    self.diff_procedures.append({
                        'procedure_name': source_proc['procedure_name'],
                        'source_body': source_diff,
                        'target_body': target_diff,
                        'source_modified': source_proc.get('last_modified_date', 'N/A'),
                        'target_modified': target_proc.get('last_modified_date', 'N/A'),
                        'source_proc': source_proc,
                        'target_proc': target_proc
                    })
            else:
                # Procedure não existe no target
                self.to_create_procedures.append(source_proc)

    def _populate_treeview_with_differences(self):
        """Popula a TreeView com as diferenças encontradas"""
        # Adiciona procedures com diferenças
        for diff in self.diff_procedures:
            self.treeview.insert("", "end", values=(
                diff['procedure_name'],
                "Procedure",
                "Alter"
            ))

        # Adiciona procedures que precisam ser criadas
        for proc in self.to_create_procedures:
            self.treeview.insert("", "end", values=(
                proc['procedure_name'],
                "Procedure",
                "Create"
            ))

    def _on_treeview_select(self, event):
        """Manipula seleção na TreeView"""
        selected_items = self.treeview.selection()
        if not selected_items:
            return

        item = selected_items[0]
        item_values = self.treeview.item(item, "values")
        
        if not item_values:
            return
            
        object_name = item_values[0]
        action = item_values[2]

        self._display_object_content(object_name, action)

    def _display_object_content(self, object_name, action):
        """Exibe o conteúdo do objeto selecionado"""
        self._clear_text_widgets()

        if action == "Alter":
            self._display_altered_procedure(object_name)
        elif action == "Create":
            self._display_create_procedure(object_name)

        self._update_line_numbers()

    def _display_altered_procedure(self, object_name):
        """Exibe procedure alterada com diff colorizado"""
        for diff in self.diff_procedures:
            if diff['procedure_name'] == object_name:
                # Insere texto fonte
                self._insert_text_with_coloring(
                    self.text_source_body, 
                    diff['source_body']
                )
                
                # Insere texto alvo
                self._insert_text_with_coloring(
                    self.text_target_body, 
                    diff['target_body']
                )
                
                # Atualiza datas
                self._set_source_modification_date(diff['source_modified'])
                self._set_target_modification_date(diff['target_modified'])
                break

    def _display_create_procedure(self, object_name):
        """Exibe procedure que precisa ser criada"""
        for proc in self.to_create_procedures:
            if proc['procedure_name'] == object_name:
                # Texto fonte com a procedure completa
                self.text_source_body.config(state="normal")
                self.text_source_body.insert("1.0", proc['procedure_body'])
                self.text_source_body.config(state="disabled")
                
                # Texto alvo vazio
                self.text_target_body.config(state="normal")
                self.text_target_body.insert("1.0", "-- Procedure não existe no target")
                self.text_target_body.config(state="disabled")
                
                # Atualiza datas
                self._set_source_modification_date(proc.get('last_modified_date', 'N/A'))
                self._set_target_modification_date('N/A')
                break

    def _insert_text_with_coloring(self, text_widget, content):
        """Insere texto com colorização baseada nos prefixos"""
        text_widget.config(state="normal")
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            
            # Insere a linha
            text_widget.insert("end", line + '\n')
            
            # Aplica tag baseada no prefixo
            if line.startswith("++"):
                text_widget.tag_add("++", line_start, f"{i+1}.end")
            elif line.startswith("--"):
                text_widget.tag_add("--", line_start, f"{i+1}.end")
            elif line.startswith("||"):
                text_widget.tag_add("||", line_start, f"{i+1}.end")
            else:
                text_widget.tag_add("  ", line_start, f"{i+1}.end")
        
        text_widget.config(state="disabled")

    def _clear_text_widgets(self):
        """Limpa os widgets de texto"""
        for widget in [self.text_source_body, self.text_target_body]:
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.config(state="disabled")

    def _update_line_numbers(self):
        """Atualiza o contador de linhas"""
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        
        # Calcula o número máximo de linhas
        max_lines = max(
            int(self.text_source_body.index("end-1c").split(".")[0]),
            int(self.text_target_body.index("end-1c").split(".")[0])
        )
        
        # Insere números das linhas
        for i in range(1, max_lines + 1):
            self.line_numbers.insert("end", f"{i:3d}\n")
            
        self.line_numbers.config(state="disabled")

    def _set_source_modification_date(self, date_str):
        """Atualiza a data de modificação do source"""
        self.lbl_source_date.config(text=f"Source - Última modificação: {date_str}")

    def _set_target_modification_date(self, date_str):
        """Atualiza a data de modificação do target"""
        self.lbl_target_date.config(text=f"Target - Última modificação: {date_str}")


# Exemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    app = MainScreen(root)
    root.mainloop()