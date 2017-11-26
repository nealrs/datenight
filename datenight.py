#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from time import gmtime, strftime, mktime
import uuid
import pytz
import json
import redis
import subprocess
import logging
import feedparser
import re

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def storeRecipes():
    # Get a ton of recipes from BuzzFeed Tasty & Food52 if they are tagged with dinner or weeknight. scrape like 5 pages?
    ra = range(1, 6)
    list = []
    for i in ra: 
        r1 = requests.get("https://www.buzzfeed.com/api/v2/feeds/tasty?p="+str(i))
        assert (r1.status_code == 200), "BAD BF HTTP REQUEST"
        assert ('buzzes' in r1.json()), "NO BF RECIPES FOUND"
        
        for b in r1.json()['buzzes']:
            if "dinner" in b['tags']:
                list.append({ 
                    "path" : "https://buzzfeed.com" + b['canonical_path'],
                    "title" : b['title']
                })
        r2 = requests.get("https://food52.com/recipes/search?cat=entrees%2Cfive-ingredients-or-fewer%2Cone-pot-wonders&page="+str(i))
        assert (r2.status_code == 200), "BAD F52 HTTP REQUEST"

        soup = BeautifulSoup(r2.text, 'html.parser')
        recipes = soup.find_all("a", class_="photo")
        assert (recipes is not None), "NO F52 RECIPES FOUND"

        for rec in recipes:
            list.append({
                "path" : "https://food52.com"+ rec.get('href').encode('utf-8'),
                "title" : rec.get('title').encode('utf-8')
            })
        
    assert (list is not None), "RECIPE LIST IS EMPTY"
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    return redisdb.set("recipes", str(json.dumps(list)))



def storeTVListings():
    eastern = pytz.timezone('US/Eastern')
    today = datetime.now(eastern).strftime('%Y-%m-%d')
    list =[]
    r = requests.get("http://api.tvmaze.com/schedule?country=US&date=" + today)
    assert (r.status_code == 200), "BAD TV MAZE HTTP REQUEST"
    
    for t in r.json():
        # removed talk shows & anything stuff that starts after 11pm
        if (t['airtime'][:2] in ["20", "21", "22"]) and (str(t['show']['network']['id']) in ["2", "8", "4", "1", "3", "9", "26", "16", "20", "13", "10", "32", "23", "65", "52"]):
            list.append({ 
                "show" : t['show']['name'],
                "episode" : t['name'],
                "network" : t['show']['network']['name'],
                "airtime" : t['airtime'],
                "runtime" : t['runtime'],
                "summary" : t['summary'],
                "url" : t['url']
            })

    assert (list is not None), "NO TV LISTINGS FOUND FOR TODAY"
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    return redisdb.set("tvlistings", str(json.dumps(list)))


# store news stories as a block of html, rather than a list / json object ~ because we won't iterate over it / use any logic to determine which part of it to display
def storeNews():
    url = "https://www.vox.com/rss/index.xml"
    rss = feedparser.parse(url)
    assert (rss is not None), "RSS PARSING ERROR"

    html = ""
    assert (rss['entries'] is not None), "NO NEWS STORIES FOUND"

    for index, s in enumerate(rss['entries']):
        if index == 3:
            break
        html = html + "<p><a href=\""+s['link']+"\">"+s['title']+"</a></p>\n"

    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    return redisdb.set("voxnews", html)


# store movie data as a block of html, rather than a list / json object ~ because we won't iterate over it / use any logic to determine which part of it to display
def storeMovies():
    html = ""
    # Opening this week
    new=""
    url = "https://www.rottentomatoes.com/browse/opening"
    r = requests.get(url)
    assert (r.status_code == 200), "BAD RT HTTP REQUEST (NEW)"
    
    movies = json.loads(re.search(r'(\[{"id".*?}]),', r.text).groups()[0])
    i=0
    for m in movies:
        if i > 7:
            break 
        if m['tomatoScore'] >= 80:
            new = new + "<a href=\"https://www.rottentomatoes.com"+m['url']+"\">"+m['title']+"</a> ("+str(m['tomatoScore'])+ "%), "
            i = i+1
    # if no new movies, that's ok, there will be an empty list, which is truthful.

    
    # Tops at the box office
    tops=""
    url = "https://www.rottentomatoes.com/browse/in-theaters"
    r = requests.get(url)
    assert (r.status_code == 200), "BAD RT HTTP REQUEST (IN THEATRES)"
    movies = json.loads(re.search(r'(\[{"id":.*?}]),', r.text).groups()[0])
    # if no movies in theatres, then we have a problem
    assert (movies is not None), "NO MOVIES FOUND IN THEATRES ~ HIGHLY UNLIKELY"
    i=0
    for m in movies:
        if i > 2:
            break 
        if m['tomatoScore'] >= 70 and m['popcornScore'] >= 80:
            tops = tops + "<a href=\"https://www.rottentomatoes.com"+m['url']+"\">"+m['title']+"</a> ("+str(m['tomatoScore'])+ "%), "
            i=i+1
    
    html="<p><strong>Opening this week:</strong> " + new[:-2]+ "</p>\n" + "<p><strong>Tops at the box office:</strong> " + tops[:-2]+ "</p>\n"
    
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    return redisdb.set("movies", html)
    

# set data
print "RUNNING SCRAPERS\n****"
storeRecipes()
storeTVListings()
storeNews()
storeMovies()


# get data (Debug)
print "CHECK OUTPUT\n****"
redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])

print "RECIPES\n****"
print redisdb.get("recipes")

print "TV LISTINGS\n****"
print redisdb.get("tvlistings")

print "VOX NEWS\n****"
print redisdb.get("voxnews")

print "MOVIES\n****"
print redisdb.get("movies")