import datetime
import os

def append_current_time(file_path):
    # 1. Explicitly check if the file exists (Great for testing branches!)
    if not os.path.exists(file_path):
        print(f"File '{file_path}' does not exist. Creating it...")
    else:
        print(f"File '{file_path}' exists. Appending to it...")

    # 2. Get and format the date
    now = datetime.datetime.now()
    date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 3. Open in append mode ('a' automatically handles creation and appending)
    with open(file_path, mode='a') as file:
        file.write(date_time_str + "\n")

# This block only runs if you execute the script directly
if __name__ == "__main__":
    append_current_time("testfile01.txt")
