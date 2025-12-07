# init_db.py  -> safe, does NOT delete data
import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    batch TEXT,
    category TEXT,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    qr_url TEXT
)
''')

conn.commit()
conn.close()
print("Database and products table verified successfully!")
