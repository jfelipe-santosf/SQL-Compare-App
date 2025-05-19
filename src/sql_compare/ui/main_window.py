import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Set, List
import pyodbc
from tkinter import simpledialog
import os

from .connection_dialog import ConnectionDialog
from ..core.schema_comparer import SchemaComparerService
from .icons import Icons

class FilterDialog(tk.Toplevel):
    def __init__(self, parent, current_filters=None):
        super().__init__(parent)
        self.title("Filter Objects")
        self.geometry("400x500")
        self.resizable(False, False)
        
        self.current_filters = current_filters or set()
        self.result = None
        
        self.create_ui()
        self.transient(parent)
        self.grab_set()

    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, 
                 text="Enter object names to filter (one per line):").pack(fill=tk.X)
        
        # Text area for filters
        self.filter_text = tk.Text(main_frame, wrap=tk.WORD, height=20)
        self.filter_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text widget
        self.filter_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.filter_text.yview)
        
        # Set current filters
        if self.current_filters:
            self.filter_text.insert('1.0', '\n'.join(sorted(self.current_filters)))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", 
                  command=self.apply).pack(side=tk.RIGHT)

    def apply(self):
        """Get filter text and split into set of names"""
        text = self.filter_text.get('1.0', tk.END).strip()
        if text:
            self.result = {name.strip() for name in text.split('\n') if name.strip()}
        else:
            self.result = set()
        self.destroy()

    def cancel(self):
        """Cancel without changing filters"""
        self.result = None
        self.destroy()

class SchemaCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Server Schema Compare")
        self.root.geometry("1200x800")
        
        # Initialize services
        self.schema_comparer = SchemaComparerService()
        
        # Initialize storage
        self.source_connection = None
        self.target_connection = None
        self.filtered_objects: Set[str] = set()
        
        # Load icons
        self.icons = Icons()
        
        # Progress tracking
        self.progress_visible = False
        
        self.create_ui()
        
    def create_ui(self):
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Top panel containing connections - now horizontal
        top_panel = ttk.LabelFrame(main_container, text="Database Selection")
        top_panel.pack(fill=tk.X, padx=5, pady=5)
        
        # Container for source and target frames
        connections_frame = ttk.Frame(top_panel)
        connections_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Source connection frame - left side
        source_frame = ttk.Frame(connections_frame)
        source_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        ttk.Label(source_frame, text="Source:").pack(side=tk.LEFT)
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.source_entry.insert(0, "Select Source")
        self.source_entry.configure(state='readonly')
        self.source_entry.bind('<Button-1>', lambda e: self.show_connection_dialog('source'))
        
        # Target connection frame - right side
        target_frame = ttk.Frame(connections_frame)
        target_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        
        ttk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(target_frame)
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.target_entry.insert(0, "Select Target")
        self.target_entry.configure(state='readonly')
        self.target_entry.bind('<Button-1>', lambda e: self.show_connection_dialog('target'))

        # Toolbar
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
          # Compare button
        self.compare_btn = ttk.Button(
            toolbar, 
            text="Compare",
            command=self.compare_schemas,
            width=10,
            image=self.icons.compare,
            compound=tk.LEFT
        )
        self.compare_btn.pack(side=tk.LEFT, padx=2)
        
        # Update button
        self.update_btn = ttk.Button(
            toolbar,
            text="Update",
            command=self.update_schema,
            width=10,
            image=self.icons.update,
            compound=tk.LEFT
        )
        self.update_btn.pack(side=tk.LEFT, padx=2)
        
        # Filter button
        self.filter_btn = ttk.Button(
            toolbar,
            text="Filter",
            command=self.show_filter_dialog,
            width=10,
            image=self.icons.filter,
            compound=tk.LEFT
        )
        self.filter_btn.pack(side=tk.LEFT, padx=2)
        
        # Main content area
        content = ttk.Frame(main_container)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Horizontal split view
        self.paned_window = ttk.PanedWindow(content, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel - Results tree
        results_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(results_frame, weight=1)
          # Create treeview for displaying differences
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("Object", "Type", "Action", "Difference"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure headings
        self.results_tree.heading("Object", text="Object Name")
        self.results_tree.heading("Type", text="Object Type")
        self.results_tree.heading("Action", text="Action")
        self.results_tree.heading("Difference", text="Difference")
          # Configure columns
        self.results_tree.column("Object", width=250, anchor="w")
        self.results_tree.column("Type", width=100, anchor="center")
        self.results_tree.column("Action", width=100, anchor="center")
        self.results_tree.column("Difference", width=200, anchor="w")
        
        # Configure tags for different states
        self.results_tree.tag_configure("different", foreground="#FFA500")  # Orange
        self.results_tree.tag_configure("source_only", foreground="#4CAF50")  # Green
        self.results_tree.tag_configure("target_only", foreground="#F44336")  # Red
        
        # Add scrollbar to results
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        # Pack results view
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right panel - Object definitions - Now side by side
        definitions_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(definitions_frame, weight=2)
        
        # Make definitions frame expand horizontally
        definitions_frame.columnconfigure(0, weight=1)
        definitions_frame.columnconfigure(1, weight=1)
        
        # Source definition frame - left side
        source_frame = ttk.LabelFrame(definitions_frame, text="Source")
        source_frame.grid(row=0, column=0, sticky='nsew', padx=(0,2))
        
        self.source_text = tk.Text(source_frame, wrap=tk.NONE, font=('Consolas', 10))
        source_vsb = ttk.Scrollbar(source_frame, orient=tk.VERTICAL, command=self.source_text.yview)
        source_hsb = ttk.Scrollbar(source_frame, orient=tk.HORIZONTAL, command=self.source_text.xview)
        self.source_text.configure(yscrollcommand=source_vsb.set, xscrollcommand=source_hsb.set)
        
        self.source_text.grid(row=0, column=0, sticky='nsew')
        source_vsb.grid(row=0, column=1, sticky='ns')
        source_hsb.grid(row=1, column=0, sticky='ew')
        
        source_frame.grid_columnconfigure(0, weight=1)
        source_frame.grid_rowconfigure(0, weight=1)
        
        # Target definition frame - right side
        target_frame = ttk.LabelFrame(definitions_frame, text="Target")
        target_frame.grid(row=0, column=1, sticky='nsew', padx=(2,0))
        
        self.target_text = tk.Text(target_frame, wrap=tk.NONE, font=('Consolas', 10))
        target_vsb = ttk.Scrollbar(target_frame, orient=tk.VERTICAL, command=self.target_text.yview)
        target_hsb = ttk.Scrollbar(target_frame, orient=tk.HORIZONTAL, command=self.target_text.xview)
        self.target_text.configure(yscrollcommand=target_vsb.set, xscrollcommand=target_hsb.set)
        
        self.target_text.grid(row=0, column=0, sticky='nsew')
        target_vsb.grid(row=0, column=1, sticky='ns')
        target_hsb.grid(row=1, column=0, sticky='ew')
        
        target_frame.grid_columnconfigure(0, weight=1)
        target_frame.grid_rowconfigure(0, weight=1)
        
        # Configure text tags for highlighting differences
        self.source_text.tag_configure('diff', background='#FFE3E3')  # Light red
        self.target_text.tag_configure('diff', background='#E3FFE3')  # Light green
        
        # Synchronize scrolling between source and target
        def on_source_scroll(*args):
            self.target_text.yview_moveto(args[0])
        def on_target_scroll(*args):
            self.source_text.yview_moveto(args[0])
            
        self.source_text.configure(yscrollcommand=lambda *args: (source_vsb.set(*args), on_source_scroll(args[0])))
        self.target_text.configure(yscrollcommand=lambda *args: (target_vsb.set(*args), on_target_scroll(args[0])))
        
        # Status and progress bar frame
        self.status_frame = ttk.Frame(main_container)
        self.status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Status bar
        self.status_bar = ttk.Label(self.status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate', length=200)
        
        # Bind selection event
        self.results_tree.bind('<<TreeviewSelect>>', self.on_item_selected)
        
    def show_progress(self, show: bool = True):
        """Show or hide progress bar with animation"""
        if show and not self.progress_visible:
            self.progress_bar.pack(side=tk.RIGHT, padx=5)
            self.progress_bar.start(10)
            self.progress_visible = True
        elif not show and self.progress_visible:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.progress_visible = False
        self.root.update_idletasks()

    def update_status(self, message: str, show_progress: bool = False):
        """Update status bar message and optionally show progress"""
        self.status_bar.config(text=message)
        self.show_progress(show_progress)
        self.root.update_idletasks()
        
    def show_filter_dialog(self):
        """Show the filter dialog and update filters"""
        dialog = FilterDialog(self.root, self.filtered_objects)
        self.root.wait_window(dialog)
        
        if dialog.result is not None:
            self.filtered_objects = dialog.result
            self.compare_schemas()  # Refresh the comparison with new filters
    
    def highlight_differences(self, source_text, target_text):
        """Highlight differences between source and target text"""
        source_lines = source_text.splitlines()
        target_lines = target_text.splitlines()
        
        # Clear existing text and tags
        self.source_text.delete('1.0', tk.END)
        self.target_text.delete('1.0', tk.END)
        
        # Compare line by line
        for i, (source_line, target_line) in enumerate(zip_longest(source_lines, target_lines, fillvalue="")):
            # Add source line
            if source_line != target_line:
                self.source_text.insert(tk.END, source_line + '\n', 'diff')
            else:
                self.source_text.insert(tk.END, source_line + '\n')
                
            # Add target line
            if source_line != target_line:
                self.target_text.insert(tk.END, target_line + '\n', 'diff')
            else:
                self.target_text.insert(tk.END, target_line + '\n')

    def display_column_differences(self, source_cols: List[Dict], target_cols: List[Dict]) -> None:
        """Display column differences between source and target tables with highlighting"""
        source_text = "Source Table Columns:\n" + "-" * 50 + "\n"
        target_text = "Target Table Columns:\n" + "-" * 50 + "\n"
        
        source_lines = []
        target_lines = []
        
        # Prepare all column details
        all_columns = set()
        if source_cols:
            all_columns.update(col['column_name'] for col in source_cols)
        if target_cols:
            all_columns.update(col['column_name'] for col in target_cols)
            
        source_dict = {col['column_name']: col for col in source_cols}
        target_dict = {col['column_name']: col for col in target_cols}
        
        # Compare columns
        for col_name in sorted(all_columns):
            source_col = source_dict.get(col_name)
            target_col = target_dict.get(col_name)
            
            if source_col:
                source_lines.append(self.format_column_details(source_col))
            else:
                source_lines.append(f"-- Column {col_name} does not exist --")
                
            if target_col:
                target_lines.append(self.format_column_details(target_col))
            else:
                target_lines.append(f"-- Column {col_name} does not exist --")
                
        # Join lines and highlight differences
        self.highlight_differences('\n'.join(source_lines), '\n'.join(target_lines))

    def on_item_selected(self, event):
        """Handle tree item selection with improved difference highlighting"""
        selection = self.results_tree.selection()
        if not selection:
            return
            
        item = self.results_tree.item(selection[0])
        object_name = item['values'][0]
        object_type = item['values'][1]
        
        if not self.source_connection or not self.target_connection:
            return
            
        try:
            self.status_bar.config(text=f"Loading {object_type.lower()} details for {object_name}...")
            
            source_conn = self.schema_comparer.connect(
                self.source_connection["server"],
                self.source_connection["database"],
                self.source_connection["authentication"],
                self.source_connection.get("username"),
                self.source_connection.get("password")
            )
            
            target_conn = self.schema_comparer.connect(
                self.target_connection["server"],
                self.target_connection["database"],
                self.target_connection["authentication"],
                self.target_connection.get("username"),
                self.target_connection.get("password")
            )
            
            # Get object IDs
            source_objects = self.schema_comparer.get_schema_objects(source_conn)
            target_objects = self.schema_comparer.get_schema_objects(target_conn)
            
            source_obj = next((obj for obj in source_objects 
                             if f"{obj['schema_name']}.{obj['object_name']}" == object_name), None)
            target_obj = next((obj for obj in target_objects 
                             if f"{obj['schema_name']}.{obj['object_name']}" == object_name), None)
            
            if object_type == "Table" and source_obj:
                # For tables, show column differences
                source_cols = self.schema_comparer.get_table_columns(source_conn, source_obj['object_id'])
                target_cols = []
                if target_obj:
                    target_cols = self.schema_comparer.get_table_columns(target_conn, target_obj['object_id'])
                self.display_column_differences(source_cols, target_cols)
                
            else:
                # For stored procedures, show definitions with highlighting
                source_def = ""
                if source_obj:
                    source_def = self.schema_comparer.get_object_definition(source_conn, source_obj['object_id'])
                
                target_def = ""
                if target_obj:
                    target_def = self.schema_comparer.get_object_definition(target_conn, target_obj['object_id'])
                
                # Update text widgets with highlighting
                self.highlight_differences(
                    source_def if source_def else "-- Object does not exist in source --",
                    target_def if target_def else "-- Object does not exist in target --"
                )
            
            source_conn.close()
            target_conn.close()
            
            self.status_bar.config(text="Ready")
            
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to load object details: {str(e)}")
    
    def show_connection_dialog(self, connection_type):
        dialog = ConnectionDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.selected_connection:
            conn_info = f"{dialog.selected_connection['server']}\\{dialog.selected_connection['database']}"
            if connection_type == "source":
                self.source_connection = dialog.selected_connection
                self.source_entry.configure(state='normal')
                self.source_entry.delete(0, tk.END)
                self.source_entry.insert(0, conn_info)
                self.source_entry.configure(state='readonly')
            else:
                self.target_connection = dialog.selected_connection
                self.target_entry.configure(state='normal')
                self.target_entry.delete(0, tk.END)
                self.target_entry.insert(0, conn_info)
                self.target_entry.configure(state='readonly')
                
    def compare_schemas(self):
        if not self.source_connection or not self.target_connection:
            messagebox.showwarning("Warning", "Please select both source and target connections first.")
            return
            
        try:
            self.update_status("Connecting to databases...", True)
            
            # Clear existing items in the tree
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Connect to databases
            try:
                source_conn = self.schema_comparer.connect(
                    self.source_connection["server"],
                    self.source_connection["database"],
                    self.source_connection["authentication"],
                    self.source_connection.get("username"),
                    self.source_connection.get("password")
                )
            except pyodbc.Error as e:
                raise ConnectionError(f"Failed to connect to source database: {str(e)}")
            
            try:
                target_conn = self.schema_comparer.connect(
                    self.target_connection["server"],
                    self.target_connection["database"],
                    self.target_connection["authentication"],
                    self.target_connection.get("username"),
                    self.target_connection.get("password")
                )
            except pyodbc.Error as e:
                source_conn.close()
                raise ConnectionError(f"Failed to connect to target database: {str(e)}")
            
            # Compare schemas
            self.update_status("Comparing schemas...", True)
            differences = self.schema_comparer.compare_schemas(source_conn, target_conn)
            
            # Display results
            self.update_status("Processing results...", True)
            for diff in differences:
                if not self.filtered_objects or diff["object"] in self.filtered_objects:
                    tags = []
                    difference_text = ""
                    
                    if diff["action"] == "Different":
                        tags = ["different"]
                        if diff["type"] == "Table":
                            source_cols = len(diff["source_details"])
                            target_cols = len(diff["target_details"])
                            difference_text = f"Columns: {target_cols} vs {source_cols} (target vs source)"
                        else:
                            difference_text = "Definitions are different"
                    elif diff["action"] == "Create":
                        tags = ["source_only"]
                        difference_text = "Exists only in source"
                    elif diff["action"] == "Drop":
                        tags = ["target_only"]
                        difference_text = "Exists only in target"
                        
                    self.results_tree.insert("", tk.END,
                        values=(
                            diff["object"],
                            diff["type"],
                            diff["action"],
                            difference_text
                        ),
                        tags=tags
                    )
            
            if not differences:
                self.update_status("No differences found between the schemas.")
                messagebox.showinfo("Comparison Complete", "No differences found between the schemas.")
            else:
                self.update_status(f"Found {len(differences)} differences")
            
            # Close connections
            source_conn.close()
            target_conn.close()
            
        except ConnectionError as e:
            self.update_status(f"Connection Error: {str(e)}")
            messagebox.showerror("Connection Error", str(e))
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.show_progress(False)
            
    def update_schema(self):
        if not self.source_connection or not self.target_connection:
            messagebox.showwarning("Warning", "Please select both source and target connections first.")
            return
            
        # Get selected items
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select the changes you want to apply.")
            return
            
        if not messagebox.askyesno("Confirm Update", 
            "Are you sure you want to apply the selected changes to the target database?"):
            return
            
        try:
            self.status_bar.config(text="Applying changes...")
            
            # Connect to databases
            source_conn = self.schema_comparer.connect(
                self.source_connection["server"],
                self.source_connection["database"],
                self.source_connection["authentication"],
                self.source_connection["username"],
                self.source_connection["password"]
            )
            
            target_conn = self.schema_comparer.connect(
                self.target_connection["server"],
                self.target_connection["database"],
                self.target_connection["authentication"],
                self.target_connection["username"],
                self.target_connection["password"]
            )
            
            cursor = target_conn.cursor()
            
            # Apply selected changes
            for item_id in selected_items:
                item = self.results_tree.item(item_id)
                full_name = item["values"][0]
                action = item["values"][2]
                
                try:
                    schema_name, object_name = full_name.split(".")
                    if action in ("Create", "Alter"):
                        definition = self.schema_comparer.get_object_definition(
                            source_conn,
                            next(obj["object_id"] for obj in self.schema_comparer.get_schema_objects(source_conn)
                                if f"{obj['schema_name']}.{obj['object_name']}" == full_name)
                        )
                        cursor.execute(definition)
                    elif action == "Drop":
                        cursor.execute(f"DROP OBJECT {full_name}")
                        
                except Exception as e:
                    messagebox.showerror("Error", 
                        f"Failed to {action.lower()} {full_name}: {str(e)}")
                    target_conn.rollback()
                    self.status_bar.config(text=f"Error applying changes: {str(e)}")
                    return
                    
            target_conn.commit()
            messagebox.showinfo("Success", "Selected changes have been applied successfully.")
            self.status_bar.config(text="Changes applied successfully")
            
            # Refresh the comparison
            self.compare_schemas()
            
            # Close connections
            source_conn.close()
            target_conn.close()
            
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def format_column_details(self, column: Dict) -> str:
        """Format column details for display."""
        nullable = "NULL" if column["is_nullable"] else "NOT NULL"
        data_type = column["data_type"]
        
        # Add length/precision/scale for applicable types
        if column["max_length"] > 0:
            if data_type in ["nvarchar", "varchar", "char", "nchar"]:
                size = column["max_length"]
                if data_type.startswith("n"):  # Unicode types
                    size = size // 2
                data_type = f"{data_type}({size})"
        elif column["precision"] > 0:
            if column["scale"] > 0:
                data_type = f"{data_type}({column['precision']},{column['scale']})"
            else:
                data_type = f"{data_type}({column['precision']})"
                
        return f"{column['column_name']} {data_type} {nullable}"
        
    def display_column_differences(self, source_cols: List[Dict], target_cols: List[Dict]) -> None:
        """Display column differences between source and target tables."""
        source_text = "Source Table Columns:\n"
        source_text += "-" * 50 + "\n"
        for col in source_cols:
            source_text += self.format_column_details(col) + "\n"
            
        target_text = "Target Table Columns:\n"
        target_text += "-" * 50 + "\n"
        for col in target_cols:
            target_text += self.format_column_details(col) + "\n"
            
        # Show in text widgets
        self.source_text.delete('1.0', tk.END)
        self.source_text.insert(tk.END, source_text)
        
        self.target_text.delete('1.0', tk.END)
        self.target_text.insert(tk.END, target_text)
