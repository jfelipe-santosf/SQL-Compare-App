"""Main entry point for SQL Server Compare application."""
from sql_compare.ui.main_window import SchemaCompareApp
import tkinter as tk

def main():
    root = tk.Tk()
    app = SchemaCompareApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
