from __future__ import (absolute_import, print_function, division)
import bcrypt

from flask import g

from . import Model
from interfaces.db import db_conn
from ghost_exceptions import NotImplementedException


def hash_password(password):
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed


class User(Model):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.admin = kwargs.get('admin', 0)
        self.pwhash = kwargs.get('pwhash', None)

        if kwargs.get('password'):
            self.set_password(kwargs.get('password'))

    def set_password(self, password):
        self.pwhash = hash_password(password)

    def save(self):
        # existing user
        if self.id:
            db_conn.execute('''SELECT * FROM users WHERE id = ?''', self.id)
            raise NotImplementedException('''can't modify users yet''')

        db_conn.execute('''INSERT INTO users (name, admin, pwhash) VALUES
                        (?, ?, ?)''', (self.name, self.admin, self.pwhash))

        g.db_modified = True
