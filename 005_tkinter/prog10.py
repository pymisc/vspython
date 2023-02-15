import tkinter as tk

# written with chatgpt's help
# write a python tkinter program to countdown label from 15 to 1  with 1 second interval

# Define the function to update the countdown label
def update_countdown():
    # Get the current value of the countdown label
    current_value = int(countdown_label["text"])

    # Decrement the value by 1
    current_value -= 1

    # Update the countdown label
    countdown_label.config(text=str(current_value))

    # If the countdown has reached 0, stop the timer
    if current_value == 0:
        window.after_cancel(timer_id)
        countdown_label.config(text="Time's up!")

    # Otherwise, schedule the next update in 1 second
    else:
        timer_id = window.after(1000, update_countdown)

# Create the Tkinter window
window = tk.Tk()
window.title("Countdown")

# Create the countdown label
countdown_label = tk.Label(window, text="15", font=("Arial", 24))
countdown_label.pack()

# Start the countdown timer
timer_id = window.after(1000, update_countdown)

# Start the Tkinter event loop
window.mainloop()
