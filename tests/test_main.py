import os
import tkinter as tk
from test_ui.test_main_screen import MainScreen
import ctypes
import subprocess

def create_folder(path):
    os.makedirs(path, exist_ok=True)

def protect_folder_owner_only(path):
    # Remove herança e dá permissão total apenas ao usuário atual
    subprocess.run(["icacls", path, "/inheritance:r"], shell=True)
    subprocess.run(["icacls", path, "/grant:r", f"{os.getlogin()}:F"], shell=True)

def prepare_environment():
    # Creates the _internal folder inside the 'app' directory
    internal_dir = os.path.join("tests", "_internal")
    data_dir = os.path.join(internal_dir, "connectiondata")

    create_folder(internal_dir)

    create_folder(data_dir)
    protect_folder_owner_only(data_dir)

if __name__ == "__main__":
    prepare_environment()

    root = tk.Tk()
    app = MainScreen(root)
    root.mainloop()