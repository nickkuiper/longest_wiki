#import packages
import wikipedia
from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

res = requests.get("https://en.wikipedia.org/wiki/List_of_architects")
soup = bs(res.text, "html.parser")

url_list = []
for link in soup.find_all("li"):
    try:
        url = link.a.get("href", "")
        if "/wiki/" in url:
            print(url)
            title = link.a.get('title')
            url = url.lower()
            dft = pd.DataFrame({'url':url, 'title':title}, index = [0])
            url_list.append(dft)
    except:
        print('Error in link')

url_list = pd.concat(url_list, axis = 0)
url_list = url_list[~url_list['url'].str.contains('wikipedia')]
url_list = url_list[~url_list['url'].str.contains('http')]
url_list = url_list[~url_list['url'].str.contains('list_of_')]
url_list = url_list[~url_list['url'].str.contains('portal|category|file|foundation|booksource|special|main_page|film|help')]


#extract the name
full_list = []
full_links = []
for i in url_list['title'].unique():
    print(i)
    try:
        p = wikipedia.page(i)
        dft = pd.DataFrame({'Title':p.title, 'Url':p.url,'Page Length':len(p.content), 'Query': i, 'pageid': p.pageid}, index = [0])
        full_list.append(dft)
        try:
            #get the links
            links_df = pd.DataFrame(p.links)
            links_df['Page'] = p.title
            full_links.append(links_df)
        except:
            print("Error in links")
    except:
        print('Error')
#Remove list of results

full_df = pd.concat(full_list, axis = 0)
links_df = pd.concat(full_links, axis = 0)
links_df.columns = ['link', 'page title']

#collect a list of people
people = full_df['Title'].unique()

#Where do most of the pages link to?
links_df.groupby(['link']).size().reset_index().sort_values(by = 0, ascending = False)

#filter based on people
links_people = links_df[links_df['link'].isin(people)]
links_people.groupby(['link']).size().reset_index().sort_values(by = 0, ascending = False)

#filter the internal referals
links_people = links_people[~(links_people['link'] == links_people['page title'])]

#links_people = links_people[links_people['link'] != 'International Standard Book Number']

#full_df.to_csv('~/Downloads/biggest_architects.csv', sep = ';')

#building a network of people right now
G=nx.from_pandas_edgelist(links_people, source='page title', target='link')

got_net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

sources = links_people['link']
targets = links_people['page title']
links_people['Weight'] = 1
weights = links_people['Weight']

edge_data = zip(sources, targets, weights)

for e in edge_data:
    src = e[0]
    dst = e[1]
    w = e[2]

    got_net.add_node(src, src, title=src)
    got_net.add_node(dst, dst, title=dst)
    got_net.add_edge(src, dst, value=w)

neighbor_map = got_net.get_adj_list()

# add neighbor data to node hover data
for node in got_net.nodes:
    node["title"] += " Neighbors:<br>" + "<br>".join(neighbor_map[node["id"]])
    node["value"] = len(neighbor_map[node["id"]])
got_net.show_buttons(filter_=['physics'])
got_net.show("network.html")


#The following settings worked best for me in the viz
options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -62503,
      "centralGravity": 0,
      "springLength": 550,
      "springConstant": 0.025,
      "damping": 0.82,
      "avoidOverlap": 0.14
    },
    "maxVelocity": 23,
    "minVelocity": 0.67,
    "timestep": 0.78
  }
}
