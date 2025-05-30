import tkinter as tk
from tkinter import ttk
import os
from test_utils import test_database_connection_manager, test_saved_connections_manager

class ConnectScreen:
    def __init__(self, master):
        # Criação da janela toplevel
        self.connect_window = tk.Toplevel(master)
        self.connect_window.geometry("390x490")
        self.connect_window.resizable(False, False)
        self.connect_window.configure(bg="#FFFFFF")
        self.connect_window.title("Select connection")
        self.connect_window.grab_set()  # Garante que a janela de conexão seja modal

        # Treeview para histórico de conexões
        frame_treeview = tk.Frame(self.connect_window, width=390, height=274)
        frame_treeview.place(x=0, y=0)

        columns = ("Server", "Database")
        treeview = ttk.Treeview(frame_treeview, columns=columns, show="headings", height=12)

        treeview.heading("Server", text="Server")
        treeview.heading("Database", text="Database")

        treeview.column("Server", width=195, anchor="center")
        treeview.column("Database", width=195, anchor="center")

        treeview.pack(fill="both", expand=True)

        # Menu de entrada
        frame_entry_menu = tk.Frame(self.connect_window, width=390, height=236, bg="#F0F0F0")
        frame_entry_menu.place(x=0, y=264)

        # Server name
        frame_server_name = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_server_name.place(x=0, y=21)
        label_server_name = tk.Label(frame_server_name, text="Server name:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_server_name.place(x=10, y=0)
        self.entry_server_name = tk.Entry(frame_server_name, width=30, bg="#FFFEFE")
        self.entry_server_name.place(x=120, y=0)

        # Authentication
        frame_authentication = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_authentication.place(x=0, y=52)
        label_authentication = tk.Label(frame_authentication, text="Authentication:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_authentication.place(x=10, y=0)

        # Substitui o entry_authentication por um dropdown
        self.dropdown_authentication = ttk.Combobox(frame_authentication, width=27, state="readonly")
        self.dropdown_authentication.place(x=120, y=0)
        self.dropdown_authentication['values'] = ("Windows Authentication", "SQL Authentication")
        self.dropdown_authentication.current(0)  # Define como padrão "Windows Authentication"
        def update_authentication(event):
            if self.dropdown_authentication.get() == "Windows Authentication":
                self.entry_user_name.config(state="normal")
                self.entry_user_name.delete(0, "end")
                self.entry_user_name.insert(0, os.getlogin())  # Insere o usuário do Windows
                self.entry_user_name.config(state="disabled")
                self.entry_password.config(state="disabled")
            else:
                self.entry_user_name.config(state="normal")
                self.entry_user_name.delete(0, "end")
                self.entry_password.config(state="normal")

        self.dropdown_authentication.bind("<<ComboboxSelected>>", update_authentication)

        # User name
        frame_user_name = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_user_name.place(x=0, y=84)
        label_user_name = tk.Label(frame_user_name, text="User name:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_user_name.place(x=10, y=0)
        self.entry_user_name = tk.Entry(frame_user_name, width=30, bg="#FFFEFE")
        self.entry_user_name.place(x=120, y=0)

        # Password
        frame_password = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_password.place(x=0, y=116)
        label_password = tk.Label(frame_password, text="Password:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_password.place(x=10, y=0)
        self.entry_password = tk.Entry(frame_password, width=30, bg="#FFFEFE", show="*")
        self.entry_password.place(x=120, y=0)

        # Database Name
        frame_database_name = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_database_name.place(x=0, y=146)
        label_database_name = tk.Label(frame_database_name, text="Database Name:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_database_name.place(x=10, y=0)

        # Cria um combobox para seleção de opções
        self.dropdown_database_name = ttk.Combobox(frame_database_name, width=27)
        self.dropdown_database_name.place(x=120, y=0)

        self.dropdown_database_name.bind("<Button-1>", self.get_databases)

        # Check Remember
        frame_check_remember = tk.Frame(frame_entry_menu, width=100, height=21, bg="#F0F0F0")
        frame_check_remember.place(x=10, y=190)
        check_remember = tk.Checkbutton(frame_check_remember, text="Remember", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        check_remember.pack(anchor="w", padx=2)

        # Botões Cancel e Connect
        btn_cancel = tk.Button(frame_entry_menu, text="Cancel", font=("Inter", 10), bg="#FFFFFF", fg="#000000", command=self.connect_window.destroy)
        btn_cancel.place(x=145, y=190, width=80, height=20)

        self.btn_connect = tk.Button(frame_entry_menu, text="Connect", font=("Inter", 10), bg="#FFFFFF", fg="#000000")
        self.btn_connect.place(x=265, y=190, width=80, height=20)

        update_authentication(None)  # Chama a função para configurar o estado inicial

        # Função para obter os bancos de dados disponíveis
    def get_databases(self, event):
        self.dropdown_database_name['values'] = []
        server_name = self.entry_server_name.get()
        user_name = self.entry_user_name.get()
        password = self.entry_password.get()
        authentication = self.dropdown_authentication.get()

        if not server_name:
            return

        if authentication == "Windows Authentication":
            user_name = None
            password = None
        else:
            if not user_name or not password:
                return

        try:
            print('Connecting to database...')
            self.db_conn = test_database_connection_manager.DatabaseConnectionManager(
                server=server_name,
                username=user_name,
                password=password,
                authentication=authentication
            )
            self.db_conn.connect()
            databases = self.db_conn.get_all_databases()
            if databases:
                self.dropdown_database_name['values'] = databases
            else:
                self.dropdown_database_name['values'] = ["No databases found"]
        except Exception as e:
            ttk.messagebox.showerror("Error", f"Failed to connect to the database: {e}")
            print(f"Error fetching databases: {e}")
    def save_connection(self):
        server_name = self.entry_server_name.get()
        user_name = self.entry_user_name.get()
        password = self.entry_password.get()
        authentication = self.dropdown_authentication.get()
        database_name = self.dropdown_database_name.get()



        # Aqui você pode salvar a conexão em um arquivo ou banco de dados
        print(f"Connection saved: {server_name}, {user_name}, {authentication}, {database_name}")

# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = ConnectScreen(root)
    root.mainloop()