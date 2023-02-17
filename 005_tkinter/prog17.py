import tkinter as tk
import random
import time
import csv

# Remake of prog15 with a Q&A file in CSV format
# Problem we are trying to solve: write a python tkinter program with use of dictionary to show question first and then show answer. Automatically swap question every 5 seconds.

# Open the CSV file for reading
with open('c:/Users/vs950/OneDrive/Documents/github/vspython/005_tkinter/questions.csv', 'r') as csv_file:
    # Create a CSV reader object
    csv_reader = csv.reader(csv_file)

    # Create an empty dictionary to store the data
    qa_dict = {}

    # Loop through each row in the CSV file
    for row in csv_reader:
        # Assume the first value in each row is the key, and the second value is the value
        key = row[0]
        value = row[1]

        # Add the key-value pair to the dictionary
        qa_dict[key] = value

# Print the dictionary
#print(qa_dict)

# Initialize the Tkinter window
root = tk.Tk()
width= root.winfo_screenwidth()               
height= root.winfo_screenheight()
root.geometry("%dx%d" %(width, height))  
root.title("Question and Answer")

# Define the label for the question
question_label = tk.Label(root, text="Question goes here")
question_label.pack(padx=20, pady=150)

# Define the label for the answer
answer_label = tk.Label(root, text="Answer goes here", font=("Helvetica", 96), fg="green")

# Define a function to get a random question from the dictionary
def get_random_question():
    return random.choice(list(qa_dict.keys()))

# Define the function to display a new question and hide the answer
def new_question():
    question = get_random_question()
    question_label.configure(text=question)
    question_label.configure(font=("Helvetica", 36), fg="brown")
    answer_label.pack_forget()

# Define the function to show the answer to the current question
def show_answer():
    question = question_label.cget("text")
    answer = qa_dict.get(question, "Unknown question")
    answer_label.configure(text=answer)
    answer_label.pack(pady=20)

# Define the function to swap to a new question every 5 seconds
def swap_question():
    while True:
        new_question()
        time.sleep(5)

# Define the button to show the answer
show_answer_button = tk.Button(root, text="Show Answer", command=show_answer)
show_answer_button.pack(pady=10)

# Display the initial question
new_question()

# Start the background thread to swap to a new question every 5 seconds
import threading
thread = threading.Thread(target=swap_question)
thread.start()

root.mainloop()
