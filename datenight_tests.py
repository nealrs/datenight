#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from datenight import *
from tidylib import tidy_document, tidy_fragment

# CONFIG PARAMS
tidyoptions={"show-warnings": False}
para_regex = r'(<p><a href=\".*?\">.*?<\/a><\/p>)' #regex string to identify paragraphs w/ links
link_regex = r'(<a href=\".*?\">.*?<\/a>)' #regex string to identify links
comma_regex = r'(<p>.*?,<\/p>)' #regex string to identify paragraphs w/ links

## TEST SCRAPERS - primarily concerned with size & format of data objects (all neccesary keys exist) - ensures data will be displayed properly. Additionally, if URLs match data providers, good assumption that data is right.
class recipeTest(unittest.TestCase):
    def setUp(self):
        self.recipes = recipes()
    
    def tearDown(self):
        pass

    def testSize(self):
        assert len(self.recipes) > 0, "Recipe list is empty"
    
    def testKeys(self):
        assert 'url' in self.recipes[0] and 'title' in self.recipes[0], "Incorrect Keys / data in recipe list"

    def testURL(self):
        assert "https://buzzfeed.com" in self.recipes[0]['url'] or "https://food52.com" in self.recipes[0]['url'], "Non BuzzFeed / F52 URLs found in recipe list"


class tvTest(unittest.TestCase):
    def setUp(self):
        self.tv = TVListings()
    
    def tearDown(self):
        pass

    def testSize(self):
        assert len(self.tv) > 0, "TV Listings are empty"
    
    def testKeys(self):
        assert 'show' in self.tv[0] and 'network' in self.tv[0] and 'airtime' in self.tv[0] and 'url' in self.tv[0], "Incorrect Keys / data in TV listings"

    def testURL(self):
        assert "http://www.tvmaze.com" in self.tv[0]['url'], "Non TVMaze URLs found in TV listings"

    def testAirtime(self):
        assert all(x['airtime'][:2] in primetime for x in self.tv), "Non primetime Airtimes found in TV Listings"


class newsTest(unittest.TestCase):
    def setUp(self):
        self.news = news()
    
    def tearDown(self):
        pass

    def testSize(self):
        assert len(self.news) > 0 and len(self.news) <=3, "Either more than 3 or no news articles found"
    
    def testKeys(self):
        assert 'url' in self.news[0] and 'title' in self.news[0], "Incorrect Keys / data in news article list"

    def testURL(self):
        assert "https://www.vox.com" in self.news[0]['url'], "Non VOX URLs found in news article list"


class newMoviesTest(unittest.TestCase):
    def setUp(self):
        self.movies = newMovies()
    
    def tearDown(self):
        pass

    def testSize(self):
        #print self.movies
        assert len(self.movies) > 0 and len(self.movies) <=8, "Either more than 7 new movies found or zero found"
    
    def testKeys(self):
        assert 'url' in self.movies[0] and 'title' in self.movies[0] and 'score' in self.movies[0], "Incorrect Keys / data in new movies list"

    def testURL(self):
        assert "https://www.rottentomatoes.com" in self.movies[0]['url'], "Non RT URLs found in new movie list"
    
    def testScore(self):
        assert all( int(x['score']) >=80 for x in self.movies), "New movies found with tomato scores below threshold"


class topMoviesTest(unittest.TestCase):
    def setUp(self):
        self.movies = topMovies()
    
    def tearDown(self):
        pass

    def testSize(self):
        #print self.movies
        assert len(self.movies) > 0 and len(self.movies) <=3, "Either more than 2 top movies found or zero found"
    
    def testKeys(self):
        assert 'url' in self.movies[0] and 'title' in self.movies[0] and 'score' in self.movies[0], "Incorrect Keys / data in top movies list"

    def testURL(self):
        assert "https://www.rottentomatoes.com" in self.movies[0]['url'], "Non RT URLs found in top movie list"
    
    def testScore(self):
        assert all( int(x['score']) >=70 for x in self.movies), "Top movies found with tomato scores below threshold"

## TEST EMAIL ASSEMBLY METHODS - primarily concerned that these methods return valid HTML. 

class emailAssemblyTest(unittest.TestCase):
    # primary concern here is to ensure we have a non-empty string that contains all sections (recipes, news, tv, movies.)
    def setUp(self):
        self.email = assembleEmail()
    
    def tearDown(self):
        pass

    def testSize(self):
        #print self.email
        assert self.email is not None and self.email is not "", "Empty email HTML"
    
    def testSections(self):
        sections = [
            "<h2>Stay in & cook together</h2>", 
            "<h2>Prepare for prime time</h2>", 
            "<h2>Catch a movie</h2>\n<p><strong>Opening this week:</strong>", 
            "<p><strong>Tops at the box office:</strong>", 
            "<h2>Have a conversation</h2>"
        ]
        assert all(x in self.email for x in sections), "Not all sections included in email"


