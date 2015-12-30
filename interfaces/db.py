from __future__ import (absolute_import, print_function, division)

import sqlite3

from flask import g
from werkzeug.local import LocalProxy


def get_db_conn():
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is None:
        g.db_conn = db_conn = sqlite3.connect('data/example.db',
                                              isolation_level=None)
    return db_conn


db_conn = LocalProxy(get_db_conn)
