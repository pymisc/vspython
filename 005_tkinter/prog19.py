import tkinter as tk

# Python tkinter to draw a lin with width 2

root = tk.Tk()

canvas = tk.Canvas(root, width=300, height=200)
canvas.pack()

# create a line with thickness of 2 pixels
line = canvas.create_line(50, 50, 250, 50, width=2)

root.mainloop()
