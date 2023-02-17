import tkinter as tk

# problem trying to solve: write python tkinter program for a text box to write into a file. 

# Define the Tkinter window
root = tk.Tk()
#root.geometry("400x300")
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
root.geometry("%dx%d" %(width, height))  
#root.title("Question and Answer")
root.title("Write to File")

# Define the text box for input
input_text = tk.Text(root)
input_text.pack(pady=10)

# Define the function to write the input to a file
def write_to_file():
    text = input_text.get("1.0", "end-1c")
    with open("output.txt", "w") as file:
        file.write(text)

# Define the button to write the input to a file
write_button = tk.Button(root, text="Write to File", command=write_to_file)
write_button.pack(pady=10)

root.mainloop()
