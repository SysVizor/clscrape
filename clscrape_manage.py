"""
    Craigslist Scraping
    -------------------
    Managing Request entries and viewing results though web portal

    This utilizes Flask for the web framework.
    http://flask.pocoo.org/

    pip install Flask

    Use localhost:5000 if launching locally.
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
    for row in clscrape.db_fetch(db, 'results'):
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
    for row in clscrape.db_fetch(db, 'requests'):
        requests.append(
            {
                'id' : row[0],
                'reqLoc' : row[1],
                'telegram_id' : row[2],
                'query' : row[3],
                'created' : row[4]
            }
        )
    return flask.render_template('requests.html', requests=requests)

@app.route("/delReq")
def delReq():
    for selected in flask.request.args.getlist('selector'):
        clscrape.db_del_req(db, selected)
    clscrape.db_result_purge(db)
    return flask.redirect('/requests')

@app.route("/addReq")
def addReq():
    telegram_id = flask.request.args.get('telegram_id')
    reqLoc = flask.request.args.get('reqLoc')
    query = flask.request.args.get('query')
    pk = clscrape.db_add_req(db,reqLoc,telegram_id,query)
    clscrape.page_parse(db, True, pk)
    return flask.redirect('/requests')

if __name__ == '__main__':
    app.run(debug=True)