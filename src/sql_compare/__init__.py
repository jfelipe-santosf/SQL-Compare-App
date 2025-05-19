"""
SQL Server Schema Compare - A tool for comparing and synchronizing SQL Server database schemas
"""

def main():
    """Entry point for the application"""
    import tkinter as tk
    from .ui.main_window import SchemaCompareApp
    
    root = tk.Tk()
    app = SchemaCompareApp(root)
    root.mainloop()
