import datetime

# Get the current date and time
now = datetime.datetime.now()

# Format the date and time as a string
date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

# Specify the file path and name
#file_path = r"C:\path\to\text\file.txt"
file_path = r"testfile01.txt"


# Open the file in append mode and write the date and time string
with open(file_path, mode='a') as file:
    file.write(date_time_str + "\n")
