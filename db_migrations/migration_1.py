from models import user


# create the basic tables
def migrate(db_conn):
    db_conn.execute('''CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        admin INTEGER,
                        pwhash TEXT
                    )''')

    db_conn.execute('''CREATE TABLE files (
                        id INTEGER PRIMARY KEY,
                        filename TEXT,
                        add_date TEXT,
                        owner INTEGER,
                        FOREIGN KEY(owner) REFERENCES users(id)
                    )''')

    db_conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        key TEXT PRIMARY KEY,
                        val BLOB
                    )''')

    admin = user.User(name='admin', admin=1, password='password')
    admin.save()
