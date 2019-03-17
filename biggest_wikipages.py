#Start logging the last edit of a page as well

#Start from one page till third connections
#I can also explore connections based on page categories -> American Architects for example
#Add a trendingness metric based on wikipedia pageviews

#Automated color picking

#fix issue with list of links
#import packages
import wikipedia
from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
import mwparserfromhell
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from dateutil.parser import parse
import plotly.plotly as py
import plotly.graph_objs as go
import config
import datetime
#plotly.offline.init_notebook_mode()

plotly.tools.set_credentials_file(username=config.username, api_key=config.api_key)

#dateframe
end_date = datetime.datetime.now().date()
start_date = end_date + datetime.timedelta(days=-31)
end_date = end_date.strftime('%Y%m%d')
start_date = start_date.strftime('%Y%m%d')

res = requests.get("https://en.wikipedia.org/wiki/List_of_architects")
soup = bs(res.text, "html.parser")

url_list = []
for link in soup.find_all("li"):
    try:
        url = link.a.get("href", "")
        if "/wiki/" in url:
            #print(url)
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

#url_list = url_list[200:300]
#extract the name

full_list = []
full_links = []
for i in url_list['title'].unique():
    print(i)
    #i = 'Thomas Cubitt'
    try:
        p = wikipedia.page(i)
        p.categories
        try:
            #get the links
            links_df = pd.DataFrame(p.links)
            links_df['Page'] = p.title
            full_links.append(links_df)
            try:
                #get the url link
                url_link = p.url.split('/')[-1]
                url = 'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&rvsection=0&titles=' + url_link + '&format=json'
                print(url)
                res = requests.get(url)
                text = list(res.json()["query"]["pages"].values())[0]["revisions"][0]["*"]
                wiki = mwparserfromhell.parse(text)
                try:
                    birth_date = wiki.split('birth_date')[1].lower()
                    birth_date = birth_date.replace('df=', '')
                    birth_date = birth_date.replace('mf=', '')
                    birth_date = birth_date.split('=')[1]
                    birth_date = birth_date.split('\n')[0].strip()
                    birth_date = birth_date.replace('{{','')
                    birth_date = birth_date.replace('}}','')
                    birth_date = birth_date.replace('|', '-')
                    birth_date = birth_date.strip('y')
                    birth_date = birth_date.strip('-')
                    birth_date = parse(birth_date, fuzzy=True).year
                    #print(birth_date)
                except:
                    print('No birth date found')
                    birth_date = ''
                try:
                    death_date = wiki.split('death_date')[1].lower()
                    death_date = death_date.replace('df=', '')
                    death_date = death_date.replace('mf=', '')
                    death_date = death_date.replace('_' ,'')
                    death_date = death_date.replace('death date and given age' ,'death date and age')
                    death_date = death_date.split('=')[1]
                    death_date = death_date.split('\n')[0].strip()
                    #maybe replace the brackets
                    death_date = death_date.replace('{{','')
                    death_date = death_date.replace('}}','')
                    death_date = death_date.replace('|', '-')
                    death_date = death_date.split('aged')[0]
                    death_date = death_date.strip('y')
                    death_date = death_date.strip('-')
                    death_date = death_date.strip(')')
                    #death_date = '20 december 1855)'
                    death_date = parse(death_date, fuzzy=True).year
                    #print(death_date)
                    #if the text is matched do the following below:
                except:
                    print('No death date found')
                    death_date = ''
            except:
                print('Error in Demographics data')
        except:
            print("Error in links")
    except:
        print('Error')
    try:
        dft = pd.DataFrame({'Title':p.title, 'Url':p.url,'Page Length':len(p.content), 'Query': i, 'pageid': p.pageid, 'Birth Year':birth_date, 'Death Year':death_date, 'url_link':url_link}, index = [0])
        full_list.append(dft)
    except:
        next

#Remove list of results
full_df = pd.concat(full_list, axis = 0)
#full_df.to_csv('arcitects.csv', index = False)
links_df = pd.concat(full_links, axis = 0)
#links_df.to_csv('architects_links.csv', index = False)
links_df.columns = ['to', 'from']

#Collect the pageviews for all the pages
urllist = full_df['url_link'].unique()
pageview_list = []
for i in urllist:
    i = i.split('/')[-1]
    print(i)
    url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/"+i+"/daily/" + start_date + "/" + end_date
    res = requests.get(url)
    dft = pd.DataFrame(res.json()['items'])
    dft.dtypes
    dft['date'] = pd.to_numeric(dft['timestamp']) / 100
    dft['date'] = dft['date'].apply(str).str.split('.').str[0]
    dft['date'] = pd.to_datetime(dft['date'])
    dft = dft[['article', 'date', 'views']]
    pageview_list.append(dft)
    #subset
pageview_df = pd.concat(pageview_list, axis = 0)
pageview_df.groupby('article')['views'].agg('sum').reset_index().sort_values('views', ascending = False)
pageview_df.groupby('article')['views'].agg('median').reset_index().sort_values('views', ascending = False)

#collect a list of people
people = full_df['Title'].unique()

#Where do most of the pages link to?
links_df.groupby(['to']).size().reset_index().sort_values(by = 0, ascending = False)

