import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()

print("ID\tProduct Name\tUnique Code")
print("-" * 50)
for row in c.execute("SELECT id, name, unique_code FROM products"):
    print(f"{row[0]}\t{row[1]}\t{row[2]}")

conn.close()
