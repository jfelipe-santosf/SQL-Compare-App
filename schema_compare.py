import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
from PIL import Image, ImageTk
from connection_dialog import ConnectionDialog
from schema_comparer import SchemaComparer

class SchemaCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Server Schema Compare")
        self.root.geometry("1200x800")
        
        # Initialize connection storage
        self.source_connection = None
        self.target_connection = None
        self.source_connection_label = None
        self.target_connection_label = None
        
        # Configure the main window style
        style = ttk.Style()
        style.configure("Compare.TButton", padding=5)
        
        self.create_ui()
        
    def create_ui(self):
        # Create main toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Compare button
        self.compare_btn = ttk.Button(
            toolbar, 
            text="Compare",
            style="Compare.TButton",
            command=self.compare_schemas
        )
        self.compare_btn.pack(side=tk.LEFT, padx=2)
        
        # Update button
        self.update_btn = ttk.Button(
            toolbar,
            text="Update",
            style="Compare.TButton",
            command=self.update_schema
        )
        self.update_btn.pack(side=tk.LEFT, padx=2)
        
        # Create main content area
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Source and Target connection panels
        source_frame = self.create_connection_panel(content, "Source")
        source_frame.pack(fill=tk.X, pady=5)
        
        target_frame = self.create_connection_panel(content, "Target")
        target_frame.pack(fill=tk.X, pady=5)
        
        # Create comparison results area
        results_frame = ttk.LabelFrame(content, text="Comparison Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for displaying differences
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("Object", "Type", "Action", "Source", "Target"),
            show="headings"
        )
        
        # Configure headings
        self.results_tree.heading("Object", text="Object Name")
        self.results_tree.heading("Type", text="Object Type")
        self.results_tree.heading("Action", text="Action")
        self.results_tree.heading("Source", text="Source")
        self.results_tree.heading("Target", text="Target")
        
        # Configure columns
        self.results_tree.column("Object", width=200)
        self.results_tree.column("Type", width=100)
        self.results_tree.column("Action", width=100)
        self.results_tree.column("Source", width=300)
        self.results_tree.column("Target", width=300)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_connection_panel(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        
        # Connection info display
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=2)
        
        # Connection button
        select_btn = ttk.Button(
            info_frame,
            text="Select Connection...",
            command=lambda: self.show_connection_dialog(title.lower())
        )
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # Connection info label
        if title.lower() == "source":
            self.source_connection_label = ttk.Label(info_frame, text="No connection selected")
            self.source_connection_label.pack(side=tk.LEFT, padx=5)
        else:
            self.target_connection_label = ttk.Label(info_frame, text="No connection selected")
            self.target_connection_label.pack(side=tk.LEFT, padx=5)
        
        return frame
        
    def show_connection_dialog(self, connection_type):
        dialog = ConnectionDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.selected_connection:
            if connection_type == "source":
                self.source_connection = dialog.selected_connection
                conn_info = f"Server: {dialog.selected_connection['server']} | Database: {dialog.selected_connection['database']}"
                self.source_connection_label.configure(text=conn_info)
            else:
                self.target_connection = dialog.selected_connection
                conn_info = f"Server: {dialog.selected_connection['server']} | Database: {dialog.selected_connection['database']}"
                self.target_connection_label.configure(text=conn_info)
                
    def compare_schemas(self):
        if not self.source_connection or not self.target_connection:
            messagebox.showwarning("Warning", "Please select both source and target connections first.")
            return
            
        try:
            comparer = SchemaComparer()
            
            # Clear existing items in the tree
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Connect to databases
            source_conn = comparer.connect(
                self.source_connection["server"],
                self.source_connection["database"],
                self.source_connection["authentication"]
            )
            
            target_conn = comparer.connect(
                self.target_connection["server"],
                self.target_connection["database"],
                self.target_connection["authentication"]
            )
            
            # Compare schemas
            differences = comparer.compare_schemas(source_conn, target_conn)
            
            # Display results
            for diff in differences:
                self.results_tree.insert("", tk.END, values=(
                    diff["object"],
                    diff["type"],
                    diff["action"],
                    diff["source"][:50] + "..." if diff["source"] else "",
                    diff["target"][:50] + "..." if diff["target"] else ""
                ))
                
            if not differences:
                messagebox.showinfo("Comparison Complete", "No differences found between the schemas.")
            
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
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
            comparer = SchemaComparer()
            
            # Connect to databases
            source_conn = comparer.connect(
                self.source_connection["server"],
                self.source_connection["database"],
                self.source_connection["authentication"]
            )
            
            target_conn = comparer.connect(
                self.target_connection["server"],
                self.target_connection["database"],
                self.target_connection["authentication"]
            )
            
            # Get the differences for selected items
            selected_diffs = []
            for item_id in selected_items:
                item = self.results_tree.item(item_id)
                object_name = item["values"][0]
                action = item["values"][2]
                
                if action == "Create":
                    definition = comparer.get_object_definition(
                        source_conn,
                        object_name.split(".")[0],
                        object_name.split(".")[1]
                    )
                    selected_diffs.append({
                        "object": object_name,
                        "action": action,
                        "definition": definition
                    })
                elif action == "Alter":
                    definition = comparer.get_object_definition(
                        source_conn,
                        object_name.split(".")[0],
                        object_name.split(".")[1]
                    )
                    selected_diffs.append({
                        "object": object_name,
                        "action": action,
                        "definition": definition
                    })
                elif action == "Drop":
                    selected_diffs.append({
                        "object": object_name,
                        "action": action,
                        "definition": None
                    })
            
            # Apply changes
            cursor = target_conn.cursor()
            for diff in selected_diffs:
                try:
                    if diff["action"] in ("Create", "Alter"):
                        cursor.execute(diff["definition"])
                    elif diff["action"] == "Drop":
                        cursor.execute(f"DROP OBJECT {diff['object']}")
                except Exception as e:
                    messagebox.showerror("Error", 
                        f"Failed to {diff['action'].lower()} {diff['object']}: {str(e)}")
                    return
                    
            target_conn.commit()
            messagebox.showinfo("Success", "Selected changes have been applied successfully.")
            
            # Refresh the comparison
            self.compare_schemas()
            
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchemaCompareApp(root)
    root.mainloop()
