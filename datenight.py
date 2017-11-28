#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from time import gmtime, strftime, mktime
import uuid
import pytz
import json
import subprocess
import logging
import feedparser
import re
import random
import webbrowser
import io

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# CONSTANTS & CONFIG
primetime = ["20", "21", "22"]
# primetime should be shows that start after 8pm ET and end before 11 ET. This removes talk shows.
primetime2 = ["8:00", "8:30", "9:00", "9:30", "10:00", "10:30"]
networks = ["2", "8", "4", "1", "3", "9", "26", "16", "20", "13", "10", "32", "23", "65", "52"]
# ids in list match networks from TV Maze: https://www.tvmaze.com/networks
"""
1 NBC
2 CBS
3 ABC
4 FOX
8 HBO
9 Showtime
10 Adult Swim
13 FX
16 SyFy
20 AMC
23 Comedy Central
26 Freeform
32 TBS
65 IFC
"""
movieregex = r'(\[{"id".*?}]),' # helps us find the movie data buried within RottenTomatoes HTML in a script tag
empty_primetime_regex= r'(<p><strong>.*?pm<\/strong><\/p>)'

# URL roots
buzzfeed = "https://www.buzzfeed.com/api/v2/feeds/tasty?p="
food52 = "https://food52.com/recipes/search?cat=entrees%2Cfive-ingredients-or-fewer%2Cone-pot-wonders&page="
tvmaze = "http://api.tvmaze.com/schedule?country=US&date="
voxnews = "https://www.vox.com/rss/index.xml"
newmovies = "https://www.rottentomatoes.com/browse/opening"
intheatres = "https://www.rottentomatoes.com/browse/in-theaters"


# GET & SCRAPE DATA
def recipes():
    # Get a ton of recipes from BuzzFeed Tasty & Food52 if they are tagged with dinner or weeknight. scrape like 5 pages?
    ra = range(1, 6)
    list = []
    for i in ra: 
        r1 = requests.get(buzzfeed+str(i))
        # For BuzzFeed, we can use this API data format: https://newsapi.org/s/buzzfeed-api
        #assert (r1.status_code == 200), "BAD BF HTTP REQUEST"
        #assert ('buzzes' in r1.json()), "NO BF RECIPES FOUND"
        
        for b in r1.json()['buzzes']:
            if "dinner" in b['tags']:
                list.append({ 
                    "url" : "https://buzzfeed.com" + b['canonical_path'],
                    "title" : b['title']
                })
        
        # For Food52, there is no API, so we scrape each page & find data we want using the class name `photo`
        r2 = requests.get(food52+str(i))
        #assert (r2.status_code == 200), "BAD F52 HTTP REQUEST"

        soup = BeautifulSoup(r2.text, 'html.parser')
        recipes = soup.find_all("a", class_="photo")
        #assert (recipes is not None), "NO F52 RECIPES FOUND"

        for rec in recipes:
            list.append({
                "url" : "https://food52.com"+ rec.get('href').encode('utf-8'),
                "title" : rec.get('title').encode('utf-8')
            })
        
    #assert (list is not None), "RECIPE LIST IS EMPTY"
    return list


def TVListings():
    eastern = pytz.timezone('US/Eastern')
    today = datetime.now(eastern).strftime('%Y-%m-%d')
    list =[]
    r = requests.get(tvmaze + today)
    # TVMAZE API DOCS & return format: https://www.tvmaze.com/api#schedule
    #assert (r.status_code == 200), "BAD TV MAZE HTTP REQUEST"
    
    for t in r.json():
        if (t['airtime'][:2] in primetime) and (str(t['show']['network']['id']) in networks):
            list.append({ 
                "show" : t['show']['name'],
                "network" : t['show']['network']['name'],
                "airtime" : t['airtime'],
                "url" : t['url']
            })

    #assert (list is not None), "NO TV LISTINGS FOUND FOR TODAY"
    return list


def news():
    list =[]
    rss = feedparser.parse(voxnews)
    #assert (rss is not None), "RSS PARSING ERROR"
    #assert (rss['entries'] is not None), "NO NEWS STORIES FOUND"

    for index, s in enumerate(rss['entries']):
        if index == 3:
            break
        list.append({ 
            "url" : s['link'],
            "title" : s['title']
        })
    return list


