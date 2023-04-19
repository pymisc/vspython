import os

# this program will generate a HTML page based on what image files it sees in a directory
# will sort files by names and also print names 

# directory path containing the jpg files
#dir_path = 'G:\My Drive\_EDUREKA_CLASSES\Devops_2023\05_docker_containers'
dir_path = 'G:\My Drive\_EDUREKA_CLASSES\Devops_2023\srl_05_docker_containers'
# create an empty list to store the names of the jpg files
jpg_files = []

# loop through all the files in the directory and check if they have a .jpg extension
for filename in os.listdir(dir_path):
    #if filename.endswith('.jpg'):
     jpg_files.append(filename)

#print(jpg_files)

# create an HTML file to display the jpg files
with open('index.html', 'w') as f:
    f.write('<html>\n')
    f.write('<body>\n')
    for jpg_file in jpg_files:
        f.write('<p>{}</p>\n'.format(jpg_file))
        f.write('<img src="{}" />\n'.format(jpg_file))
    f.write('</body>\n')
    f.write('</html>\n')
