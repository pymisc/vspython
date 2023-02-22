import psutil

# Get the disk usage for the root directory
#disk_usage = psutil.disk_usage('/')
disk_usage = psutil.disk_usage('c:')


# Print the total, used, and free space
#print(f"Total: {disk_usage.total / (1024**3):.2f} GB")
#print(f"Used: {disk_usage.used / (1024**3):.2f} GB")
#print(f"Free: {disk_usage.free / (1024**3):.2f} GB")

print(disk_usage)
