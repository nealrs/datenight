# Date Night Script

My girlfriend and I often find ourselves in _analysis paralysis_ when date night roles around. Should we go out? Stay in? What would we even cook? Is there anything good on TV tonight / at the movies? What if we just want to talk?

It's not a serious problem, but it made me think: why not use technology to improve my relationship? Because I'd prefer to enjoy my time with Bae, rather than planning it.

This code sample is comprised of five web scraper methods, which feed into generator functions which compose the body of an HTML email:

1. `storeRecipes()` ~ Scrapes BuzzFeed Tasty & Food52 for dinner recipes we can cook at home (returns JSON)
2. `storeTVListings()` ~ Scrapes TV Maze for tonight's primetime TV listings for our agreed upon channels (returns JSON)
3. `storeNews()` ~ Retrieves the latest 3 stories from Vox's RSS feed. (returns JSON)
4. `storeNewMovies()` ~ Scrapes Rotten Tomatoes for this week's new releases, based on our RT score criteria. (returns JSON)
5. `storeTopMovies()` ~ Scrapes Rotten Tomatoes for this week's top movies at the box office, based on our RT score criteria. (returns JSON)

As part of a larger application (not included here), a daily cron job runs the scrapers, stores the data in Redis, and then generates & sends a customized HTML email to me & my girlfriend. I chose to only include the scrapers & HTML generation in this sample, because the core data is what matters most.

# Setup & execution
Install dependencies `pip install -r requirements.txt` and run `python datenight.py` to execute the script. It should both print the final HTML to console & open a webbrowser to render it.

# Testing

Execute the included PyUnit tests by running `python datenight_tests.py`. Unit tests are written to ensure that data exists / is in the right format for HTML output. 
