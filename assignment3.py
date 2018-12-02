from sys import platform as sys_pf
if sys_pf == 'darwin':
    import matplotlib
    matplotlib.use("TkAgg")
import requests
import collections
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import matplotlib
import networkx as nx
from matplotlib.pyplot import show


def tokenize(string):
    return ''.join(re.findall('[\w|\d]+', string))

#相对路径转绝对路径
def absolute_urls(url,relative_url):
    return urljoin(url,relative_url)


def get_source_page_html(urls):
    headers = {"User-Agent" : "User-Agent:Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}
    r = requests.get(urls, headers=headers).content.decode('utf8')
    return r


def list_stations(each_line_souce_page):
    ##很难用一种过滤方式找到正确的所有站点，这里用了笨的办法，用两种过滤方式，然后用Max,每条线取找到最多站点的。
    soup=BeautifulSoup(each_line_souce_page,'html.parser')
    eachline_stations_one=[]
    eachline_stations_two=[]
    eachline_stations=[]

    x=soup.find_all('table',attrs={'data-sort':'sortDisabled'})
    for table in x:
        title=table.find('caption')
        if title==None:continue
        if title.string==None:continue
        if title.string[-1]=="表":
            stationlist=table.find_all('a')
            for i in stationlist:
                if i.string==None:continue
                if i.string[-1] =='站':
                    eachline_stations_one.append(i.string)
    y=soup.find('table',attrs={'data-sort':'sortDisabled'})
    stationlist_two = y.find_all('a')
    for i in stationlist_two:
        if i.string == None: continue
        if i.string[-1] == '站':
            eachline_stations_two.append(i.string)
    return max(eachline_stations_one,eachline_stations_two,key=lambda k: len(k))


def find_lines_with_stations():
    lines_and_stations=collections.defaultdict(list)
    url='https://baike.baidu.com/item/%E5%8C%97%E4%BA%AC%E5%9C%B0%E9%93%81/408485'
    soup = BeautifulSoup(get_source_page_html(url), 'html.parser')
    table=soup.find('table',attrs={'width':'658'})
    lines=table.find_all('a')
    lines.pop()
    for line in lines:
        lines_and_stations[line.string]=list_stations(get_source_page_html(absolute_urls(url,(line.get('href')))))
    return lines_and_stations


def display_lines_stations(dic):
    for i in dic:
        print("{}:{}\n".format(i, dic[i]))


def distance(element1, element2):
    for sublist in l:
        if element1 in sublist and element2 in sublist:
            return abs(sublist.index(element1) - sublist.index(element2))


def search_destination(graph, start, get_succsssors, is_goal_predicate, strategy_func):
    pathes = [[start]]
    seen = set()
    chosen_pathes = []
    while pathes:
        path = pathes.pop(0)
        frontier = path[-1]
        if frontier in seen: continue

        for city in get_succsssors(frontier, graph):
            if city in path: continue  # remove the loop
            new_path = path + [city]
            pathes.append(new_path)
            if is_goal_predicate(city): return new_path

        pathes = strategy_func(pathes)
        seen.add(frontier)
    return chosen_pathes

#加入经过路线的功能
def search_destination_add_by_way(start,destination,by_way_stations):
    path=[]
    by_way_segment=[]
    first_segment=search_destination(stations_connection_graph, start, get_succsssors,lambda n:n ==by_way_stations[0],shortest_path_priority)
    first_segment.pop()
    for i,by_way in enumerate(by_way_stations):
        if i<=len(by_way_stations)-2:
            by_way_segment+=search_destination(stations_connection_graph,by_way_stations[i], get_succsssors,lambda n:n ==by_way_stations[i+1],shortest_path_priority)
            by_way_segment.pop()
    last_segment=search_destination(stations_connection_graph,by_way_stations[-1],get_succsssors,lambda n:n==destination,shortest_path_priority)
    return print(first_segment+by_way_segment+last_segment)

def get_succsssors(froninter, graph):
    return graph[froninter]

def is_goal(node,destination):
    return node ==destination

def sort_pathes(pathes, func,beam):
    return sorted(pathes, key=func)[:beam]

#这里假设每组相邻站之间距离差不多
def shortest_path_priority(pathes):
    return sort_pathes(pathes, lambda p:len(p), beam=30)

#换成最少方案,是用path里相隔两个位置的元素做判断
def mininum_change_station(pathes):
    return sort_pathes(pathes, lambda p: number_lines(p), beam=30)

def number_lines(path):
    lines=0
    if len(path)==2:return 0
    for i in range(len(path)-1):
        if i==0:continue
        lines+=line_transfer(path[i-1],path[i+1])
    return lines

def line_transfer(a,b):
    for sublist in l:
        if a in sublist and b in sublist:return 0
    return 1
def comprehensive_sort(pathes):
    return sort_pathes(pathes, lambda p: (len(p) + number_lines(p)), beam=30)



t=find_lines_with_stations()
#display_lines_stations(t)
l=t.values()
allstations=[]
for i in l:
    for x in i:
        allstations.append(x)
all_stations=set(allstations)

from collections import defaultdict
#station_connection 为个地铁站之间联系的graph
stations_connection=defaultdict(list)

for station_one in all_stations:
    for station_two in all_stations:
        if station_one==station_two:continue
        if distance(station_one,station_two)==1:
            stations_connection[station_one].append(station_two)

stations_connection_graph=nx.Graph(stations_connection)
nx.draw(stations_connection_graph,with_labels=True,node_size=30)
#show()

"""
"""

print("最少换乘方案\n{}\n\n".format(search_destination(stations_connection_graph,'首经贸站',get_succsssors, lambda n: n =='西二旗站',mininum_change_station)))
print("最短路程方案\n{}\n\n".format(search_destination(stations_connection_graph,'首经贸站',get_succsssors, lambda n: n =='西二旗站',shortest_path_priority)))
#print(search_destination(stations_connection_graph,'首经贸站',get_succsssors, lambda n: n =='西二旗站',comprehensive_sort))

#加入中途站，作为第三个输入 Input:Start ,Destination,by_way
search_destination_add_by_way("五道口站","张自忠路站",["望京站",'东四站',"芍药居站"])