simply change the set website in new.py to match your website and novel, and change the min chapter and max chapter to ex: 1-357
this will crawl and download the novel for chapters 1-357

Next, you will use packer.py to pack the html files into a single pdf file, this will also proccess and remove anything other than the text that is needed.
NOTE: be sure to change content_div = soup.find('div', class_='content-area')
content_div represents the container your text is in!
you can find it by using the inspect element tool in the browser!
by default it is
soup.find('div', class_='content-area')
div is the type and class is the name

i have attached a image to help you find your content_div.

content area selects nearly the whole page, but it worked for what i needed it for.
![image](https://github.com/user-attachments/assets/b8ab93cc-cc1e-4f12-9d77-c7a5dec63e05)

in reality, in most cases something like "read_container" would be better.
![image](https://github.com/user-attachments/assets/5c6329d2-6098-4425-91ba-569f81fda86c)
