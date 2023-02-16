import tkinter as tk
import random

class RandomNumberDisplay:
    def __init__(self, master):
        self.master = master
        master.title("Random Number Display")

        self.label = tk.Label(master, font=("Helvetica", 36))
        self.label.pack()

        self.current_number = None
        self.remaining = 10

        self.show_random_number()

    def show_random_number(self):
        if self.remaining == 0:
            self.label.config(text="Done!")
        else:
            self.current_number = random.randint(1, 100)
            self.label.config(text=str(self.current_number))
            self.remaining -= 1
            self.master.after(1000, self.show_random_number)

root = tk.Tk()
app = RandomNumberDisplay(root)
root.mainloop()
