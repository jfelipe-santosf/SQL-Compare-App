import difflib
import tkinter as tk

text1 = """linha 1 comum
linha 2 modificada que é muito longa para testar o scroll horizontal
linha 3
linha 4"""

text2 = """linha 1 comum
linha 2 original que também é muito longa para testar o scroll horizontal
linha 3 alterada
linha 5"""

root = tk.Tk()
root.title("Comparação lado a lado com scroll sincronizado")

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# Text widgets
txt1 = tk.Text(frame, width=50, height=30, font=("Consolas", 12), wrap=tk.NONE, undo=True)
txt2 = tk.Text(frame, width=50, height=30, font=("Consolas", 12), wrap=tk.NONE, undo=True)
txt1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
txt2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Scrollbars verticais e horizontais
v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=lambda *args: (txt1.yview(*args), txt2.yview(*args)))
h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=lambda *args: (txt1.xview(*args), txt2.xview(*args)))

txt1.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
txt2.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

# Cores
txt1.tag_config("removed", background="misty rose")
txt2.tag_config("added", background="pale green")
txt1.tag_config("changed", background="light goldenrod")
txt2.tag_config("changed", background="light goldenrod")
txt1.tag_config("equal", background="white")
txt2.tag_config("equal", background="white")

def insert_line(txt, line, tag=None):
    txt.insert(tk.END, line + "\n", tag)

lines1 = text1.splitlines()
lines2 = text2.splitlines()

matcher = difflib.SequenceMatcher(None, lines1, lines2)
opcodes = matcher.get_opcodes()

# Preencher com comparação
for tag, i1, i2, j1, j2 in opcodes:
    if tag == "equal":
        for l1, l2 in zip(lines1[i1:i2], lines2[j1:j2]):
            insert_line(txt1, l1, "equal")
            insert_line(txt2, l2, "equal")
    elif tag == "replace":
        for l1 in lines1[i1:i2]:
            insert_line(txt1, l1, "changed")
        for l2 in lines2[j1:j2]:
            insert_line(txt2, l2, "changed")
    elif tag == "delete":
        for l1 in lines1[i1:i2]:
            insert_line(txt1, l1, "removed")
        for _ in range(i2 - i1):
            insert_line(txt2, "", "equal")
    elif tag == "insert":
        for _ in range(j2 - j1):
            insert_line(txt1, "", "equal")
        for l2 in lines2[j1:j2]:
            insert_line(txt2, l2, "added")

# Desabilitar edição
txt1.config(state=tk.DISABLED)
txt2.config(state=tk.DISABLED)

# Sincronizar scroll do mouse
def on_mousewheel(event):
    delta = int(-1*(event.delta/120))
    txt1.yview_scroll(delta, "units")
    txt2.yview_scroll(delta, "units")
    return "break"

def on_shift_mousewheel(event):
    delta = int(-1*(event.delta/120))
    txt1.xview_scroll(delta, "units")
    txt2.xview_scroll(delta, "units")
    return "break"

txt1.bind("<MouseWheel>", on_mousewheel)
txt2.bind("<MouseWheel>", on_mousewheel)
txt1.bind("<Shift-MouseWheel>", on_shift_mousewheel)
txt2.bind("<Shift-MouseWheel>", on_shift_mousewheel)

root.mainloop()
