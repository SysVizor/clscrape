"""
    Claigslist Scraping
    -------------------
    Functions for program. Called by main and manage

    python-telegram-bot is required for notification
    https://github.com/python-telegram-bot/python-telegram-bot

    pip install python-telegram-bot
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import time
import random
import telegram

def db_check(db):
    if os.path.isfile(db) == False:
        # Create new database
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute('''CREATE TABLE requests (
            id integer,
            reqLoc text,
            telegram_id text,
            query text,
            created text
        )''')
        con.commit()
        cur.execute('''CREATE TABLE results (
            pid integer,
            repost integer,
            listing_created text,
            title text,
            href text,
            price integer,
            loc text,
            request_id integer,
            notification_sent text
        )''')
        con.commit()
        con.close()

def db_add_req(db,reqLoc,telegram_id,query):
    str_time = time.strftime('%Y-%m-%d %H:%M')
    pk = time.strftime('%Y%m%d%H%M%S') + str(random.randint(100,999))
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute('insert into requests values (?,?,?,?,?)', (pk,reqLoc,telegram_id,query,str_time))
    con.commit()
    con.close()
    return pk

def page_parse(db, request_new, request_id):
    con = sqlite3.connect(db)
    cur = con.cursor()
    # Get request details
    cur.execute("select reqLoc from requests where id = ?", (request_id,))
    location = cur.fetchone()[0]
    cur.execute("select query from requests where id = ?", (request_id,))
    query = cur.fetchone()[0]

    # Fetch page
    uri = 'https://' + location + '.craigslist.org/search/sss?query=' + query.replace(" ", "%20") + '&sort=rel'
    data = requests.get(uri)
    main = BeautifulSoup(data.text, 'html.parser')
    ul = main.find('ul', {'class': 'rows'})
    
    # Parse listings
    for li in ul.find_all('li'):
        #CL ID
        pid = li['data-pid']
        #CL REPOST ID
        if li.has_attr('data-repost-of'):
            repost = li['data-repost-of']
        else:
            repost = None
        #POST TIMESTAMP
        for t in li.find_all('time'):
            ptime = t['datetime']
        #POST META
        a = li.find('a', {'class': 'result-title hdrlnk'})
        title = a.text.strip()
        href = a['href']
        price = li.find('span', {'class': 'result-price'})
        price = str(price)[28:-7]
        loc = li.find('span', {'class': 'result-hood'})
        loc = str(loc)[28:-8]
        if request_new == True:
            cur.execute("insert into results values (?,?,?,?,?,?,?,?,?)", (pid,repost,ptime,title,href,price,loc,request_id,'NR'))
            con.commit()
        else:
            # Check if listing in database
            cur.execute("select pid from results where pid = ? and request_id = ?", (pid, request_id))
            if cur.fetchall() == []:
                # Create new entry in database
                cur.execute("insert into results values (?,?,?,?,?,?,?,?,?)", (pid,repost,ptime,title,href,price,loc,request_id,None))
                con.commit()
            else:
                # Update existing entry in database
                cur.execute("select price from results where pid = ? and request_id = ?", (pid,request_id))
                if int(price) != cur.fetchone()[0]:
                    cur.execute("update results set price = ?, notification_sent = ? where pid = ? and request_id = ?", (price,'UPDATE',pid,request_id))
                    con.commit()
    con.close()

def db_fetch(db, tble):
    q = "select * from " + str(tble)
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute(q)
    res = cur.fetchall()
    con.close()
    return res

def db_del_req(db, selected):
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("delete from requests where id = ?", (selected,))
    con.commit()
    con.close()

def db_result_purge(db):
    con = sqlite3.connect(db)
    cur = con.cursor()
    # Remove results where request has been removed
    cur.execute('''select distinct rs.request_id
    from results rs
    left join requests rq on rs.request_id = rq.id
    where rq.id is null
    ''')
    for id in cur.fetchall():
        cur.execute("delete from results where request_id = ?", (id[0],))
        con.commit()
    con.close()

def db_result_cleanup(db):
    con = sqlite3.connect(db)
    cur = con.cursor()
    # Remove expired results
    cur.execute("select href from results")
    for href in cur.fetchall():
        data = requests.get(href[0])
        main = BeautifulSoup(data.text, 'html.parser')
        pt = main.find('h2', {'class': 'postingtitle'})
        if pt == None:
            cur.execute("delete from results where href = ?", (href[0],))
            con.commit()
    con.close()

def telegram_notify(db, bot_id):
    bot = telegram.Bot(token=bot_id)
    con = sqlite3.connect(db)
    cur = con.cursor()
    # Send notification telegram_id when listing is new or updated
    cur.execute('''select rq.telegram_id, rs.notification_sent,
    rs.title, rs.price, rs.href, rs.loc, rs.pid, request_id
    from results rs
    inner join requests rq on rs.request_id = rq.id
    where rs.notification_sent = 'UPDATE'
    or rs.notification_sent is null and rs.repost is null
    ''')
    for listing in cur.fetchall():
        str_time = time.strftime('%Y-%m-%d %H:%M')
        if listing[1] == 'UPDATE':
            message = 'LISTING UPDATED - ' + listing[2] + '\n'
        else:
            message = 'NEW LISTING - ' + listing[2] + '\n'
        message = message + listing[2] + '\n$' + str(listing[3]) + '\n' + listing[4] + '\n' + listing[5]
        bot.send_message(chat_id=listing[0], text=message)
        cur.execute("update results set notification_sent = ? where pid = ? and request_id = ?", (str_time,listing[6],listing[7]))
        con.commit()
    con.close()