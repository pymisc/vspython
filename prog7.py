from tkinter import ttk
from tkinter import *


root = Tk()
root.title('Basic sum program for 1st graders')
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
#root.geometry("%dx%d" %(width, height))    
root.geometry('1250x400')
# BACKUP/Original - root.geometry('250x200+250+200')
root.configure(bg='gray')


####### NOTE: Positioning Widgets With Grid Layout Manager 
Label(text="R1C1", width=10, height=2, font=('Times 36')).grid(row=0, column=0)
Label(text="R1C2", width=10, height=2, font=('Times 36')).grid(row=0, column=1)
Label(text="R1C3", width=10, height=2, font=('Times 36')).grid(row=0, column=2)
Label(text="R1C4", width=10, height=2, font=('Times 36')).grid(row=0, column=3)

Label(text="R2C1", width=10, height=2, font=('Times 36')).grid(row=1, column=0)
Label(text="R2C2", width=10, height=2, font=('Times 36')).grid(row=1, column=1)
Label(text="R2C3", width=10, height=2, font=('Times 36')).grid(row=1, column=2)
Label(text="R2C4", width=10, height=2, font=('Times 36')).grid(row=1, column=3)

Label(text="R3C1", width=10, height=2, font=('Times 36')).grid(row=2, column=0)
Label(text="R3C2", width=10, height=2, font=('Times 36')).grid(row=2, column=1)
Label(text="R3C3", width=10, height=2, font=('Times 36')).grid(row=2, column=2)
Label(text="R3C4", width=10, height=2, font=('Times 36')).grid(row=2, column=3)


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

