import tkinter as tk

class CountDown:
    def __init__(self, master):
        self.master = master
        self.counter = 99
        #self.canvas = tk.Canvas(master, width=200, height=200)
        self.canvas = tk.Canvas(master)
        self.canvas.pack()
        self.circle = self.canvas.create_oval(50, 50, 150, 150)
        self.text = self.canvas.create_text(100, 100, text=str(self.counter), font=('Arial', 40))
        self.timer = self.master.after(1000, self.count)

    def count(self):
        self.counter -= 1
        self.canvas.itemconfig(self.text, text=str(self.counter))
        if self.counter > 0:
            self.canvas.after(1000, self.count)
        else:
            self.master.after_cancel(self.timer)
            self.canvas.delete(self.circle)
            self.canvas.delete(self.text)

root = tk.Tk()
root.title("Countdown")
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
root.geometry("%dx%d" %(width, height))  
app = CountDown(root)

root.mainloop()