def newMovies():
    # Opening this week
    list=[]
    r = requests.get(newmovies)
    #assert (r.status_code == 200), "BAD RT HTTP REQUEST (NEW)"
    # use regex to capture movie data from source code block.
    movies = json.loads(re.search(movieregex, r.text).groups()[0])
    i=0
    for m in movies:
        if i > 7:
            break 
        if m['tomatoScore'] >= 80:
            list.append({
                "url" : "https://www.rottentomatoes.com"+m['url'],
                "title" : m['title'],
                "score" : str(m['tomatoScore'])
            })
            i = i+1
    return list
    # if no new movies, that's ok, there will be an empty list, which is ok.


def topMovies():    
    # Tops at the box office
    list=[]
    r = requests.get(intheatres)
    #assert (r.status_code == 200), "BAD RT HTTP REQUEST (IN THEATRES)"
    # use regex to capture movie data from source code block.
    movies = json.loads(re.search(movieregex, r.text).groups()[0])
    # if no movies in theatres, then we have a problem, because that's highly unlikely. There's always something playing, so there should always be some top movies.
    #assert (movies is not None), "NO MOVIES FOUND IN THEATRES ~ HIGHLY UNLIKELY"
    i=0
    for m in movies:
        if i > 2:
            break 
        if m['tomatoScore'] >= 70 and m['popcornScore'] >= 80:
            list.append({
                "url" : "https://www.rottentomatoes.com"+m['url'],
                "title" : m['title'],
                "score" : str(m['tomatoScore'])
            })
            i=i+1

    #assert (list is not None), "NO HIGH QUALITY MOVIES FOUND TODAY" #while unlikely, it is possible we won't have any good movies
    return list


# PROCESS DATA & ASSEMBLE EMAIL
def assembleEmail():
    # GET DATA
    recipe_list = recipes()
    tv_list = TVListings()
    newMovies_list = newMovies()
    topMovies_list = topMovies()
    news_list = news()

    # GENERATE EMAIL, SECTION BY SECTION
    html = recipeHTML(recipe_list) + tvHTML(tv_list) + newMovieHTML(newMovies_list) + topMovieHTML(topMovies_list) + newsHTML(news_list)
    return html


def previewHTML(html):
    # PREVIEW EMAIL IN BROWSER
    path = os.path.abspath('temp.html')
    url = 'file://' + path
    with io.open(path, mode='w', encoding="utf-8") as f:
        f.write(html)
    webbrowser.open(url)


def recipeHTML(data):
    html = "<h2>Stay in & cook together</h2>"
    random_recipes = random.sample(data, 3)
    for r in random_recipes: 
        html = html + ("<p><a href=\"%s\">%s</a></p>" % (r['url'], r['title']))
    return html


def tvHTML(data):
    html = "<h2>Prepare for prime time</h2>"
    for t in primetime2: #iterate through listings matching primetime showtimes and start grouping them together by airtime
        line = "<p><strong>%s pm</strong>: " % (t)
        for e in data:
            time = str(int(e['airtime'][:2])-12) + e['airtime'][2:] #convert to 24 hour time for comparison
            if time == t: 
                line = line + ("<a href=\"%s\">%s</a> (%s), " % (e['url'], e['show'], e['network']))
        line = line[:-2] +"</p>"
        line = re.sub(empty_primetime_regex, '', line) # excise empty timeslots from html
        html = html + line
    return html


def newsHTML(data):
    html = "<h2>Have a conversation</h2>"
    random_news = random.sample(data, 3)
    for r in random_news: 
        html = html + ("<p><a href=\"%s\">%s</a></p>" % (r['url'], r['title']))
    return html


def newMovieHTML(data):
    html = "<h2>Catch a movie</h2>\n<p><strong>Opening this week:</strong> "
    i=0
    for m in data:
        if i > 7:
            break 
        html = html + ("<a href=\"%s\">%s</a> (%s%%), " % (m['url'], m['title'], m['score']))
        i = i+1
    html = html[:-2] + "</p>"
    return html


def topMovieHTML(data):
    html = "<p><strong>Tops at the box office:</strong> "
    i=0
    for m in data:
        if i > 2:
            break 
        html = html + ("<a href=\"%s\">%s</a> (%s%%), " % (m['url'], m['title'], m['score']))
        i = i+1
    html = html[:-2] + "</p>"
    return html



if __name__ == "__main__":
    print "RUNNING SCRAPERS & GENERATING EMAIL HTML\n****"
    html = assembleEmail()
    print html 
    previewHTML(html)