import tkinter as tk

root = tk.Tk()
listbox = tk.Listbox(root)
listbox.pack()
for item in ["Opción 1", "Opción 2", "Opción 3"]:
    listbox.insert(tk.END, item)

root.mainloop()
