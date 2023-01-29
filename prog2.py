import os
from PIL import Image

datapath="C:\TEMP_DATA"

output = os.listdir(datapath)

print("Below are the li")
print(output)


im = Image.open('C:\TEMP_DATA\20160528_161826.jpg')
exif = im.getexif()
creation_time = exif.get(36867)
print(creation_time)
