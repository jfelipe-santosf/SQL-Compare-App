import tkinter as tk

class FilterScreen:
    def __init__(self, master, position: dict):
        # Criação da janela toplevel
        self.filter_window = tk.Toplevel(master)
        self.filter_window.geometry(f"400x300+{position['x']}+{position['y']+20}")
        self.filter_window.title("filter objects by name")
        self.filter_window.resizable(False, False)
        self.filter_window.grab_set()  # Garante que a janela de filtro seja modal

        # Configurações da janela principal
        self.filter_window.configure(bg="#F0F0F0")

        # Adiciona um frame para organizar o Text widget e o Scrollbar
        frame_text = tk.Frame(self.filter_window, bg="#FFFFFF", width=400, height=250)
        frame_text.place(x=0, y=0)

        # Adiciona um scrollbar vertical ao Text widget
        scrollbar = tk.Scrollbar(frame_text, orient="vertical", bg="#F0F0F0")
        self.text_area = tk.Text(frame_text, wrap="none", font=("Inter", 10), yscrollcommand=scrollbar.set, bg="#FFFFFF")
        scrollbar.config(command=self.text_area.yview)

        # Posiciona o Text widget e o Scrollbar
        self.text_area.place(x=0, y=0, width=385, height=250)
        scrollbar.place(x=385, y=0, width=15, height=250)

        # Adiciona botões Cancelar e Adicionar
        btn_cancel = tk.Button(self.filter_window, text="Cancel", font=("Inter", 12), bg="#FFFFFF", fg="#000000", command=self.filter_window.destroy)
        btn_cancel.place(x=90, y=266, width=100, height=21)

        btn_add = tk.Button(self.filter_window, text="Add", font=("Inter", 12), bg="#FFFFFF", fg="#000000", command=self.add_item)
        btn_add.place(x=210, y=266, width=100, height=21)

    def save_list(self):
        # Obtém o conteúdo do Text widget
        items = self.text_area.get("1.0", "end-1c").splitlines()
        print("Items:", items)  # Exemplo: imprime os itens no console

    def add_item(self):
        # Adiciona um item ao Text widget
        self.text_area.insert("end", "New Item\n")

# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = FilterScreen(root)
    root.mainloop()