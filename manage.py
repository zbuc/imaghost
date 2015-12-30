#!/usr/bin/env python

from __future__ import (absolute_import, print_function, division)
import imp
import os
import inspect


class MigrationError(Exception):
    pass


from flask import g
from flask.ext.script import Manager

from ghost import app
from interfaces.db import db_conn
from ghost_exceptions import NotImplementedException

manager = Manager(app)


# create an empty migrations table
def create_migrations_table():
    db_conn.execute('''CREATE TABLE migrations (id INTEGER PRIMARY KEY,
        run_date TEXT)''')


# find the last-run migration. returns 0 if none run.
def find_max_migration():
    c = db_conn.execute('''SELECT * FROM migrations ORDER BY id DESC
                        LIMIT 1''')
    row = c.fetchone()
    if not row:
        return 0
    else:
        return row[0]


# returns migrations > max_migration found in the db_migrations module
# they should be named migration_#.py
def find_migrations(max_migration=0):
    cmd_folder = os.path.realpath(os.path.abspath(os.path.split(
        inspect.getfile(inspect.currentframe()))[0]))

    migrations = []
    i = max_migration + 1
    while True:
        try:
            mig = imp.find_module('migration_%d' % i,
                                  [cmd_folder + '/db_migrations'])
            migrations.append((i, 'migration_%d' % i, mig))
        except ImportError:
            print("Found %d migration(s)" % len(migrations))
            return migrations

        i += 1


def mark_migration_complete(migration_id):
    db_conn.execute('''INSERT INTO migrations (id, run_date) VALUES
                    (?, datetime('now'))''', (migration_id,))


def execute_migrations(migrations):
    print("Executing %d migrations" % len(migrations))
    for migration in migrations:
        name = migration[1]
        filehandle = migration[2][0]
        pathname = migration[2][1]
        description = migration[2][2]
        # print("Name: %s\nFile: %s\nPathname: %s\nDescription: %s" %
        #       (name, filehandle, pathname, description))
        try:
            module = imp.load_module(name, filehandle, pathname, description)
            module.migrate(db_conn)
            mark_migration_complete(migration[0])
            g.db_modified = True
        except Exception, e:
            raise MigrationError("Error running %s: %s" % (name, e))


@manager.command
def setup_db():
    # running every db migration in order should get us an up-to-date DB
    db_conn.execute("BEGIN TRANSACTION")
    c = db_conn.execute('''SELECT name FROM sqlite_master
                        WHERE type="table" AND name="migrations"''')
    if not c.fetchone():
        # no migrations table present, let's start fresh
        print("No migrations table found, creating")
        create_migrations_table()

    max_migration = find_max_migration()
    print("Found migrations table, running from migration %d" %
          max_migration)

    migrations = find_migrations(max_migration)
    execute_migrations(migrations)


if __name__ == "__main__":
    manager.run()
