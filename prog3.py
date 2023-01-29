from tkinter import *
from tkinter import ttk
import time


root = Tk()
root.title('Vikas')
root.geometry("600x400")

#value = 0
def step():
    for x in range(10):
        my_progress['value'] += 10
        #my_progress.start(10)
        root.update_idletasks()
        my_label.config(text=my_progress['value'])
        time.sleep(1)

#def stop():
#    my_progress.stop()

my_progress = ttk.Progressbar(root, orient=HORIZONTAL, 
    length=400, mode='determinate' )
my_progress.pack(pady=20)

my_label0 = Label(root, text="PROGRESS STATUS",  font=('Times 14'), width=30, height=1, bg='#fff', fg='#f00')
#my_label0.size("20")
my_label0.pack(pady=20)

my_label = Label(root, text="")
my_label.pack(pady=20)

my_button = Button(root, text="Progress", command=step)
my_button.pack(pady=20)

#my_button2 = Button(root, text="Stop", command=stop)
#my_button2.pack(pady=20)


root.mainloop()
