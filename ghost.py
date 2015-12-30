#!/usr/bin/env python

# an easy to use and lightweight web-accessible local storage server

import ssl
import sqlite3
from flask import Flask, Response, request, abort, g
from werkzeug.local import LocalProxy
app = Flask(__name__)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('ssl/imag.host.key.crt', 'ssl/imag.host.key')


def get_db_conn():
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is None:
        g.db_conn = db_conn = sqlite3.connect('data/example.db', isolation_level=None)
    return db_conn


db_conn = LocalProxy(get_db_conn)


@app.teardown_appcontext
def close_db_conn(error):
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is None:
        return

    if error is None:
        print("Committing database changes...")
        db_conn.execute("COMMIT")
    else:
        print("Rolling back database changes...")
        db_conn.execute("ROLLBACK")

    db_conn.close()
    g.db_conn = None


@app.route('/')
def index():
    cur = db_conn.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_file():
    if not session.get('logged_in'):
        abort(401)
    db_conn.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    db_conn.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=9666,
            debug=True, ssl_context=context)
