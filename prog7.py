from tkinter import ttk
from tkinter import *

root = Tk()
root.title('Basic sum program for 1st graders')
root.geometry('1250x400')
root.configure(bg='gray')

####### NOTE: Positioning Widgets With Grid Layout Manager 
Label(text="R1C1", width=10, height=2, font=('Times 36')).grid(row=0, column=0, padx=8, pady=8)
Label(text="R1C2", width=10, height=2, font=('Times 36')).grid(row=0, column=1, padx=8, pady=8)
Label(text="R1C3", width=10, height=2, font=('Times 36')).grid(row=0, column=2, padx=8, pady=8)

Label(text="R2C1", width=10, height=2, font=('Times 36')).grid(row=1, column=0, padx=8, pady=8)
Label(text="R2C2", width=10, height=2, font=('Times 36')).grid(row=1, column=1, padx=8, pady=8)
Label(text="R2C3", width=10, height=2, font=('Times 36')).grid(row=1, column=2, padx=8, pady=8)

root.mainloop()