#filter based on people
links_people = links_df[links_df['to'].isin(people)]
links_people.groupby(['to']).size().reset_index().sort_values(by = 0, ascending = False)

#filter the internal referals
links_people = links_people[~(links_people['to'] == links_people['from'])]

#count the link and the page title
biggest_to = links_people.groupby('to').size().reset_index().sort_values(by=0,ascending = False)
biggest_to.columns = ['Title', 'links_to']
biggest_from = links_people.groupby('from').size().reset_index().sort_values(by=0,ascending = False)
biggest_from.columns = ['Title', 'links_from']
full_df = pd.merge(full_df,biggest_to, left_on = 'Title', right_on = 'Title')
full_df = pd.merge(full_df,biggest_from, left_on = 'Title', right_on = 'Title')

#Born and death analysis
full_df.groupby('Birth Year').size().sort_values(0, ascending = False).reset_index()
full_df.groupby('Death Year').size().sort_values(0, ascending = False).reset_index()

#Create a century variable
full_df['Century'] = round(pd.to_numeric(full_df['Birth Year']) // 100 + 1, 0).apply(str).str.split('.').str[0] + 'th'
full_df['Century'].unique()
min(pd.to_numeric(full_df['Birth Year']))
#For now create a color dict, but this should be faster in the future
colorsIdx = {'nanth': 'grey','13th': 'rgb(215,48,39)', '14th': 'rgb(215,148,39)', '15th':'blue', '16th':'red'\
,'17th':'yellow', '18th': 'darkgreen', '19th':'orange', '20th':'purple'}
cols      = full_df['Century'].map(colorsIdx)


#Do a cluster analysis based on page length and conections
size = full_df['Page Length']
trace0 = go.Scatter(
    y=full_df['links_to'],
    x=full_df['Page Length'],
    text = full_df['Title'] + '<br>' + full_df['Century'] + ' Century',
    mode='markers',
    marker=dict(
        size=size,
        sizemode='area',
        color=cols,
        sizeref=2.*max(size)/(40.**2),
        sizemin=4
    )
)

layout_comp = go.Layout(
    title='Relationship Page Length and Conncections',
    hovermode='closest',
    xaxis=dict(
        title='Wikipedia Page Length',
        ticklen=5,
        zeroline=False,
        gridwidth=2,
    ),
    yaxis=dict(
        title='Connections to',
        ticklen=5,
        gridwidth=2,
    ),
)

data = [trace0]
fig_comp = go.Figure(data=data, layout=layout_comp)
py.iplot(fig_comp,filename='Architects Conncections')

#Create a plot for from and to connections as well
size = full_df['links_to']
trace0 = go.Scatter(
    y=full_df['links_to'],
    x=full_df['links_from'],
    text = full_df['Title'] + '<br>' + full_df['Century'] + ' Century',
    mode='markers',
    marker=dict(
        size=size,
        sizemode='area',
        color=cols,
        sizeref=2.*max(size)/(40.**2),
        sizemin=4
    )
)

layout_comp = go.Layout(
    title='Relationship Links from and Links to',
    hovermode='closest',
    xaxis=dict(
        title='Connections from',
        ticklen=5,
        zeroline=False,
        gridwidth=2,
    ),
    yaxis=dict(
        title='Connections to',
        ticklen=5,
        gridwidth=2,
    ),
)

data = [trace0]
fig_comp = go.Figure(data=data, layout=layout_comp)
py.iplot(fig_comp, xaxis = '', yaxis = '',filename='Architects Conncections 2')
#full_df.to_csv('~/Downloads/biggest_architects.csv', sep = ';')

#Add the colors for the network plot
full_df['Colors'] = full_df['Century'].map(colorsIdx)
#merge with the links_people
links_people = pd.merge(full_df[['Title', 'Century']], links_people, left_on = 'Title', right_on = 'from')

#building a network of people right now
G=nx.from_pandas_edgelist(links_people, source='from', target='to')

got_net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

sources = links_people['to']
targets = links_people['from']
links_people['Weight'] = 1
weights = links_people['Weight']
century = links_people['Century']

edge_data = zip(sources, targets, weights, century)

for e in edge_data:
    try:
        src = e[0]
        dst = e[1]
        w = e[2]
        color_src = full_df[full_df['Title'] == e[0]].reset_index()['Colors'][0]
        color_dst = full_df[full_df['Title'] == e[1]].reset_index()['Colors'][0]

        got_net.add_node(src, src, title=src, color = color_src, borderWidth = 1)
        got_net.add_node(dst, dst, title=dst, color = color_dst,  borderWidth = 1)
        got_net.add_edge(src, dst, value=w, color = 'grey')
    except:
        print('Error with matching')

neighbor_map = got_net.get_adj_list()
got_net.barnes_hut(gravity=-62503, central_gravity=0, spring_length=550, spring_strength=0.001, damping=0.9, overlap=0.14)
# add neighbor data to node hover data
for node in got_net.nodes:
    node["title"] += " Neighbors:<br>" + "<br>".join(neighbor_map[node["id"]])
    node["value"] = len(neighbor_map[node["id"]])
got_net.show_buttons(filter_=['physics'])
got_net.show("network.html")
