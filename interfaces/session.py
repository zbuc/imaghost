from __future__ import (absolute_import, print_function, division)

import os
import errno
import sqlite3
from uuid import uuid4
from json import dumps, loads
from collections import MutableMapping

from flask.sessions import SessionInterface, SessionMixin
from flask import g

from interfaces.db import db_conn
from ghost_exceptions import NotImplementedException


class SqliteSession(MutableMapping, SessionMixin):
    _get_sql = 'SELECT val FROM sessions WHERE key = ?'
    _set_sql = 'REPLACE INTO sessions (key, val) VALUES (?, ?)'
    _del_sql = 'DELETE FROM sessions WHERE key = ?'
    _ite_sql = 'SELECT key FROM sessions'
    _len_sql = 'SELECT COUNT(*) FROM sessions'

    def __init__(self, sid, *args, **kwargs):
        self.sid = sid
        self.modified = False

    def __getitem__(self, key):
        key = dumps(key, 0)
        rv = None
        for row in db_conn.execute(self._get_sql, (key,)):
            rv = loads(str(row[0]))
            break
        if rv is None:
            raise KeyError('Key not in this session')
        return rv

    def __setitem__(self, key, value):
        key = dumps(key, 0)
        value = buffer(dumps(value, 2))
        db_conn.execute(self._set_sql, (key, value))
        self.modified = True

    def __delitem__(self, key):
        key = dumps(key, 0)
        db_conn.execute(self._del_sql, (key,))
        self.modified = True

    def __iter__(self):
        for row in db_conn.execute(self._ite_sql):
            yield loads(str(row[0]))

    def __len__(self):
        for row in db_conn.execute(self._len_sql):
            return row[0]

    # These proxy classes are needed in order
    # for this session implementation to work properly.
    # That is because sometimes flask will chain method calls
    # with session'setdefault' calls.
    # Eg: session.setdefault('_flashes', []).append(1)
    # With these proxies, the changes made by chained
    # method calls will be persisted back to the sqlite
    # database.
    class CallableAttributeProxy(object):
        def __init__(self, session, key, obj, attr):
            self.session = session
            self.key = key
            self.obj = obj
            self.attr = attr

        def __call__(self, *args, **kwargs):
            rv = self.attr(*args, **kwargs)
            self.session[self.key] = self.obj
            return rv

    class PersistedObjectProxy(object):
        def __init__(self, session, key, obj):
            self.session = session
            self.key = key
            self.obj = obj

        def __getattr__(self, name):
            attr = getattr(self.obj, name)
            if callable(attr):
                return SqliteSession.CallableAttributeProxy(
                    self.session, self.key, self.obj, attr)
            return attr

    def setdefault(self, key, value):
        if key not in self:
            self[key] = value
            self.modified = True
        return SqliteSession.PersistedObjectProxy(
            self, key, self[key])


class SqliteSessionInterface(SessionInterface):
    def __init__(self):
        pass

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = str(uuid4())
        rv = SqliteSession(sid)
        return rv

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        cookie_exp = self.get_expiration_time(app, session)
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True, domain=domain)
