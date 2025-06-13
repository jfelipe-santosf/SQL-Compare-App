import tkinter as tk
from tkinter import ttk
from app.utils import ScreenNavigationManager as snm, DatabaseConnectionManager as dcm
from app.core import CompareProcedureSchema as cps

class MainScreen:
    def __init__(self, master):
        self.comparer = cps()
        # Configuração da janela principal
        self.root = master
        self.root.geometry("1040x585")
        self.root.configure(bg="#F0F0F0")
        self.root.title("SQL Server Compare")
        self.root.resizable(True, True)
        self.root.state('zoomed')

        # [...] (o restante do código de inicialização permanece igual até a parte dos widgets de texto)

        # Frame para o texto fonte (esquerda)
        frame_source_scroll = tk.Frame(frame_object_body)
        frame_source_scroll.grid(row=0, column=0, sticky="nsew", padx=(0,5))

        scrollbar_source_y = tk.Scrollbar(frame_source_scroll, orient="vertical")
        scrollbar_source_y.pack(side="right", fill="y")
        scrollbar_source_x = tk.Scrollbar(frame_source_scroll, orient="horizontal")
        scrollbar_source_x.pack(side="bottom", fill="x")

        self.text_source_body = tk.Text(frame_source_scroll, bg="#FFFFFF", wrap="none", 
                                 yscrollcommand=self._sync_scroll_y,
                                 xscrollcommand=scrollbar_source_x.set)
        self.text_source_body.pack(side="left", fill="both", expand=True)

        scrollbar_source_y.config(command=self._yview_all)
        scrollbar_source_x.config(command=self.text_source_body.xview)

        # Frame para o contador de linhas (centro)
        self.frame_line_numbers = tk.Frame(frame_object_body, width=30)
        self.frame_line_numbers.grid(row=0, column=1, sticky="ns")

        # Contador de linhas
        self.line_numbers = tk.Text(self.frame_line_numbers, width=4, bg="#F0F0F0", state="disabled", wrap="none")
        self.line_numbers.pack(side="left", fill="y")

        # Frame para o texto alvo (direita)
        frame_target_scroll = tk.Frame(frame_object_body)
        frame_target_scroll.grid(row=0, column=2, sticky="nsew", padx=(5,0))

        scrollbar_target_y = tk.Scrollbar(frame_target_scroll, orient="vertical")
        scrollbar_target_y.pack(side="right", fill="y")
        scrollbar_target_x = tk.Scrollbar(frame_target_scroll, orient="horizontal")
        scrollbar_target_x.pack(side="bottom", fill="x")

        self.text_target_body = tk.Text(frame_target_scroll, bg="#FFFFFF", wrap="none", 
                                 yscrollcommand=self._sync_scroll_y,
                                 xscrollcommand=scrollbar_target_x.set)
        self.text_target_body.pack(side="left", fill="both", expand=True)

        scrollbar_target_y.config(command=self._yview_all)
        scrollbar_target_x.config(command=self.text_target_body.xview)

        # [...] (o restante do código de inicialização permanece igual)

        # Configurações de sincronização de scroll
        self._setup_scroll_sync()

    def _setup_scroll_sync(self):
        """Configura a sincronização de scroll entre os painéis"""
        # Configura os comandos de scroll vertical
        self.text_source_body['yscrollcommand'] = self._sync_scroll_y
        self.text_target_body['yscrollcommand'] = self._sync_scroll_y
        
        # Configura os comandos de scroll horizontal (opcional, se necessário)
        self.text_source_body['xscrollcommand'] = lambda *args: self._sync_scroll_x(args, source=True)
        self.text_target_body['xscrollcommand'] = lambda *args: self._sync_scroll_x(args, source=False)
        
        # Vincula os eventos de teclado e mouse para sincronização
        self.text_source_body.bind("<MouseWheel>", self._on_mousewheel)
        self.text_target_body.bind("<MouseWheel>", self._on_mousewheel)
        self.text_source_body.bind("<Button-4>", self._on_mousewheel)  # Para Linux
        self.text_source_body.bind("<Button-5>", self._on_mousewheel)  # Para Linux
        self.text_target_body.bind("<Button-4>", self._on_mousewheel)  # Para Linux
        self.text_target_body.bind("<Button-5>", self._on_mousewheel)  # Para Linux
        
        # Vincula as setas do teclado
        self.text_source_body.bind("<Up>", lambda e: self._keyboard_scroll("up"))
        self.text_source_body.bind("<Down>", lambda e: self._keyboard_scroll("down"))
        self.text_target_body.bind("<Up>", lambda e: self._keyboard_scroll("up"))
        self.text_target_body.bind("<Down>", lambda e: self._keyboard_scroll("down"))
        
        # Vincula Page Up/Down
        self.text_source_body.bind("<Prior>", lambda e: self._keyboard_scroll("pageup"))
        self.text_source_body.bind("<Next>", lambda e: self._keyboard_scroll("pagedown"))
        self.text_target_body.bind("<Prior>", lambda e: self._keyboard_scroll("pageup"))
        self.text_target_body.bind("<Next>", lambda e: self._keyboard_scroll("pagedown"))

    def _sync_scroll_y(self, *args):
        """Sincroniza o scroll vertical entre os painéis"""
        # Atualiza ambas as scrollbars verticais
        self.text_source_body.yview_moveto(args[0])
        self.text_target_body.yview_moveto(args[0])
        self.line_numbers.yview_moveto(args[0])
        
        # Atualiza o contador de linhas
        self._update_line_numbers()

    def _sync_scroll_x(self, args, source=True):
        """Sincroniza o scroll horizontal entre os painéis (opcional)"""
        if source:
            self.text_target_body.xview_moveto(args[0])
        else:
            self.text_source_body.xview_moveto(args[0])

    def _yview_all(self, *args):
        """Comando de scroll vertical para todos os painéis"""
        self.text_source_body.yview(*args)
        self.text_target_body.yview(*args)
        self.line_numbers.yview(*args)

    def _on_mousewheel(self, event):
        """Manipula o evento de rolagem do mouse"""
        if event.num == 4 or event.delta > 0:  # Rolar para cima (Linux/Windows)
            self._yview_all("scroll", "-1", "units")
        elif event.num == 5 or event.delta < 0:  # Rolar para baixo (Linux/Windows)
            self._yview_all("scroll", "1", "units")
        return "break"  # Previne o comportamento padrão

    def _keyboard_scroll(self, direction):
        """Manipula a rolagem pelo teclado"""
        if direction == "up":
            self._yview_all("scroll", "-1", "units")
        elif direction == "down":
            self._yview_all("scroll", "1", "units")
        elif direction == "pageup":
            self._yview_all("scroll", "-1", "pages")
        elif direction == "pagedown":
            self._yview_all("scroll", "1", "pages")
        return "break"  # Previne o comportamento padrão

    def _update_line_numbers(self):
        """Atualiza o contador de linhas central"""
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        
        # Obtém o número máximo de linhas entre os dois painéis
        source_lines = int(self.text_source_body.index("end-1c").split(".")[0])
        target_lines = int(self.text_target_body.index("end-1c").split(".")[0])
        max_lines = max(source_lines, target_lines)
        
        # Adiciona os números das linhas
        for i in range(1, max_lines + 1):
            self.line_numbers.insert("end", f"{i}\n")
        
        self.line_numbers.config(state="disabled")
        
        # Sincroniza a posição vertical do contador de linhas
        first_visible_line = self.text_source_body.index("@0,0").split(".")[0]
        self.line_numbers.yview_moveto(self.text_source_body.yview()[0])

    # [...] (o restante dos métodos permanece igual)