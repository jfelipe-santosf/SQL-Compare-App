# main.py
import tkinter as tk
from app.ui.main_screen import MainScreen
# from app.config import DATA_DIR
import subprocess
import os

# def protect_folder_owner_only(path):
#     try:
#         subprocess.run(["icacls", str(path), "/inheritance:r"], shell=True, check=True)
#         subprocess.run(["icacls", str(path), "/grant:r", f"{os.getlogin()}:F"], shell=True, check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Warning: Could not set folder permissions: {e}")

if __name__ == "__main__":
    # protect_folder_owner_only(DATA_DIR)
    root = tk.Tk()
    app = MainScreen(root)
    root.mainloop()