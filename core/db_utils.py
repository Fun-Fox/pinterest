import sqlite3

__all__ = ['init_db', 'is_image_exist', 'insert_image', 'close_db']


def init_db():
    conn = sqlite3.connect('db/pinterest_images.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (url TEXT PRIMARY KEY, scale TEXT,task_dir TEXT)''')
    conn.commit()
    return conn


def is_image_exist(conn, url):
    c = conn.cursor()
    c.execute("SELECT url,task_dir  FROM images WHERE url=?", (url,))
    return c.fetchone()


def insert_image(conn, url, task_dir, scale=None, ):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO images (url, scale,task_dir) VALUES (?, ?,?)", (url, scale, task_dir))
    conn.commit()


def close_db(conn):
    conn.close()
