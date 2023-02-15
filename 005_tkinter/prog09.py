import tkinter as tk

# This program is generated with help of chatgpt
# write a python tkinter program to take two numbers in separate text box and add by click on button and show answer in a label


# Define the function to add the two numbers
def add_numbers():
    # Get the numbers from the text boxes
    num1 = float(num1_box.get())
    num2 = float(num2_box.get())

    # Add the numbers
    result = num1 + num2

    # Display the result in the label
    result_label.config(text=f"Result: {result}")

# Create the Tkinter window
window = tk.Tk()
window.title("Add Two Numbers")

# Create the two text boxes
num1_box = tk.Entry(window)
num1_box.pack()

num2_box = tk.Entry(window)
num2_box.pack()

# Create the button to add the numbers
add_button = tk.Button(window, text="Add", command=add_numbers)
add_button.pack()

# Create the label to display the result
result_label = tk.Label(window, text="Result:")
result_label.pack()

# Start the Tkinter event loop
window.mainloop()
