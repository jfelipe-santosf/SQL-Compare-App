import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict
import pyodbc

from ..utils.connection_manager import ConnectionManager
from ..core.schema_comparer import SchemaComparerService, ConnectionError, DatabaseError

class ConnectionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Select Connection")
        self.geometry("500x600")
        self.resizable(False, False)
        self.connection_manager = ConnectionManager()
        self.selected_connection = None
        self.schema_comparer = SchemaComparerService()
        
        # Progress tracking
        self.progress_visible = False
        self.progress_bar = None  # Initialize as None
        self.status_label = None  # Initialize as None
        
        # Track if databases have been fetched
        self.databases_fetched = False
        
        self.create_ui()
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
        self.db_combo = ttk.Combobox(db_frame, state="readonly")
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
        
        # Status and progress frame
        status_frame = ttk.Frame(details_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        
        # Pack progress bar but hide it initially
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_bar.pack_forget()

        # Bind events
        self.auth_combo.bind('<<ComboboxSelected>>', self.on_auth_change)
        self.conn_tree.bind('<<TreeviewSelect>>', self.on_connection_select)
        self.conn_tree.bind('<Double-1>', lambda e: self.connect())
        self.db_combo.bind('<Button-1>', self.on_db_combo_click)

    def populate_recent_connections(self):
        # Clear the treeview
        for i in self.conn_tree.get_children():
            self.conn_tree.delete(i)
        
        # Get recent connections from the manager
        recent_connections = self.connection_manager.get_recent_connections()
        
        # Insert into treeview
        for conn in recent_connections:
            self.conn_tree.insert("", tk.END, values=(conn["server"], conn["database"]))

    def show_progress(self, show: bool = True):
        """Show or hide progress bar with animation"""
        if not self.progress_bar:
            return
            
        try:
            if show and not self.progress_visible:
                self.progress_bar.pack(side=tk.RIGHT, padx=5)
                self.progress_bar.start(10)
                self.progress_visible = True
            elif not show and self.progress_visible:
                try:
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                except tk.TclError:
                    pass  # Widget might have been destroyed
                self.progress_visible = False
            self.update_idletasks()
        except (tk.TclError, AttributeError):
            pass  # Handle any Tkinter errors gracefully

    def update_status(self, message: str, show_progress: bool = False, error: bool = False):
        """Update status message and optionally show progress"""
        if not self.status_label:
            return
            
        try:
            self.status_label.config(
                text=message,
                foreground="red" if error else "gray"
            )
            self.show_progress(show_progress)
            self.update_idletasks()
        except tk.TclError:
            pass  # Handle any Tkinter errors gracefully

    def on_db_combo_click(self, event):
        """Handle database combo click event"""
        if not self.databases_fetched:
            self.fetch_databases()

    def fetch_databases(self):
        """Fetch available databases from the server with improved error handling"""
        server = self.server_entry.get().strip()
        if not server:
            messagebox.showwarning("Warning", "Please enter a server name first.")
            return
            
        self.update_status("Connecting to server...", True)
        
        try:
            # Build connection details
            auth_type = self.auth_combo.get()
            username = None
            password = None
            
            if auth_type != "Windows Authentication":
                username = self.user_entry.get().strip()
                password = self.pass_entry.get().strip()
                if not username or not password:
                    self.update_status("Username and password are required", False, True)
                    return

            # Try to connect to master database first
            conn = self.schema_comparer.connect(
                server, "master", auth_type, username, password
            )
            
            self.update_status("Retrieving databases...", True)
            
            # Get user databases and sort them
            cursor = conn.cursor()
            databases = [row.name for row in cursor.execute(
                "SELECT name FROM sys.databases WHERE database_id > 4 AND state_desc = 'ONLINE'"
            )]
            databases.sort()  # Sort databases alphabetically
            conn.close()
            
            # Update combobox
            current_value = self.db_combo.get()
            self.db_combo['values'] = databases
            if current_value in databases:
                self.db_combo.set(current_value)
            elif databases:
                self.db_combo.set(databases[0])
                
            self.update_status(f"Found {len(databases)} databases", False)
            self.databases_fetched = True
                
        except ConnectionError as e:
            self.update_status(str(e), False, True)
            messagebox.showerror("Connection Error", str(e))
        except Exception as e:
            self.update_status("Failed to retrieve databases", False, True)
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.show_progress(False)
            
    def on_auth_change(self, event=None):
        """Handle authentication type change."""
        if self.auth_combo.get() == "Windows Authentication":
            self.user_entry.configure(state="disabled")
            self.pass_entry.configure(state="disabled")
        else:
            self.user_entry.configure(state="normal")
            self.pass_entry.configure(state="normal")
            
    def on_connection_select(self, event=None):
        """Handle selection of a saved connection."""
        selection = self.conn_tree.selection()
        if not selection:
            return
            
        item = self.conn_tree.item(selection[0])
        recent_connections = self.connection_manager.get_recent_connections()
        
        try:
            conn = next((c for c in recent_connections if 
                      c["server"] == item["values"][0] and 
                      c["database"] == item["values"][1]), None)
                      
            if not conn:
                return
                
            # Update server
            self.server_entry.delete(0, tk.END)
            self.server_entry.insert(0, conn["server"])
            
            # Update authentication
            self.auth_combo.set(conn.get("authentication", "Windows Authentication"))
            
            # Enable entries temporarily to update their values
            self.user_entry.configure(state="normal")
            self.pass_entry.configure(state="normal")
            
            # Clear fields
            self.user_entry.delete(0, tk.END)
            self.pass_entry.delete(0, tk.END)
            
            # Update SQL Server Authentication fields if needed
            if conn.get("authentication") == "SQL Server Authentication":
                if conn.get("username"):
                    self.user_entry.insert(0, conn["username"])
                if conn.get("password"):
                    self.pass_entry.insert(0, conn["password"])
            else:
                # Disable for Windows Authentication
                self.user_entry.configure(state="disabled")
                self.pass_entry.configure(state="disabled")
            
            # Update database if available
            if conn.get("database"):
                self.db_combo.set(conn["database"])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load connection details: {str(e)}")
            
    def connect(self):
        """Handle connection button click with improved error handling"""
        try:
            # Get and validate inputs
            server = self.server_entry.get().strip()
            database = self.db_combo.get().strip()
            auth_type = self.auth_combo.get()
            
            if not server or not database:
                messagebox.showwarning("Warning", "Please enter both server name and database.")
                return
                
            self.update_status("Testing connection...", True)
                
            # Build connection details
            self.selected_connection = {
                "server": server,
                "database": database,
                "authentication": auth_type
            }
            
            # Add SQL Server Authentication details if needed
            if auth_type == "SQL Server Authentication":
                username = self.user_entry.get().strip()
                password = self.pass_entry.get().strip()
                
                if not username or not password:
                    self.update_status("Username and password are required", False, True)
                    return
                    
                self.selected_connection.update({
                    "username": username,
                    "password": password
                })
            
            # Test the connection before saving
            conn = self.schema_comparer.connect(
                server, database, auth_type,
                self.selected_connection.get("username"),
                self.selected_connection.get("password")
            )
            conn.close()
            
            # Save connection if requested
            if self.remember_var.get():
                self.connection_manager.add_connection(self.selected_connection)
            
            self.destroy()
            
        except ConnectionError as e:
            self.update_status(str(e), False, True)
            messagebox.showerror("Connection Error", str(e))
            self.selected_connection = None
        except Exception as e:
            self.update_status("Failed to establish connection", False, True)
            messagebox.showerror("Error", f"Failed to save connection: {str(e)}")
            self.selected_connection = None
        finally:
            self.show_progress(False)
    
    def cancel(self):
        """Handle cancel button click."""
        self.selected_connection = None
        self.destroy()
