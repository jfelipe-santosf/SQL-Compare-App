import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Exemplo Treeview com Menu de Contexto")

        # Frame
        frame_treeview = ttk.Frame(root)
        frame_treeview.pack(fill="both", expand=True)

        # Treeview
        self.tree = ttk.Treeview(frame_treeview, columns=("col1",), show="headings")
        self.tree.heading("col1", text="Nome da Conexão")
        self.tree.pack(fill="both", expand=True)

        # Preenche a treeview com exemplo
        for i in range(3):
            self.tree.insert("", "end", values=(f"Conexão {i+1}",))

        # Menu de contexto
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Refresh", command=self.get_saved_connections)
        self.menu.add_command(label="Remover", command=self.remover_item)

        # Bind do botão direito
        self.tree.bind("<Button-3>", self.mostrar_menu)

    def get_saved_connections(self):
        print("Recarregando conexões...")

    def remover_item(self):
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)

    def mostrar_menu(self, event):
        # Seleciona o item sob o mouse antes de mostrar o menu
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.menu.tk_popup(event.x_root, event.y_root)

root = tk.Tk()
App(root)
root.mainloop()
