web_page = str()
with open('C://Users/n3wto/Scripts/tests_node/server/index.html', 'r') as file:
    for line in file.readlines():
        web_page += line.split('\n')[0]

    file.close()

with open('html.txt', 'a') as file2:
    file2.write(web_page)
    file2.close()