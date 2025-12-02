import sqlite3
import uuid
import qrcode
import os

# Ensure qr_codes folder exists
if not os.path.exists("qr_codes"):
    os.makedirs("qr_codes")

product_name = input("Enter product name: ")
unique_code = str(uuid.uuid4())

# Store in database
conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute("INSERT INTO products (name, unique_code) VALUES (?, ?)", (product_name, unique_code))
conn.commit()
conn.close()

# Generate QR code for verification URL (web app link to be built next)
verify_url = f"http://192.168.1.2:5000/verify/{unique_code}"

img = qrcode.make(verify_url)
img.save(f"qr_codes/{product_name}_{unique_code}.png")

print(f"Product registered! QR Code saved as {product_name}_{unique_code}.png")
print(f"Verification URL: {verify_url}")
