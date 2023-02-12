from tkinter import ttk
from tkinter import *
import time

## NOTE: Side-by-Side Positioning with Pack

root = Tk()
root.title('Basic sum program for 1st graders')
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
root.geometry("%dx%d" %(width, height))    
root.configure(bg='gray')
# root.geometry("800x600")

test = Label(root, text="red", bg="red", fg="white", font=('Times 36'))
test.pack(padx=5, pady=15, side=LEFT)

test = Label(root, text="green", bg="green", fg="white", font=('Times 36'))
test.pack(padx=5, pady=20, side=LEFT)

test = Label(root, text="purple", bg="purple", fg="white", font=('Times 36'))
test.pack(padx=5, pady=20, side=LEFT)

'''
test1 = Label(root, text="Red", bg="red", fg="white")
test1.pack(side='top')
test2 = Label(root, text="Green", bg="green", fg="white")
test2.pack(side='top')
test3 = Label(root, text="Purple", bg="purple", fg="white")
test3.pack(side='top')

##############################
my_label0 = Label(root, text="Add below numbers:",  font=('Times 36'), bg='yellow', fg='black')
#my_label0 = Label(root, text="Label0",  font=('Times 36'), width=30, height=4, bg='yellow', fg='black')
my_label0.pack(pady=5)

my_label1 = Label(root, text="Label1",  font=('Times 36'), bg='yellow', fg='black')
#my_label1 = Label(root, text="Label1",  font=('Times 36'), width=30, height=4, bg='yellow', fg='black')
my_label1.pack(pady=5)

my_label2 = Label(root, text="Label2",  font=('Times 36'),  bg='yellow', fg='black')
#my_label2 = Label(root, text="Label2",  font=('Times 36'), width=30, height=4, bg='yellow', fg='black')
my_label2.pack(pady=5)

my_label3 = Label(root, text="Label3",  font=('Times 36'),  bg='yellow', fg='black')
#my_label3 = Label(root, text="Label2",  font=('Times 36'), width=30, height=4, bg='yellow', fg='black')
my_label3.pack(pady=5)
'''

root.mainloop()
