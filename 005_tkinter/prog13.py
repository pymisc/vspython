import tkinter as tk
import random

# python tkinter program to show random number 10 times with 1 second delay 
# Now make two numbers show up on screen and both random! :)

class RandomNumberDisplay:
    def __init__(self, master):
        self.master = master
        master.title("Baisc maths - add two numbers")

        self.label0 = tk.Label(master, font=("Helvetica", 96))
        self.label0A = tk.Label(master, font=("Helvetica", 96))
        self.label1 = tk.Label(master, font=("Helvetica", 96))
        self.label2 = tk.Label(master, font=("Helvetica", 96))
        self.label3 = tk.Label(master, font=("Helvetica", 96))
 
        self.label0.config(text="Add below two numbers:")

        self.label0.pack()
        self.label0A.pack()
        self.label1.pack()
        self.label2.pack()
        self.label3.pack()

        self.current_number = None
        self.remaining = 10

        self.show_random_number()

    def show_random_number(self):
        if self.remaining == 0:
            self.label0.config(text="")
            self.label1.config(text="Good job!")
            self.label2.config(text="Math sums done!")
        else:
            # First random number - label 1
            self.current_number = random.randint(10, 50)
            self.label1.config(text=str(self.current_number))
            # second random number - label 2
            self.current_number = random.randint(10, 50)
            self.label2.config(text=str(self.current_number))
            # below is the timer functionality and delay 1000 being 1 second.
            self.remaining -= 1
            self.master.after(1000, self.show_random_number)

root = tk.Tk()
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
root.geometry("%dx%d" %(width, height))  
app = RandomNumberDisplay(root)
root.mainloop()
