# main.py
import tkinter as tk
from app.ui import MainScreen

if __name__ == "__main__":
    # protect_folder_owner_only(DATA_DIR)
    root = tk.Tk()
    app = MainScreen(root)
    root.mainloop()