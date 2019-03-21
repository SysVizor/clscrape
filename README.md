# clscrape
A Craigslist scraping application written in Python
---

There are plenty of applications that can scrape through web pages, but all of the ones that I found either had a cost associated to it or didn't do what I wanted to do.

So I built my own. This application will parse through the listings on given search criteria and send notifications via telegram for new listings (or updated pricing). And to top it all off, has a management application to make it easy/easier to use.

To accomplish all of this I used:
- BeautifulSoup
- SQLite3
- Flask
- python-telegram-bot

If you're not familiar with SQL or databases in general, you're in luck. SQLite does not require a server application to be set up, and everything is created and managed by the program.

## Installation
Prerequisites:
- [Python3](https://www.python.org/)
- [Flask](http://flask.pocoo.org/)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

Simply download or clone the repository, and place the files wherever you like.

## Usage
The first thing to do is run <code>clscrape_manage.py</code>. This will create the database file, and host the management page on <code>localhost:5000</code>, which can be opened in a web browser.

Once you open the page, navigate to <code>Manage Requests</code>. Here a new query to search through on Craigslist can be added.

Both the email and telegram id are optional, and email notifications are not currently implemented. For telegram notifications to work, you must enter _your_ telegram chat id (the easiest way to get this is by forwarding a message to @getidsbot)

The Query field is anything that you might type into the search bar on the left.

## Updates and Notifications
If you want to get notifications, you will first need to set up a Telegram Bot (the easiest way to do this is by messaging @BotFather). Once you have your bot's token, copy it into the <code>bot_id</code> variable in <code>clscrape_main.py</code>. And send a message to your new bot.

Now, create a scheduled task with for <code>clscrape_main.py</code> and run it at any time interval that you feel comfortable with. However, I suggest nothing shorter than 5 minutes, and this interval should be larger if you have a large number of requests.
