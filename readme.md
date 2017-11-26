# Date Night Script

My girlfriend and I find ourselves in analysis paralysis when date night roles around. Should we go out? Stay in? What would we even cook? Is there anything good on TV tonight / at the movies? What if we just want to talk?

It's not a serious problem, but it made me think: why can't I use technology to improve my relationship? Because I'd like to enjoy my time with her, rather than planning it.

This code sample is comprised of four web scraper methods:

1. `storeRecipes()` ~ Scrapes BuzzFeed Tasty & Food52 for dinner recipes we can cook at home (returns JSON)
2. `storeTVListings()` ~ Scrapes TV Maze for tonight's primetime TV listings for our agreed upon channels (returns JSON)
3. `storeNews()` ~ Retrieves the latest 3 stories from Vox's RSS feed. (returns HTML)
4. `storeMovies()` ~ Scrapes Rotten Tomatoes for this week's new releases & what's tops at the box office, based on our RT score criteria. (returns HTML)

As part of a larger application (not included here), a daily cron job runs the scrapers, stores the data in Redis, and sends a customized HTML email to me & my girlfriend. 

I chose to only include the scrapers in this sample, because the core data is what matters most.

# Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set a `REDIS_URL` environment variable. Does not matter if it's a local or remote Redis instance.

# Running the script

Run `python datenight.py` to run scrapers and review the output. 

`storeRecipes()` and `storeTVListings()` return JSON for further processing in a larger app/email script. `storeNews()` and `storeMovies()` return HTML strings ready for rendering in app/email.

# Testing

Assertion tests are included inline to ensure HTTP requests are successful and that they do contain useful data. If no data is found or API results are empty, the script will throw an `AssertionError`.


