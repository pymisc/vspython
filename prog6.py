from tkinter import ttk
from tkinter import *


root = Tk()
root.title('Basic sum program for 1st graders')
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
#root.geometry("%dx%d" %(width, height))    
root.geometry('650x400')
# BACKUP/Original - root.geometry('250x200+250+200')
root.configure(bg='gray')


####### NOTE: Positioning Widgets With Grid Layout Manager 
Label(text="Position 1", width=10, font=('Times 36')).grid(row=0, column=0)
Label(text="Position 2", width=10, font=('Times 36')).grid(row=0, column=1)
Label(text="Position 3", width=10, font=('Times 36')).grid(row=1, column=0)
Label(text="Position 4", width=10, font=('Times 36')).grid(row=1, column=1)


'''
####### NOTE: Positioning Widgets With Place Layout Manager 
Label(root, text="Position 1 : x=15, y=0", bg="#FFFF00", fg="white", font=('Times 36')).place(x=15, y=0)
Label(root, text="Position 2 : x=30, y=100", bg="#3300CC", fg="white", font=('Times 36')).place(x=30, y=100)
Label(root, text="Position 3 : x=45, y=200", bg="#FF0099", fg="white", font=('Times 36')).place(x=45, y=200)


###### NOTE: Vertical Positioning with Pack 
test = Label(root, text="Red", bg="red", fg="white", font=('Times 36'))
test.pack(side=BOTTOM)
test = Label(root, text="Green", bg="green", fg="white", font=('Times 36'))
test.pack(side=BOTTOM)
test = Label(root, text="Purple", bg="purple", fg="white", font=('Times 36'))
test.pack(side=BOTTOM)


###### NOTE: Side-by-Side Positioning with Pack
test = Label(root, text="red", bg="red", fg="white", font=('Times 36'))
test.pack(padx=5, pady=15, side=LEFT)
test = Label(root, text="green", bg="green", fg="white", font=('Times 36'))
test.pack(padx=5, pady=20, side=LEFT)
test = Label(root, text="purple", bg="purple", fg="white", font=('Times 36'))
test.pack(padx=5, pady=20, side=LEFT)
'''

root.mainloop()

