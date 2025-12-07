# list_product.py
import sqlite3

DB_PATH = "products.db"


def get_all_products():
    """
    Returns a list of dicts:
    [
      { "id": 1, "name": "...", "brand": "...", "batch": "...",
        "category": "...", "code": "...", "description": "...", "qr_url": "..." },
      ...
    ]
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    c = conn.cursor()

    c.execute("""
        SELECT id, name, brand, batch, category, code, description, qr_url
        FROM products
        ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()

    products = [dict(row) for row in rows]
    return products
