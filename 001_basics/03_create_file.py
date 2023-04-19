import datetime

# Get the current date in yyyy-mm-dd format
date_str = datetime.date.today().strftime("%Y-%m-%d")

# Open the text file in append mode and write the date to the end of the file
with open("testfile01.txt", "a") as f:
    f.write(date_str + "\n")
