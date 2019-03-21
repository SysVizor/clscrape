"""
    Claigslist Scraping
    -------------------
    Functions for program. Called by main and manage

    python-telegram-bot is required for notifications
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
    """
        Check if the database exists.
        Create a new one if not found
    """
    if os.path.isfile(db) == False:
        print("Creating new database. This may take a while...")
        # Create new database
        con = sqlite3.connect(db)
        cur = con.cursor()
        # Create tables
        index = 0
        print("Creating request table")
        cur.execute('''CREATE TABLE requests (
            id integer,
            loc_id integer,
            telegram_id text,
            email text,
            cat_id integer,
            query text,
            created text
        )''')
        con.commit()
        print("Creating results table")
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
        print("Creating category table")
        cur.execute('''CREATE TABLE category (
            id integer,
            parent_id integer,
            description text,
            value text,
            usage_index integer
        )''')
        con.commit()
        print("Creating location table")
        cur.execute('''CREATE TABLE location (
            id integer,
            description text,
            value text,
            usage_index integer
        )''')
        # Add Categories to Category table
        index = 0
        category = [('ccc','community'),
        ('eee','events'),('sss','for sale'),
        ('ggg','gigs'),('hhh','housing'),
        ('jjj','jobs'),('rrr','resumes'),('bbb','services')]
        # Add base categories
        for i in category:
            cur.execute('insert into category values (?,?,?,?,?)', (index,None,i[1],i[0],0))
            con.commit()
            print("Added",i[1], "to category table")
            index += 1
        # Add subcategories
        data = requests.get('https://newyork.craigslist.org/')
        main = BeautifulSoup(data.text, 'html.parser')
        category = main.find('div', {'id': 'center'})
        for p_cat in category.find_all('ul'):
            parent = p_cat['id'][:-1]
            if parent != 'forums':
                for li in p_cat.find_all('li'):
                    for a in li.find_all('a'):
                        value = a['href'][-3:].strip()
                        description = a.text.strip()
                        cur.execute('select id from category where value = ?', (parent,))
                        p_id = cur.fetchone()[0]
                        cur.execute('insert into category values (?,?,?,?,?)', (index,p_id,description,value,0))
                        con.commit()
                        print("Added", description, "to category table")
                        index += 1
        # Add Locations to Location table
        index = 0
        data = requests.get('https://geo.craigslist.org/iso/us')
        main = BeautifulSoup(data.text, 'html.parser')
        ul = main.find('ul', {'class': 'height6 geo-site-list'})
        for city in ul.find_all('a'):
            value = city['href'].strip()
            description = city.text.strip()
            cur.execute('insert into location values (?,?,?,?)', (index,description,value,0))
            con.commit()
            print("Added", description, "to location table")
            index += 1
        con.close()
        print("Database created successfully!")

def db_add_loc(db,href,description):
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute('select id from location order by id desc limit 1')
    index = int(cur.fetchone()[0]) + 1
    cur.execute('insert into location values (?,?,?,?)', (index,description,href,1000))
    con.commit()
    con.close()

def db_add_req(db,reqLoc,telegram_id,email,cat,query):
    """
        Add a request to database
    """
    str_time = time.strftime('%Y-%m-%d %H:%M')
    pk = time.strftime('%Y%m%d%H%M%S') + str(random.randint(100,999))
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute('insert into requests values (?,?,?,?,?,?,?)', (pk,reqLoc,telegram_id,email,cat,query,str_time))
    con.commit()
    cur.execute('select usage_index from category where id = ?', (cat,))
    c_usage = int(cur.fetchone()[0]) + 1
    cur.execute('update category set usage_index = ? where id = ?', (c_usage, cat))
    con.commit()
    cur.execute('select usage_index from location where id = ?', (reqLoc,))
    l_usage = int(cur.fetchone()[0]) + 1
    cur.execute('update location set usage_index = ? where id = ?', (l_usage, reqLoc))
    con.commit()
    con.close()
    return pk

def page_parse(db, request_new, request_id):
    """
        Scrape listings for request
    """
    con = sqlite3.connect(db)
    cur = con.cursor()
    # Get request details
    cur.execute('''select l.value, c.value, rq.query
        from requests rq
        inner join location l on rq.loc_id = l.id
        inner join category c on rq.cat_id = c.id
        where rq.id = ?''', (request_id,))
    q = cur.fetchone()
    # Fetch page
    uri = q[0] + '/search/' + q[1] + '?query=' + q[2].replace(" ", "%20") + '&sort=rel'
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

def db_fetch(db, tble, cols):
    """
        Get table from database
    """
    q = "select " + str(cols) + " from " + str(tble)
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute(q)
    res = cur.fetchall()
    con.close()
    return res

def db_del_row(db, tble, selected):
    """
        Remove a request from database
    """
    q = "delete from " + tble + " where id = ?"
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute(q, (selected,))
    con.commit()
    con.close()

def db_result_purge(db):
    """
        Purge entires from results where request no longer exists
    """
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
    """
        Remove entires from results where listing no longer active
    """
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
    """
        Send a notification via telegram
    """
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