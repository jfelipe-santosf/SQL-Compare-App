import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import pyodbc

class ConnectionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Select Connection")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Store the connection info
        self.selected_connection = None
        self.load_recent_connections()
        
        self.create_ui()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
    def create_ui(self):
        # Recent connections list
        list_frame = ttk.LabelFrame(self, text="Select Connection", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create columns
        columns = ("server", "database")
        self.conn_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        self.conn_tree.heading("server", text="Server name")
        self.conn_tree.heading("database", text="Database")
        
        # Configure column widths
        self.conn_tree.column("server", width=250)
        self.conn_tree.column("database", width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.conn_tree.yview)
        self.conn_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack list and scrollbar
        self.conn_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load recent connections
        self.populate_recent_connections()
        
        # Connection details frame
        details_frame = ttk.LabelFrame(self, text="Connection Details", padding=10)
        details_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        
        # Server name
        server_frame = ttk.Frame(details_frame)
        server_frame.pack(fill=tk.X, pady=5)
        ttk.Label(server_frame, text="Server name:", width=15, anchor='e').pack(side=tk.LEFT, padx=5)
        self.server_entry = ttk.Entry(server_frame)
        self.server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Authentication
        auth_frame = ttk.Frame(details_frame)
        auth_frame.pack(fill=tk.X, pady=5)
        ttk.Label(auth_frame, text="Authentication:", width=15, anchor='e').pack(side=tk.LEFT, padx=5)
        self.auth_combo = ttk.Combobox(auth_frame, values=["Windows Authentication", "SQL Server Authentication"], state="readonly")
        self.auth_combo.set("Windows Authentication")
        self.auth_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Username
        user_frame = ttk.Frame(details_frame)
        user_frame.pack(fill=tk.X, pady=5)
        ttk.Label(user_frame, text="User name:", width=15, anchor='e').pack(side=tk.LEFT, padx=5)
        self.user_entry = ttk.Entry(user_frame, state="disabled")
        self.user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Password
        pass_frame = ttk.Frame(details_frame)
        pass_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pass_frame, text="Password:", width=15, anchor='e').pack(side=tk.LEFT, padx=5)
        self.pass_entry = ttk.Entry(pass_frame, show="*", state="disabled")
        self.pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
          # Database
        db_frame = ttk.Frame(details_frame)
        db_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_frame, text="Database:", width=15, anchor='e').pack(side=tk.LEFT, padx=5)
        self.db_combo = ttk.Combobox(db_frame)
        self.db_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Remember checkbox
        remember_frame = ttk.Frame(details_frame)
        remember_frame.pack(fill=tk.X, pady=5)
        self.remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(remember_frame, text="Remember", variable=self.remember_var).pack(side=tk.LEFT, padx=20)
        
        # Buttons
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Connect", command=self.connect).pack(side=tk.RIGHT, padx=5)
        
        # Bind events
        self.auth_combo.bind('<<ComboboxSelected>>', self.on_auth_change)
        self.conn_tree.bind('<<TreeviewSelect>>', self.on_connection_select)
        self.conn_tree.bind('<Double-1>', lambda e: self.connect())
          # Bind database combo to fetch databases when clicked
        self.db_combo.bind('<Button-1>', lambda e: self.fetch_databases())
        # Fetch databases when dropdown list is requested
        self.db_combo.bind('<<ComboboxClicked>>', lambda e: self.fetch_databases())
        
    def fetch_databases(self):
        server = self.server_entry.get().strip()
        if not server:
            messagebox.showwarning("Warning", "Please enter a server name first.")
            return
            
        try:
            # Build connection string based on authentication type
            if self.auth_combo.get() == "Windows Authentication":
                conn_str = f'DRIVER={{SQL Server}};SERVER={server};Trusted_Connection=yes;'
            else:
                username = self.user_entry.get().strip()
                password = self.pass_entry.get().strip()
                if not username or not password:
                    messagebox.showwarning("Warning", "Please enter username and password.")
                    return
                conn_str = f'DRIVER={{SQL Server}};SERVER={server};UID={username};PWD={password}'
            
            # Connect and fetch databases
            conn = pyodbc.connect(conn_str, timeout=3)
            cursor = conn.cursor()
            databases = [row.name for row in cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")]  # Skip system DBs
            conn.close()
            
            # Update combobox
            current_value = self.db_combo.get()
            self.db_combo['values'] = databases
            if current_value in databases:
                self.db_combo.set(current_value)
            elif databases:
                self.db_combo.set(databases[0])
                
        except pyodbc.Error as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def on_server_changed(self):
        # Clear and update databases when server changes
        self.db_combo.set('')
        self.db_combo['values'] = []
        self.fetch_databases()
        
    def on_auth_change(self, event=None):
        if self.auth_combo.get() == "Windows Authentication":
            self.user_entry.configure(state="disabled")
            self.pass_entry.configure(state="disabled")
        else:
            self.user_entry.configure(state="normal")
            self.pass_entry.configure(state="normal")
        # Refresh databases with new authentication
        self.fetch_databases()
            
    def on_connection_select(self, event=None):
        selection = self.conn_tree.selection()
        if selection:
            item = self.conn_tree.item(selection[0])
            conn = next((c for c in self.recent_connections if 
                       c["server"] == item["values"][0] and 
                       c["database"] == item["values"][1]), None)
            if conn:
                self.server_entry.delete(0, tk.END)
                self.server_entry.insert(0, conn["server"])
                self.auth_combo.set(conn["authentication"])
                if "username" in conn:
                    self.user_entry.delete(0, tk.END)
                    self.user_entry.insert(0, conn["username"])
                if "database" in conn:
                    self.db_combo.set(conn["database"])
                self.on_auth_change()
                
    def connect(self):
        self.selected_connection = {
            "server": self.server_entry.get(),
            "authentication": self.auth_combo.get(),
            "username": self.user_entry.get() if self.auth_combo.get() == "SQL Server Authentication" else None,
            "password": self.pass_entry.get() if self.auth_combo.get() == "SQL Server Authentication" else None,
            "database": self.db_combo.get()
        }
        
        if self.remember_var.get():
            self.save_connection(self.selected_connection)
            
        self.destroy()
        
    def cancel(self):
        self.selected_connection = None
        self.destroy()
        
    def load_recent_connections(self):
        try:
            with open('recent_connections.json', 'r') as f:
                self.recent_connections = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.recent_connections = []
            
    def save_connection(self, connection):
        # Remove password before saving
        conn_to_save = connection.copy()
        if "password" in conn_to_save:
            del conn_to_save["password"]
            
        # Check if connection already exists
        existing = next((i for i, c in enumerate(self.recent_connections)
                        if c["server"] == conn_to_save["server"] and
                        c["database"] == conn_to_save["database"]), None)
                        
        if existing is not None:
            self.recent_connections.pop(existing)
            
        # Add new connection at the beginning
        self.recent_connections.insert(0, conn_to_save)
        
        # Keep only last 10 connections
        self.recent_connections = self.recent_connections[:10]
        
        # Save to file
        with open('recent_connections.json', 'w') as f:
            json.dump(self.recent_connections, f, indent=2)
            
    def populate_recent_connections(self):
        # Clear existing items
        for item in self.conn_tree.get_children():
            self.conn_tree.delete(item)
            
        # Add recent connections
        for conn in self.recent_connections:
            self.conn_tree.insert("", tk.END, values=(conn["server"], conn["database"]))
