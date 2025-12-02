import os
import uuid
import qrcode
from io import BytesIO
from flask import (
    Flask, render_template, render_template_string,
    request, redirect, url_for, session, send_file
)
from flask_mysqldb import MySQL

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
app.secret_key = "your-super-secret-key"

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Kavyansh@123'
app.config['MYSQL_DB'] = 'fakeproductdb'
mysql = MySQL(app)

@app.route("/")
def home():
    return redirect(url_for('auth'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    login_error = ""
    register_error = ""
    register_msg = ""
    if request.method == "POST":
        if 'login_submit' in request.form:
            company = request.form.get("company_login", "").strip()
            password = request.form.get("password_login", "").strip()
            cur = mysql.connection.cursor()
            cur.execute("SELECT password FROM companies WHERE company = %s", (company,))
            row = cur.fetchone()
            cur.close()
            if row and row[0] == password:
                session['company'] = company
                return redirect(url_for("dashboard"))
            else:
                login_error = "Invalid login. Please try again!"
        elif 'register_submit' in request.form:
            company = request.form.get("company_register", "").strip()
            password = request.form.get("password_register", "").strip()
            if not company or not password:
                register_error = "Both fields are required."
            else:
                cur = mysql.connection.cursor()
                try:
                    cur.execute('INSERT INTO companies (company, password) VALUES (%s, %s)', (company, password))
                    mysql.connection.commit()
                    cur.close()
                    register_msg = "Company successfully registered! Please log in."
                except Exception as e:
                    cur.close()
                    register_error = "Company name already exists."
    return render_template('auth.html',
                          login_error=login_error,
                          register_error=register_error,
                          register_msg=register_msg)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    error = ""
    msg = ""
    if request.method == 'POST':
        company = request.form.get('company', '').strip()
        new_password = request.form.get('new_password', '').strip()
        if not company or not new_password:
            error = "Both fields are required."
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM companies WHERE company = %s", (company,))
            row = cur.fetchone()
            if not row:
                error = "Company not found."
            else:
                cur.execute("UPDATE companies SET password = %s WHERE company = %s", (new_password, company))
                mysql.connection.commit()
                cur.close()
                msg = "Password reset successful! Please log in."
    return render_template('reset_password.html', error=error, msg=msg)

@app.route('/dashboard')
def dashboard():
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))
    cur = mysql.connection.cursor()
    query = "SELECT id, name, unique_code FROM products WHERE registered_by = %s"
    cur.execute(query, (company,))
    products = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', company=company, products=products)

@app.route('/register-product', methods=['GET', 'POST'])
def register_product():
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))
    error = ""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            error = "Please provide the product name."
        else:
            unique_code = str(uuid.uuid4())
            cur = mysql.connection.cursor()
            try:
                query = "INSERT INTO products (name, unique_code, registered_by) VALUES (%s, %s, %s)"
                cur.execute(query, (name, unique_code, company))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('dashboard'))
            except Exception as e:
                cur.close()
                error = "An error occurred, possibly duplicate unique code."
    return render_template('register_product.html', error=error)

# --- NEW: Delete Product ---
@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id = %s AND registered_by = %s", (product_id, company))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard'))

# --- NEW: Update Product ---
@app.route('/update-product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM products WHERE id = %s AND registered_by = %s", (product_id, company))
    row = cur.fetchone()
    error = ""
    if not row:
        cur.close()
        return redirect(url_for('dashboard'))
    name = row[0]
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        if not new_name:
            error = "Product name cannot be empty."
        else:
            cur.execute("UPDATE products SET name = %s WHERE id = %s AND registered_by = %s", (new_name, product_id, company))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('dashboard'))
    cur.close()
    return render_template('update_product.html', name=name, error=error, product_id=product_id)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Product Verification</title>
</head>
<body>
    <h2>{{ message }}</h2>
</body>
</html>
"""

@app.route("/verify/<unique_code>")
def verify(unique_code):
    cur = mysql.connection.cursor()
    query = "SELECT name FROM products WHERE unique_code = %s"
    cur.execute(query, (unique_code,))
    product = cur.fetchone()
    cur.close()
    if product:
        return render_template_string(HTML_TEMPLATE, message=f"Product '{product[0]}' is REAL.")
    else:
        return render_template_string(HTML_TEMPLATE, message="Product NOT FOUND. This may be FAKE.")

@app.route('/product/<int:product_id>/qr')
def show_qr(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT unique_code FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    if not product:
        return "Product not found", 404
    unique_code = product[0]
    verify_url = f"http://192.168.29.238:5000/verify/{unique_code}"
      # Set to your actual LAN IP
    img = qrcode.make(verify_url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/testdb')
def testdb():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return "Database connection SUCCESSFUL!"
    except Exception as e:
        return f"Database connection FAILED: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
