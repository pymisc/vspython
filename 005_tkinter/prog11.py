import tkinter as tk

# tkinter timer from 10 to 1 with 1 second delay (from chatgopt)

count = 10

def countdown():
    global count
    if count > 0:
        label.config(text=count)
        count -= 1
        label.after(1000, countdown)  # 1000ms = 1 second delay

# Create the Tkinter window
root = tk.Tk()
root.title("Countdown")

# Create the label to display the countdown
label = tk.Label(root, font=("Arial", 96), width=4)
label.pack(padx=50, pady=50)

# Call the countdown function to start the countdown
countdown()

# Start the Tkinter event loop
root.mainloop()
