from tkinter import *
from tkinter import ttk
import time

root = Tk()
root.title('Vikas')
root.geometry("600x400")

my_label0 = Label(root, text="PROGRESS STATUS",  font=('Times 14'), width=30, height=1, bg='yellow', fg='black')
my_label0.pack(pady=20)

my_label = Label(root, text="")
my_label.pack(pady=20)

root.mainloop()
