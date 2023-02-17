import tkinter as tk

# Problem trying to solve: write a python tkinter program with use of dictionary to show question first and then show answer
# 

# Define the dictionary of questions and answers
qa_dict = {
    "What is the capital of France?": "Paris",
    "What is the largest planet in our solar system?": "Jupiter",
    "What is the tallest mountain in the world?": "Mount Everest"
}

# Initialize the Tkinter window
root = tk.Tk()
root.geometry("400x300")
root.title("Question and Answer")

# Define the label for the question
question_label = tk.Label(root, text="Question goes here")
question_label.pack(pady=20)

# Define the label for the answer
answer_label = tk.Label(root, text="Answer goes here", font=("Helvetica", 16), fg="green")

# Define the function to display a new question and hide the answer
def new_question():
    question = get_random_question()
    question_label.configure(text=question)
    answer_label.pack_forget()

# Define the function to show the answer to the current question
def show_answer():
    question = question_label.cget("text")
    answer = qa_dict.get(question, "Unknown question")
    answer_label.configure(text=answer)
    answer_label.pack(pady=20)

# Define the button for a new question
new_question_button = tk.Button(root, text="New Question", command=new_question)
new_question_button.pack(pady=10)

# Define the button to show the answer
show_answer_button = tk.Button(root, text="Show Answer", command=show_answer)
show_answer_button.pack(pady=10)

# Define a function to get a random question from the dictionary
import random
def get_random_question():
    return random.choice(list(qa_dict.keys()))

# Display the initial question
new_question()

root.mainloop()
