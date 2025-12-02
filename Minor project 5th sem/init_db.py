import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unique_code TEXT NOT NULL UNIQUE
)
''')

conn.commit()
conn.close()
print("Database and table created successfully!")
