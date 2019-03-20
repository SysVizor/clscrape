"""
    Claigslist Scraping
    -------------------
    Check for new and updated listings. Send notification via telegram if found.
    
    Be sure to add YOUR telegram bot ID to the bot_id variable! Or notifications will NOT work.

    Set this process as a scheduled task at your desired interval. I suggest nothing shorter than 5 minutes.
"""

import sqlite3
import clscrape


# If the database name is changed, be sure it matches the name in clscrape_manange.py
db = 'clscrape.db'

# ADD TELEGRAM BOT ID HERE!
bot_id = ''
# Be sure to place the bot id inside quotes

# Check if database exists
clscrape.db_check(db)
# Connect to existing database
con = sqlite3.connect(db)
cur = con.cursor()

# Iterate page_parse function for each request
cur.execute("select id from requests")
for id in cur.fetchall():
    clscrape.page_parse(db, False, id[0])

con.close()

clscrape.telegram_notify(db,bot_id)