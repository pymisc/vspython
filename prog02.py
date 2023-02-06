import os
from PIL import Image

# NOT WORKING AS OF 02.05.2023
#from PIL import Image

datapath="C:\TEMP_DATA"

output = os.listdir(datapath)

print("###############################################")
print("Below are the list of files available:")
print(output)
print("###############################################")

im = Image.open("C:\TEMP_DATA\20160515_183653.jpg")
exif = im.getexif()
creation_time = exif.get(36867)
print(creation_time)
