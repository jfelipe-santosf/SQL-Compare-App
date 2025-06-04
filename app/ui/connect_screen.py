import tkinter as tk
from tkinter import ttk, messagebox
import os, threading
from app.utils import DatabaseConnectionManager as dcm, SavedConnectionsManager as scm

class ConnectScreen:
    def __init__(self, master, position: dict, on_connect_callback=None):
        # define gerenciadores de janelas e callbacks
        self.on_connect_callback = on_connect_callback
        self.was_cancelled = True
        # Criação da janela toplevel
        self.connect_window = tk.Toplevel(master)
        self.connect_window.geometry(f"390x490+{position['x']}+{position['y']+20}")
        self.connect_window.resizable(False, False)
        self.connect_window.configure(bg="#FFFFFF")
        self.connect_window.title("Select connection")
        self.connect_window.grab_set()  # Garante que a janela de conexão seja modal
        self.connect_window.transient(master)  # Define a janela como filha da janela principal

        # Treeview para histórico de conexões
        frame_treeview = tk.Frame(self.connect_window, width=390, height=274)
        frame_treeview.place(x=0, y=0)

        columns = ("Server", "Database")
        self.treeview = ttk.Treeview(frame_treeview, columns=columns, show="headings", height=12, selectmode="browse")

        self.treeview.heading("Server", text="Server")
        self.treeview.heading("Database", text="Database")

        self.treeview.column("Server", width=195, anchor="center")
        self.treeview.column("Database", width=195, anchor="center")

        self.treeview.pack(fill="both", expand=True)

        # cria menu de contexto
        self.menu = tk.Menu(self.connect_window, tearoff=0)

        self.menu.add_command(label="Refresh", command=self.get_saved_connections)
        self.menu.add_separator()
        self.menu.add_command(label="Connect", command=self.menu_connect)
        self.menu.add_command(label="Delete", command=self._delete_selected_connection)
        self.menu.add_separator()
        self.menu.add_command(label="Clear historic connection", command= self.clear_historic_connections)
        self.menu.add_command(label="Exit", command=self._on_window_close)

        # Menu de entrada
        frame_entry_menu = tk.Frame(self.connect_window, width=390, height=236, bg="#F0F0F0")
        frame_entry_menu.place(x=0, y=264)

        # nome do servidor
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

        # tipo de autenticação
        self.dropdown_authentication = ttk.Combobox(frame_authentication, width=27, state="readonly")
        self.dropdown_authentication.place(x=120, y=0)
        self.dropdown_authentication['values'] = ("Windows Authentication", "SQL Authentication")
        self.dropdown_authentication.current(0)  # Define como padrão "Windows Authentication"

        # Atualiza os campos de autenticação quando o tipo é alterado
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

        # nome do usuário
        frame_user_name = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_user_name.place(x=0, y=84)
        label_user_name = tk.Label(frame_user_name, text="User name:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_user_name.place(x=10, y=0)
        self.entry_user_name = tk.Entry(frame_user_name, width=30, bg="#FFFEFE")
        self.entry_user_name.place(x=120, y=0)

        # senha
        frame_password = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_password.place(x=0, y=116)
        label_password = tk.Label(frame_password, text="Password:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_password.place(x=10, y=0)
        self.entry_password = tk.Entry(frame_password, width=30, bg="#FFFEFE", show="*")
        self.entry_password.place(x=120, y=0)

        # nome do banco de dados
        frame_database_name = tk.Frame(frame_entry_menu, width=390, height=21, bg="#F0F0F0")
        frame_database_name.place(x=0, y=146)
        label_database_name = tk.Label(frame_database_name, text="Database Name:", font=("Inter", 10), bg="#F0F0F0", fg="#000000")
        label_database_name.place(x=10, y=0)
        self.dropdown_database_name = ttk.Combobox(frame_database_name, width=27)
        self.dropdown_database_name.place(x=120, y=0)

        # Check Remember
        frame_check_remember = tk.Frame(frame_entry_menu, width=100, height=21, bg="#F0F0F0")
        frame_check_remember.place(x=15, y=185)
        self.var_check_remember = tk.BooleanVar(value=False)  # Variável para o estado do checkbox
        self.check_remember = tk.Checkbutton(frame_check_remember, text="Remember", font=("Inter", 10), bg="#F0F0F0", fg="#000000", variable=self.var_check_remember)
        self.check_remember.pack(anchor="w", padx=2)

        # Botões Cancel e Connect
        btn_cancel = tk.Button(frame_entry_menu, text="Cancel", font=("Inter", 10), bg="#FFFFFF", fg="#000000", command=self._on_window_close)
        btn_cancel.place(x=145, y=190, width=80, height=20)

        self.btn_connect = tk.Button(frame_entry_menu, text="Connect", font=("Inter", 10), bg="#FFFFFF", fg="#000000",
                                     command=self.on_connect_btn)
        self.btn_connect.place(x=265, y=190, width=80, height=20)
        
        update_authentication(None)
        self.get_saved_connections()

        # Bindings e eventos
        self.connect_window.bind("<Return>", lambda event: self.on_connect_btn())
        self.connect_window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self.treeview.bind("<Button-3>", self.show_context_menu)
        self.treeview.bind("<ButtonRelease-1>", self.on_treeview_select)
        self.treeview.bind("<double-Button-1>", self.menu_connect)
        self.dropdown_database_name.bind("<Button-1>", lambda e: threading.Thread(target=self.get_databases).start())

    def _delete_selected_connection(self):
        """ Exclui a conexão selecionada no Treeview.
        Se nenhuma conexão estiver selecionada, exibe um aviso."""
        
        selected_items = self.treeview.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No connection selected to delete.")
            return
        
        iid = selected_items[0]
        conn_data = None
        
        # Encontra os dados da conexão selecionada
        for conn in self.connections:
            if conn.get("connection_id") == iid:
                conn_data = conn
                break
        
        if not conn_data:
            return
        
        # Confirmação
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Delete connection:\nServer: {conn_data['server_name']}\nDatabase: {conn_data['database_name']}?"
        )
        if not confirm:
            return

        try:
            # Remove da lista interna e do arquivo
            scm().delete_connection(connection_id=iid)
        
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
                db_conn = dcm(
                    server=server_name,
                    username=user_name,
                    password=password,
                    authentication=authentication
                )
                db_conn.connect()
                databases = db_conn.get_all_databases()
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
            self.connections = scm().get_all_connections()

            # Limpa o Treeview antes de adicionar novas conexões
            self.treeview.delete(*self.treeview.get_children())

            # Verifica se há conexões salvas
            if not self.connections:
                return
            
            # Preenche o Treeview com as conexões salvas
            for conn in self.connections:
                # Adiciona cada conexão ao Treeview
                self.treeview.insert("", "end", iid=conn["connection_id"], values=(conn["server_name"], conn["database_name"]))

        except Exception as e:
            # Log de erro (opcional)
            messagebox.showerror("Error", f"Failed to load saved connections: {e}")
    
    def on_connect_btn(self):
        if not self._validate_fields():
            return
        connection_data = {
            "server_name": self.entry_server_name.get(),
            "user_name": self.entry_user_name.get() if self.dropdown_authentication.get() == "SQL Authentication" else None,
            "password": self.entry_password.get() if self.dropdown_authentication.get() == "SQL Authentication" else None,
            "authentication": self.dropdown_authentication.get(),
            "database_name": self.dropdown_database_name.get()
        }
        
        if self.var_check_remember.get():
            self.save_connection(connection_data)

        self.was_cancelled = False
        if self.on_connect_callback:
            self.on_connect_callback(connection_data)
        self.connect_window.destroy()

    def menu_connect(self):
        iid = self.treeview.selection()[0]  # Obtém o ID do item selecionado
        for connection in self.connections:
            if connection["connection_id"] == iid:
                connection_data = {
                    "server_name": connection["server_name"],
                    "user_name": connection["user_name"],
                    "password": connection["password"],
                    "authentication": connection["authentication"],
                    "database_name": connection["database_name"]
                }
        if self.var_check_remember.get():
            self.save_connection(connection_data)
        
        self.was_cancelled = False
        if self.on_connect_callback:
            self.on_connect_callback(connection_data)
        self.connect_window.destroy()

    def on_treeview_select(self, event):
        selected_items = self.treeview.selection()  # Obtém os itens selecionados
        if not selected_items:
            return
        iid = selected_items[0]  # Pega o primeiro item selecionado

        # Encontra a conexão correspondente no dicionário salvo
        for conn in self.connections:
            if conn["connection_id"] == iid:
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

    def save_connection(self, connection_data):
        server_name = connection_data["server_name"]
        user_name = connection_data["user_name"]
        password = connection_data["password"]
        authentication = connection_data["authentication"]
        database_name = connection_data["database_name"]

        scm().save_connection(
            server_name=server_name,
            user_name=user_name,
            password=password,
            authentication=authentication,
            database_name=database_name
        )

    def _validate_fields(self):
        """
        Valida os campos de entrada para garantir que estão preenchidos corretamente.
        
        Returns:
            bool: True se todos os campos estiverem válidos, False caso contrário.
        """
        if not self.entry_server_name.get():
            messagebox.showwarning("Warning", "Server name is required.")
            return False
        if self.dropdown_authentication.get() == "SQL Authentication":
            if not self.entry_user_name.get() or not self.entry_password.get():
                messagebox.showwarning("Warning", "User name and password are required for SQL Authentication.")
                return False
        if not self.dropdown_database_name.get():
            messagebox.showwarning("Warning", "Database name is required.")
            return False
        return True
    
    def show_context_menu(self, event):
        """Exibe o menu de contexto quando o botão direito é clicado na Treeview"""
        try:
            row_id = self.treeview.identify_row(event.y)

            if row_id:
                self.treeview.selection_set(row_id)
                self.menu.entryconfig("Connect", state="normal")
                self.menu.entryconfig("Delete", state="normal")
            else:
                self.treeview.selection_remove(self.treeview.selection())
                self.menu.entryconfig("Connect", state="disabled")
                self.menu.entryconfig("Delete", state="disabled")
            if not self.treeview.get_children():
                self.menu.entryconfig("Clear historic connection", state="disabled")
            else:
                self.menu.entryconfig("Clear historic connection", state="normal")
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def clear_historic_connections(self):
        """Remove todas as conexões salvas"""
        confirm = messagebox.askyesno(
            "Clear All Connections",
            "This will delete ALL saved connections.\nAre you sure you want to continue?",
            icon='warning'
        )
        
        if confirm:
            try:
                scm().delete_all_connections()
                self.get_saved_connections()
                messagebox.showinfo("Success", "All connections have been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear connections: {str(e)}")

    def _on_window_close(self):
        """Chamado quando a janela é fechada sem conectar"""
        if self.on_connect_callback:
            self.on_connect_callback(None)  # Envia None para indicar cancelamento
        self.connect_window.destroy()

# Exemplo de como abrir a tela
if __name__ == "__main__":
    root = tk.Tk()
    app = ConnectScreen(root)
    root.mainloop()