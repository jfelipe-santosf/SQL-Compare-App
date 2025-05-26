import tkinter as tk

class FilterScreen:
    def __init__(self, master):
        # Criação da janela toplevel
        self.filter_window = tk.Toplevel(master)
        self.filter_window.geometry("400x300")
        self.filter_window.title("filter objects by name")
        # self.filter_window.resizable(False, False)
        self.filter_window.grab_set()  # Garante que a janela de filtro seja modal

        # Adiciona um frame para organizar o Text widget e o Scrollbar
        frame_text = tk.Frame(self.filter_window)
        frame_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Adiciona um scrollbar vertical ao Text widget
        scrollbar = tk.Scrollbar(frame_text, orient="vertical")
        self.text_area = tk.Text(frame_text, wrap="none", font=("Inter", 10), yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text_area.yview)

        # Empacota o Text widget e o Scrollbar
        self.text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botão para salvar ou processar a lista
        self.btn_save = tk.Button(self.filter_window, text="Save", command=self.save_list)
        self.btn_save.pack(pady=5)

    def save_list(self):
        # Obtém o conteúdo do Text widget
        items = self.text_area.get("1.0", "end-1c").splitlines()
        print("Items:", items)  # Exemplo: imprime os itens no console

# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = FilterScreen(root)
    root.mainloop()