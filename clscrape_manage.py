"""
    Craigslist Scraping
    -------------------
    Managing Request entries and viewing results though web portal

    This utilizes Flask for the web framework.
    http://flask.pocoo.org/

    pip install Flask

    Use localhost:5000 to access if launching locally.
"""
import flask
import os
import clscrape

# If the database name is changed, be sure it matches the name in clscrape_main.py
db = 'clscrape.db'

app = flask.Flask(__name__)

# Check if database exists
clscrape.db_check(db)

@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
def home():
    return flask.render_template('home.html')

@app.route("/results")
def res():
    listings = []
    for row in clscrape.db_fetch(db, 'results', '*'):
        listings.append(
            {
                'pid' : row[0],
                'repost' : row[1],
                'listing_created' : row[2],
                'title' : row[3],
                'href' : row[4],
                'price' : row[5],
                'loc' : row[6],
                'request_id' : row[7],
                'notification_sent' : row[8]
            }
        )
    return flask.render_template('results.html', listings=listings)

@app.route("/requests")
def req():
    requests = []
    for row in clscrape.db_fetch(db, '''requests rq
        left join location l on rq.loc_id = l.id
        left join category c on rq.cat_id = c.id ''', '''rq.id, l.description,
        rq.telegram_id, rq.email, c.description, rq.query, rq.created'''):
        requests.append(
            {
                'id' : row[0],
                'reqLoc' : row[1],
                'telegram_id' : row[2],
                'email' : row[3],
                'categrory': row[4],
                'query' : row[5],
                'created' : row[6]
            }
        )
    cats = []
    for row in clscrape.db_fetch(db, '''category c1 left join category c2 on c2.id = c1.parent_id
        order by c1.usage_index desc, c2.description, c1.description''',\
        'c1.id, c2.description, c1.description'):
        if row[1] == None:
            desc = row[2]
        else: desc = row[1] + '-' + row[2]
        cats.append(
            {
                'id': row[0],
                'description': desc
            }
        )
    locs = []
    for row in clscrape.db_fetch(db, 'location order by usage_index desc, description', 'id, description'):
        locs.append(
            {
                'id': row[0],
                'description': row[1]
            }
        )
    return flask.render_template('requests.html', requests=requests, cats=cats, locs=locs)

@app.route("/delReq")
def delReq():
    for selected in flask.request.args.getlist('selector'):
        clscrape.db_del_row(db, 'requests', selected)
    clscrape.db_result_purge(db)
    return flask.redirect('/requests')

@app.route("/addReq")
def addReq():
    telegram_id = flask.request.args.get('telegram_id')
    email = flask.request.args.get('email')
    reqLoc = flask.request.args.get('reqLoc')
    cat = flask.request.args.get('cat').strip()
    query = flask.request.args.get('query').strip()
    pk = clscrape.db_add_req(db,reqLoc,telegram_id,email,cat,query)
    clscrape.page_parse(db, True, pk)
    return flask.redirect('/requests')

@app.route("/delLoc")
def delLoc():
    selected = flask.request.args.get('reqLoc')
    clscrape.db_del_row(db,'location', selected)
    return flask.redirect('/requests')

@app.route("/addLoc")
def addLoc():
    locURL = flask.request.args.get('locURL')
    locDesc = flask.request.args.get('locDesc')
    clscrape.db_add_loc(db,locURL,locDesc)
    return flask.redirect('/requests')

if __name__ == '__main__':
    app.run(debug=True)