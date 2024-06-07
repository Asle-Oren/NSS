import urllib.request, json

import os

with open('Utlånsystem.csv', 'rb') as f:
    try:  # catch OSError in case of a one line file 
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
    except OSError:
        f.seek(0)
    last_line = f.readline().decode()

    last_line = last_line[:-2]#trim newline and carrige return chars
    for i in range(len(last_line)-1,0,-1):
        #print(f'{last_line[i]=}')
        if last_line[i] == ";":
            index = i
            #print(f'{index=}')
            break

    last_number_id_in_file = last_line[index+1:]
    #print(last_number_id_in_file)
    id = last_number_id_in_file + 1

exit()




isbn = input('Scan book to get title: ')
#isbn = "1633438538"

url = 'https://openlibrary.org/search.json?q='+isbn
#print(url)
contents = urllib.request.urlopen(url)
#print(contents)
json_object = json.load(contents)

title = json_object["docs"][0]["title"]

#print(json_object)
print(title)

#print(contents)
#contents.findall