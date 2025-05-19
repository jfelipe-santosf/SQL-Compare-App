import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Set, List
import pyodbc
from tkinter import simpledialog
import os
from itertools import zip_longest

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
        
        # Vertical split view
        self.paned_window = ttk.PanedWindow(content, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Top panel - Results tree
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
          # Configure tags for different states (sem cores nos nomes dos objetos)
        self.results_tree.tag_configure("different", foreground="black")
        self.results_tree.tag_configure("source_only", foreground="black")
        self.results_tree.tag_configure("target_only", foreground="black")
        
        # Add scrollbar to results
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        # Pack results view
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
          # Bottom panel - Object definitions - Side by side
        definitions_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(definitions_frame, weight=1)
        
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
          # Configure text tags for highlighting differences (usando cores do Visual Studio)
        self.source_text.tag_configure('diff', background='#FDD8D6')  # VS Studio vermelho claro para remoções
        self.target_text.tag_configure('diff', background='#DDF7DD')  # VS Studio verde claro para adições
          # Synchronize scrolling between source and target
        def on_source_vertical_scroll(*args):
            self.target_text.yview_moveto(args[0])
        def on_target_vertical_scroll(*args):
            self.source_text.yview_moveto(args[0])
        def on_source_horizontal_scroll(*args):
            self.target_text.xview_moveto(args[0])
        def on_target_horizontal_scroll(*args):
            self.source_text.xview_moveto(args[0])
            
        # Configure vertical scrolling sync
        self.source_text.configure(yscrollcommand=lambda *args: (source_vsb.set(*args), on_source_vertical_scroll(args[0])))
        self.target_text.configure(yscrollcommand=lambda *args: (target_vsb.set(*args), on_target_vertical_scroll(args[0])))
        
        # Configure horizontal scrolling sync
        self.source_text.configure(xscrollcommand=lambda *args: (source_hsb.set(*args), on_source_horizontal_scroll(args[0])))
        self.target_text.configure(xscrollcommand=lambda *args: (target_hsb.set(*args), on_target_horizontal_scroll(args[0])))
        
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

    def highlight_differences(self, source_content, target_content):
        """Highlight differences between source and target text"""
        source_lines = source_content.splitlines()
        target_lines = target_content.splitlines()
        
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
    def _format_column_details_dacfx(self, column: Dict) -> str:
        """Format column details in DACFx style with fixed width columns"""
        # Column name (25 chars)
        name = column['column_name'].ljust(25)
        
        # Data type (35 chars)
        data_type = column['data_type']
        if data_type in ['decimal', 'numeric']:
            data_type += f"({column['precision']},{column['scale']})"
        elif data_type in ['varchar', 'nvarchar', 'char', 'nchar']:
            length = 'max' if column['max_length'] == -1 else str(column['max_length'])
            data_type += f"({length})"
        data_type = data_type.ljust(35)
        
        # Nullable (10 chars)
        nullable = "YES" if column['is_nullable'] else "NO"
        nullable = nullable.ljust(10)
        
        # Identity (10 chars)
        identity = ""
        if column.get('is_identity'):
            seed = column.get('identity_seed', 1)
            incr = column.get('identity_increment', 1)
            identity = f"({seed},{incr})"
        identity = identity.ljust(10)
        
        # Default (10 chars)
        default = "YES" if column.get('default_definition') else ""
        default = default.ljust(10)
        
        # Computed (10 chars)
        computed = "YES" if column.get('is_computed') else ""
        computed = computed.ljust(10)
        
        return f"{name}{data_type}{nullable}{identity}{default}{computed}"

    def _format_proc_header(self, obj: Dict) -> List[str]:
        """Format stored procedure header in DACFx style"""
        return [
            "-- Object Properties --",
            f"Schema:             {obj['schema_name']}",
            f"Type:               {obj['object_type']}",
            f"ANSI NULLS:        {'ON' if obj['is_ansi_nulls_on'] else 'OFF'}",
            f"Quoted Identifier: {'ON' if obj['is_quoted_identifier_on'] else 'OFF'}",
            f"Create Date:       {obj['create_date']}",
            f"Last Modified:     {obj['modify_date']}",
            "-" * 80
        ]

    def display_column_differences(self, source_cols: List[Dict], target_cols: List[Dict]) -> None:
        """Display column differences between source and target tables with highlighting"""
        # Headers
        source_header = [
            "-- Source Table Structure --",
            "-" * 80,
            "Column Name                 Data Type                           Nullable   Identity   Default   Computed",
            "--------------------------------------------------------------------------------------",
            ""
        ]
        
        target_header = [
            "-- Target Table Structure --",
            "-" * 80,
            "Column Name                 Data Type                           Nullable   Identity   Default   Computed",
            "--------------------------------------------------------------------------------------",
            ""
        ]
        
        # Clear existing text
        self.source_text.delete('1.0', tk.END)
        self.target_text.delete('1.0', tk.END)
        
        # Add headers
        self.source_text.insert(tk.END, "\n".join(source_header))
        self.target_text.insert(tk.END, "\n".join(target_header))
        
        # Prepare all column details
        all_columns = set()
        source_cols = source_cols or []
        target_cols = target_cols or []
        
        all_columns.update(col['column_name'] for col in source_cols)
        all_columns.update(col['column_name'] for col in target_cols)
        
        source_dict = {col['column_name']: col for col in source_cols}
        target_dict = {col['column_name']: col for col in target_cols}
        
        # Compare columns
        for col_name in sorted(all_columns):
            source_col = source_dict.get(col_name)
            target_col = target_dict.get(col_name)
            
            if source_col and target_col:
                source_details = self._format_column_details_dacfx(source_col)
                target_details = self._format_column_details_dacfx(target_col)
                
                # Compare each property
                if self._columns_are_different(source_col, target_col):
                    self.source_text.insert(tk.END, source_details + '\n', 'diff')
                    self.target_text.insert(tk.END, target_details + '\n', 'diff')
                else:
                    self.source_text.insert(tk.END, source_details + '\n')
                    self.target_text.insert(tk.END, target_details + '\n')
            else:
                if source_col:
                    self.source_text.insert(tk.END, self._format_column_details_dacfx(source_col) + '\n', 'diff')
                    self.target_text.insert(tk.END, f"-- Column {col_name} does not exist in target --\n", 'diff')
                else:
                    self.source_text.insert(tk.END, f"-- Column {col_name} does not exist in source --\n", 'diff')
                    self.target_text.insert(tk.END, self._format_column_details_dacfx(target_col) + '\n', 'diff')

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
                # Obter definições e propriedades do objeto
                source_props = []
                target_props = []
                source_def = ""
                target_def = ""

                # Propriedades do objeto fonte
                if source_obj:
                    # Propriedades básicas
                    source_props.extend([
                        f"-- Object Properties --",
                        f"Schema: {source_obj['schema_name']}",
                        f"Create Date: {source_obj['create_date']}",
                        f"Last Modified: {source_obj['modify_date']}",
                        f"ANSI NULLS: {'ON' if source_obj['is_ansi_nulls_on'] else 'OFF'}",
                        f"Quoted Identifier: {'ON' if source_obj['is_quoted_identifier_on'] else 'OFF'}",
                        ""
                    ])

                    # Para stored procedures e funções, obter parâmetros e dependências
                    if object_type in ["Stored Procedure", "Function"]:
                        params = self.schema_comparer.execute_query(source_conn, """
                            SELECT 
                                p.name, t.name as data_type, p.max_length,
                                p.precision, p.scale, p.is_output,
                                p.has_default_value, p.default_value,
                                p.parameter_id
                            FROM sys.parameters p
                            JOIN sys.types t ON p.user_type_id = t.user_type_id
                            WHERE object_id = ?
                            ORDER BY parameter_id
                        """, (source_obj['object_id'],))

                        if params:
                            source_props.extend([
                                "-- Parameters --",
                                *[self._format_parameter(p) for p in params],
                                ""
                            ])

                        # Checar uso de XML, CLR, etc
                        props = self.schema_comparer.execute_query(source_conn, """
                            SELECT 
                                OBJECTPROPERTY(?, 'ExecIsXMLDocument') as is_xml,
                                OBJECTPROPERTY(?, 'IsSchemaBound') as is_schema_bound,
                                OBJECTPROPERTY(?, 'IsEncrypted') as is_encrypted,
                                OBJECTPROPERTY(?, 'ExecIsStartup') as is_startup,
                                OBJECTPROPERTY(?, 'ExecIsRecompiled') as is_recompiled,
                                OBJECT_DEFINITION(?) as definition
                            """, (source_obj['object_id'],) * 6)

                        if props and props[0]:
                            features = []
                            prop = props[0]
                            if prop['is_xml']: features.append('Returns XML')
                            if prop['is_schema_bound']: features.append('Schema Bound')
                            if prop['is_encrypted']: features.append('Encrypted')
                            if prop['is_startup']: features.append('Startup')
                            if prop['is_recompiled']: features.append('Recompile')
                            
                            if features:
                                source_props.extend([
                                    "-- Features --",
                                    *features,
                                    ""
                                ])

                    # Obter a definição do objeto
                    definition = self.schema_comparer.get_object_definition(source_conn, source_obj['object_id'])
                    source_def = definition if definition else "-- No definition available --"

                # Propriedades do objeto alvo
                if target_obj:
                    # Propriedades básicas
                    target_props.extend([
                        f"-- Object Properties --",
                        f"Schema: {target_obj['schema_name']}",
                        f"Create Date: {target_obj['create_date']}",
                        f"Last Modified: {target_obj['modify_date']}",
                        f"ANSI NULLS: {'ON' if target_obj['is_ansi_nulls_on'] else 'OFF'}",
                        f"Quoted Identifier: {'ON' if target_obj['is_quoted_identifier_on'] else 'OFF'}",
                        ""
                    ])

                    # Para stored procedures e funções, obter parâmetros e dependências
                    if object_type in ["Stored Procedure", "Function"]:
                        params = self.schema_comparer.execute_query(target_conn, """
                            SELECT 
                                p.name, t.name as data_type, p.max_length,
                                p.precision, p.scale, p.is_output,
                                p.has_default_value, p.default_value,
                                p.parameter_id
                            FROM sys.parameters p
                            JOIN sys.types t ON p.user_type_id = t.user_type_id
                            WHERE object_id = ?
                            ORDER BY parameter_id
                        """, (target_obj['object_id'],))

                        if params:
                            target_props.extend([
                                "-- Parameters --",
                                *[self._format_parameter(p) for p in params],
                                ""
                            ])

                        # Checar uso de XML, CLR, etc
                        props = self.schema_comparer.execute_query(target_conn, """
                            SELECT 
                                OBJECTPROPERTY(?, 'ExecIsXMLDocument') as is_xml,
                                OBJECTPROPERTY(?, 'IsSchemaBound') as is_schema_bound,
                                OBJECTPROPERTY(?, 'IsEncrypted') as is_encrypted,
                                OBJECTPROPERTY(?, 'ExecIsStartup') as is_startup,
                                OBJECTPROPERTY(?, 'ExecIsRecompiled') as is_recompiled,
                                OBJECT_DEFINITION(?) as definition
                            """, (target_obj['object_id'],) * 6)

                        if props and props[0]:
                            features = []
                            prop = props[0]
                            if prop['is_xml']: features.append('Returns XML')
                            if prop['is_schema_bound']: features.append('Schema Bound')
                            if prop['is_encrypted']: features.append('Encrypted')
                            if prop['is_startup']: features.append('Startup')
                            if prop['is_recompiled']: features.append('Recompile')
                            
                            if features:
                                target_props.extend([
                                    "-- Features --",
                                    *features,
                                    ""
                                ])

                    # Obter a definição do objeto
                    definition = self.schema_comparer.get_object_definition(target_conn, target_obj['object_id'])
                    target_def = definition if definition else "-- No definition available --"

                # Juntar propriedades e definição
                full_source = "\n".join(source_props) + "\n-- Definition --\n" + source_def
                full_target = "\n".join(target_props) + "\n-- Definition --\n" + target_def

                # Atualizar widgets com highlighting
                self.highlight_differences(
                    full_source if source_obj else "-- Object does not exist in source --",
                    full_target if target_obj else "-- Object does not exist in target --"
                )

            source_conn.close()
            target_conn.close()
            self.status_bar.config(text="Ready")
            
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to load object details: {str(e)}")

    def _format_parameter(self, param):
        """Format a parameter for display in DACFx style"""
        p_type = param['data_type']
        
        # Add length/precision/scale for appropriate types
        if p_type in ['varchar', 'nvarchar', 'char', 'nchar']:
            p_type += f"({param['max_length']})" if param['max_length'] != -1 else "(max)"
        elif p_type in ['decimal', 'numeric']:
            p_type += f"({param['precision']},{param['scale']})"
            
        parts = [
            "@" + param['name'].ljust(20),
            p_type.ljust(15),
            'OUTPUT' if param['is_output'] else '',
            f"= {param['default_value']}" if param['has_default_value'] else ''
        ]
        
        return ' '.join(p for p in parts if p)

    def _format_definition_with_go(self, text: str) -> str:
        """Format object definition with GO statements in DACFx style"""
        result = []
        current_batch = []
        
        for line in text.splitlines():
            if line.strip().upper() == 'GO':
                if current_batch:
                    result.append('\n'.join(current_batch))
                    result.append('GO')
                    current_batch = []
            else:
                current_batch.append(line)
                
        if current_batch:
            result.append('\n'.join(current_batch))
            result.append('GO')
            
        return '\n'.join(result)

    def _compare_proc_properties(self, source: Dict, target: Dict) -> List[str]:
        """Compare stored procedure properties following DACFx rules"""
        differences = []
        
        if source['is_ansi_nulls_on'] != target['is_ansi_nulls_on']:
            differences.append('ANSI_NULLS setting')
        if source['is_quoted_identifier_on'] != target['is_quoted_identifier_on']:
            differences.append('QUOTED_IDENTIFIER setting')
            
        # Compare additional properties
        source_props = source.get('additional_properties', {})
        target_props = target.get('additional_properties', {})
        
        for prop in ['ExecIsXMLDocument', 'IsSchemaBound', 'IsEncrypted', 
                    'ExecIsStartup', 'ExecIsRecompiled']:
            if source_props.get(prop) != target_props.get(prop):
                differences.append(prop.replace('ExecIs', '').replace('Is', ''))
                
        return differences

    def highlight_differences(self, source_content: str, target_content: str):
        """Highlight differences between source and target text in DACFx style"""
        source_lines = source_content.splitlines()
        target_lines = target_content.splitlines()
        
        # Clear existing text and tags
        self.source_text.delete('1.0', tk.END)
        self.target_text.delete('1.0', tk.END)
        
        # Compare line by line with improved formatting
        for source_line, target_line in zip_longest(source_lines, target_lines, fillvalue=""):
            # Preserve indentation
            source_indent = len(source_line) - len(source_line.lstrip())
            target_indent = len(target_line) - len(target_line.lstrip())
            
            # Add source line with appropriate tag
            if source_line != target_line:
                self.source_text.insert(tk.END, " " * source_indent)
                self.source_text.insert(tk.END, source_line.lstrip() + '\n', 'diff')
            else:
                self.source_text.insert(tk.END, source_line + '\n')
            
            # Add target line with appropriate tag
            if source_line != target_line:
                self.target_text.insert(tk.END, " " * target_indent)
                self.target_text.insert(tk.END, target_line.lstrip() + '\n', 'diff')
            else:
                self.target_text.insert(tk.END, target_line + '\n')
