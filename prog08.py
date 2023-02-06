from tkinter import ttk
from tkinter import *

# DROP DOWN USING TKINTER

root = Tk()
root.title('Basic sum program for 1st graders')
root.geometry('1250x400')
root.configure(bg='gray')

# Combobox creation
n = StringVar()
monthchoosen = ttk.Combobox(root, width = 27, textvariable = n, font=('Times 36'))
  
# Adding combobox drop down list
monthchoosen['values'] = (' January', ' February', ' March', ' April', ' May', 
    ' June', ' July',  'August', ' September', ' October', ' November', ' December')
  
monthchoosen.grid(column = 1, row = 5)
monthchoosen.current()

root.mainloop()