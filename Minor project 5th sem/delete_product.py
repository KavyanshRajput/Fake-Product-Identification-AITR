# delete_product.py
import os
import sqlite3

DB_PATH = "products.db"


def delete_product_by_id(product_id):
    """
    Deletes a product row by id and removes its QR image file if qr_url is set.
    To be called from a Flask route /delete_product/<id>.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get QR path first (if any)
    c.execute("SELECT qr_url FROM products WHERE id = ?", (product_id,))
    row = c.fetchone()

    if row:
        qr_url = row["qr_url"]  # stored like "/qr_codes/filename.png"
        if qr_url:
            # Strip leading "/" and build full path
            file_path = qr_url.lstrip("/")
            if os.path.exists(file_path):
                os.remove(file_path)

        # Delete from DB
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()

    conn.close()
