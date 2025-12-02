import sqlite3
import os

def get_product_by_name_or_code(conn, mode, value):
    """Fetches the product row for given mode/value."""
    c = conn.cursor()
    if mode == 'name':
        c.execute("SELECT name, unique_code FROM products WHERE name = ?", (value,))
    elif mode == 'code':
        c.execute("SELECT name, unique_code FROM products WHERE unique_code = ?", (value,))
    else:
        return []
    return c.fetchall()

def delete_product():
    print("Delete Product Options:")
    print("1. Delete by Product Name")
    print("2. Delete by Unique Code")
    choice = input("Select option (1/2): ").strip()

    conn = sqlite3.connect('products.db')

    if choice == '1':
        name = input("Enter the EXACT product name: ").strip()
        products = get_product_by_name_or_code(conn, 'name', name)
        for pname, code in products:
            img_path = f"qr_codes/{pname}_{code}.png"
            if os.path.exists(img_path):
                os.remove(img_path)
                print(f"Deleted image: {img_path}")

        c = conn.cursor()
        c.execute("DELETE FROM products WHERE name = ?", (name,))
        conn.commit()
        print(f"Product(s) named '{name}' deleted (if present).")

    elif choice == '2':
        code = input("Enter the unique code: ").strip()
        products = get_product_by_name_or_code(conn, 'code', code)
        for pname, code in products:
            img_path = f"qr_codes/{pname}_{code}.png"
            if os.path.exists(img_path):
                os.remove(img_path)
                print(f"Deleted image: {img_path}")

        c = conn.cursor()
        c.execute("DELETE FROM products WHERE unique_code = ?", (code,))
        conn.commit()
        print(f"Product with code '{code}' deleted (if present).")

    else:
        print("Not a valid option! Please choose 1 or 2.")

    conn.close()

if __name__ == "__main__":
    delete_product()
