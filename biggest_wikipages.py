#import packages
import wikipedia
from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd

res = requests.get("https://en.wikipedia.org/wiki/List_of_architects")
soup = bs(res.text, "html.parser")

url_list = []
for link in soup.find_all("a"):
    url = link.get("href", "")
    if "/wiki/" in url:
        print(url)
        url = url.lower()
        url_list.append(url)

url_list = pd.DataFrame(url_list)
#regex = re.compile('wikipedia')

url_list = url_list[~url_list[0].str.contains('wikipedia')]
url_list = url_list[~url_list[0].str.contains('http')]
url_list = url_list[~url_list[0].str.contains('list_of_')]
url_list = url_list[~url_list[0].str.contains('portal|category|file|foundation|booksource|special|main_page|film|help')]
url_list['Name'] = url_list[0].str.split('/wiki/').str[1].str.replace('_',' ')

#select only unique names

#extract the name
full_list = []
for i in url_list['Name']:
    print(i)
    try:
        p = wikipedia.page(i)
        dft = pd.DataFrame({'Title':p.title, 'Url':p.url,'Page Length':len(p.content), 'Query': i}, index = [0])
        full_list.append(dft)
    except:
        print('Error')
#Remove list of results

full_df = pd.concat(full_list, axis = 0)
full_df.to_csv('~/Downloads/biggest_architects.csv', sep = ';')
