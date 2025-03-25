import sqlite3

__all__ = ['init_db', 'is_image_exist', 'insert_image', 'close_db']

def init_db():
    conn = sqlite3.connect('pinterest_images.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (url TEXT PRIMARY KEY, scale TEXT)''')
    conn.commit()
    return conn

def is_image_exist(conn, url):
    c = conn.cursor()
    c.execute("SELECT url FROM images WHERE url=?", (url,))
    return c.fetchone() is not None

def insert_image(conn, url, scale=None):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO images (url, scale) VALUES (?, ?)", (url, scale))
    conn.commit()

def close_db(conn):
    conn.close()