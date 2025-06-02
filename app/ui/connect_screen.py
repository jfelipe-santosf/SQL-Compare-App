import tkinter as tk
from tkinter import ttk, messagebox
import os
from app.utils import database_connection_manager, saved_connections_manager
import threading

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
        self.treeview = ttk.Treeview(frame_treeview, columns=columns, show="headings", height=12)

        self.treeview.heading("Server", text="Server")
        self.treeview.heading("Database", text="Database")

        self.treeview.column("Server", width=195, anchor="center")
        self.treeview.column("Database", width=195, anchor="center")

        self.treeview.pack(fill="both", expand=True)

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

        self.dropdown_database_name.bind("<Button-1>", lambda e: threading.Thread(target=self.get_databases).start())

        # Check Remember
        frame_check_remember = tk.Frame(frame_entry_menu, width=100, height=21, bg="#F0F0F0")
        frame_check_remember.place(x=10, y=190)
        self.check_remember = tk.Checkbutton(frame_check_remember, text="Remember", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        self.check_remember.pack(anchor="w", padx=2)

        # Botões Cancel e Connect
        btn_cancel = tk.Button(frame_entry_menu, text="Cancel", font=("Inter", 10), bg="#FFFFFF", fg="#000000", command=self.connect_window.destroy)
        btn_cancel.place(x=190, y=190, width=80, height=20)

        self.btn_connect = tk.Button(frame_entry_menu, text="Connect", font=("Inter", 10), bg="#FFFFFF", fg="#000000",
                                     command=self.connect)
        self.btn_connect.place(x=275, y=190, width=80, height=20)

        self.btn_delete = tk.Button(
            frame_entry_menu, text="Delete", font=("Inter", 10),
            bg="#FFFFFF", fg="#000000", command=self.delete_selected_connection
        )
        self.btn_delete.place(x=105, y=190, width=80, height=20)

        self.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)
        
        update_authentication(None)
        self.get_saved_connections()
    
    def connect(self):
        if self.check_remember.var.get():
            # Salva a conexão se a opção "Remember" estiver marcada
            self.save_connection()

    def delete_selected_connection(self):
        selected_item = self.treeview.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "No connection selected to delete.")
            return

        values = self.treeview.item(selected_item, 'values')
        if not values:
            return

        server, database = values

        # Confirmação
        confirm = messagebox.askyesno("Confirm Delete", f"Delete connection:\nServer: {server}\nDatabase: {database}?")
        if not confirm:
            return

        try:
            # Remove da lista interna e do arquivo
            scm = saved_connections_manager.SavedConnectionsManager()
            scm.delete_connection(server_name=server, database_name=database)

            # Atualiza o Treeview
            self.get_saved_connections()
            messagebox.showinfo("Success", "Connection deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete connection: {e}")
        
        # Função para obter os bancos de dados disponíveis
    def get_databases(self, event=None):
        def run():
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
                self.db_conn = database_connection_manager.DatabaseConnectionManager(
                    server=server_name,
                    username=user_name,
                    password=password,
                    authentication=authentication
                )
                self.db_conn.connect()
                databases = self.db_conn.get_all_databases()
                self.connect_window.after(0, lambda: self.dropdown_database_name.config(
                    values=databases if databases else ["No databases found"]
                ))
            except Exception as e:
                print(f"Error fetching databases: {e}")

        threading.Thread(target=run).start()


    def get_saved_connections(self):
        """
        Obtém todas as conexões salvas do gerenciador de conexões.
        
        Returns:
            list: Lista de dicionários contendo todas as conexões salvas,
                ordenadas pela data de modificação (mais recente primeiro).
                Cada conexão contém:
                - server_name (str)
                - user_name (str)
                - password (str, descriptografada)
                - authentication (str)
                - database_name (str)
                - last_modified (str, ISO format)
                
        Example:
            [
                {
                    "server_name": "server1",
                    "user_name": "user1",
                    "password": "mypassword",
                    "authentication": "Windows",
                    "database_name": "db1",
                    "last_modified": "2023-05-15T12:30:45.123456"
                },
                ...
            ]
        """
        try:
            # Obtém todas as conexões do gerenciador
            self.connections = saved_connections_manager.SavedConnectionsManager().get_all_connections()

            # Limpa o Treeview antes de adicionar novas conexões
            self.treeview.delete(*self.treeview.get_children())

            # Verifica se há conexões salvas
            if not self.connections:
                return
            
            # Preenche o Treeview com as conexões salvas
            for conn in self.connections:
                # Adiciona cada conexão ao Treeview
                self.treeview.insert("", "end", values=(conn["server_name"], conn["database_name"]))

        except Exception as e:
            # Log de erro (opcional)
            messagebox.showerror("Error", f"Failed to load saved connections: {e}")
            
    def on_treeview_select(self, event):
        selected_item = self.treeview.focus()  # Obtém o item selecionado
        if not selected_item:
            return

        values = self.treeview.item(selected_item, 'values')  # Retorna (server, database)
        server, database = values

        # Encontra a conexão correspondente no dicionário salvo
        for conn in self.connections:
            if conn["server_name"] == server and conn["database_name"] == database:
                # Preenche os campos
                self.entry_server_name.delete(0, tk.END)
                self.entry_server_name.insert(0, conn["server_name"])

                self.dropdown_authentication.set(conn["authentication"])

                # Atualiza os campos de autenticação de acordo com a seleção
                if conn["authentication"] == "Windows Authentication":
                    self.entry_user_name.config(state="normal")
                    self.entry_user_name.delete(0, tk.END)
                    self.entry_user_name.insert(0, os.getlogin())
                    self.entry_user_name.config(state="disabled")
                    self.entry_password.config(state="disabled")
                else:
                    self.entry_user_name.config(state="normal")
                    self.entry_user_name.delete(0, tk.END)
                    self.entry_user_name.insert(0, conn["user_name"])

                    self.entry_password.config(state="normal")
                    self.entry_password.delete(0, tk.END)
                    self.entry_password.insert(0, conn["password"])

                self.dropdown_database_name.set(conn["database_name"])
                break

    def save_connection(self):
        server_name = self.entry_server_name.get()
        user_name = self.entry_user_name.get()
        password = self.entry_password.get()
        authentication = self.dropdown_authentication.get()
        database_name = self.dropdown_database_name.get()

        saved_connections_manager.SavedConnectionsManager().save_connection(
            server_name=server_name,
            user_name=user_name,
            password=password,
            authentication=authentication,
            database_name=database_name
        )
        # Aqui você pode salvar a conexão em um arquivo ou banco de dados
        print(f"Connection saved: {server_name}, {user_name}, {authentication}, {database_name}")

# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = ConnectScreen(root)
    root.mainloop()