class recipeHTMLTest(unittest.TestCase):
    # ensure that we have a list of 3 recipes & that HTML is valid
    def setUp(self):
        self.html = recipeHTML(recipes())
    
    def tearDown(self):
        pass
    
    def testEmpty(self):
        assert self.html is not None and self.html is not "", "Empty recipe HTML"
    
    def testSize(self):
        count = len(re.findall(para_regex, self.html))
        assert count > 0 and count <=3, "HTML contains either 0 or more than 3 recipe lines"
    
    def testHTMLValidate(self):
        htmlFragment, errors = tidy_fragment(self.html, tidyoptions)
        assert errors is not None, "Recipe HTML validation error"
        

class tvHTMLTest(unittest.TestCase):
    # ensure that we have a non-empty list of TV listings, that HTML is valid, an that there are no trailing commas
    def setUp(self):
        self.html = tvHTML(TVListings())
    
    def tearDown(self):
        pass
    
    def testEmpty(self):
        #print self.html
        assert self.html is not None and self.html is not "", "Empty TV listing HTML block"
    
    # check for trailing commas at end of lines
    def testTrailingComma(self):
        count = len(re.findall(comma_regex, self.html))
        assert count <1, "Trailing commas found at end of lines in primetime HTML block"

    # test for blank primetime lines - count length of empty_primetime_regex
    def testEmptyLines(self):
        count = len(re.findall(empty_primetime_regex, self.html))
        assert count <1, "Empty primetime slot found in HTML"
     
    #def testSize(self):
        #count = len(re.findall(para_regex, self.html))
        #assert count > 0 and count <=3, "HTML contains either 0 or more than 3 recipe lines"
    
    def testHTMLValidate(self):
        htmlFragment, errors = tidy_fragment(self.html, tidyoptions)
        assert errors is not None, "TV listings HTML validation error" 


class newsHTMLTest(unittest.TestCase):
    # ensure that we have non-empty / appropriate # of news articles & that HTML is valid
    def setUp(self):
        self.html = newsHTML(news())
    
    def tearDown(self):
        pass
    
    def testEmpty(self):
        assert self.html is not None and self.html is not "", "Empty news HTML"
    
    def testSize(self):
        count = len(re.findall(para_regex, self.html))
        assert count > 0 and count <=3, "HTML contains either 0 or more than 3 news articles"
    
    def testHTMLValidate(self):
        htmlFragment, errors = tidy_fragment(self.html, tidyoptions)
        assert errors is not None, "News HTML validation error"


class newMoviesHTMLTest(unittest.TestCase):
    # ensure that we have a non-empty list of movies, that HTML is valid, an that there are no trailing commas
    def setUp(self):
        self.html = newMovieHTML(newMovies())
    
    def tearDown(self):
        pass
    
    def testEmpty(self):
        assert self.html is not None and self.html is not "", "Empty new movies HTML"
    
    def testSize(self):
        count = len(re.findall(link_regex, self.html))
        assert count > 0 and count <=8, "HTML contains either 0 or more than 8 new movies"
    
    # check for trailing commas at end of lines
    def testTrailingComma(self):
        count = len(re.findall(comma_regex, self.html))
        assert count <1, "Trailing commas found at end of new movies HTML"

    def testHTMLValidate(self):
        htmlFragment, errors = tidy_fragment(self.html, tidyoptions)
        assert errors is not None, "New movies HTML validation error"


class topMoviesHTMLTest(unittest.TestCase):
    # ensure that we have a non-empty list of movies, that HTML is valid, an that there are no trailing commas
    def setUp(self):
        self.html = topMovieHTML(topMovies())
    
    def tearDown(self):
        pass
    
    def testEmpty(self):
        assert self.html is not None and self.html is not "", "Empty top movies HTML"
    
    def testSize(self):
        count = len(re.findall(link_regex, self.html))
        assert count > 0 and count <=3, "HTML contains either 0 or more than 3 top movies"
    
    #check for trailing commas at end of lines
    def testTrailingComma(self):
        count = len(re.findall(comma_regex, self.html))
        assert count <1, "Trailing commas found at end of top movies HTML"

    def testHTMLValidate(self):
        htmlFragment, errors = tidy_fragment(self.html, tidyoptions)
        assert errors is not None, "Top movies HTML validation error"


if __name__ == "__main__":
    unittest.main()